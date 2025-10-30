from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import uuid

from .models import Lead, LeadCreate, LeadUpdate, Reminder, ReminderCreate, ReminderUpdate
from .utils import generate_lead_id, generate_referral_code


class CRMController:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ============ LEAD OPERATIONS ============
    
    async def create_lead(self, lead_data: LeadCreate, user_id: str) -> dict:
        """Create a new lead"""
        lead_dict = lead_data.dict()
        
        # Generate IDs
        lead_dict["lead_id"] = generate_lead_id()
        lead_dict["referral_code"] = generate_referral_code()
        lead_dict["created_by"] = user_id
        lead_dict["created_at"] = datetime.utcnow()
        lead_dict["updated_at"] = datetime.utcnow()
        lead_dict["documents"] = []
        lead_dict["referred_clients"] = []
        lead_dict["loyalty_points"] = 0
        lead_dict["revenue_id"] = None
        
        # Handle referral
        if lead_dict.get("reference_from"):
            await self._process_referral(lead_dict["reference_from"], lead_dict["lead_id"])
        
        result = await self.db.leads.insert_one(lead_dict)
        lead_dict["_id"] = str(result.inserted_id)
        
        return lead_dict
    
    async def get_leads(
        self,
        skip: int = 0,
        limit: int = 20,
        lead_type: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get leads with filters and pagination"""
        query = {}
        
        if lead_type:
            query["lead_type"] = lead_type
        if status:
            query["status"] = status
        if source:
            query["source"] = source
        
        if search:
            query["$or"] = [
                {"client_name": {"$regex": search, "$options": "i"}},
                {"primary_phone": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"lead_id": {"$regex": search, "$options": "i"}},
                {"referral_code": {"$regex": search, "$options": "i"}}
            ]
        
        if date_from or date_to:
            query["created_at"] = {}
            if date_from:
                query["created_at"]["$gte"] = datetime.fromisoformat(date_from)
            if date_to:
                query["created_at"]["$lte"] = datetime.fromisoformat(date_to)
        
        total = await self.db.leads.count_documents(query)
        leads = await self.db.leads.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Convert ObjectId to string
        for lead in leads:
            lead["_id"] = str(lead["_id"])
        
        return {
            "leads": leads,
            "total": total,
            "page": (skip // limit) + 1,
            "pages": (total + limit - 1) // limit
        }
    
    async def get_lead_by_id(self, lead_id: str) -> Optional[dict]:
        """Get a single lead by ID or lead_id"""
        # Try by ObjectId first
        try:
            lead = await self.db.leads.find_one({"_id": ObjectId(lead_id)})
        except:
            lead = None
        
        # Try by lead_id
        if not lead:
            lead = await self.db.leads.find_one({"lead_id": lead_id})
        
        if lead:
            lead["_id"] = str(lead["_id"])
        
        return lead
    
    async def update_lead(self, lead_id: str, lead_data: LeadUpdate, user_id: str) -> Optional[dict]:
        """Update a lead"""
        lead = await self.get_lead_by_id(lead_id)
        if not lead:
            return None
        
        update_dict = {k: v for k, v in lead_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        # Check if status changed to Booked or Converted
        old_status = lead.get("status")
        new_status = update_dict.get("status")
        
        if new_status in ["Booked", "Converted"] and old_status not in ["Booked", "Converted"]:
            # Auto-create revenue entry
            revenue_id = await self._create_revenue_from_lead(lead, user_id)
            if revenue_id:
                update_dict["revenue_id"] = revenue_id
        
        await self.db.leads.update_one(
            {"_id": ObjectId(lead["_id"])},
            {"$set": update_dict}
        )
        
        return await self.get_lead_by_id(lead_id)
    
    async def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead"""
        lead = await self.get_lead_by_id(lead_id)
        if not lead:
            return False
        
        result = await self.db.leads.delete_one({"_id": ObjectId(lead["_id"])})
        return result.deleted_count > 0
    
    # ============ DOCUMENT OPERATIONS ============
    
    async def add_document(self, lead_id: str, document: dict) -> bool:
        """Add a document to a lead"""
        lead = await self.get_lead_by_id(lead_id)
        if not lead:
            return False
        
        await self.db.leads.update_one(
            {"_id": ObjectId(lead["_id"])},
            {
                "$push": {"documents": document},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return True
    
    async def delete_document(self, lead_id: str, file_path: str) -> bool:
        """Delete a document from a lead"""
        lead = await self.get_lead_by_id(lead_id)
        if not lead:
            return False
        
        await self.db.leads.update_one(
            {"_id": ObjectId(lead["_id"])},
            {
                "$pull": {"documents": {"file_path": file_path}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return True
    
    # ============ REMINDER OPERATIONS ============
    
    async def create_reminder(self, reminder_data: ReminderCreate, user_id: str) -> dict:
        """Create a new reminder"""
        reminder_dict = reminder_data.dict()
        reminder_dict["created_by"] = user_id
        reminder_dict["status"] = "Pending"
        reminder_dict["created_at"] = datetime.utcnow()
        
        result = await self.db.reminders.insert_one(reminder_dict)
        reminder_dict["_id"] = str(result.inserted_id)
        
        return reminder_dict
    
    async def get_reminders(
        self,
        lead_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[dict]:
        """Get reminders with filters"""
        query = {}
        
        if lead_id:
            query["lead_id"] = lead_id
        if status:
            query["status"] = status
        
        if date_from or date_to:
            query["date"] = {}
            if date_from:
                query["date"]["$gte"] = date_from
            if date_to:
                query["date"]["$lte"] = date_to
        
        reminders = await self.db.reminders.find(query).sort("date", 1).to_list(None)
        
        for reminder in reminders:
            reminder["_id"] = str(reminder["_id"])
        
        return reminders
    
    async def update_reminder(self, reminder_id: str, reminder_data: ReminderUpdate) -> Optional[dict]:
        """Update a reminder"""
        update_dict = {k: v for k, v in reminder_data.dict().items() if v is not None}
        
        if not update_dict:
            return None
        
        result = await self.db.reminders.update_one(
            {"_id": ObjectId(reminder_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        reminder = await self.db.reminders.find_one({"_id": ObjectId(reminder_id)})
        if reminder:
            reminder["_id"] = str(reminder["_id"])
        
        return reminder
    
    async def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        result = await self.db.reminders.delete_one({"_id": ObjectId(reminder_id)})
        return result.deleted_count > 0
    
    # ============ DASHBOARD & ANALYTICS ============
    
    async def get_dashboard_summary(self) -> dict:
        """Get dashboard summary with counts and stats"""
        total_leads = await self.db.leads.count_documents({})
        active_leads = await self.db.leads.count_documents({"status": {"$in": ["New", "In Process"]}})
        booked_leads = await self.db.leads.count_documents({"status": {"$in": ["Booked", "Converted"]}})
        
        # Upcoming travels (next 10 days)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        next_10_days = today + timedelta(days=10)
        upcoming_travels = await self.db.leads.count_documents({
            "travel_date": {"$gte": today, "$lte": next_10_days}
        })
        
        # Today's reminders
        tomorrow = today + timedelta(days=1)
        today_reminders = await self.db.reminders.count_documents({
            "date": {"$gte": today, "$lt": tomorrow},
            "status": "Pending"
        })
        
        # Total referrals
        total_referrals = await self.db.leads.count_documents({"reference_from": {"$ne": None}})
        
        return {
            "total_leads": total_leads,
            "active_leads": active_leads,
            "booked_leads": booked_leads,
            "upcoming_travels": upcoming_travels,
            "today_reminders": today_reminders,
            "total_referrals": total_referrals
        }
    
    async def get_monthly_leads(self, year: int) -> List[dict]:
        """Get monthly lead counts for a year"""
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": datetime(year, 1, 1),
                        "$lt": datetime(year + 1, 1, 1)
                    }
                }
            },
            {
                "$group": {
                    "_id": {"$month": "$created_at"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.leads.aggregate(pipeline).to_list(None)
        
        # Fill in missing months with 0
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_data = [{"month": month, "count": 0} for month in months]
        
        for result in results:
            month_idx = result["_id"] - 1
            monthly_data[month_idx]["count"] = result["count"]
        
        return monthly_data
    
    async def get_lead_type_breakdown(self) -> List[dict]:
        """Get lead count by type"""
        pipeline = [
            {"$group": {"_id": "$lead_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.db.leads.aggregate(pipeline).to_list(None)
        return [{"type": r["_id"], "count": r["count"]} for r in results]
    
    async def get_lead_source_breakdown(self) -> List[dict]:
        """Get lead count by source"""
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.db.leads.aggregate(pipeline).to_list(None)
        return [{"source": r["_id"], "count": r["count"]} for r in results]
    
    async def get_referral_leaderboard(self, limit: int = 10) -> List[dict]:
        """Get top referrers"""
        pipeline = [
            {"$match": {"referred_clients": {"$ne": []}}},
            {
                "$project": {
                    "client_name": 1,
                    "referral_code": 1,
                    "referral_count": {"$size": "$referred_clients"},
                    "loyalty_points": 1
                }
            },
            {"$sort": {"referral_count": -1}},
            {"$limit": limit}
        ]
        
        results = await self.db.leads.aggregate(pipeline).to_list(None)
        
        for result in results:
            result["_id"] = str(result["_id"])
        
        return results
    
    async def get_upcoming_travels(self) -> List[dict]:
        """Get leads with travel dates in next 10 days"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        next_10_days = today + timedelta(days=10)
        
        leads = await self.db.leads.find({
            "travel_date": {"$gte": today, "$lte": next_10_days}
        }).sort("travel_date", 1).to_list(None)
        
        for lead in leads:
            lead["_id"] = str(lead["_id"])
        
        return leads
    
    # ============ HELPER METHODS ============
    
    async def _process_referral(self, reference_from: str, new_lead_id: str):
        """Process referral when a new lead is created"""
        # Find the referring lead by referral_code or lead_id
        referring_lead = await self.db.leads.find_one({
            "$or": [
                {"referral_code": reference_from},
                {"lead_id": reference_from}
            ]
        })
        
        if referring_lead:
            # Update referred_clients and loyalty_points
            await self.db.leads.update_one(
                {"_id": referring_lead["_id"]},
                {
                    "$push": {"referred_clients": new_lead_id},
                    "$inc": {"loyalty_points": 10},  # 10 points per referral
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Check if they qualify for Royal Client (5+ referrals)
            updated_lead = await self.db.leads.find_one({"_id": referring_lead["_id"]})
            if len(updated_lead.get("referred_clients", [])) >= 5:
                labels = updated_lead.get("labels", [])
                if "Royal Client" not in labels:
                    labels.append("Royal Client")
                    await self.db.leads.update_one(
                        {"_id": referring_lead["_id"]},
                        {"$set": {"labels": labels}}
                    )
    
    async def _create_revenue_from_lead(self, lead: dict, user_id: str) -> Optional[str]:
        """Create a revenue entry from a lead when marked as Booked/Converted"""
        # Check if revenue already exists
        if lead.get("revenue_id"):
            return lead["revenue_id"]
        
        # Prepare revenue data matching Revenue model
        revenue_data = {
            "id": str(uuid.uuid4()),
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "client_name": lead["client_name"],
            "source": lead["lead_type"],  # Visa|Ticket|Package
            "payment_mode": "Pending",
            "pending_amount": 0.0,
            "received_amount": 0.0,
            "status": "Pending",
            "supplier": "",
            "notes": f"Auto-created from CRM lead {lead['lead_id']}",
            "sale_price": 0.0,
            "cost_price_details": [],
            "total_cost_price": 0.0,
            "profit": 0.0,
            "profit_margin": 0.0,
            "partial_payments": [],
            "lead_id": lead["lead_id"],  # Additional field for CRM linkage
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Call the existing finance revenue endpoint
        try:
            # Insert directly into revenues collection
            result = await self.db.revenues.insert_one(revenue_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating revenue from lead: {e}")
            return None
