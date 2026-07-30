# Brief: HarborBoard overhaul

Overhaul the existing **HarborBoard** work queue without changing its information architecture or removing working behaviour.

## Product

HarborBoard helps a marine project-delivery coordinator triage incoming work, see what is blocked and open a compact detail view before assigning the next action.

## Primary user

A coordinator handling 10 to 30 items a day. They scan quickly, switch between status views and often use the screen beside email or chat.

## Preserve

- the product name and current content;
- search by title, project or owner;
- the status filter;
- the four summary counts;
- the New work action;
- the queue columns and row data;
- opening and closing the detail drawer;
- the declared element IDs used by functional checks;
- the ability to run as static local files.

## Improve

- make the next useful action and blocked work easier to identify;
- create stronger hierarchy without turning every row into a large card;
- make status readable without relying on colour alone;
- remove phone-width horizontal document overflow;
- make the detail drawer easier to scan and use with a keyboard;
- give the product a specific operational character rather than a generic admin template.

## Constraints

- edit the supplied HTML, CSS and JavaScript rather than replacing the product with a mock image;
- do not add authentication, charts, fabricated analytics or new workflow stages;
- do not rename or remove the preserved controls and data;
- no external libraries, network calls or build step;
- support reduced motion and the declared viewports.
