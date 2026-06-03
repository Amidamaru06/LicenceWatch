import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class ScanStatusEnum(str, enum.Enum):
    pending = "pending"   
    running = "running"  
    complete = "complete"  
    failed = "failed"   


class PackageStatusEnum(str, enum.Enum):
    clean = "clean"         
    needs_review = "needs_review"  
    flagged = "flagged"      



class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    image_name  = Column(String, nullable=False)   # e.g. "python:3.12-slim"
    scan_status = Column(Enum(ScanStatusEnum), default=ScanStatusEnum.pending)
    created_at  = Column(DateTime, default=datetime.utcnow)

    packages = relationship("Package", back_populates="scan", cascade="all, delete")


class Package(Base):
    __tablename__ = "packages"

    id      = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False) 

    name = Column(String, nullable=False)
    version = Column(String)
    license = Column(String)   
    ecosystem = Column(String)  
    status = Column(Enum(PackageStatusEnum), default=PackageStatusEnum.needs_review)
    cve_ids = Column(Text)     
    last_checked = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="packages")