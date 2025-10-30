from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentItem(BaseModel):
    file_name: str
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    size: int  # in bytes


class Lead(BaseModel):
    lead_id: Optional[str] = None
    client_name: str
    primary_phone: str
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    lead_type: str  # Visa|Ticket|Package
    source: str  # Instagram|Referral|Walk-in|Website|Other
    reference_from: Optional[str] = None  # lead_id or referral_code
    travel_date: Optional[datetime] = None
    status: str = "New"  # New|In Process|Booked|Cancelled|Converted
    labels: List[str] = []
    notes: Optional[str] = None
    documents: List[DocumentItem] = []
    loyalty_points: int = 0
    referral_code: Optional[str] = None
    referred_clients: List[str] = []
    revenue_id: Optional[str] = None  # Link to finance revenue entry
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LeadCreate(BaseModel):
    client_name: str
    primary_phone: str
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    lead_type: str
    source: str
    reference_from: Optional[str] = None
    travel_date: Optional[datetime] = None
    status: str = "New"
    labels: List[str] = []
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    client_name: Optional[str] = None
    primary_phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    lead_type: Optional[str] = None
    source: Optional[str] = None
    reference_from: Optional[str] = None
    travel_date: Optional[datetime] = None
    status: Optional[str] = None
    labels: Optional[List[str]] = None
    notes: Optional[str] = None
    loyalty_points: Optional[int] = None


class Reminder(BaseModel):
    title: str
    lead_id: Optional[str] = None
    description: Optional[str] = None
    date: datetime
    priority: str = "Medium"  # Low|Medium|High
    created_by: Optional[str] = None
    status: str = "Pending"  # Pending|Done
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReminderCreate(BaseModel):
    title: str
    lead_id: Optional[str] = None
    description: Optional[str] = None
    date: datetime
    priority: str = "Medium"


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
