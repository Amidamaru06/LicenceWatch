from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from .models import ScanStatusEnum, PackageStatusEnum



class PackageOut(BaseModel):

    id:           int
    name:         str
    version:      Optional[str]
    license:      Optional[str]
    ecosystem:    Optional[str]
    status:       PackageStatusEnum
    cve_ids:      Optional[str]   
    last_checked: datetime

    class Config:
        from_attributes = True  



class ScanCreate(BaseModel):
   
    image_name: str            

class ScanOut(BaseModel):
   
    id:          int
    image_name:  str
    scan_status: ScanStatusEnum
    created_at:  datetime
    packages:    List[PackageOut] = []

    @property
    def clean_count(self) -> int:
        return sum(1 for p in self.packages if p.status == PackageStatusEnum.clean)

    @property
    def flagged_count(self) -> int:
        return sum(1 for p in self.packages if p.status == PackageStatusEnum.flagged)

    @property
    def review_count(self) -> int:
        return sum(1 for p in self.packages if p.status == PackageStatusEnum.needs_review)

    class Config:
        from_attributes = True