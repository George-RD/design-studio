# Brief: Northstar security settings review

Audit and polish the supplied **Northstar account security** page. This is a focused quality pass, not a redesign.

## User goal

A signed-in user needs to understand their current protection, turn two-factor authentication on or off, inspect active sessions and update a recovery email.

## Preserve

- the current page structure and restrained visual character;
- all supplied content and session data;
- two-factor state changes;
- recovery email save behaviour;
- the session overflow control;
- the declared element IDs;
- static local execution.

## Scope

- identify and fix functional, accessibility, responsive and visual-quality defects;
- improve hierarchy, spacing, states and copy only where the existing page is unclear;
- retain the basic information architecture;
- do not add new security features, authentication flows, account data or navigation sections.

## Constraints

- no external libraries, network calls or build step;
- all controls must work with keyboard and pointer;
- visible focus is required;
- support reduced motion and the declared viewports;
- preserve a compact settings-page feel rather than turning each line into a large promotional card.
