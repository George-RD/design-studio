import { readFileSync } from 'node:fs';
import { isDeepStrictEqual } from 'node:util';

// This branch is reached only when a Design Intent supplies composition evidence.
let contract;
function compositionContract() {
  contract ??= JSON.parse(readFileSync(
    new URL('../../composition-contract.json', import.meta.url), 'utf8',
  ));
  return contract;
}

export class CompositionInputError extends Error {}

const object = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value) => typeof value === 'string' && value.trim().length > 0;
const evidenceFor = (evidence, kinds) => Array.isArray(evidence) && evidence.some(
  (item) => object(item) && kinds.includes(item.kind) && text(item.ref),
);

function validateInput(composition, profile, intent) {
  if (!object(composition)) throw new CompositionInputError('preflight must be an object');
  const fields = [...profile.requiredInputFields, ...profile.optionalInputFields];
  if (profile.requiredInputFields.some((field) => !Object.hasOwn(composition, field)) ||
      Object.keys(composition).some((field) => !fields.includes(field))) {
    throw new CompositionInputError('preflight must use the declared input fields');
  }
  if (!text(composition.project) || typeof composition.strategySensitive !== 'boolean' ||
      !profile.skillAvailability.includes(composition.growthArsenal) || !Array.isArray(composition.artifacts)) {
    throw new CompositionInputError('preflight requires project, boolean strategySensitive, skill availability and artifacts');
  }
  if (intent.lane === 'Document') throw new CompositionInputError('website preflight is not a Document procedure');
  const designations = Object.hasOwn(composition, 'designations') ? composition.designations : [];
  if (!Array.isArray(designations)) throw new CompositionInputError('designations must be an array');
  const seen = new Set();
  for (const item of designations) {
    if (!object(item) || !profile.facets.some((facet) => facet.id === item.facet) ||
        !text(item.path) || !text(item.revision) ||
        !evidenceFor(item.evidence, ['user-designation']) || seen.has(item.facet) ||
        Object.keys(item).some((key) => !['facet', 'path', 'revision', 'evidence'].includes(key))) {
      throw new CompositionInputError('each designation requires a unique facet, exact source and user-designation evidence');
    }
    seen.add(item.facet);
  }
}

function audienceContext(entries, profile) {
  if (!Array.isArray(entries)) return null;
  const result = {facts: [], hypotheses: [], simulations: [], unverified: []};
  for (const entry of entries) {
    if (!object(entry) || !profile.audienceCategories.includes(entry.category) ||
        !profile.audienceKinds.includes(entry.kind) || !text(entry.text) ||
        !profile.confidenceLevels.includes(entry.confidence) || !Array.isArray(entry.evidence)) {
      return null;
    }
    if (entry.kind === 'hypothesis') result.hypotheses.push(entry);
    else if (entry.kind === 'simulated') result.simulations.push(entry);
    else if (evidenceFor(entry.evidence, entry.kind === 'confirmed'
      ? ['user-confirmation'] : ['research'])) result.facts.push(entry);
    else result.unverified.push(entry);
  }
  result.unresolvedCategories = profile.audienceCategories.filter(
    (category) => !result.facts.some((fact) => fact.category === category),
  );
  return result;
}

function candidateFor(artifact, project, rules, profile) {
  if (!object(artifact) || !['path', 'role', 'scope', 'state'].every(
    (key) => text(artifact[key]),
  )) return null;
  const rule = rules.find((item) => item.role === artifact.role);
  const provenance = artifact.provenance;
  if (!rule || artifact.scope !== rule.scope || !object(provenance) ||
      provenance.project !== project || !text(provenance.revision) ||
      ![...(rule.compatibleStates ?? [rule.requiredState]), 'stale'].includes(artifact.state) ||
      !evidenceFor(provenance.evidence, profile.evidenceKinds[artifact.role])) return null;
  const allowed = profile.facets.filter((facet) => facet.role === artifact.role).map((facet) => facet.id);
  const facets = artifact.role === 'offer-copy' ? provenance.facets : allowed;
  if (!Array.isArray(facets) || !facets.length ||
      facets.some((facet) => !allowed.includes(facet))) return null;
  const dependencies = provenance.dependencies;
  if (!Array.isArray(dependencies) || dependencies.some((dependency) =>
    !object(dependency) || !profile.facets.some((facet) => facet.id === dependency.facet) ||
    !text(dependency.path) || !text(dependency.revision))) return null;
  for (const facet of facets) {
    if ((profile.requiredDependencies[facet] ?? []).some((dependency) =>
      !dependencies.some((item) => item.facet === dependency))) return null;
  }
  const audience = artifact.role === 'audience-context' ? audienceContext(provenance.audience, profile) : null;
  if (artifact.role === 'audience-context' && !audience?.facts.length) return null;
  return {path: artifact.path, revision: provenance.revision, facets, provenance, audience, stale: artifact.state === 'stale'};
}

export function resolveCompositionReadiness(composition, intent) {
  const {artifactRoles, compositionReadiness: profile} = compositionContract();
  validateInput(composition, profile, intent);
  const candidates = composition.artifacts.map(
    (artifact) => candidateFor(artifact, composition.project, artifactRoles, profile),
  ).filter(Boolean);
  const nodes = new Map();
  for (const {id: facet} of profile.facets) {
    const designation = (composition.designations ?? []).find((item) => item.facet === facet);
    const matching = candidates.filter((candidate) => candidate.facets.includes(facet) &&
      (!designation || candidate.path === designation.path && candidate.revision === designation.revision));
    const unique = matching.filter((candidate, index) =>
      !matching.slice(0, index).some((other) => isDeepStrictEqual(candidate, other)));
    const selected = unique.length === 1 ? unique[0] : null;
    nodes.set(facet, {
      selected,
      state: unique.length > 1 ? 'conflicting' : !selected ? 'missing' : selected.stale ? 'stale' : 'ready',
      reasons: unique.length > 1 ? ['equal-authority-candidates'] : !selected
        ? ['no-current-authority'] : selected.stale ? ['explicitly-stale'] : [],
    });
  }

  // Five fixed facets bound traversal. Evaluate non-required sources too: a visual
  // artifact may explicitly depend on product facts even during a local polish.
  const freshness = (facet, visiting = new Set()) => {
    const node = nodes.get(facet);
    if (visiting.has(facet)) return {state: 'stale', reasons: ['dependency-cycle']};
    if (node.state !== 'ready') return node;
    const next = new Set([...visiting, facet]);
    const reasons = [];
    for (const dependency of node.selected.provenance.dependencies) {
      // A combined offer/copy export can point its copy facet at its own offer
      // facet. That internal handoff is not an offer depending on itself.
      if (facet === 'offer-positioning' && node.selected.facets.includes('commercial-copy') &&
          dependency.facet === facet && dependency.path === node.selected.path &&
          dependency.revision === node.selected.revision) continue;
      const source = nodes.get(dependency.facet);
      if (!source?.selected || freshness(dependency.facet, next).state !== 'ready') {
        reasons.push(`dependency-unready:${dependency.facet}`);
      } else if (source.selected.path !== dependency.path || source.selected.revision !== dependency.revision) {
        reasons.push(`dependency-changed:${dependency.facet}`);
      }
    }
    return reasons.length ? {state: 'stale', reasons: [...new Set(reasons)].sort()} : node;
  };
  const facets = {};
  const actions = [];
  for (const {id: facet, role} of profile.facets) {
    const owner = artifactRoles.find((rule) => rule.role === role).owner;
    const required = facet === 'visual-design'
      ? intent.visualAuthority === 'accepted-design-system'
      : composition.strategySensitive;
    const {selected} = nodes.get(facet);
    const status = required ? freshness(facet) : {state: 'not-applicable', reasons: []};
    facets[facet] = {
      state: status.state, role, owner,
      authority: status.state === 'ready' && selected ? {path: selected.path, revision: selected.revision} : null,
      reasons: status.reasons,
    };
    if (status.state === 'stale' && selected) {
      facets[facet].staleSource = {path: selected.path, revision: selected.revision};
    }
    if (required && selected?.audience) facets[facet].audience = selected.audience;
    if (profile.statePrecedence.includes(status.state)) {
      const adjacent = status.state !== 'conflicting' && composition.growthArsenal === 'available' &&
        ['audience-context', 'offer-copy'].includes(role);
      const action = status.state === 'conflicting' ? 'request-user-designation' : adjacent
        ? role === 'audience-context' ? 'request-audience-context' : 'request-approved-offer-copy'
        : role === 'visual-design' ? 'verify-visual-authority'
          : status.state === 'stale' ? 'revalidate-supplied-inputs' : 'confirm-supplied-inputs';
      actions.push({facet, owner, action, skill: adjacent ? 'growth-arsenal' : null});
    }
  }
  const states = Object.values(facets).map((facet) => facet.state);
  const state = profile.statePrecedence.find((value) => states.includes(value)) ??
    (states.includes('ready') ? 'ready' : 'not-applicable');
  return {state, mayProceed: !actions.length, adjacentSkill: composition.growthArsenal, facets, actions};
}
