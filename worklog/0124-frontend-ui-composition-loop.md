# Commit Title

docs(frontend): define UI composition loop

# Changed File Scope

- Root agent workflow guide and Korean localized agent guide.
- Frontend engineering guide and Korean localized frontend guide.
- Worklog entry for frontend UI loop guidance.

# Reason

Frontend changes need an explicit UI-focused loop for shared components, shared styles, compact controls, pagination, and text spacing checks before commit.

# Impact

- Adds UI composition to the default frontend loop check policy.
- Documents a frontend UI loop for reusable component lookup, shared style usage, compact control spacing, pagination state, and responsive text/layout verification.
- Keeps Korean localized guidance synchronized.

# Verification

- `git diff --check`
- `make check`
- Loop check: documentation-only change; frontend UI composition loop is defined, with no runtime implementation loop required.
