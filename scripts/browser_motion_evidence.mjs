export function mergeMotionEvidence(samples) {
  const evidence = (samples || []).filter(Boolean);
  if (!evidence.length) {
    return {
      prefersReducedMotion: false,
      maxMs: 0,
      activeElementCount: 0,
      samples: [],
    };
  }
  return {
    prefersReducedMotion: evidence.every((sample) => sample.prefersReducedMotion),
    maxMs: Math.max(...evidence.map((sample) => Number(sample.maxMs) || 0)),
    activeElementCount: Math.max(
      ...evidence.map((sample) => Number(sample.activeElementCount) || 0),
    ),
    samples: evidence.flatMap((sample) => (sample.samples || []).map((entry) => ({
      ...entry,
      observedAtMs: Number.isFinite(sample.observedAtMs)
        ? sample.observedAtMs
        : null,
    }))).slice(0, 8),
  };
}
