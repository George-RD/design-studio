import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { realpathSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export class DesignAuthorityInputError extends Error {
  constructor(message) {
    super(message);
    this.name = 'DesignAuthorityInputError';
  }
}

const normalise = (text) => text.replace(/\r\n?/g, '\n');

const fail = (message) => { throw new DesignAuthorityInputError(message); };
const identifier = /^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$/;
const referenceOf = (value) => value.match(/^\{([^{}]+)\}$/)?.[1] ?? null;
const types = ['color', 'dimension', 'number', 'font-family', 'duration', 'css'];

function string(value, at) {
  if (typeof value !== 'string' || !value.trim()) fail(`${at} must be a non-empty string`);
}

function object(value, at, required = [], optional = []) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${at} must be an object`);
  for (const key of required) if (!Object.hasOwn(value, key)) fail(`${at}.${key} is required`);
  if (required.length || optional.length) {
    for (const key of Object.keys(value)) {
      if (![...required, ...optional].includes(key)) fail(`unsupported field ${at}.${key}`);
    }
  }
}

function portablePath(value, at) {
  string(value, at);
  if (/[:\\\x00-\x1f]/.test(value) || value.split('/').some((part) => !part || part === '.' || part === '..')) {
    fail(`${at} must be a project-relative portable path`);
  }
}

function evidence(value, at) {
  object(value, at, ['path', 'sha256']);
  portablePath(value.path, `${at}.path`);
  if (typeof value.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(value.sha256)) {
    fail(`${at}.sha256 must be a lowercase SHA-256 digest`);
  }
}

// JSON.parse validates syntax first. This small lexical pass only rejects duplicate
// keys, including escaped spellings, instead of silently choosing the last value.
function rejectDuplicateKeys(json) {
  const lexemes = json.match(/"(?:\\.|[^"\\])*"|[{}\[\]:,]/g) ?? [];
  const stack = [];
  for (let i = 0; i < lexemes.length; i += 1) {
    const item = lexemes[i];
    if (item === '{' || item === '[') stack.push(item === '{' ? new Set() : null);
    else if (item === '}' || item === ']') stack.pop();
    else if (item.startsWith('"') && lexemes[i + 1] === ':') {
      const key = JSON.parse(item);
      if (stack.at(-1)?.has(key)) fail(`duplicate JSON key: ${key}`);
      stack.at(-1)?.add(key);
    }
  }
}

// The owned Markdown subset ignores examples and comments when looking for
// guidance or authority links. Mask comments rather than joining text across
// them; a hidden span must not manufacture a heading or link delimiter.
function visibleMarkdown(markdown) {
  let fence = null;
  let comment = false;
  let code = null;
  const lines = normalise(markdown).split('\n');
  return lines.map((raw, lineIndex) => {
    if (fence) {
      const closing = raw.match(/^ {0,3}(`{3,}|~{3,})([ \t]*)$/);
      if (closing && closing[1][0] === fence[0] && closing[1].length >= fence.length) fence = null;
      return '';
    }
    if (!comment && !code) {
      const opening = raw.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
      if (opening && (opening[1][0] !== '`' || !opening[2].includes('`'))) {
        fence = opening[1];
        return '';
      }
    }
    let line = '';
    for (let offset = 0; offset < raw.length;) {
      if (comment) {
        const end = raw.indexOf('-->', offset);
        const next = end < 0 ? raw.length : end + 3;
        line += ' '.repeat(next - offset);
        offset = next;
        if (end >= 0) comment = false;
      } else if (code) {
        const run = raw.slice(offset).match(/^`+/)?.[0];
        if (run?.length === code) code = null;
        const length = run?.length ?? 1;
        // Code has visible content, but cannot manufacture Markdown structure.
        line += 'x'.repeat(length);
        offset += length;
      } else if (raw[offset] === '\\') {
        line += raw.slice(offset, offset + 2);
        offset += 2;
      } else if (raw.startsWith('<!--', offset)) {
        comment = true;
      } else if (raw[offset] === '`') {
        const run = raw.slice(offset).match(/^`+/)[0];
        const rest = lines.slice(lineIndex).join('\n').slice(offset + run.length).split(/\n[ \t]*\n/, 1)[0];
        if ([...rest.matchAll(/`+/g)].some((closing) => closing[0].length === run.length)) {
          code = run.length;
          line += 'x'.repeat(run.length);
        } else line += run; // Unmatched delimiters are rendered literally.
        offset += run.length;
      } else {
        line += raw[offset];
        offset += 1;
      }
    }
    return line;
  }).join('\n');
}

function hasAuthorityLink(markdown) {
  // The generated index uses ordinary inline Markdown links. Bracket nesting
  // distinguishes usable links from images (including links in image alt text).
  const text = visibleMarkdown(markdown).split('\n')
    .map((line) => /^(?: {4}| {0,3}\t)/.test(line) ? '' : line).join('\n');
  const brackets = [];
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] === '\\') { index += 1; continue; }
    if (text[index] === '[') brackets.push({ index, image: text[index - 1] === '!' });
    else if (text[index] === ']') {
      const opening = brackets.pop();
      if (!opening || opening.image || brackets.some((parent) => parent.image)) continue;
      if (text.slice(opening.index + 1, index).trim() &&
          /^\((?:\.\/)?DESIGN\.md(?:#[^)\s]*)?\)/.test(text.slice(index + 1))) return true;
    }
  }
  return false;
}

function validateGuidance(body) {
  const sections = new Map();
  let current = null;
  for (const line of visibleMarkdown(body).split('\n')) {
    const heading = line.match(/^## (.+?)\s*$/)?.[1];
    if (heading) {
      if (sections.has(heading)) fail(`duplicate guidance heading: ${heading}`);
      sections.set(heading, '');
      current = heading;
    } else if (current) sections.set(current, `${sections.get(current)}\n${line}`);
  }
  for (const heading of ['Overview', 'Application guidance', 'Anti-goals', 'Ownership boundaries']) {
    if (!sections.get(heading)?.trim()) fail(`DESIGN.md requires non-empty ${heading} guidance`);
  }
}

// Deliberately bounded literal functions, not a browser CSS grammar. Unknown
// functions fail closed so new resource-loading syntax cannot bypass locality.
const literalFunctions = new Set([
  'rgb', 'rgba', 'hsl', 'hsla', 'hwb', 'lab', 'lch', 'oklab', 'oklch', 'color', 'color-mix', 'light-dark',
  'calc', 'min', 'max', 'clamp', 'round', 'mod', 'rem', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
  'atan2', 'pow', 'sqrt', 'hypot', 'log', 'exp', 'abs', 'sign',
  'linear-gradient', 'radial-gradient', 'conic-gradient',
  'repeating-linear-gradient', 'repeating-radial-gradient', 'repeating-conic-gradient',
  'cubic-bezier', 'steps', 'linear', 'repeat', 'minmax', 'fit-content',
  'translate', 'translatex', 'translatey', 'translatez', 'translate3d',
  'scale', 'scalex', 'scaley', 'scalez', 'scale3d', 'rotate', 'rotatex', 'rotatey', 'rotatez', 'rotate3d',
  'skew', 'skewx', 'skewy', 'matrix', 'matrix3d', 'perspective',
  'blur', 'brightness', 'contrast', 'drop-shadow', 'grayscale', 'hue-rotate', 'invert', 'opacity', 'saturate', 'sepia',
]);

function validateLiteral(value, id) {
  if (/[;{}<>\\\x00-\x1f@!]/.test(value) || /\/\*|\*\//.test(value) ||
      /^(?:initial|inherit|unset|revert|revert-layer)$/i.test(value.trim())) {
    fail(`token ${id} requires a literal CSS value or a tracked token reference`);
  }
  const stack = [];
  let quote = null;
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (quote) {
      if (character === quote) quote = null;
    } else if (character === '"' || character === "'") quote = character;
    else if (character === '(' || character === '[') {
      if (character === '(') {
        const name = value.slice(0, index).match(/(-?[a-zA-Z_][-a-zA-Z0-9_]*|--[-a-zA-Z0-9_]+)\s*$/)?.[1].toLowerCase();
        if ((name && !literalFunctions.has(name)) ||
            (name === 'color' && /^\s*--/.test(value.slice(index + 1)))) {
          fail(`token ${id} requires a literal CSS value or a tracked token reference`);
        }
      }
      stack.push(character);
    }
    else if (character === ')' || character === ']') {
      if (stack.pop() !== (character === ')' ? '(' : '[')) fail(`unbalanced CSS value: ${id}`);
    }
  }
  if (quote || stack.length) fail(`unbalanced CSS value: ${id}`);
}

function validateValues(tokens, overrides = {}) {
  const values = Object.fromEntries(Object.entries(tokens).map(([id, token]) => [id, token.value]));
  for (const [id, value] of Object.entries(overrides)) {
    if (!Object.hasOwn(tokens, id)) fail(`unknown theme token: ${id}`);
    values[id] = value;
  }
  const done = new Set();
  function visit(id, visiting = new Set()) {
    if (done.has(id)) return;
    if (visiting.has(id)) fail(`cyclic token reference: ${id}`);
    string(values[id], `token ${id} value`);
    const reference = referenceOf(values[id]);
    if (reference) {
      if (!Object.hasOwn(tokens, reference)) fail(`unresolved token reference: ${reference}`);
      if (tokens[id].type !== tokens[reference].type) fail(`cross-type token reference: ${id}`);
      visiting.add(id);
      visit(reference, visiting);
      visiting.delete(id);
    } else validateLiteral(values[id], id);
    done.add(id);
  }
  for (const id of Object.keys(tokens)) visit(id);
}

export function validateDesignAuthority(markdown) {
  string(markdown, 'DESIGN.md');
  const match = normalise(markdown).match(/^---\n([\s\S]*?)\n---(?:\n|$)([\s\S]*)$/);
  if (!match) fail('DESIGN.md requires JSON front matter');
  let profile;
  try { profile = JSON.parse(match[1]); } catch { fail('DESIGN.md front matter must be valid JSON'); }
  rejectDuplicateKeys(match[1]);
  object(profile, 'profile', ['profile', 'schemaVersion', 'name', 'tokens', 'provenance', 'links'], ['themes']);
  if (profile.profile !== 'design-studio/design-authority' || profile.schemaVersion !== 1) {
    fail('unsupported design authority profile');
  }
  string(profile.name, 'name');
  object(profile.tokens, 'tokens');
  if (!Object.keys(profile.tokens).length) fail('tokens must not be empty');
  const cssNames = new Set();
  for (const [id, token] of Object.entries(profile.tokens)) {
    if (!identifier.test(id)) fail(`invalid token identifier: ${id}`);
    object(token, `token ${id}`, ['type', 'role', 'css', 'value']);
    if (!types.includes(token.type)) fail(`unsupported token type: ${id}`);
    if (typeof token.role !== 'string' || !identifier.test(token.role)) fail(`invalid semantic role: ${id}`);
    if (typeof token.css !== 'string' || !/^--[a-z][a-z0-9-]*$/.test(token.css)) fail(`invalid CSS token name: ${id}`);
    if (cssNames.has(token.css)) fail(`duplicate CSS token name: ${token.css}`);
    cssNames.add(token.css);
  }
  validateValues(profile.tokens);
  if (Object.hasOwn(profile, 'themes')) {
    object(profile.themes, 'themes');
    for (const [theme, overrides] of Object.entries(profile.themes)) {
      if (!/^[a-z][a-z0-9-]*$/.test(theme)) fail(`invalid theme identifier: ${theme}`);
      object(overrides, `theme ${theme}`);
      if (!Object.keys(overrides).length) fail(`theme ${theme} must have an override`);
      validateValues(profile.tokens, overrides);
    }
  }
  object(profile.provenance, 'provenance', ['runId', 'acceptedIteration', 'sourceTokenPaths', 'acceptance']);
  string(profile.provenance.runId, 'provenance.runId');
  if (!Number.isInteger(profile.provenance.acceptedIteration) || profile.provenance.acceptedIteration < 1) {
    fail('provenance.acceptedIteration must be a positive integer');
  }
  const paths = profile.provenance.sourceTokenPaths;
  if (!Array.isArray(paths) || !paths.length) fail('sourceTokenPaths requires at least one path');
  for (const path of paths) portablePath(path, 'sourceTokenPaths');
  if (new Set(paths).size !== paths.length) fail('sourceTokenPaths must be unique');
  evidence(profile.provenance.acceptance, 'provenance.acceptance');
  object(profile.links, 'links', ['designDna'], ['documentVisualContract']);
  for (const [key, link] of Object.entries(profile.links)) evidence(link, `links.${key}`);
  validateGuidance(match[2]);
  return { profile, guidance: match[2].trim() };
}

function declaresProfile(header) {
  if (header === undefined) return false;
  try {
    const parsed = JSON.parse(header);
    return !!parsed && typeof parsed === 'object' && !Array.isArray(parsed) && Object.hasOwn(parsed, 'profile');
  } catch { /* Recognize damaged declarations without accepting malformed JSON. */ }
  // Tokenize complete strings so prose values cannot masquerade as keys. Decode
  // escaped JSON key spellings even when the surrounding header is damaged.
  const lexemes = header.match(/"(?:\\.|[^"\\])*"|'[^']*'|[{}\[\]:,]|[^\s{}\[\]:,]+/g) ?? [];
  const containers = [];
  for (let i = 0; i < lexemes.length; i += 1) {
    const item = lexemes[i];
    if (item === '{' || item === '[') { containers.push(item); continue; }
    if (item === '}' || item === ']') { containers.pop(); continue; }
    if (containers.length > 1 || containers[0] === '[') continue;
    const previous = lexemes[i - 1];
    const keyPosition = i === 0 || previous === '{' || previous === ',' || lexemes[i + 1] === ':';
    if (!keyPosition) continue;
    let key = item;
    if (item.startsWith('"')) {
      try { key = JSON.parse(item); } catch { continue; }
    } else if (item.startsWith("'")) key = item.slice(1, -1);
    if (key === 'profile') return true;
  }
  return false;
}

export function inspectDesignAuthority(markdown) {
  string(markdown, 'DESIGN.md');
  const text = normalise(markdown);
  // A missing closing delimiter still leaves a header to inspect. Never scan
  // the Markdown body of a closed header for profile names or examples.
  const header = text.match(/^---\n([\s\S]*?)(?:\n---(?:\n|$)|$)/)?.[1];
  if (declaresProfile(header)) {
    const { profile } = validateDesignAuthority(markdown);
    return { status: 'valid-profile', provenance: profile.provenance,
      tokenCount: Object.keys(profile.tokens).length, acceptanceVerified: false };
  }
  return { status: 'legacy-unprofiled', acceptanceVerified: false };
}

export function deriveDesignAuthority(markdown) {
  const { profile } = validateDesignAuthority(markdown);
  const cssValue = (value) => {
    const reference = referenceOf(value);
    return reference ? `var(${profile.tokens[reference].css})` : value;
  };
  const block = (selector, values) => `${selector} {\n${Object.keys(values).sort().map(
    (id) => `  ${profile.tokens[id].css}: ${cssValue(values[id])};`,
  ).join('\n')}\n}\n`;
  const base = Object.fromEntries(Object.entries(profile.tokens).map(([id, token]) => [id, token.value]));
  const blocks = [block(':root', base)];
  // Alias variables resolve before inheritance. Re-emit the effective token set
  // at each theme boundary so nested themes neither inherit resolved aliases
  // nor leak another theme's overridden primitives.
  for (const theme of Object.keys(profile.themes ?? {}).sort()) {
    blocks.push(block(`[data-theme="${theme}"]`, { ...base, ...profile.themes[theme] }));
  }
  return {
    schemaVersion: 1,
    design: normalise(markdown),
    authorityDigest: createHash('sha256').update(normalise(markdown)).digest('hex'),
    tokensCss: blocks.join('\n'),
    tokenRoles: Object.fromEntries(Object.keys(profile.tokens).sort().map((id) => {
      const { type, role, css, value } = profile.tokens[id];
      return [id, { type, role, css, reference: referenceOf(value) }];
    })),
    provenance: profile.provenance,
    links: profile.links,
    acceptanceVerified: false,
  };
}

const canonical = (value) => JSON.stringify(value, function (_key, item) {
  return item && typeof item === 'object' && !Array.isArray(item)
    ? Object.fromEntries(Object.keys(item).sort().map((key) => [key, item[key]])) : item;
});
const digest = (text) => createHash('sha256').update(normalise(text)).digest('hex');

export function checkDesignAuthorityParity(markdown, consumers) {
  object(consumers, 'consumers');
  const expected = deriveDesignAuthority(markdown);
  const source = validateDesignAuthority(markdown);
  const findings = [];
  const add = (ruleId, consumer, message) => findings.push({ ruleId, consumer, message });
  const required = ['tokensCss', 'skillTokensCss', 'skillDesign', 'skillIndex', 'designDna'];
  if (source.profile.links.documentVisualContract) required.push('documentVisualContract');
  for (const key of required) {
    if (typeof consumers[key] !== 'string') add('consumer-missing', key, 'Required consumer was not supplied');
  }
  for (const key of ['tokensCss', 'skillTokensCss']) {
    if (typeof consumers[key] === 'string' && normalise(consumers[key]) !== expected.tokensCss) {
      add('token-value-drift', key, 'CSS differs from the deterministic export; regenerate or review the accepted token authority');
    }
  }
  if (typeof consumers.skillDesign === 'string') {
    try {
      const actual = deriveDesignAuthority(consumers.skillDesign);
      const copied = validateDesignAuthority(consumers.skillDesign);
      if (canonical(actual.tokenRoles) !== canonical(expected.tokenRoles)) {
        add('semantic-role-drift', 'skillDesign', 'Token roles, types, CSS names or semantic relationships differ');
      }
      if (actual.tokensCss !== expected.tokensCss) add('token-value-drift', 'skillDesign', 'Token or theme values differ');
      if (canonical(actual.provenance) !== canonical(expected.provenance) || canonical(actual.links) !== canonical(expected.links)) {
        add('provenance-drift', 'skillDesign', 'Acceptance provenance or linked authority digests differ');
      }
      if (copied.guidance !== source.guidance || copied.profile.name !== source.profile.name) {
        add('guidance-drift', 'skillDesign', 'Application guidance or system name differs');
      }
    } catch (error) {
      if (!(error instanceof DesignAuthorityInputError)) throw error;
      add('invalid-consumer', 'skillDesign', error.message);
    }
  }
  if (typeof consumers.skillIndex === 'string' && !hasAuthorityLink(consumers.skillIndex)) {
    add('authority-pointer-missing', 'skillIndex', 'The generated skill index must link to its portable DESIGN.md copy');
  }
  for (const [link, key] of [['designDna', 'designDna'], ['documentVisualContract', 'documentVisualContract']]) {
    if (source.profile.links[link] && typeof consumers[key] === 'string' && digest(consumers[key]) !== source.profile.links[link].sha256) {
      add('provenance-drift', key, 'Linked authority content no longer matches its recorded digest');
    }
  }
  return {
    status: findings.length ? 'parity-failed' : 'verified-parity',
    authorityDigest: expected.authorityDigest,
    findings,
    acceptanceVerified: false,
  };
}

async function readConsumer(path) {
  try { return await readFile(path, 'utf8'); } catch (error) {
    if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return null;
    throw error;
  }
}

async function main(argv) {
  const [command, inputPath, outputPath] = argv;
  if (command === 'inspect' && argv.length === 2) {
    process.stdout.write(`${JSON.stringify(inspectDesignAuthority(await readFile(inputPath, 'utf8')))}\n`);
  } else if (command === 'validate' && argv.length === 2) {
    const { profile } = validateDesignAuthority(await readFile(inputPath, 'utf8'));
    process.stdout.write(`${JSON.stringify({
      status: 'valid-profile', provenance: profile.provenance,
      tokenCount: Object.keys(profile.tokens).length, acceptanceVerified: false,
    })}\n`);
  } else if (command === 'export' && argv.length === 3) {
    const derived = deriveDesignAuthority(await readFile(inputPath, 'utf8'));
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, `${JSON.stringify(derived, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
    process.stdout.write(`${JSON.stringify({
      status: 'derived', authorityDigest: derived.authorityDigest,
      acceptanceVerified: derived.acceptanceVerified,
    })}\n`);
  } else if (command === 'check' && argv.length === 4) {
    const skill = argv[3];
    const consumers = {};
    for (const [key, path] of Object.entries({
      tokensCss: outputPath, skillTokensCss: join(skill, 'assets/tokens.css'),
      skillDesign: join(skill, 'DESIGN.md'), skillIndex: join(skill, 'SKILL.md'),
      designDna: join(skill, 'design-dna.md'), documentVisualContract: join(skill, 'document-visual-contract.json'),
    })) consumers[key] = await readConsumer(path);
    const report = checkDesignAuthorityParity(await readFile(inputPath, 'utf8'), consumers);
    process.stdout.write(`${JSON.stringify(report)}\n`);
    if (report.findings.length) process.exitCode = 2;
  } else {
    throw new DesignAuthorityInputError('usage: inspect DESIGN.md | validate DESIGN.md | export DESIGN.md output.json | check DESIGN.md tokens.css skill-directory');
  }
}

function isCliEntryPoint() {
  if (!process.argv[1]) return false;
  try {
    // Node resolves module symlinks, including macOS /var -> /private/var.
    // Compare physical paths while keeping imports from eval/stdin inert.
    return realpathSync(fileURLToPath(import.meta.url)) === realpathSync(resolve(process.argv[1]));
  } catch (error) {
    if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return false;
    throw error;
  }
}

if (isCliEntryPoint()) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`ERROR ${error.message}\n`);
    process.exitCode = error instanceof DesignAuthorityInputError || error instanceof SyntaxError ? 2 : 1;
  });
}
