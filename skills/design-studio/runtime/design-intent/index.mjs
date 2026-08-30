import { readFile, writeFile } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const CONTRACT = JSON.parse(
  readFileSync(new URL('../../design-intent-contract.json', import.meta.url), 'utf8'),
);
const REQUIRED_FIELDS = new Set(CONTRACT.requiredFields);
const LANE_PROCEDURES = new Set(CONTRACT.laneProcedures);
const PRECEDENCE_RULES = new Map(CONTRACT.precedence.map((rule) => [rule.id, rule]));

export class DesignIntentInputError extends Error {
  constructor(message) {
    super(message);
    this.name = 'DesignIntentInputError';
  }
}

function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new DesignIntentInputError(`${name} must be an object`);
  }
  return value;
}

function requireString(value, name) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new DesignIntentInputError(`${name} must be a non-empty string`);
  }
  return value;
}

function requireStringArray(value, name) {
  if (!Array.isArray(value)) {
    throw new DesignIntentInputError(`${name} must be an array`);
  }
  return value.map((item, index) => requireString(item, `${name}[${index}]`));
}

function requireEnum(value, name, allowed) {
  const checked = requireString(value, name);
  if (!allowed.includes(checked)) {
    throw new DesignIntentInputError(`${name} must be one of: ${allowed.join(', ')}`);
  }
  return checked;
}

function requireFields(record) {
  for (const field of CONTRACT.requiredFields) {
    if (!Object.hasOwn(record, field)) {
      throw new DesignIntentInputError(`design intent must include ${field}`);
    }
  }

  const unexpected = Object.keys(record)
    .filter((field) => !REQUIRED_FIELDS.has(field))
    .sort();
  if (unexpected.length) {
    throw new DesignIntentInputError(
      `design intent has unexpected fields: ${unexpected.join(', ')}`,
    );
  }
}

export function validateDesignIntent(input) {
  const intent = requireObject(input, 'design intent');
  requireFields(intent);

  if (intent.schemaVersion !== CONTRACT.schemaVersion) {
    throw new DesignIntentInputError(`schemaVersion must be ${CONTRACT.schemaVersion}`);
  }

  const lane = requireEnum(intent.lane, 'lane', CONTRACT.enums.lane);
  const designMode = requireEnum(
    intent[CONTRACT.classificationField],
    CONTRACT.classificationField,
    CONTRACT.enums.designMode,
  );
  const surface = requireEnum(intent.surface, 'surface', CONTRACT.enums.surface);
  const visualAuthority = requireEnum(
    intent.visualAuthority,
    'visualAuthority',
    CONTRACT.enums.visualAuthority,
  );
  requireEnum(
    intent.compositionState,
    'compositionState',
    CONTRACT.enums.compositionState,
  );
  const systemEffect = requireEnum(
    intent.systemEffect,
    'systemEffect',
    CONTRACT.enums.systemEffect,
  );

  const requiredCapabilities = requireStringArray(
    intent.requiredCapabilities,
    'requiredCapabilities',
  );
  for (const capability of requiredCapabilities) {
    requireEnum(
      capability,
      'requiredCapabilities entry',
      CONTRACT.enums.requiredCapability,
    );
  }

  const selectedProcedures = requireStringArray(
    intent.selectedProcedures,
    'selectedProcedures',
  );
  requireStringArray(intent.assumptions, 'assumptions');
  requireStringArray(intent.unresolved, 'unresolved');
  const precedenceRule = requireEnum(
    intent.precedenceRule,
    'precedenceRule',
    [...PRECEDENCE_RULES.keys()],
  );

  const modeRule = CONTRACT.modeRules[designMode];
  if (lane !== modeRule.lane) {
    throw new DesignIntentInputError(`${designMode} requires lane ${modeRule.lane}`);
  }
  if (!modeRule.surfaces.includes(surface)) {
    throw new DesignIntentInputError(`${designMode} does not allow surface ${surface}`);
  }
  if (!modeRule.visualAuthorities.includes(visualAuthority)) {
    throw new DesignIntentInputError(
      `${designMode} does not allow visualAuthority ${visualAuthority}`,
    );
  }
  if (!modeRule.systemEffects.includes(systemEffect)) {
    throw new DesignIntentInputError(
      `${designMode} does not allow systemEffect ${systemEffect}`,
    );
  }
  for (const capability of modeRule.requiredCapabilities) {
    if (!requiredCapabilities.includes(capability)) {
      throw new DesignIntentInputError(
        `requiredCapabilities must include ${capability} for ${designMode}`,
      );
    }
  }
  if (!selectedProcedures.includes(modeRule.requiredProcedure)) {
    throw new DesignIntentInputError(
      `selectedProcedures must include ${modeRule.requiredProcedure} for ${designMode}`,
    );
  }
  for (const procedure of selectedProcedures) {
    if (LANE_PROCEDURES.has(procedure) && procedure !== modeRule.requiredProcedure) {
      throw new DesignIntentInputError(
        `selectedProcedures cannot include lane procedure ${procedure} for ${designMode}`,
      );
    }
  }

  const precedence = PRECEDENCE_RULES.get(precedenceRule);
  if (!precedence.allowedModes.includes(designMode)) {
    throw new DesignIntentInputError(
      `precedenceRule ${precedenceRule} does not allow designMode ${designMode}`,
    );
  }

  return intent;
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
    throw new DesignIntentInputError('usage: node index.mjs [input.json] [output.json]');
  }
  const inputText = argv[0] ? await readFile(argv[0], 'utf8') : await readStdin();
  const result = validateDesignIntent(JSON.parse(inputText));
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
    process.exitCode = error instanceof DesignIntentInputError || error instanceof SyntaxError ? 2 : 1;
  });
}
