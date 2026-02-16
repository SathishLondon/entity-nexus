from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

from typing import List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

# --- Enums ---
class EntitySource(str, Enum):
    DNB = "dnb"
    COMPANIES_HOUSE = "companies_house"
    INTERNAL = "internal"

# --- Generic Clean Models ---
class Address(BaseModel):
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None
    full_address: Optional[str] = None

class EntityBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[Address] = None
    industry_code: Optional[str] = None
    legal_form: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_usd: Optional[float] = None
    duns: Optional[str] = None

# --- D&B Specific Models (Partial Reflection of JSON) ---
class DnBCode(BaseModel):
    description: Optional[str] = None
    dnbCode: Optional[int] = None

class DnBAddress(BaseModel):
    addressCountry: Optional[dict] = None # { "isoAlpha2Code": "US" }
    addressLocality: Optional[dict] = None # { "name": "San Francisco" }
    addressRegion: Optional[dict] = None # { "name": "California", "abbreviatedName": "CA" }
    postalCode: Optional[str] = None
    streetAddress: Optional[dict] = None # { "line1": "..." }
    streetNumber: Optional[str] = None
    streetName: Optional[str] = None

class DnBOrganization(BaseModel):
    duns: str
    primaryName: str
    registeredName: Optional[str] = None
    primaryAddress: Optional[DnBAddress] = None
    # Add other fields as needed for mapping

class DnBResponse(BaseModel):
    organization: DnBOrganization

# --- Ingestion & Resolution ---
class EntityIngest(EntityBase):
    source: EntitySource
    source_id: str
    raw_data: Optional[dict] = None # Store complete JSON for audit
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    
class ResolvedEntity(EntityBase):
    id: str # UUID
    confidence_score: float
    sources: List[EntitySource]
    # Lineage: which source provided which field
    field_lineage: dict[str, EntitySource] = {}
