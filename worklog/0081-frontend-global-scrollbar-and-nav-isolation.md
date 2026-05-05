# commit title
frontend: add global scrollbar rules and isolate nav from content scrolling

# changed file scope
- src/frontend/FRONTEND.md
- src/frontend/src/styles/app.css

# reason
- Apply one consistent scrollbar design across all scrollable UI containers.
- Prevent the top nav area from being affected by content scrolling behavior and scrollbar rendering.
- Document scrollbar styling as a frontend rule so future additions follow the same pattern.

# impact
- Scrollable areas now use shared dark-theme-friendly scrollbar tokens and visuals.
- App layout scroll is constrained to the main content region, leaving nav visually stable.
- Frontend guide now explicitly requires global scrollbar rule usage for scrollable containers.
