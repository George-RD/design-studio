import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const MECHANICAL_SCHEMA_VERSION = 1;
export const MECHANICAL_DETECTOR = 'design-studio';
export const MECHANICAL_RUNTIME_VERSION = 1;

export class MechanicalInputError extends Error {
  constructor(message) {
    super(message);
    this.name = 'MechanicalInputError';
  }
}

const SOURCE_FAILURE_RULES = [
  ['semanticControlFailures', 'semantic-control'],
  ['accessibleNameFailures', 'accessible-name'],
  ['altTextFailures', 'alternative-text'],
  ['landmarkFailures', 'document-landmark'],
  ['focusVisibilityFailures', 'focus-visibility'],
  ['placeholderLinkFailures', 'placeholder-link'],
  ['debugControlFailures', 'debug-control'],
];

const BROWSER_FAILURE_RULES = [
  ['contrastFailures', 'contrast'],
  ['clippedContentFailures', 'content-clipping'],
  ['keyboardFailures', 'keyboard-reachability'],
  ['focusFailures', 'focus-visibility'],
  ['touchTargetFailures', 'touch-target-size'],
  ['resourceFailures', 'resource-load'],
  ['fatalConsoleErrors', 'fatal-console-error'],
];

const PAGE_ARTIFACT_FAILURE_RULES = [
  ['printableAreaOverflowFailures', 'printable-area-overflow'],
  ['clippedContentFailures', 'page-content-clipping'],
  ['furnitureFailures', 'document-furniture'],
  ['printContrastFailures', 'print-contrast'],
];

function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new MechanicalInputError(`${name} must be an object`);
  }
  return value;
}

function requireBoolean(value, name) {
  if (typeof value !== 'boolean') {
    throw new MechanicalInputError(`${name} must be a boolean`);
  }
  return value;
}

function requireString(value, name, { allowEmpty = false } = {}) {
  if (typeof value !== 'string' || (!allowEmpty && !value.trim())) {
    throw new MechanicalInputError(`${name} must be ${allowEmpty ? 'a string' : 'a non-empty string'}`);
  }
  return value;
}

function requireNonNegativeInteger(value, name) {
  if (!Number.isInteger(value) || value < 0) {
    throw new MechanicalInputError(`${name} must be a non-negative integer`);
  }
  return value;
}

function requirePositiveInteger(value, name) {
  if (!Number.isInteger(value) || value <= 0) {
    throw new MechanicalInputError(`${name} must be a positive integer`);
  }
  return value;
}

function requirePositiveNumber(value, name) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) {
    throw new MechanicalInputError(`${name} must be a positive number`);
  }
  return value;
}

function requireFailureArray(value, name) {
  if (!Array.isArray(value)) {
    throw new MechanicalInputError(`${name} must be an array`);
  }
  return value.map((item, index) => {
    const entry = requireObject(item, `${name}[${index}]`);
    return {
      location: requireString(entry.location ?? 'unknown', `${name}[${index}].location`),
      value: entry.value ?? null,
      evidence: requireString(entry.evidence, `${name}[${index}].evidence`),
    };
  });
}

function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

function stableJson(value) {
  return JSON.stringify(canonicalize(value));
}

function sha256(value) {
  return `sha256:${createHash('sha256').update(value).digest('hex')}`;
}

function findingSignature({ ruleId, target, location, value }) {
  return sha256(stableJson({ ruleId, target, location, value }));
}

function createFinding({ ruleId, target, location = 'document', value = null, evidence }) {
  const finding = {
    ruleId,
    severity: 'primary',
    status: 'open',
    target,
    location,
    value,
    evidence,
    authority: null,
    reason: null,
  };
  return { signature: findingSignature(finding), ...finding };
}

function findingsFromFailureArray(target, ruleId, failures) {
  return failures.map((failure) =>
    createFinding({
      ruleId,
      target,
      location: failure.location,
      value: failure.value,
      evidence: failure.evidence,
    }),
  );
}

function evaluateSource(source) {
  const target = requireString(source.target ?? 'site source', 'source.target');
  const completed = requireBoolean(source.completed, 'source.completed');
  if (!completed) {
    return {
      pass: {
        target,
        kind: 'source',
        completed: false,
        reason: requireString(source.reason, 'source.reason'),
      },
      findings: [],
    };
  }

  const findings = [];
  const pageTitle = requireString(source.pageTitle, 'source.pageTitle', { allowEmpty: true }).trim();
  const language = requireString(source.language, 'source.language', { allowEmpty: true }).trim();
  const headingOrderValid = requireBoolean(source.headingOrderValid, 'source.headingOrderValid');
  const primaryHeadingCount = requireNonNegativeInteger(source.primaryHeadingCount, 'source.primaryHeadingCount');
  const motionPresent = requireBoolean(source.motionPresent, 'source.motionPresent');
  const reducedMotionHandled = requireBoolean(source.reducedMotionHandled, 'source.reducedMotionHandled');

  if (!pageTitle) {
    findings.push(
      createFinding({
        ruleId: 'document-title',
        target,
        value: '',
        evidence: 'The current document has no non-empty page title.',
      }),
    );
  }
  if (!language) {
    findings.push(
      createFinding({
        ruleId: 'document-language',
        target,
        value: '',
        evidence: 'The current document has no declared language.',
      }),
    );
  }
  if (!headingOrderValid) {
    findings.push(
      createFinding({
        ruleId: 'heading-order',
        target,
        value: false,
        evidence: 'Heading levels in the current document are not in a sensible order.',
      }),
    );
  }
  if (primaryHeadingCount !== 1) {
    findings.push(
      createFinding({
        ruleId: 'primary-heading-count',
        target,
        value: primaryHeadingCount,
        evidence: `Expected exactly one primary heading for this document context; observed ${primaryHeadingCount}.`,
      }),
    );
  }
  if (motionPresent && !reducedMotionHandled) {
    findings.push(
      createFinding({
        ruleId: 'reduced-motion-source',
        target,
        value: false,
        evidence: 'Motion is present without a source-level reduced-motion path.',
      }),
    );
  }

  for (const [field, ruleId] of SOURCE_FAILURE_RULES) {
    findings.push(...findingsFromFailureArray(target, ruleId, requireFailureArray(source[field], `source.${field}`)));
  }

  return {
    pass: { target, kind: 'source', completed: true },
    findings,
  };
}

function readViewport(value, name) {
  const viewport = requireObject(value, name);
  return {
    width: requirePositiveInteger(viewport.width, `${name}.width`),
    height: requirePositiveInteger(viewport.height, `${name}.height`),
  };
}

function evaluateBrowserPass(browserPass, index) {
  const name = `browser[${index}]`;
  const target = requireString(browserPass.target, `${name}.target`);
  const completed = requireBoolean(browserPass.completed, `${name}.completed`);
  if (!completed) {
    return {
      pass: {
        target,
        kind: 'browser',
        completed: false,
        reason: requireString(browserPass.reason, `${name}.reason`),
      },
      findings: [],
    };
  }

  const requestedViewport = readViewport(browserPass.requestedViewport, `${name}.requestedViewport`);
  const actualViewport = readViewport(browserPass.actualViewport, `${name}.actualViewport`);
  const scrollWidth = requireNonNegativeInteger(browserPass.scrollWidth, `${name}.scrollWidth`);
  const clientWidth = requireNonNegativeInteger(browserPass.clientWidth, `${name}.clientWidth`);
  const motionPresent = requireBoolean(browserPass.motionPresent, `${name}.motionPresent`);
  const reducedMotionVerified = requireBoolean(browserPass.reducedMotionVerified, `${name}.reducedMotionVerified`);

  const findings = [];
  if (
    actualViewport.width !== requestedViewport.width ||
    actualViewport.height !== requestedViewport.height
  ) {
    findings.push(
      createFinding({
        ruleId: 'viewport-mismatch',
        target,
        value: { requested: requestedViewport, actual: actualViewport },
        evidence: `Requested ${requestedViewport.width}x${requestedViewport.height}; observed ${actualViewport.width}x${actualViewport.height}.`,
      }),
    );
  }
  if (scrollWidth > clientWidth) {
    findings.push(
      createFinding({
        ruleId: 'horizontal-overflow',
        target,
        value: { scrollWidth, clientWidth },
        evidence: `Document scroll width ${scrollWidth}px exceeds client width ${clientWidth}px.`,
      }),
    );
  }
  if (motionPresent && !reducedMotionVerified) {
    findings.push(
      createFinding({
        ruleId: 'reduced-motion-browser',
        target,
        value: false,
        evidence: 'Rendered motion remains active or materially unchanged under reduced-motion emulation.',
      }),
    );
  }

  for (const [field, ruleId] of BROWSER_FAILURE_RULES) {
    findings.push(
      ...findingsFromFailureArray(target, ruleId, requireFailureArray(browserPass[field], `${name}.${field}`)),
    );
  }

  return {
    pass: { target, kind: 'browser', completed: true },
    findings,
  };
}

function readPageSize(value, name) {
  const pageSize = requireObject(value, name);
  return {
    name: requireString(pageSize.name, `${name}.name`),
    widthMm: requirePositiveNumber(pageSize.widthMm, `${name}.widthMm`),
    heightMm: requirePositiveNumber(pageSize.heightMm, `${name}.heightMm`),
  };
}

function evaluatePageArtifactPass(pageArtifact, index) {
  const name = `pageArtifacts[${index}]`;
  const target = requireString(pageArtifact.target, `${name}.target`);
  const completed = requireBoolean(pageArtifact.completed, `${name}.completed`);
  if (!completed) {
    return {
      pass: {
        target,
        kind: 'page-artifact',
        completed: false,
        reason: requireString(pageArtifact.reason, `${name}.reason`),
      },
      findings: [],
    };
  }

  const pageCount = requirePositiveInteger(pageArtifact.pageCount, `${name}.pageCount`);
  const pageSize = readPageSize(pageArtifact.pageSize, `${name}.pageSize`);
  const findings = [];

  for (const [field, ruleId] of PAGE_ARTIFACT_FAILURE_RULES) {
    findings.push(
      ...findingsFromFailureArray(target, ruleId, requireFailureArray(pageArtifact[field], `${name}.${field}`)),
    );
  }

  return {
    pass: { target, kind: 'page-artifact', completed: true, pageCount, pageSize },
    findings,
  };
}

function applyWaivers(findings, waivers) {
  if (!Array.isArray(waivers)) {
    throw new MechanicalInputError('waivers must be an array');
  }

  const normalizedWaivers = waivers.map((waiver, index) => {
    const item = requireObject(waiver, `waivers[${index}]`);
    return {
      ruleId: requireString(item.ruleId, `waivers[${index}].ruleId`),
      target: requireString(item.target, `waivers[${index}].target`),
      location: requireString(item.location, `waivers[${index}].location`),
      value: item.value ?? null,
      authority: requireString(item.authority, `waivers[${index}].authority`),
      reason: requireString(item.reason, `waivers[${index}].reason`),
    };
  });

  return findings.map((finding) => {
    const waiver = normalizedWaivers.find(
      (candidate) =>
        candidate.ruleId === finding.ruleId &&
        candidate.target === finding.target &&
        candidate.location === finding.location &&
        stableJson(candidate.value) === stableJson(finding.value),
    );
    if (!waiver) {
      return finding;
    }
    return {
      ...finding,
      status: 'waived',
      authority: waiver.authority,
      reason: waiver.reason,
    };
  });
}

function normalizeComparisonSnapshot(value) {
  if (value == null) {
    return null;
  }
  const snapshot = requireObject(value, 'comparisonSnapshot');
  const snapshotId = requireString(snapshot.snapshotId, 'comparisonSnapshot.snapshotId');
  if (!Array.isArray(snapshot.findings)) {
    throw new MechanicalInputError('comparisonSnapshot.findings must be an array');
  }
  const findings = snapshot.findings.map((finding, index) => {
    const item = requireObject(finding, `comparisonSnapshot.findings[${index}]`);
    return {
      signature: requireString(item.signature, `comparisonSnapshot.findings[${index}].signature`),
      ruleId: requireString(item.ruleId, `comparisonSnapshot.findings[${index}].ruleId`),
      target: requireString(item.target, `comparisonSnapshot.findings[${index}].target`),
      status: requireString(item.status, `comparisonSnapshot.findings[${index}].status`),
    };
  });
  return { snapshotId, findings };
}

export function evaluateMechanicalSnapshot(input) {
  const record = requireObject(input, 'input');
  if (record.schemaVersion !== MECHANICAL_SCHEMA_VERSION) {
    throw new MechanicalInputError(`schemaVersion must be ${MECHANICAL_SCHEMA_VERSION}`);
  }

  const generatedAt = record.generatedAt == null
    ? new Date().toISOString()
    : requireString(record.generatedAt, 'generatedAt');
  const source = evaluateSource(requireObject(record.source, 'source'));
  if (!Array.isArray(record.browser)) {
    throw new MechanicalInputError('browser must be an array');
  }
  const browser = record.browser.map((item, index) =>
    evaluateBrowserPass(requireObject(item, `browser[${index}]`), index),
  );

  const pageArtifactInput = record.pageArtifacts ?? [];
  if (!Array.isArray(pageArtifactInput)) {
    throw new MechanicalInputError('pageArtifacts must be an array');
  }
  const pageArtifacts = pageArtifactInput.map((item, index) =>
    evaluatePageArtifactPass(requireObject(item, `pageArtifacts[${index}]`), index),
  );

  const currentResults = [source, ...browser, ...pageArtifacts];
  const findings = applyWaivers(
    currentResults.flatMap((result) => result.findings),
    record.waivers ?? [],
  ).sort((left, right) => left.signature.localeCompare(right.signature));
  const passes = currentResults.map((result) => result.pass);
  const comparison = normalizeComparisonSnapshot(record.comparisonSnapshot ?? null);
  const currentSignatures = new Set(findings.map((finding) => finding.signature));
  const notReproduced = comparison
    ? comparison.findings
        .filter((finding) => !currentSignatures.has(finding.signature))
        .map((finding) => ({
          signature: finding.signature,
          ruleId: finding.ruleId,
          target: finding.target,
          previousStatus: finding.status,
          status: 'not-reproduced',
        }))
        .sort((left, right) => left.signature.localeCompare(right.signature))
    : [];

  const snapshotPayload = {
    detector: MECHANICAL_DETECTOR,
    version: MECHANICAL_RUNTIME_VERSION,
    passes,
    findings,
  };

  return {
    schemaVersion: MECHANICAL_SCHEMA_VERSION,
    detector: MECHANICAL_DETECTOR,
    version: MECHANICAL_RUNTIME_VERSION,
    snapshotId: sha256(stableJson(snapshotPayload)),
    generatedAt,
    comparisonSnapshotId: comparison?.snapshotId ?? null,
    passes,
    findings,
    notReproduced,
  };
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function main(argv) {
  if (argv.length > 2) {
    throw new MechanicalInputError('usage: node index.mjs [input.json] [output.json]');
  }
  const inputText = argv[0] ? await readFile(argv[0], 'utf8') : await readStdin();
  const result = evaluateMechanicalSnapshot(JSON.parse(inputText));
  const outputText = `${JSON.stringify(result, null, 2)}\n`;
  if (argv[1]) {
    await writeFile(argv[1], outputText, 'utf8');
  } else {
    process.stdout.write(outputText);
  }
}

const isCli = process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (isCli) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`ERROR ${error.message}\n`);
    process.exitCode = error instanceof MechanicalInputError || error instanceof SyntaxError ? 2 : 1;
  });
}
