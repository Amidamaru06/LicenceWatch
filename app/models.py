import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


# --- Enums ---
# These are like a set of fixed choices. Using enums means the database
# will reject any value that isn't in the list (prevents typos).

class ScanStatusEnum(str, enum.Enum):
    """The four possible states a scan can be in."""
    pending  = "pending"   # just created, not started yet
    running  = "running"   # syft is scanning right now
    complete = "complete"  # finished successfully
    failed   = "failed"    # something went wrong


class PackageStatusEnum(str, enum.Enum):
    """How we classify each package after checking its license and CVEs."""
    clean        = "clean"         # safe to use
    needs_review = "needs_review"  # someone should check this
    flagged      = "flagged"       # has a known CVE or bad license


# --- Database tables ---
# Each class below becomes a table in the database.
# Each class attribute with Column(...) becomes a column in that table.

class Scan(Base):
    """
    One row per scan request.
    When the user types 'python:3.12-slim' and clicks SCAN, we create one Scan row.
    """
    __tablename__ = "scans"

    id          = Column(Integer, primary_key=True, index=True)
    image_name  = Column(String, nullable=False)   # e.g. "python:3.12-slim"
    scan_status = Column(Enum(ScanStatusEnum), default=ScanStatusEnum.pending)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # This links a Scan to all its Package rows.
    # cascade="all, delete" means if we delete a Scan, its Packages are deleted too.
    packages = relationship("Package", back_populates="scan", cascade="all, delete")


class Package(Base):
    """
    One row per package found inside a scanned image.
    A single scan can produce hundreds of Package rows.
    """
    __tablename__ = "packages"

    id      = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)  # which scan this belongs to

    name         = Column(String, nullable=False)
    version      = Column(String)
    license      = Column(String)   # e.g. "MIT" or "GPL-3.0-only"
    ecosystem    = Column(String)   # e.g. "PyPI" or "npm"
    status       = Column(Enum(PackageStatusEnum), default=PackageStatusEnum.needs_review)
    cve_ids      = Column(Text)     # comma-separated, e.g. "CVE-2023-1234, CVE-2024-5678"
    last_checked = Column(DateTime, default=datetime.utcnow)

    # This links back to the parent Scan row.
    scan = relationship("Scan", back_populates="packages")