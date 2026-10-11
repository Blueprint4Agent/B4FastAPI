# Commit Title

docs: publish the project under the MIT license

# Changed File Scope

Root LICENSE and English/Korean README license sections.

# Reason

The user explicitly selected MIT for public reuse. The repository previously had asset-specific notices but no project license.

# Design

Add the standard MIT text with Blueprint4Agent contributors attribution. Preserve third-party notices and distinguish the separately maintained B4React submodule.

# Verification Plan

Root make verify-plan/verify and text/link review. Compare license text with the Open Source Initiative MIT text. No runtime changes or new tests are needed.

# Impact

Defines the selected reuse terms for original project material without replacing third-party notices.

# Loop Alignment

Documentation/legal metadata only; backend and frontend runtime loops are not applicable.

# Verification

- Standard MIT text compared with https://opensource.org/license/mit; user selected MIT explicitly.
- Root full-branch verify-plan/verify passed; unknown LICENSE classification retained full scope. 450 backend tests passed; unchanged frontend receipts reused and contracts/package/branding passed.
- Existing third-party notices retained. No runtime changes or live deployment, and no new tests were added for license text.
