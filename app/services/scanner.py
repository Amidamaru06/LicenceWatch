import subprocess
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

ECOSYSTEM_MAP = {
    "python": "PyPI",
    "pip":"PyPI",
    "npm":"npm",
    "gem":"RubyGems",
    "java-archive":"Maven",
    "go-module":"Go",
    "rust-crate":"crates.io",
    "cargo":"crates.io",
    "deb":"Debian",
    "rpm":"Red Hat",
    "apk":"Alpine",
    "nuget":"NuGet",
}


def scan_image(image_name: str) -> list[dict[str, Any]]:
    
    logger.info(f"Starting syft scan: {image_name}")

    try:
        result = subprocess.run(["syft", image_name, "-o", "json", "--quiet"],capture_output=True,text=True,timeout=300,)

        if result.returncode != 0:
            raise RuntimeError(f"syft failed: {result.stderr or 'unknown error'}")

        packages: list[dict[str, Any]] = []
        for artifact in json.loads(result.stdout).get("artifacts", []):
            packages.append({"name":artifact.get("name", ""),"version":artifact.get("version", ""), "license": _extract_license(artifact.get("licenses", [])),
                "ecosystem": ECOSYSTEM_MAP.get(artifact.get("type", "").lower(),artifact.get("type", "")),})

        logger.info(f"Found {len(packages)} packages in {image_name}")
        return packages

    except FileNotFoundError:
        raise RuntimeError()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Scan timed out for {image_name}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not parse syft output: {e}")


def _extract_license(licenses: list) -> str | None:
    if not licenses:
        return None
    first = licenses[0]
    if isinstance(first, dict):
        return first.get("value") or first.get("spdxExpression")
    return first if isinstance(first, str) else None