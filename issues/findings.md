# Design Studio - Iteration 2 Visual & Harness Findings

This document tracks visual design defects and harness execution constraints identified during the Iteration 2 evaluation of the Design Studio landing page (`docs/index.html`).

## 1. Visual Design Defects

### Hero Zone (Zone 2)
- **Overlap & Clipping**: The right-side dark preview panel shows clipped white text fragments ("…dio"), clipped purple text ("…e Code"), a vertical rotated "OVERVIEW" label, and faint low-contrast text near the bottom ("…ed evaluation"). These read as rendering artifacts.
- **Manifesto Text Cutoff**: The left column body paragraph is clipped at the bottom of the viewport under the 800×600 aspect ratio.

### Video / Proof Zone (Zone 5)
- **Play Button Overlap**: The large circular play button is positioned directly on top of the video title and subtitle, obscuring the text "Design Studio" and the subtitle.
- **Low Contrast / Truncation**: The purple subtitle text inside the video card is truncated and has very low contrast against the dark background.

### Install / CTA Zone (Zone 8)
- **Code Container Clipping**: The command block container is horizontally truncated at the right edge, clipping the command string (`claude plugin install https://g…`), making it impossible to read or copy the full URL.

---

## 2. Harness Execution Findings

### Critical Viewport Lock Bug
- **Symptom**: The OMP browser automation environment is locked to a viewport of 800×600.
- **Impact**: 
  - Attempts to set the viewport to 390px (mobile) or 1440px (desktop) fail.
  - The mobile screenshot capture (`iter-2-mobile.png`) is byte-for-byte identical to the desktop capture (`iter-2-desktop.png`).
  - Mobile layout verification and responsive overflow testing are blocked in this environment.
  - Non-scrolled zones (Footer, Differentiators) are not captured in the 800×600 viewport, preventing their visual scoring.

---

## 3. Stale References & Inconsistencies (Fixed)
- **Stale Proper Nouns**: Removed remaining occurrences of "frontend harness" from `agents/evaluator.md` and `agents/design-agent.md`, renaming them to "Design Studio harness" to match the new branding.
- **Agent Count Inconsistency**: Reconciled `agents/evaluator.md` stating it was a "3-agent" harness to "4-agent Design Studio harness" to match `SKILL.md` and `design-agent.md`.
