import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {setTimeout as pause} from 'node:timers/promises';

export function planRelease({bundle,markets,pairBand,publicationHash,validatePublication,now=Date.now()}) {
  const at=Date.parse(bundle.manifest.asOf);
  if(!Number.isFinite(at)||at>now)throw Error('invalid_release_time');
  if(markets.length!==38||new Set(markets.map(m=>m.marketId)).size!==38)throw Error('expected_38_unique_markets');
  const source=new Map(bundle.rows.map(r=>[r.entityId,r]));
  const target=new Map();
  const fromRow=id=>{
    const row=source.get(id);
    if(!row||row.status==='DATA_HOLD')throw Error('release_entity_unavailable:'+id);
    return {referenceTicks:String(row.referenceMicros),lowerTicks:String(row.lowerMicros),upperTicks:String(row.upperMicros)};
  };
  for(const m of markets){
    const legs=m.kind==='PAIR'?{numerator:fromRow(m.numeratorEntityId),denominator:fromRow(m.denominatorEntityId)}:{};
    const band=m.kind==='PAIR'?pairBand(legs.numerator,legs.denominator,m.pairScaleTicks??'1000000000'):fromRow(m.entityId);
    target.set(m.marketId,{band,legs});
  }
  const publications=[];
  for(const m of markets){
    const {band,legs}=target.get(m.marketId);
    const matches=['referenceTicks','lowerTicks','upperTicks'].every(k=>String(m[k])===band[k]);
    if(matches)continue;
    if(m.phase==='kickoff')throw Error('live_match_active:'+m.symbol);
    if(m.effectiveAt&&Date.parse(m.effectiveAt)>at)throw Error('refusing_to_replace_newer_publication:'+m.symbol);
    const marketVersion=(BigInt(m.marketVersion)+1n).toString();
    const material={marketId:m.marketId,marketVersion,matchId:'index-price:'+bundle.manifest.asOf,
                    phase:'correction',sourceHash:bundle.manifestHash,...band};
    const marketHash=publicationHash(material);
    const p={...m,...material,...legs,marketHash,
      expectedMarketVersion:m.marketVersion,expectedMarketHash:m.marketHash,
      effectiveAt:bundle.manifest.asOf,verifiedComplete:true,
      terms:{...m.terms,termsVersion:(BigInt(m.terms.termsVersion)+1n).toString(),effectiveFromMarketVersion:marketVersion},
      mark:{...m.mark,marketVersion,marketHash,markSequence:'1',priceTicks:band.referenceTicks,observedAtMs:String(at)},
      bandPolicyVersion:bundle.manifest.bandPolicyVersion,
      ...(m.kind!=='PAIR'?{indexState:{densityPpm:source.get(m.entityId).densityPpm}}:{}),
    };
    validatePublication(p);publications.push(p);
  }
  return {target,publications};
}

export async function applyRelease({bundle,client,runtime,queue,publish,dependencies,onProgress=()=>{},timeoutMs=180000,delay=()=>pause(1000)}) {
  const rpc=async name=>{
    const r=await client.rpc(name);
    if(r.error)throw Error(name+':'+(r.error.code??'database_error'));
    return r.data;
  };
  const markets=await rpc('list_active_market_publications');
  const plan=planRelease({bundle,markets,...dependencies});
  const saved=await rpc('read_index_price_release');
  if(saved?.manifestText&&Date.parse(JSON.parse(saved.manifestText).asOf)>Date.parse(bundle.manifest.asOf))
    throw Error('refusing_to_replace_newer_official_index');
  // Check every live runtime fence before the first database or queue write.
  for(const market of markets){
    const snapshot=await runtime.marketSnapshot({marketId:market.marketId});
    if(snapshot.status!=='RUNNING'||snapshot.marketVersion!==market.marketVersion||snapshot.marketHash!==market.marketHash)
      throw Error('market_publication_in_progress:'+market.symbol);
  }
  onProgress({stage:'preflight_complete',markets:38,changed:plan.publications.length});
  await publish(client,bundle);
  onProgress({stage:'official_index_imported',asOf:bundle.manifest.asOf});
  for(const p of plan.publications){
    await queue(p);
    onProgress({stage:'band_update_queued',symbol:p.symbol,marketVersion:p.marketVersion});
  }
  const deadline=Date.now()+timeoutMs;
  let current;
  for(;;){
    current=await rpc('list_active_market_publications');
    if(current.length===38&&current.every(m=>{
      const target=plan.target.get(m.marketId);
      return target&&['referenceTicks','lowerTicks','upperTicks'].every(k=>String(m[k])===target.band[k]);
    }))break;
    if(Date.now()>=deadline)throw Error('band_updates_pending; rerun the same command to resume');
    await delay();
  }
  for(const m of current){
    const snapshot=await runtime.marketSnapshot({marketId:m.marketId});
    const band=plan.target.get(m.marketId).band;
    if(snapshot.status!=='RUNNING'||snapshot.marketVersion!==m.marketVersion||snapshot.marketHash!==m.marketHash||
       !['referenceTicks','lowerTicks','upperTicks'].every(k=>String(snapshot[k])===band[k]))
      throw Error('runtime_band_verification_failed:'+m.symbol);
  }
  return {asOf:bundle.manifest.asOf,markets:38,changed:plan.publications.length,
          databaseBandsVerified:true,runtimeBandsVerified:true};
}

async function main(){
  const source=resolve(process.argv[2]??'.');
  const backend=resolve(process.argv[3]??'/opt/blackbook/index-backend');
  const config=JSON.parse(readFileSync('/etc/blackbook/native.json','utf8'));
  const db=new URL(config.DATABASE_URL);
  if(config.BLACKBOOK_MODE!=='production'||db.hostname!=='127.0.0.1'||db.pathname!=='/blackbook_production')
    throw Error('expected_native_production_database');
  for(const [key,value] of Object.entries(config))process.env[key]=String(value);
  if(!config.INDEX_PUBLICATION_TOKEN||!config.TRADING_RUNTIME_TOKEN)throw Error('native_publication_tokens_missing');
  const module=path=>import(pathToFileURL(resolve(backend,path)).href);
  const [{createDatabaseClient},{loadCurrentPublicPrices},{publishIndexPrices},lifecycle,{TradingRuntimeClient}]=await Promise.all([
    module('packages/runtime/database-client.js'),module('apps/api/src/public-price-index.js'),
    module('apps/api/src/index-publish-main.js'),module('apps/api/src/market-lifecycle.js'),
    module('apps/api/src/trading-runtime-client.js'),
  ]);
  const bundle=loadCurrentPublicPrices(source);
  if(Date.parse(bundle.manifest.asOf)!==Date.parse('2026-11-04T00:00:00Z')||bundle.manifest.snapshotRows!==12351||bundle.manifest.movementRows!==15713)
    throw Error('unexpected_verified_index_release');
  const ready=await fetch('http://127.0.0.1:3000/ready',{signal:AbortSignal.timeout(10000)});
  const state=await ready.json();
  if(!ready.ok||state.mode!=='production'||state.markets?.length!==38||!state.markets.every(m=>m.status==='ready'))
    throw Error('native_api_not_ready');
  const client=createDatabaseClient();
  if(client.constructor.name!=='PostgresRpcClient')throw Error('native_postgres_client_required');
  try{
    const runtime=new TradingRuntimeClient({baseUrl:config.TRADING_RUNTIME_URL,authToken:config.TRADING_RUNTIME_TOKEN,
      fetchImpl:(url,options)=>fetch(url,{...options,signal:AbortSignal.timeout(15000)})});
    const queue=async p=>{
      const r=await fetch('http://127.0.0.1:3000/internal/index-publications',{
        method:'POST',headers:{authorization:'Bearer '+config.INDEX_PUBLICATION_TOKEN,'content-type':'application/json'},
        body:JSON.stringify(p),signal:AbortSignal.timeout(15000),
      });
      if(r.status!==202)throw Error('band_publication_rejected:'+p.symbol+':HTTP_'+r.status);
    };
    const result=await applyRelease({bundle,client,runtime,queue,publish:publishIndexPrices,
      dependencies:lifecycle,onProgress:message=>console.log(JSON.stringify(message))});
    console.log(JSON.stringify(result));
  }finally{await client.close();}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)
  main().catch(error=>{console.error(error.message);process.exitCode=1;});
