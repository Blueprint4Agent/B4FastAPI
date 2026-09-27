"""Exercise configured branding in an isolated frontend using the normal Make hooks."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="b4-configured-build-") as directory:
        root = Path(directory)
        child = root / "src/frontend"
        shutil.copytree(
            ROOT / "src/frontend",
            child,
            ignore=shutil.ignore_patterns(
                ".git",
                "node_modules",
                "dist",
                "target",
                "gen",
                ".env",
                "project.local.json",
                "project-brand",
                "test-results",
                "playwright-report",
            ),
        )
        (child / "node_modules").symlink_to(
            ROOT / "src/frontend/node_modules", target_is_directory=True
        )
        shutil.copytree(
            ROOT / "scripts",
            root / "scripts",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        for folder in ("src/backend", "docker"):
            (root / folder).mkdir(parents=True)
            shutil.copyfile(
                ROOT / folder / ".env.example", root / folder / ".env.example"
            )
        manifest = json.loads((ROOT / "project.example.json").read_text())
        manifest.update(
            name="테스트 & Acme",
            short_name="ACME",
            identifier="com.acme.desktop",
            logo="branding/logo.svg",
        )
        (root / "project.json").write_text(json.dumps(manifest))
        (root / "branding").mkdir()
        (root / "branding/logo.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14" fill="blue"/></svg>'
        )
        # Full env initialization has separate fixtures; reproduce the public CI/Docker build input here.
        subprocess.run(["python3", "scripts/project_identity.py"], cwd=root, check=True)
        subprocess.run(
            ["make", "project-config-check", "test", "test-routes"],
            cwd=child,
            check=True,
        )


if __name__ == "__main__":
    main()
