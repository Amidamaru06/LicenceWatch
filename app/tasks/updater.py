import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..database import SessionLocal
from .. import models
from ..services import osv_checker, license_checker

logger    = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def recheck_packages() -> None:
    logger.info("=== Daily recheck starting ===")
    db = SessionLocal()

    try:
        packages = (
            db.query(models.Package)
            .filter(models.Package.status.in_([
                models.PackageStatusEnum.flagged,
                models.PackageStatusEnum.needs_review,
            ]))
            .all()
        )

        if not packages:
            logger.info("Nothing to recheck today.")
            return

        logger.info(f"Rechecking {len(packages)} packages...")
        semaphore = asyncio.Semaphore(10)

        async def _recheck(pkg: models.Package) -> None:
            async with semaphore:
                cve_ids = await osv_checker.check_osv(pkg.name, pkg.version, pkg.ecosystem)

            new_cve_str    = ", ".join(cve_ids) if cve_ids else None
            license_status = license_checker.check_license(pkg.license)
            new_status     = models.PackageStatusEnum.flagged if cve_ids else models.PackageStatusEnum[license_status]

            if new_status != pkg.status or new_cve_str != pkg.cve_ids:
                logger.info(f"  {pkg.name}: {pkg.status.value} → {new_status.value}")
                pkg.status       = new_status
                pkg.cve_ids      = new_cve_str
                pkg.last_checked = datetime.utcnow()

        await asyncio.gather(*[_recheck(p) for p in packages])
        db.commit()
        logger.info("=== Daily recheck complete ===")

    except Exception as e:
        logger.error(f"Daily recheck failed: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(recheck_packages, trigger="interval", hours=24,
                      id="daily_recheck", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started (runs every 24 h).")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)