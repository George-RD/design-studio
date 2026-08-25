# Milestone 0 blind output preference review

The lane harness records task clarity, originality, defects, elapsed time, cost, failures and recovery for each completed run. Output preference is comparison-level evidence and is recorded separately so the reviewer cannot see which lane or tool produced an option before ranking it.

## Prepare a review packet

After all three lanes for one fixture are `complete` and validate against their receipts:

```bash
python3 scripts/run_boundary_benchmark_preference.py prepare \
  --matrix harness-output/benchmarks/milestone-0/matrices/m0-001/matrix.json \
  --fixture marketing-surface \
  --comparison-id m0-001-marketing-preference
```

Preparation copies the three receipted outputs under randomized labels `A`, `B` and `C` and writes:

```text
harness-output/benchmarks/milestone-0/comparisons/<comparison-id>/
  comparison.json
  review/
    manifest.json
    context/
      brief.md
      acceptance.json
    submissions/
      A/
      B/
      C/
  private/
    assignment.json
```

Give the preference reviewer only the `review/` directory. It contains the frozen brief, acceptance contract, anonymized outputs and review rubric. Lane names, tool versions, run IDs and the private A/B/C assignment are excluded from the public review manifest.

The review tree and private assignment are SHA-256 receipted. Mutation after preparation makes completion fail.

## Review rubric

Rank only the rendered outcomes and interactions. Do not infer authorship or use source provenance.

The rubric asks for evidence on:

- **intentionality and specificity**: whether the result feels deliberately shaped for the brief rather than assembled from interchangeable template choices;
- **interaction polish**: clarity and coherence of states, transitions and feedback;
- **scope discipline**: whether the result solves the brief without unsupported invention or decorative detours;
- **visible outcome**: overall preference based only on the rendered result.

The intentionality dimension is deliberately perceptual rather than a second mechanical anti-pattern catalogue. Impeccable remains the owner of generic detector rules; Design Studio owns the source-blind comparison and decision evidence.

Submit review evidence in this shape. Rank groups allow ties:

```json
{
  "schemaVersion": 1,
  "rubricVersion": 1,
  "reviewer": "reviewer-id",
  "ranking": [["B"], ["A", "C"]],
  "rationale": "Concrete overall preference evidence.",
  "evidence": {
    "A": {
      "summary": "Visible outcome evidence.",
      "intentionalitySpecificity": "Brief-specific visual or interaction evidence.",
      "interactionPolish": "Interaction evidence.",
      "scopeDiscipline": "Scope evidence."
    },
    "B": {
      "summary": "Visible outcome evidence.",
      "intentionalitySpecificity": "Brief-specific visual or interaction evidence.",
      "interactionPolish": "Interaction evidence.",
      "scopeDiscipline": "Scope evidence."
    },
    "C": {
      "summary": "Visible outcome evidence.",
      "intentionalitySpecificity": "Brief-specific visual or interaction evidence.",
      "interactionPolish": "Interaction evidence.",
      "scopeDiscipline": "Scope evidence."
    }
  }
}
```

## Lock the review, then reveal provenance

```bash
python3 scripts/run_boundary_benchmark_preference.py complete \
  --comparison harness-output/benchmarks/milestone-0/comparisons/m0-001-marketing-preference/comparison.json \
  --review /path/to/blind-review.json
```

Completion first preserves the validated review as `evidence/blind-review.json`. Only after that file is durably written does the transaction load the private A/B/C mapping. The result then records the revealed ranking and aggregates the existing lane metrics without replacing the raw lane evidence.

Validate the complete receipt at any time:

```bash
python3 scripts/run_boundary_benchmark_preference.py validate \
  --comparison harness-output/benchmarks/milestone-0/comparisons/m0-001-marketing-preference/comparison.json
```

A comparison result is admissible only while the review packet, private assignment, source matrix, completed lane results and preserved blind review still match their receipts.
