"""Public project identity generation; standard-library only for Docker builds."""

import argparse
import json
import os
from pathlib import Path
import re
import sys

FIELDS = {
    "version",
    "slug",
    "name",
    "short_name",
    "identifier",
    "features",
    "logo",
    "logo_dark",
}


def validate_manifest(value: object) -> dict:
    if not isinstance(value, dict) or set(value) - FIELDS:
        raise ValueError(
            "Project manifest must be an object with supported public fields only"
        )
    if type(value.get("version")) is not int or value["version"] != 1:
        raise ValueError("Project version must be 1")
    for key, limit in (("name", 60), ("short_name", 16)):
        text = value.get(key)
        if (
            not isinstance(text, str)
            or text != text.strip()
            or not re.fullmatch(r"[\w .&()\-]{1," + str(limit) + "}", text)
        ):
            raise ValueError(f"Invalid project {key}")
    slug = value.get("slug")
    if (
        not isinstance(slug, str)
        or len(slug) > 40
        or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug)
    ):
        raise ValueError(
            "Project slug must be lowercase kebab-case (maximum 40 characters)"
        )
    identifier = value.get("identifier")
    if (
        not isinstance(identifier, str)
        or len(identifier) > 150
        or not re.fullmatch(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*){2,}", identifier)
    ):
        raise ValueError(
            "Project identifier must be lowercase reverse-DNS, e.g. com.example.myapp"
        )
    features = value.get("features")
    if (
        not isinstance(features, dict)
        or set(features) != {"login", "email", "oauth"}
        or any(type(flag) is not bool for flag in features.values())
    ):
        raise ValueError("features must contain boolean login, email and oauth values")
    if not features["login"] and (features["email"] or features["oauth"]):
        raise ValueError("email/oauth require login=true")
    for key in ("logo", "logo_dark"):
        if key in value and (not isinstance(value[key], str) or not value[key].strip()):
            raise ValueError(f"{key} must be a non-empty local file path")
    if "logo_dark" in value and "logo" not in value:
        raise ValueError("logo_dark requires logo")
    return value


def brand_plan(data: dict, manifest_dir: Path, child: Path) -> dict[Path, bytes]:
    output: dict[Path, bytes] = {}
    identity = {
        key: data[key] for key in ("version", "name", "short_name", "identifier")
    }
    for key, url_key in (("logo", "logo_url"), ("logo_dark", "logo_dark_url")):
        if key not in data:
            continue
        asset = Path(data[key])
        if (
            asset.is_absolute()
            or ".." in asset.parts
            or not asset.parts
            or asset.parts[0] != "branding"
        ):
            raise ValueError(f"{key} must be a relative file under branding/")
        source = (manifest_dir / asset).resolve()
        if not source.is_relative_to((manifest_dir / "branding").resolve()):
            raise ValueError(f"{key} must stay under branding/")
        extension = source.suffix.lower()
        if (
            extension not in {".svg", ".png", ".webp", ".jpg", ".jpeg"}
            or not source.is_file()
        ):
            raise ValueError(f"{key} must reference an existing SVG/PNG/WEBP/JPEG file")
        if source.stat().st_size > 2_000_000:
            raise ValueError(f"{key} exceeds the 2 MB branding asset limit")
        filename = f"{key}{extension}"
        output[child / "public/project-brand" / filename] = source.read_bytes()
        identity[url_key] = f"/project-brand/{filename}"
    output[child / "project.local.json"] = (
        json.dumps(identity, ensure_ascii=False, indent=4) + "\n"
    ).encode()
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default=os.environ.get("PROJECT_CONFIG", "project.json")
    )
    parser.add_argument("--output", default="src/frontend")
    args = parser.parse_args()
    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    config = Path(args.config)
    if not config.exists() and args.config == "project.json":
        print("[branding] No project.json; keep the existing/default frontend identity")
        return 0
    try:
        data = validate_manifest(json.loads(config.read_text(encoding="utf-8")))
        output = brand_plan(data, config.parent, target)
        for path in output:
            if path.is_symlink() or not path.resolve().is_relative_to(target.resolve()):
                raise ValueError(
                    "Generated branding must stay inside its output directory"
                )
        for path, content in output.items():
            if path.exists() and path.read_bytes() == content:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print("[branding] Public frontend identity generated")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError):
        print(
            "[error] Cannot read public project configuration or branding assets",
            file=sys.stderr,
        )
    except ValueError as error:
        print(f"[error] {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
