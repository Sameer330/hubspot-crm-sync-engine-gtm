from typing import Optional
from pydantic import BaseModel
from enum import Enum

# ENUMS
class LifecycleStage(str, Enum):
    LEAD = 'lead'
    MQL = 'marketingqualifiedlead'
    SQL = 'salesqualifiedlead'
    OPPORTUNITY = 'opportunity'
    CUSTOMER = 'customer'

class DealStage(str, Enum):
    APPOINTMENT_SCHEDULED = "appointmentscheduled"
    QUALIFIED_TO_BUY = "qualifiedtobuy"
    PRESENTATION_SCHEDULED = "presentationscheduled"
    DECISION_MAKER_BOUGHT_IN = "decisionmakerboughtin"
    CONTRACT_SENT = "contractsent"
    CLOSED_WON = "closedwon"
    CLOSED_LOST = "closedlost"

class SyncAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"

# CLASSES
class CRMContact(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    lifecycle_stage: LifecycleStage = LifecycleStage.LEAD
    job_title: Optional[str] = None

class CRMCompany(BaseModel):
    name: str
    domain: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None

class CRMDeal(BaseModel):
    deal_name: str
    amount: float
    pipeline_stage: DealStage = DealStage.APPOINTMENT_SCHEDULED

class SyncResult(BaseModel):
    action: SyncAction
    contact_id: str
    company_id: str
    deal_id: Optional[str] = None
    is_duplicate: bool