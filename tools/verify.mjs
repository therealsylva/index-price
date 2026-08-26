import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const defaultRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
if (args.includes("--help")) {
  console.log("usage: node tools/verify.mjs [--root PATH]");
  process.exit(0);
}
if (args.length !== 0 && (args.length !== 2 || args[0] !== "--root")) {
  throw new Error("usage: node tools/verify.mjs [--root PATH]");
}
const root = args.length === 2 ? resolve(args[1]) : defaultRoot;
const HEX_256 = /^[0-9a-f]{64}$/;
const ENTITY_ID = /^[A-Za-z0-9][A-Za-z0-9:._-]{0,127}$/;
const SHARD_NAME = /^(?:snapshot|movements)-[0-9]{3}\.json$/;
const SNAPSHOT_KEYS = [
  "asOf", "bandAsOf", "bandHorizonEnd", "densityPpm", "displayName", "entityId", "kind",
  "lastSportingEventAt", "lowerMicros", "priceHash", "referenceMicros", "status", "upperMicros", "version",
];
const MOVEMENT_KEYS = [
  "asOf", "entityId", "logReturnPpm", "newReferenceMicros", "previousReferenceMicros", "priceHash", "version",
];

function fail(message) {
  throw new Error(`price publication verification failed: ${message}`);
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function json(bytes, label) {
  try { return JSON.parse(bytes.toString("utf8")); }
  catch { fail(`invalid JSON in ${label}`); }
}

function exactKeys(value, expected, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(`${label} is not an object`);
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    fail(`${label} contains unexpected or missing fields`);
  }
}

function safePath(path, label) {
  if (typeof path !== "string" || path.startsWith("/") || path.includes("\\")) fail(`unsafe ${label}`);
  const absolute = resolve(root, path);
  if (relative(root, absolute).startsWith("..")) fail(`unsafe ${label}`);
  return absolute;
}

function timestamp(value, label) {
  if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) fail(`invalid ${label}`);
}

function integer(value, label, minimum = Number.MIN_SAFE_INTEGER, maximum = Number.MAX_SAFE_INTEGER) {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) fail(`invalid ${label}`);
}

function commitment(row, hashField, label) {
  if (!HEX_256.test(row[hashField] ?? "")) fail(`invalid ${label} commitment`);
  const material = { ...row };
  delete material[hashField];
  if (sha256(`${canonical(material)}\n`) !== row[hashField]) fail(`${label} commitment mismatch`);
}

const pointerBytes = readFileSync(join(root, "football", "current.json"));
const pointer = json(pointerBytes, "football/current.json");
exactKeys(pointer, ["asOf", "manifest", "manifestSha256", "publication", "schema"], "current pointer");
if (pointer.schema !== "blackbook.index.price-pointer.v1"
  || !/^\d{4}-\d{2}-\d{2}$/.test(pointer.publication ?? "")
  || pointer.manifest !== `football/${pointer.publication}/manifest.json`
  || !HEX_256.test(pointer.manifestSha256 ?? "")) fail("invalid current pointer");
timestamp(pointer.asOf, "pointer timestamp");

const manifestPath = safePath(pointer.manifest, "manifest path");
const manifestBytes = readFileSync(manifestPath);
if (sha256(manifestBytes) !== pointer.manifestSha256) fail("manifest hash mismatch");
const manifest = json(manifestBytes, pointer.manifest);
exactKeys(manifest, [
  "asOf", "automaticReferenceMovement", "bandHorizonEnd", "bandHorizonHours", "bandPolicyVersion",
  "changedEntities", "files", "friendliesIncluded", "methodologyVersion", "movementRows", "schema",
  "snapshotId", "snapshotRows", "source", "status",
], "manifest");
if (manifest.schema !== "blackbook.index.price-manifest.v1"
  || manifest.status !== "CANONICAL_PRICE_PUBLICATION"
  || manifest.methodologyVersion !== "RC3.1"
  || manifest.asOf !== pointer.asOf
  || manifest.automaticReferenceMovement !== false
  || manifest.friendliesIncluded !== false
  || manifest.bandHorizonHours !== 72
  || typeof manifest.bandPolicyVersion !== "string"
  || typeof manifest.snapshotId !== "string"
  || !Array.isArray(manifest.files)) fail("invalid manifest metadata");
timestamp(manifest.asOf, "manifest timestamp");
timestamp(manifest.bandHorizonEnd, "band horizon");
if (Date.parse(manifest.bandHorizonEnd) - Date.parse(manifest.asOf) !== 72 * 60 * 60 * 1_000) {
  fail("invalid 72-hour band horizon");
}
integer(manifest.snapshotRows, "snapshot count", 1);
integer(manifest.movementRows, "movement count", 0);
integer(manifest.changedEntities, "changed entity count", 0);
exactKeys(manifest.source, ["canonicalManifestSha256"], "manifest source");
if (!HEX_256.test(manifest.source.canonicalManifestSha256 ?? "")) fail("invalid source commitment");

const publicationDirectory = dirname(manifestPath);
const snapshotRows = [];
const movementRows = [];
const declared = new Set();
for (const file of manifest.files) {
  exactKeys(file, ["kind", "name", "rows", "sha256"], "shard declaration");
  if (!SHARD_NAME.test(file.name ?? "") || declared.has(file.name)
    || !["SNAPSHOT", "MOVEMENTS"].includes(file.kind) || !HEX_256.test(file.sha256 ?? "")) {
    fail("invalid shard declaration");
  }
  declared.add(file.name);
  integer(file.rows, "shard row count", 1);
  const shardPath = resolve(publicationDirectory, file.name);
  if (dirname(shardPath) !== publicationDirectory) fail("unsafe shard path");
  const bytes = readFileSync(shardPath);
  if (sha256(bytes) !== file.sha256) fail(`hash mismatch for ${file.name}`);
  const shard = json(bytes, file.name);
  exactKeys(shard, ["kind", "rows", "schema"], file.name);
  if (shard.schema !== "blackbook.index.price-publication.v1"
    || shard.kind !== file.kind || !Array.isArray(shard.rows) || shard.rows.length !== file.rows) {
    fail(`invalid shard ${file.name}`);
  }
  (file.kind === "SNAPSHOT" ? snapshotRows : movementRows).push(...shard.rows);
}

const entities = new Set();
for (const row of snapshotRows) {
  exactKeys(row, SNAPSHOT_KEYS, "snapshot row");
  if (!ENTITY_ID.test(row.entityId ?? "") || entities.has(row.entityId)
    || !["CLUB", "PLAYER"].includes(row.kind) || typeof row.displayName !== "string" || !row.displayName.trim()
    || !["AVAILABLE", "PARTIAL_COVERAGE", "DATA_HOLD"].includes(row.status)) fail("invalid snapshot identity");
  entities.add(row.entityId);
  timestamp(row.asOf, "snapshot timestamp");
  timestamp(row.bandAsOf, "band timestamp");
  timestamp(row.bandHorizonEnd, "row band horizon");
  timestamp(row.lastSportingEventAt, "sporting timestamp");
  if (row.asOf !== manifest.asOf || row.bandAsOf !== manifest.asOf || row.bandHorizonEnd !== manifest.bandHorizonEnd) {
    fail(`snapshot timing mismatch for ${row.entityId}`);
  }
  integer(row.version, "snapshot version", 1);
  integer(row.densityPpm, "density", 0, 1_000_000);
  integer(row.lowerMicros, "lower price", 1);
  integer(row.referenceMicros, "reference price", 1);
  integer(row.upperMicros, "upper price", 1);
  if (!(row.lowerMicros < row.referenceMicros && row.referenceMicros < row.upperMicros)) {
    fail(`invalid price band for ${row.entityId}`);
  }
  commitment(row, "priceHash", `snapshot ${row.entityId}`);
}

const movementHashes = new Set();
const changedEntities = new Set();
for (const row of movementRows) {
  exactKeys(row, MOVEMENT_KEYS, "movement row");
  if (!ENTITY_ID.test(row.entityId ?? "") || !entities.has(row.entityId)) fail("invalid movement entity");
  timestamp(row.asOf, "movement timestamp");
  if (Date.parse(row.asOf) > Date.parse(manifest.asOf)) fail(`future movement for ${row.entityId}`);
  integer(row.version, "movement version", 1);
  integer(row.previousReferenceMicros, "previous price", 1);
  integer(row.newReferenceMicros, "new price", 1);
  integer(row.logReturnPpm, "movement return");
  commitment(row, "priceHash", `movement ${row.entityId}`);
  if (movementHashes.has(row.priceHash)) fail("duplicate movement commitment");
  movementHashes.add(row.priceHash);
  changedEntities.add(row.entityId);
}

if (snapshotRows.length !== manifest.snapshotRows
  || movementRows.length !== manifest.movementRows
  || changedEntities.size !== manifest.changedEntities) fail("manifest count mismatch");

console.log(`verified ${manifest.snapshotRows.toLocaleString("en-US")} prices and ${manifest.movementRows.toLocaleString("en-US")} movements as of ${manifest.asOf}`);
