---
{
  "profile": "design-studio/design-authority",
  "schemaVersion": 1,
  "name": "Archive",
  "tokens": {
    "color.ink": {
      "type": "color",
      "role": "text.primary",
      "css": "--color-ink",
      "value": "#14222e"
    },
    "color.action": {
      "type": "color",
      "role": "action.primary",
      "css": "--color-action",
      "value": "{color.ink}"
    },
    "space.unit": {
      "type": "dimension",
      "role": "spacing.unit",
      "css": "--space-unit",
      "value": "0.5rem"
    },
    "space.control": {
      "type": "dimension",
      "role": "spacing.control",
      "css": "--space-control",
      "value": "{space.unit}"
    }
  },
  "themes": {
    "dark": {
      "color.ink": "#f5f2ea"
    }
  },
  "provenance": {
    "runId": "fixture-authority",
    "acceptedIteration": 2,
    "sourceTokenPaths": [
      "src/theme.css"
    ],
    "acceptance": {
      "path": "harness-output/runs/fixture-authority/finish/acceptance.json",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  },
  "links": {
    "designDna": {
      "path": "harness-output/design-system/design-dna.md",
      "sha256": "9da8c9fe2fffa2c821ad44762e4673445d7954bc4c67f257fb97152f85d2545a"
    }
  }
}
---

# Archive design system

## Overview

Quiet hierarchy for a working archive. The design DNA owns the full visual thesis.

## Application guidance

Use color.action for primary controls and space.control for compact control spacing.
Component states use distinct token names; the dark theme only overrides existing values.

## Anti-goals

Do not apply compact control spacing to long reading passages.

## Ownership boundaries

This profile describes shared token roles and values. design-dna.md owns the wider visual
thesis, motifs and motion. A linked document-visual-contract.json owns page geometry,
furniture, pagination and print rules. Neither can silently redefine shared tokens.
