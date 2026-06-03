"""
Reference: https://spdx.org/licenses/
"""

CLEAN_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
    "ISC", "Unlicense", "0BSD", "CC0-1.0", "WTFPL", "Zlib", "Python-2.0",
}

REVIEW_LICENSES = {
    "LGPL-2.0-only", "LGPL-2.0-or-later",
    "LGPL-2.1-only", "LGPL-2.1-or-later",
    "LGPL-3.0-only", "LGPL-3.0-or-later",
    "MPL-2.0", "CDDL-1.0",
    "EPL-1.0", "EPL-2.0",
    "EUPL-1.1", "EUPL-1.2",
    # Short aliases
    "LGPL-2.0", "LGPL-2.1", "LGPL-3.0",
}

FLAGGED_LICENSES = {
    "GPL-1.0-only", "GPL-1.0-or-later",
    "GPL-2.0-only", "GPL-2.0-or-later",
    "GPL-3.0-only", "GPL-3.0-or-later",
    "AGPL-1.0", "AGPL-3.0-only", "AGPL-3.0-or-later",
    "SSPL-1.0", "BUSL-1.1", "Commons-Clause", "PROPRIETARY",
    # Short aliases
    "GPL-2.0", "GPL-3.0", "AGPL-3.0",
}


def check_license(license_str: str | None) -> str:
    if not license_str:
        return "needs_review"

    normalized = license_str.strip()

    if normalized in CLEAN_LICENSES:
        return "clean"
    if normalized in FLAGGED_LICENSES:
        return "flagged"
    if normalized in REVIEW_LICENSES:
        return "needs_review"

    return "needs_review" 