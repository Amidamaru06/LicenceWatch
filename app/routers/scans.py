import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db, SessionLocal
from ..services import scanner, license_checker, osv_checker
router = APIRouter(prefix="/api/scans", tags=["scans"])
logger = logging.getLogger(__name__)




@router.post("/", response_model=schemas.ScanOut, status_code=201)
def create_scan(
    scan_data: schemas.ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),):
    new_scan = models.Scan(
        image_name  = scan_data.image_name,
        scan_status = models.ScanStatusEnum.pending,
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan) 
    background_tasks.add_task(run_scan, new_scan.id, scan_data.image_name)

    return new_scan


@router.get("/", response_model=list[schemas.ScanOut])
def list_scans(db: Session = Depends(get_db)):
    """Return all past scans, newest first."""
    all_scans = db.query(models.Scan).order_by(models.Scan.created_at.desc()).all()
    return all_scans


@router.get("/{scan_id}", response_model=schemas.ScanOut)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()

    if scan is None:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    return scan


async def run_scan(scan_id: int, image_name: str):
    db = SessionLocal()

    try:
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        scan.scan_status = models.ScanStatusEnum.running
        db.commit()


        raw_packages = await asyncio.to_thread(scanner.scan_image, image_name)

        semaphore = asyncio.Semaphore(10)

        async def check_one_package_for_cves(pkg):
            async with semaphore:
                return await osv_checker.check_osv(
                    package_name = pkg["name"],
                    version      = pkg.get("version"),
                    ecosystem    = pkg.get("ecosystem"),)
        tasks = [check_one_package_for_cves(pkg) for pkg in raw_packages]
        cve_results = await asyncio.gather(*tasks)

        for pkg_data, cve_ids in zip(raw_packages, cve_results):

    
            license_status = license_checker.check_license(pkg_data["license"])

            if cve_ids:
                final_status = models.PackageStatusEnum.flagged
            else:
                final_status = models.PackageStatusEnum[license_status]

            package = models.Package(
                scan_id      = scan_id,
                name         = pkg_data["name"],
                version      = pkg_data.get("version"),
                license      = pkg_data.get("license"),
                ecosystem    = pkg_data.get("ecosystem"),
                status       = final_status,
                cve_ids      = ", ".join(cve_ids) if cve_ids else None,
                last_checked = datetime.utcnow(),
            )
            db.add(package)

        db.commit()
        scan.scan_status = models.ScanStatusEnum.complete
        db.commit()
        logger.info(f"Scan {scan_id} finished — {len(raw_packages)} packages processed.")

    except Exception as error:
        logger.error(f"Scan {scan_id} failed: {error}", exc_info=True)

        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if scan:
            scan.scan_status = models.ScanStatusEnum.failed
            db.commit()

    finally:
        db.close()