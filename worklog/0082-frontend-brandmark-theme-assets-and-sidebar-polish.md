# commit title
frontend: polish sidebar toggle and add theme-specific brand mark assets

# changed file scope
- src/frontend/src/styles/app.css
- src/frontend/src/components/ui/display/BrandMark.tsx
- src/frontend/public/icons/b4a-mark.svg
- src/frontend/public/icons/b4a-mark.png
- src/frontend/public/icons/b4a-mark-dark.svg
- src/frontend/public/icons/b4a-mark-dark.png

# reason
- Remove visual chrome from the sidebar toggle button and keep its position fixed at the top-left even when sidebar width changes.
- Improve light-theme panel/border readability by increasing surface contrast.
- Support theme-specific brand mark rendering with light/dark asset variants and png fallback.

# impact
- Sidebar toggle now stays anchored and uses a cleaner icon-only appearance.
- Light mode card/border separation is more visible.
- Brand icon now switches by theme (light vs dark) while preserving svg-first with png fallback.
