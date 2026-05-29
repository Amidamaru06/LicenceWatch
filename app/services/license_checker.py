CLEAN_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unlicense",
    "0BSD",
    "CC0-1.0",
    "WTFPL",
    "Zlib",
    "Python-2.0",
}
 
REVIEW_LICENSES = {
    "LGPL-2.0-only",
    "LGPL-2.0-or-later",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "MPL-2.0",
    "CDDL-1.0",
    "EPL-1.0",
    "EPL-2.0",
    "EUPL-1.1",
    "EUPL-1.2",
    # Short aliases people also use
    "LGPL-2.0",
    "LGPL-2.1",
    "LGPL-3.0",
}
 
FLAGGED_LICENSES = {
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "SSPL-1.0",
    # Short aliases
    "GPL-2.0",
    "GPL-3.0",
    "AGPL-3.0",
}
 
 
def classify_license(license_str: str) -> str:
    if not license_str or license_str.strip().lower() in ("unknown", "none", ""):
        return "needs_review"
    normalised = license_str.strip().upper()
 
    for lic in FLAGGED_LICENSES:
        if lic.upper() in normalised:
            return "flagged"
 
    for lic in REVIEW_LICENSES:
        if lic.upper() in normalised:
            return "needs_review"
 
    for lic in CLEAN_LICENSES:
        if lic.upper() in normalised:
            return "clean"
 
    return "needs_review"
 
 
def get_license_explanation(license_str: str) -> str:
    status = classify_license(license_str)
 
    explanations = {
        "clean": f"{license_str} is a permissive license. No restrictions on use.",
        "needs_review": (
            f"{license_str or 'Unknown license'} — check whether your use case "
            "complies with this license's conditions before shipping."
        ),
        "flagged": (
            f"{license_str} is a copyleft license. Distributing software that links "
            "to this package may require you to open-source your own code."
        ),
    }
    return explanations[status]
