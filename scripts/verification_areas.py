"""Verification ownership is separate from application regression depth.

Only explicit owners narrow checks. Unknown paths and shared build inputs expand to
all areas; API/domain test selection remains a separate policy.
"""

FRONTEND_AREAS = {
    "frontend-app",
    "contracts",
    "branding",
    "discovery",
    "style-studio",
    "harness",
    "governance",
}
PARENT_AREAS = FRONTEND_AREAS | {"backend", "deployment", "publication"}
GUIDES = {
    "AGENTS.md",
    "FRONTEND.md",
    "TEST.md",
    "src/backend/BACKEND.md",
    "src/backend/TEST.md",
}
HARNESS = {
    "verification.py",
    "verification_scope.py",
    "verification_areas.py",
    "verification_runner.py",
    "verification_cache.py",
    "verification_backend.py",
    "verification_contract.py",
    "test_verification_backend.py",
    "test_verification_contract.py",
    "git_hooks.py",
    "validate_git_governance.py",
    "validate-git-governance.sh",
    "test_verification.py",
    "test_verification_scope.py",
    "test_verification_areas.py",
    "test_verification_runner.py",
    "test_verification_cache.py",
    "test_git_hooks.py",
    "test_performance_governance.py",
    "test_page_family_governance.py",
}


def owned_areas(path, parent):
    """Return explicit ownership, or None when shared/unknown impact needs full."""
    name = path.rsplit("/", 1)[-1]
    if path in GUIDES or name == "AGENTS.md":
        return {"governance"}
    if path.endswith(".md"):
        return (
            set()
        )  # Documentation anywhere; executable/config files are never matched.
    if path.startswith((".githooks/", ".github/WORKLOG_TEMPLATE")):
        return {"governance"}
    if path.startswith("scripts/") and name in HARNESS:
        return {"harness"}
    if path.startswith("contracts/"):
        return {"contracts"}
    if parent:
        if path.startswith(
            ("src/backend/app/", "src/backend/tests/", "src/backend/alembic/")
        ) or path in (
            "src/backend/pyproject.toml",
            "src/backend/uv.lock",
            "src/backend/alembic.ini",
            "src/backend/.env.example",
        ):
            return {"backend"}
        if path == "docker/Dockerfile":
            return None  # Shared application build/dependency input.
        if path.startswith("docker/"):
            return {"deployment"}
        if name in {
            "env.py",
            "check_backend_architecture.py",
            "test_backend_architecture.py",
        } and path.startswith("scripts/"):
            return {"backend"}
        if path == "scripts/check-frontend-contract.mjs":
            return {"contracts", "harness"}
        if path == "scripts/package-frontend.mjs":
            return {"contracts", "frontend-app"}
        if path in {"scripts/indexnow.py", "scripts/test_indexnow.py"}:
            return {"publication"}
        if path in {
            "scripts/project_identity.py",
            "scripts/project_init.py",
            "scripts/test_project_init.py",
            "scripts/test_project_build.py",
            "project.json",
            "project.example.json",
        } or path.startswith("branding/"):
            return {"branding", "deployment"}
        return None
    if (
        path.startswith(
            (
                "scripts/style-studio",
                "tests/style-studio/",
                "src/components/features/style-studio/",
                "src/api/styleStudio/",
                "src/hooks/api/styleStudio/",
            )
        )
        or "StyleStudio" in name
        or path.endswith("/useStyleStudio.ts")
        or path == "playwright.style-studio.config.ts"
    ):
        return {"frontend-app", "style-studio"}
    if path.startswith(("scripts/public-discovery", "tests/discovery/")) or path in {
        "scripts/test-discovery.mjs",
        "playwright.discovery.config.ts",
    }:
        return {"discovery"}
    if path.startswith(("scripts/project-config", "public/project-brand/")) or path in {
        "project.local.json",
        "project.example.json",
    }:
        return {"frontend-app", "branding", "discovery"}
    if path.startswith("public/home-previews/"):
        return {"frontend-app", "discovery"}
    if path.startswith(
        ("src/", "public/", "tests/e2e/", "tests/production/", "tests/fixtures/")
    ) or path in {"playwright.config.ts", "playwright.production.config.ts"}:
        return {"frontend-app"}
    if path in {"scripts/generate-api.mjs"}:
        return {"contracts", "frontend-app"}
    return None
