from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/packages", tags=["packages"])


@router.get("/{package_id}", response_model=schemas.PackageOut)
def get_package(package_id: int, db: Session = Depends(get_db)):
    package = db.query(models.Package).filter(models.Package.id == package_id).first()

    if package is None:
        raise HTTPException(status_code=404, detail=f"Package {package_id} not found")

    return package