import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export class DocumentContractInputError extends Error {
  constructor(message) {
    super(message);
    this.name = 'DocumentContractInputError';
  }
}

function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new DocumentContractInputError(`${name} must be an object`);
  }
  return value;
}

function requireString(value, name) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new DocumentContractInputError(`${name} must be a non-empty string`);
  }
  return value;
}

function requireArray(value, name) {
  if (!Array.isArray(value)) {
    throw new DocumentContractInputError(`${name} must be an array`);
  }
  return value;
}

export function validateDocumentVisualContract(input) {
  const contract = requireObject(input, 'document visual contract');
  if (contract.schemaVersion !== 1) {
    throw new DocumentContractInputError('schemaVersion must be 1');
  }
  if (contract.surface !== 'paginated-artifact') {
    throw new DocumentContractInputError('surface must be paginated-artifact');
  }
  if (contract.rendererNeutral !== true) {
    throw new DocumentContractInputError('rendererNeutral must be true');
  }

  const page = requireObject(contract.page, 'page');
  const defaultSize = requireString(page.defaultSize, 'page.defaultSize');
  const sizes = requireObject(page.sizes, 'page.sizes');
  if (!Object.hasOwn(sizes, defaultSize)) {
    throw new DocumentContractInputError('page.sizes must define page.defaultSize');
  }
  requireObject(page.margins, 'page.margins');
  requireObject(page.grid, 'page.grid');

  requireObject(requireObject(contract.typography, 'typography').roles, 'typography.roles');
  const colour = requireObject(contract.colour, 'colour');
  requireObject(colour.roles, 'colour.roles');
  requireObject(colour.grayscale, 'colour.grayscale');
  requireObject(requireObject(contract.spacing, 'spacing').rhythm, 'spacing.rhythm');
  requireObject(contract.furniture, 'furniture');
  requireObject(contract.components, 'components');

  const pagination = requireObject(contract.pagination, 'pagination');
  requireArray(pagination.keepTogether, 'pagination.keepTogether');
  requireObject(pagination.orphanWidow, 'pagination.orphanWidow');
  requireString(pagination.repeatedHeadings, 'pagination.repeatedHeadings');
  requireString(pagination.continuation, 'pagination.continuation');
  requireArray(pagination.breakPriority, 'pagination.breakPriority');

  const qa = requireObject(contract.qa, 'qa');
  requireArray(qa.visualLenses, 'qa.visualLenses');
  requireArray(qa.mechanicalRules, 'qa.mechanicalRules');
  requireArray(qa.representativeFixtures, 'qa.representativeFixtures');

  if (contract.adapters != null) {
    requireArray(contract.adapters, 'adapters');
  }

  return contract;
}

export async function publishDocumentVisualContract(inputPath, outputPath) {
  const input = JSON.parse(await readFile(inputPath, 'utf8'));
  const contract = validateDocumentVisualContract(input);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(contract, null, 2)}\n`, 'utf8');
  return contract;
}

async function main(argv) {
  if (argv.length !== 2) {
    throw new DocumentContractInputError('usage: node index.mjs proposed-contract.json output.json');
  }
  await publishDocumentVisualContract(argv[0], argv[1]);
}

const isCli = process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (isCli) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`ERROR ${error.message}\n`);
    process.exitCode = error instanceof DocumentContractInputError || error instanceof SyntaxError ? 2 : 1;
  });
}
