import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..database import SessionLocal
from .. import models
from ..services import osv_checker, license_checker

logger    = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def recheck_packages():
    logger.info("Daily recheck starting...")
    db = SessionLocal()

    try:
        packages_to_check = (
            db.query(models.Package)
            .filter(models.Package.status.in_([
                models.PackageStatusEnum.flagged,
                models.PackageStatusEnum.needs_review, ])).all())

        if not packages_to_check:
            logger.info("No packages need rechecking today.")
            return

        logger.info(f"Rechecking {len(packages_to_check)} packages.")
        semaphore = asyncio.Semaphore(10)

        async def recheck_one(package):
            async with semaphore:
                cve_ids = await osv_checker.check_osv(
                    package_name = package.name,
                    version = package.version,
                    ecosystem = package.ecosystem,)

            license_status = license_checker.check_license(package.license)

            if cve_ids:
                new_status = models.PackageStatusEnum.flagged
            else:
                new_status = models.PackageStatusEnum[license_status]

            new_cve_str = ", ".join(cve_ids) if cve_ids else None

            status_changed = new_status != package.status
            cves_changed   = new_cve_str != package.cve_ids

            if status_changed or cves_changed:
                logger.info(
                    f"{package.name} {package.version}:"
                    f"{package.status.value} {new_status.value}")
                package.status = new_status
                package.cve_ids = new_cve_str
                package.last_checked = datetime.utcnow()

        tasks = [recheck_one(pkg) for pkg in packages_to_check]
        await asyncio.gather(*tasks)

        db.commit()
        logger.info("Daily recheck complete.")

    except Exception as error:
        logger.error(f"Daily recheck failed: {error}", exc_info=True)

    finally:
        db.close()


def start_scheduler():

    scheduler.add_job(
        recheck_packages,
        trigger= "interval",
        hours= 24,
        id = "daily_recheck",
        replace_existing = True,)
    scheduler.start()
    logger.info("Scheduler started — will recheck packages every 24 hours.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")