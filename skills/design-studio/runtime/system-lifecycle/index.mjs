import { createHash } from 'node:crypto';
import { parseStrictJson } from '../json.mjs';
import { realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { validateDesignIntent } from '../design-intent/index.mjs';
import { validateDesignAuthority, inspectDesignAuthority, checkDesignAuthorityParity } from '../design-authority/index.mjs';
import { validateDocumentVisualContract } from '../document-contract/index.mjs';

export class SystemLifecycleInputError extends Error {
  constructor(message) { super(message); this.name = 'SystemLifecycleInputError'; }
}

// Logical output names, not a second design authority. The host maps these to
// its proven project paths and supplies null for an observed absent output.
const OUTPUTS = ['design', 'designDna', 'tokensCss', 'skillDesign', 'skillTokensCss',
  'skillIndex', 'skillDesignDna', 'documentVisualContract', 'skillDocumentVisualContract'];
const normalise = (text) => text.replace(/\r\n?/g, '\n');
const digest = (text) => createHash('sha256').update(normalise(text)).digest('hex');
const canonical = (value) => JSON.stringify(value, (_key, item) =>
  item && typeof item === 'object' && !Array.isArray(item)
    ? Object.fromEntries(Object.keys(item).sort().map((key) => [key, item[key]])) : item);
const equal = (a, b) => canonical(a) === canonical(b);
const fail = (message) => { throw new SystemLifecycleInputError(message); };
function object(value, at, keys) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${at} must be an object`);
  if (keys && !equal(Object.keys(value).sort(), [...keys].sort())) fail(`${at} has missing or unknown fields`);
  return value;
}
function string(value, at) {
  if (typeof value !== 'string' || !value.trim()) fail(`${at} must be a non-empty string`);
  return value;
}
function path(value) {
  string(value, 'evidence path');
  if (/[:\\\x00-\x1f]/.test(value) || value.split('/').some((part) => !part || part === '.' || part === '..')) {
    fail('evidence path must be project-relative');
  }
  return value;
}
function record(value, at) {
  object(value, at, ['path', 'content']);
  path(value.path);
  string(value.content, `${at}.content`);
  let data;
  try { data = parseStrictJson(value.content); } catch (error) { fail(`${at}: ${error.message}`); }
  return { data: object(data, at), reference: { path: value.path, sha256: digest(value.content) } };
}
function manifest(bundle, at) {
  object(bundle, at, OUTPUTS);
  return Object.fromEntries(OUTPUTS.map((key) => [key,
    bundle[key] === null ? null : digest(string(bundle[key], `${at}.${key}`))]));
}
function verifyBundle(bundle) {
  const { profile } = validateDesignAuthority(bundle.design);
  const parity = checkDesignAuthorityParity(bundle.design, {
    tokensCss: bundle.tokensCss, skillTokensCss: bundle.skillTokensCss,
    skillDesign: bundle.skillDesign, skillIndex: bundle.skillIndex,
    designDna: bundle.skillDesignDna,
    ...(bundle.skillDocumentVisualContract === null ? {} : { documentVisualContract: bundle.skillDocumentVisualContract }),
  });
  if (parity.status !== 'verified-parity') fail(`consumer parity failed: ${JSON.stringify(parity.findings)}`);
  if (digest(string(bundle.designDna, 'designDna')) !== digest(bundle.skillDesignDna)) fail('project and skill DNA differ');
  const linked = !!profile.links.documentVisualContract;
  if (linked !== (bundle.documentVisualContract !== null) || linked !== (bundle.skillDocumentVisualContract !== null)) {
    fail('document contract must be linked and present in both consumers, or absent from both');
  }
  if (linked) {
    if (digest(bundle.documentVisualContract) !== digest(bundle.skillDocumentVisualContract)) fail('project and skill document contracts differ');
    const document = validateDocumentVisualContract(parseStrictJson(bundle.documentVisualContract));
    for (const [location, tokenId] of Object.entries(object(document.sharedTokenBindings ?? {}, 'shared token bindings'))) {
      string(tokenId, 'shared token ID');
      const parts = location.split('.');
      if (!['typography', 'colour', 'spacing', 'page'].includes(parts[0]) || parts.length < 2 ||
          parts.some((part) => !/^[A-Za-z][A-Za-z0-9_-]*$/.test(part)) || !Object.hasOwn(profile.tokens, tokenId)) {
        fail('shared document binding must name a document role and a portable token');
      }
      const value = parts.reduce((current, key) => current && Object.hasOwn(current, key) ? current[key] : undefined, document);
      if (value !== `{${tokenId}}`) fail('shared document roles must use symbolic portable token references');
    }
  }
  return profile;
}
function verifySurfaceProof(request, acceptance, rows) {
  const { data: accepted } = acceptance;
  if (accepted.status !== 'accepted' ||
      (request.intent.lane === 'Document' ? accepted.artifactValidated !== true : accepted.serveValidated !== true) ||
      accepted.iterationIntegrity !== true ||
      !Number.isInteger(accepted.sourceIteration) || accepted.sourceIteration < 1) fail('current final-tree acceptance is required');
  const byPath = new Map(rows.map((item) => [item.reference.path, item]));
  const tree = byPath.get(accepted.treeManifest);
  if (!tree || tree.data.treePath !== accepted.selectedTree || !Object.keys(object(tree.data.files, 'tree files')).length) {
    fail('accepted tree manifest is missing or belongs to another tree');
  }
  for (const [name, hash] of Object.entries(tree.data.files)) {
    path(name);
    if (typeof hash !== 'string' || !/^[a-f0-9]{64}$/.test(hash)) fail('tree file requires SHA-256');
  }
  const mechanical = rows.find((item) => item.data.snapshotId === accepted.mechanicalSnapshotId);
  if (!mechanical || !Array.isArray(mechanical.data.passes) || !mechanical.data.passes.length ||
      mechanical.data.passes.some((pass) => !pass || pass.completed !== true) || !Array.isArray(mechanical.data.findings)) {
    fail('accepted mechanical snapshot must be current and complete');
  }
  const kind = request.intent.lane === 'Document' ? 'page-artifact' : 'browser';
  if (!mechanical.data.passes.some((pass) => pass.kind === kind)) fail('mechanical evidence has the wrong medium');
  for (const finding of mechanical.data.findings) object(finding, 'mechanical finding');
  const acknowledged = accepted.acknowledgedPrimaryFindings ?? [];
  if (!Array.isArray(acknowledged) || mechanical.data.findings.some((finding) =>
    finding.status === 'open' && finding.severity === 'primary' && !acknowledged.includes(finding.signature))) {
    fail('unacknowledged primary mechanical finding');
  }
  if (!Array.isArray(accepted.viewportEvidence) || !accepted.viewportEvidence.length) fail('rendered evidence is required');
  for (const renderPath of accepted.viewportEvidence) {
    const rendered = byPath.get(renderPath)?.data;
    if (!rendered || rendered.status !== 'verified' || !equal(rendered.treeManifest, tree.reference) ||
        !Array.isArray(rendered.evidence) || !rendered.evidence.length || rendered.evidence.some((item) => typeof item !== 'string' || !item.trim())) {
      fail('rendered evidence must be verified for the accepted tree');
    }
    if (rendered.kind !== kind || new Set(rendered.evidence).size !== rendered.evidence.length) fail('rendered medium or evidence identity is invalid');
    const sizes = kind === 'page-artifact' ? rendered.pageSizes : rendered.viewports;
    const dimensions = kind === 'page-artifact' ? ['widthMm', 'heightMm'] : ['width', 'height'];
    if (!Array.isArray(sizes) || sizes.length !== rendered.evidence.length || sizes.some((size) =>
      !size || dimensions.some((key) => !Number.isFinite(size[key]) || size[key] <= 0))) fail('measured rendered dimensions are required');
    if (kind === 'page-artifact' ? !Number.isInteger(rendered.pageCount) || rendered.pageCount !== sizes.length : sizes.length < 2) {
      fail('complete ordered pages or both interactive viewports are required');
    }
  }
}

/** Verify supplied acceptance and exact staged consumers; never mutate files or accept a rendered design. */
export function verifyDesignSystemTransition(request) {
  object(request, 'transition', ['schemaVersion', 'intent', 'before', 'candidate', 'acceptance', 'evidence', 'approval']);
  if (request.schemaVersion !== 1) fail('unsupported lifecycle schemaVersion');
  const intent = validateDesignIntent(request.intent);
  const before = manifest(request.before, 'before');
  const candidate = request.candidate === null ? null : manifest(request.candidate, 'candidate');
  const { data: approval, reference: approvalRef } = record(request.approval, 'approval');
  const acceptance = record(request.acceptance, 'acceptance');
  object(approval, 'system acceptance', ['schemaVersion', 'status', 'runId', 'intentDigest', 'systemEffect',
    'before', 'candidate', 'surfaceAcceptance', 'evidence', 'reusableRule', 'retainsVisualWorld']);
  if (approval.schemaVersion !== 1 || !['accepted', 'rejected', 'candidate'].includes(approval.status)) fail('unsupported system acceptance');
  string(approval.runId, 'approval.runId');
  if (approval.intentDigest !== digest(canonical(intent)) || approval.systemEffect !== intent.systemEffect ||
      !equal(approval.before, before) || !equal(approval.candidate, candidate) ||
      !equal(approval.surfaceAcceptance, acceptance.reference)) fail('system acceptance does not bind the intent, incumbent, candidate and surface acceptance');
  if (typeof approval.retainsVisualWorld !== 'boolean' ||
      (approval.reusableRule !== null && (typeof approval.reusableRule !== 'string' || !approval.reusableRule.trim()))) {
    fail('system acceptance requires a boolean continuity decision and a reusable rule or null');
  }
  if (!Array.isArray(request.evidence)) fail('evidence must be an array');
  const rows = request.evidence.map((item, index) => record(item, `evidence[${index}]`));
  const paths = [approvalRef.path, acceptance.reference.path, ...rows.map((row) => row.reference.path)];
  if (new Set(paths).size !== paths.length) fail('system, surface and evidence paths must be distinct');
  if (!equal(approval.evidence, rows.map((row) => row.reference))) fail('approval does not bind the supplied evidence');
  const receipt = {
    schemaVersion: 1, status: approval.status, requestedEffect: intent.systemEffect,
    plannedEffect: 'none', systemEffect: 'none', authorityBefore: before, authorityAfter: before,
    authorityRevisionBefore: before.design, authorityRevisionAfter: before.design,
    derivedOutputs: {}, invalidatedDownstream: [],
    provenance: { runId: approval.runId, intentDigest: approval.intentDigest,
      systemAcceptance: approvalRef, surfaceAcceptance: acceptance.reference, evidence: rows.map((row) => row.reference) },
  };
  if (approval.status !== 'accepted') return receipt;
  verifySurfaceProof(request, acceptance, rows);
  if (['preserve', 'none'].includes(intent.systemEffect)) {
    if (candidate && !equal(before, candidate)) fail('local work cannot change global outputs');
    return { ...receipt, status: 'unchanged', plannedEffect: intent.systemEffect, systemEffect: intent.systemEffect };
  }
  if (!['establish', 'extend', 'replace', 'extract'].includes(intent.systemEffect)) fail('unsupported transition effect');
  if (intent.systemEffect === 'establish' && Object.values(before).some((value) => value !== null)) fail('establish requires absent incumbent outputs');
  if (!candidate) fail('a system mutation requires a candidate');
  if (candidate.design === before.design) fail('a system mutation requires a new canonical authority revision');
  const profile = verifyBundle(request.candidate);
  if (intent.systemEffect === 'extend') {
    if (request.before.design === null || inspectDesignAuthority(request.before.design).status !== 'valid-profile') {
      fail('a reusable extension requires profiled authority; explicitly extract legacy conventions first');
    }
    const incumbent = verifyBundle(request.before);
    string(approval.reusableRule, 'accepted reusable rule');
    if (approval.retainsVisualWorld !== true) fail('extension requires accepted visual-world continuity');
    for (const [id, token] of Object.entries(incumbent.tokens)) {
      if (!profile.tokens[id] || ['type', 'role', 'css'].some((key) => token[key] !== profile.tokens[id][key])) {
        fail('extension cannot remove or rename established token identities; resolve a replacement intent');
      }
    }
  }
  if (before.documentVisualContract !== candidate.documentVisualContract && intent.lane !== 'Document') {
    fail('changed Document rules require Document acceptance, not browser-only proof');
  }
  if (before.documentVisualContract !== null && candidate.documentVisualContract === null) {
    fail('system publication must not discard accepted Document rules');
  }
  if (intent.lane === 'Document' && candidate.documentVisualContract === null) fail('Document system publication requires its accepted contract');
  if (intent.systemEffect === 'extract') {
    if (request.before.design !== null && inspectDesignAuthority(request.before.design).status === 'valid-profile') {
      fail('extraction cannot replace accepted profiled authority; resolve a replacement intent');
    }
    const source = rows.filter((row) => row.data.kind === 'source-inspection');
    if (source.length !== 1) fail('extraction requires one bound source inspection');
    const inspected = source[0].data;
    const tree = rows.find((row) => row.reference.path === acceptance.data.treeManifest);
    if (inspected.status !== 'verified' || !equal(inspected.treeManifest, tree.reference) ||
        inspected.candidateRevision !== candidate.design) fail('source inspection must verify this candidate and accepted tree');
    object(inspected.files, 'inspected source files');
    for (const sourcePath of profile.provenance.sourceTokenPaths) {
      if (!/^[a-f0-9]{64}$/.test(inspected.files[sourcePath] ?? '')) fail('source inspection must cover every source token path');
    }
  }
  if (profile.provenance.runId !== approval.runId || profile.provenance.acceptedIteration !== acceptance.data.sourceIteration ||
      !equal(profile.provenance.acceptance, acceptance.reference)) fail('candidate provenance must match the accepted final tree');
  return { ...receipt, status: 'verified-transition', plannedEffect: intent.systemEffect, derivedOutputs: candidate };
}

/** Validate fresh host readback and its retained transaction journal, not host I/O itself. */
export function verifyDesignSystemPublication(input) {
  object(input, 'publication input', ['request', 'observed', 'publication']);
  const verified = verifyDesignSystemTransition(input.request);
  if (verified.status !== 'verified-transition') fail('publication requires a verified mutating transition');
  const observed = manifest(input.observed, 'observed');
  const { data: journal, reference: journalRef } = record(input.publication, 'publication journal');
  if ([verified.provenance.systemAcceptance, verified.provenance.surfaceAcceptance, ...verified.provenance.evidence]
    .some((reference) => reference.path === journalRef.path)) fail('publication journal cannot overwrite acceptance or evidence');
  if (journal.schemaVersion !== 1 || journal.transitionDigest !== digest(canonical(verified)) ||
      !equal(journal.before, verified.authorityBefore) || !equal(journal.after, verified.derivedOutputs)) {
    fail('publication journal must bind the verified transition and both output manifests');
  }
  for (const guard of ['exclusiveAccess', 'incumbentRechecked', 'stageRechecked', 'rollbackReady']) {
    if (journal[guard] !== true) fail(`publication requires ${guard}`);
  }
  const receipt = { ...verified, provenance: { ...verified.provenance, publication: journalRef } };
  if (journal.status === 'rolled-back') {
    string(journal.failure, 'publication failure');
    if (!equal(observed, verified.authorityBefore)) fail('rollback incomplete: observed outputs differ from incumbent');
    return { ...receipt, status: 'rolled-back', derivedOutputs: {}, failure: journal.failure };
  }
  if (journal.status !== 'published' || journal.failure !== null) fail('publication or recovery is incomplete');
  if (!equal(observed, verified.derivedOutputs)) fail('published readback differs from accepted staged outputs');
  verifyBundle(input.observed);
  const changedIncumbent = Object.values(verified.authorityBefore).some((value) => value !== null);
  return { ...receipt, status: 'published', systemEffect: verified.plannedEffect,
    authorityAfter: observed, authorityRevisionAfter: observed.design,
    invalidatedDownstream: changedIncumbent ? [{ role: 'visual-design',
      authorityBefore: verified.authorityBefore, replacementRevision: observed.design }] : [],
  };
}

async function main() {
  const operations = { verify: verifyDesignSystemTransition, publication: verifyDesignSystemPublication };
  if (process.argv.length !== 3 || !Object.hasOwn(operations, process.argv[2])) {
    fail('usage: node index.mjs verify|publication < request.json');
  }
  let input = '';
  for await (const chunk of process.stdin) input += chunk;
  const result = operations[process.argv[2]](parseStrictJson(input));
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}
function isCliEntryPoint() {
  if (!process.argv[1]) return false;
  try { return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url)); }
  catch (error) {
    if (['ENOENT', 'ENOTDIR'].includes(error.code)) return false;
    throw error;
  }
}
if (isCliEntryPoint()) main().catch((error) => {
  process.stderr.write(`ERROR ${error.message}\n`);
  process.exitCode = error instanceof SyntaxError || error.name.endsWith('InputError') ? 2 : 1;
});
