import httpx
import logging

logger = logging.getLogger(__name__)
OSV_API_URL = "https://api.osv.dev/v1/query"


async def check_osv(package_name: str,version: str | None, ecosystem: str | None,)-> list[str]:

    if not package_name:
        return []

    payload: dict = {"package": {"name": package_name}}
    if version:
        payload["version"] = version
    if ecosystem:
        payload["package"]["ecosystem"] = ecosystem

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(OSV_API_URL, json=payload)
            response.raise_for_status()

            cve_ids: list[str] = []
            for vuln in response.json().get("vulns", []):
                aliases = vuln.get("aliases", [])
                cve_aliases = [a for a in aliases if a.startswith("CVE-")]
                cve_ids.extend(cve_aliases if cve_aliases else [vuln.get("id", "")])

            return [c for c in cve_ids if c]
    except httpx.HTTPStatusError as e:
        logger.warning(f"OSV API {e.response.status_code} for {package_name}")
    except httpx.TimeoutException:
        logger.warning(f"OSV timeout for {package_name}")
    except Exception as e:
        logger.warning(f"OSV check failed for {package_name}: {e}")
    return []