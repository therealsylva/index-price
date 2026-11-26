#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run as root on the VPS.' >&2; exit 1; }
source_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
backend=/opt/blackbook/index-backend
node=/usr/local/bin/node
test -f "$backend/deploy/native/run.mjs"
systemctl is-active --quiet blackbook-api.service
cd "$source_root"
"$node" tools/verify.mjs
BLACKBOOK_NATIVE_BACKEND_ROOT="$backend" "$node" tests/native-index-release.test.mjs
maker_was_active=0
if systemctl is-active --quiet blackbook-maker.service; then maker_was_active=1; fi
restore_maker() {
  local status=$?
  if [[ $maker_was_active == 1 ]]; then systemctl start blackbook-maker.service || true; fi
  if [[ $status != 0 ]]; then echo 'Index update incomplete. Rerun this exact pinned release to resume; do not reset runtime or maker state.' >&2; fi
  exit "$status"
}
trap restore_maker EXIT
systemctl stop blackbook-maker.service
"$node" tools/apply_native_index_release.mjs "$source_root" "$backend"
systemctl restart blackbook-api.service
verified=0
for attempt in {1..12}; do
  if "$node" --input-type=module - <<'JS'
const response=await fetch('http://127.0.0.1:3000/v1/indices/catalog?limit=500',{signal:AbortSignal.timeout(15000)});
if(!response.ok)throw Error('index_catalog_HTTP_'+response.status);
const catalog=await response.json();
if(catalog.asOf!=='2026-11-26T00:00:00.000000Z')throw Error('index_catalog_release_not_refreshed');
console.log('API serves the verified November 26 index release.');
JS
  then verified=1; break; fi
  sleep 2
done
[[ $verified == 1 ]] || { echo 'API catalog verification failed.' >&2; exit 1; }
echo 'Index reference and band update verified; maker resumes with its existing state.'
