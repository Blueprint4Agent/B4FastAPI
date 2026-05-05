# commit title
frontend: add shared tooltip component and apply to sidebar/navbar

# changed file scope
- src/frontend/src/components/ui/overlays/Tooltip.tsx
- src/frontend/src/components/ui/index.ts
- src/frontend/src/components/layout/AppSidebar.tsx
- src/frontend/src/components/layout/AppNavbar.tsx
- src/frontend/src/pages/main/ShowCasePage.tsx
- src/frontend/src/locales/en.json
- src/frontend/src/styles/app.css

# reason
- Add a reusable tooltip primitive for hover/focus guidance.
- Show compact navigation labels in collapsed sidebar and add a tooltip for the nav brand action.
- Fix tooltip UX so it closes on click and prevent left-edge clipping on the navbar brand mark.

# impact
- Shared tooltip component is available for future feature reuse.
- Sidebar and navbar now provide clearer navigation hints without relying on title attributes.
- Tooltip behavior is more predictable (opens on interaction, closes on click/blur) and nav-brand tooltip no longer clips at the viewport edge.
