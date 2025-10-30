from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from accounting_service import AccountingService
from activity_logger import ActivityLogger
import shutil
import base64

# Import CRM module
from crm.controllers import CRMController

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize accounting service
accounting = AccountingService(db)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

# Create the main app without a prefix
app = FastAPI()

# Create upload directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    hashed_password: str
    role: str = "admin"  # admin or viewer
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    username: str
    role: str

class CostPriceDetail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_name: str
    category: str  # Hotel/Flight/Land/Other
    amount: float
    payment_date: str
    notes: Optional[str] = ""
    linked_expense_id: Optional[str] = None

class PartialPayment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    amount: float
    bank_name: str
    payment_mode: str
    notes: Optional[str] = ""

class Revenue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    client_name: str
    source: str  # Visa, Ticket, Package, Insurance
    payment_mode: str
    pending_amount: float
    received_amount: float
    status: str  # Pending/Completed
    supplier: Optional[str] = ""
    notes: Optional[str] = ""
    sale_price: Optional[float] = 0.0
    cost_price_details: Optional[List[Dict]] = []
    total_cost_price: Optional[float] = 0.0
    profit: Optional[float] = 0.0
    profit_margin: Optional[float] = 0.0
    partial_payments: Optional[List[Dict]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RevenueCreate(BaseModel):
    date: str
    client_name: str
    source: str
    payment_mode: str
    pending_amount: float
    received_amount: float
    status: str
    supplier: Optional[str] = ""
    notes: Optional[str] = ""
    sale_price: Optional[float] = 0.0
    cost_price_details: Optional[List[Dict]] = []
    partial_payments: Optional[List[Dict]] = []

class RevenueUpdate(BaseModel):
    date: Optional[str] = None
    client_name: Optional[str] = None
    source: Optional[str] = None
    payment_mode: Optional[str] = None
    pending_amount: Optional[float] = None
    received_amount: Optional[float] = None
    status: Optional[str] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None
    sale_price: Optional[float] = None
    cost_price_details: Optional[List[Dict]] = None
    partial_payments: Optional[List[Dict]] = None

class Expense(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    category: str
    payment_mode: str
    amount: float
    description: Optional[str] = ""
    purchase_type: str = "General Expense"
    supplier_gstin: Optional[str] = ""
    invoice_number: Optional[str] = ""
    gst_rate: Optional[float] = 0.0
    linked_revenue_id: Optional[str] = None
    linked_cost_detail_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExpenseCreate(BaseModel):
    date: str
    category: str
    payment_mode: str
    amount: float
    description: Optional[str] = ""
    purchase_type: str = "General Expense"  # General Expense, Purchase for Resale, Office Use
    supplier_gstin: Optional[str] = ""
    invoice_number: Optional[str] = ""
    gst_rate: Optional[float] = 0.0
    linked_revenue_id: Optional[str] = None
    linked_cost_detail_id: Optional[str] = None

class ExpenseUpdate(BaseModel):
    date: Optional[str] = None
    category: Optional[str] = None
    payment_mode: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    purchase_type: Optional[str] = None
    supplier_gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    gst_rate: Optional[float] = None
    linked_revenue_id: Optional[str] = None
    linked_cost_detail_id: Optional[str] = None

# ===== BANK ACCOUNTS MODELS =====
class BankAccountModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bank_name: str
    account_number: str
    ifsc_code: str
    holder_name: str
    account_type: str  # Savings/Current
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BankAccountCreate(BaseModel):
    bank_name: str
    account_number: str
    ifsc_code: str
    holder_name: str
    account_type: str

class BankAccountUpdate(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    holder_name: Optional[str] = None
    account_type: Optional[str] = None

# ===== VENDOR MODELS =====
class VendorModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_name: str
    contact: Optional[str] = ""
    vendor_type: str  # Hotel/Flight/Land/Other
    bank_name: Optional[str] = ""
    bank_account_number: Optional[str] = ""
    bank_ifsc: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VendorCreate(BaseModel):
    vendor_name: str
    contact: Optional[str] = ""
    vendor_type: str
    bank_name: Optional[str] = ""
    bank_account_number: Optional[str] = ""
    bank_ifsc: Optional[str] = ""

class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    contact: Optional[str] = None
    vendor_type: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc: Optional[str] = None

# ===== ACTIVITY LOG MODELS =====
class ActivityLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str  # CREATE/UPDATE/DELETE
    module: str  # Revenue/Expense/Vendor/Bank
    description: str
    user: str = "admin"

class DashboardSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    pending_payments: float
    net_profit: float

class MonthlyData(BaseModel):
    month: str
    revenue: float
    expenses: float

class ReportResponse(BaseModel):
    period: str
    total_revenue: float
    total_expenses: float
    net_profit: float
    revenue_by_source: dict
    expense_by_category: dict

# Helper functions
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("username")
    except JWTError:
        return None

# Initialize admin user
async def init_admin():
    admin = await db.users.find_one({"username": "admin"})
    if not admin:
        hashed_password = pwd_context.hash("admin123")
        admin_user = User(username="admin", hashed_password=hashed_password, role="admin")
        doc = admin_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logging.info("Admin user created with username: admin, password: admin123")
    
    # Create viewer user for CA
    viewer = await db.users.find_one({"username": "viewer"})
    if not viewer:
        hashed_password = pwd_context.hash("viewer123")
        viewer_user = User(username="viewer", hashed_password=hashed_password, role="viewer")
        doc = viewer_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logging.info("Viewer user created with username: viewer, password: viewer123")

@app.on_event("startup")
async def startup_event():
    await init_admin()
    await accounting.initialize_accounts()
    logging.info("Accounting system initialized")

# Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    if not user or not pwd_context.verify(request.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({"username": user['username'], "role": user.get('role', 'admin')}, SECRET_KEY, algorithm=ALGORITHM)
    return LoginResponse(token=token, username=user['username'], role=user.get('role', 'admin'))

# ===== HELPER FUNCTIONS FOR SALE & COST TRACKING =====

def calculate_cost_profit(sale_price: float, cost_price_details: List[Dict]) -> Dict:
    """Calculate total cost, profit, and profit margin"""
    total_cost = sum(detail.get('amount', 0) for detail in cost_price_details)
    profit = sale_price - total_cost
    profit_margin = (profit / sale_price * 100) if sale_price > 0 else 0
    
    return {
        'total_cost_price': total_cost,
        'profit': profit,
        'profit_margin': round(profit_margin, 2)
    }

async def create_linked_expenses(revenue_id: str, revenue_data: dict):
    """Create expense entries from cost_price_details"""
    # Check if auto-expense sync is enabled
    settings = await db.admin_settings.find_one({})
    if settings and not settings.get('auto_expense_sync', True):
        return []
    
    cost_details = revenue_data.get('cost_price_details', [])
    if not cost_details:
        return []
    
    linked_expense_ids = []
    
    for detail in cost_details:
        # Only create expense if payment status is not "Pending" or if it's paid
        payment_status = detail.get('payment_status', 'Done')
        
        expense_data = {
            'id': str(uuid.uuid4()),
            'date': detail.get('payment_date', revenue_data['date']),
            'category': detail.get('category', 'Vendor Payment'),
            'payment_mode': 'Bank Transfer',
            'amount': detail.get('amount', 0),
            'description': f"Auto-generated from Revenue - {revenue_data['client_name']} - Vendor: {detail.get('vendor_name', 'N/A')} - Status: {payment_status}",
            'purchase_type': 'General Expense',
            'supplier_gstin': '',
            'invoice_number': '',
            'gst_rate': 0,
            'linked_revenue_id': revenue_id,
            'linked_cost_detail_id': detail.get('id'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Insert expense
        await db.expenses.insert_one(expense_data)
        
        # Create accounting ledger entry for expense only if payment is Done
        if payment_status == 'Done':
            await accounting.create_expense_ledger_entry(expense_data)
        
        # Update detail with linked_expense_id
        detail['linked_expense_id'] = expense_data['id']
        linked_expense_ids.append(expense_data['id'])
    
    return linked_expense_ids

async def create_partial_payment_ledgers(revenue_id: str, client_name: str, partial_payments: List[Dict]):
    """Create ledger entries for each partial payment"""
    for payment in partial_payments:
        # Create ledger entry for this partial payment
        ledger_entry = {
            'id': str(uuid.uuid4()),
            'date': payment['date'],
            'account': f"Customer - {client_name}",
            'description': f"Partial payment received - {payment['payment_mode']} via {payment['bank_name']}",
            'debit': 0.0,
            'credit': payment['amount'],
            'type': 'credit',
            'reference_id': revenue_id,
            'reference_type': 'partial_payment',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.ledgers.insert_one(ledger_entry)


async def process_vendor_payments(revenue_id: str, cost_price_details: List[Dict]):
    """Process vendor partial payments for each cost detail"""
    for cost_detail in cost_price_details:
        vendor_payments = cost_detail.get('vendor_payments', [])
        if vendor_payments:
            # Create ledger entries for vendor payments
            await accounting.create_vendor_payment_ledger_entries(revenue_id, cost_detail, vendor_payments)


async def update_linked_expenses(revenue_id: str, old_details: List, new_details: List):
    """Update linked expenses based on cost detail changes"""
    settings = await db.admin_settings.find_one({})
    if settings and not settings.get('auto_expense_sync', True):
        return
    
    # Create dict of old details by ID
    old_details_map = {d.get('id'): d for d in old_details if d.get('id')}
    new_details_map = {d.get('id'): d for d in new_details if d.get('id')}
    
    # Find deleted, updated, and added details
    old_ids = set(old_details_map.keys())
    new_ids = set(new_details_map.keys())
    
    deleted_ids = old_ids - new_ids
    added_ids = new_ids - old_ids
    common_ids = old_ids & new_ids
    
    # Delete expenses for removed cost details
    for detail_id in deleted_ids:
        expense_id = old_details_map[detail_id].get('linked_expense_id')
        if expense_id:
            await db.expenses.delete_one({'id': expense_id})
            await db.ledgers.delete_many({'reference_id': expense_id})
    
    # Update expenses for modified cost details
    for detail_id in common_ids:
        old_detail = old_details_map[detail_id]
        new_detail = new_details_map[detail_id]
        
        expense_id = old_detail.get('linked_expense_id')
        if expense_id and new_detail.get('amount') != old_detail.get('amount'):
            # Update expense amount
            old_amount = old_detail.get('amount', 0)
            new_amount = new_detail.get('amount', 0)
            
            await db.expenses.update_one(
                {'id': expense_id},
                {'$set': {'amount': new_amount}}
            )
            
            # Update ledger with difference
            expense = await db.expenses.find_one({'id': expense_id}, {'_id': 0})
            if expense:
                await accounting.update_expense_ledger_entry(expense_id, old_amount, new_amount, expense)
    
    # Create expenses for added cost details
    for detail_id in added_ids:
        detail = new_details_map[detail_id]
        revenue = await db.revenues.find_one({'id': revenue_id}, {'_id': 0})
        
        expense_data = {
            'id': str(uuid.uuid4()),
            'date': detail.get('payment_date', revenue['date']),
            'category': detail.get('category', 'Vendor Payment'),
            'payment_mode': 'Bank Transfer',
            'amount': detail.get('amount', 0),
            'description': f"Auto-generated from Revenue - {revenue['client_name']} - Vendor: {detail.get('vendor_name', 'N/A')}",
            'purchase_type': 'General Expense',
            'linked_revenue_id': revenue_id,
            'linked_cost_detail_id': detail_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.expenses.insert_one(expense_data)
        await accounting.create_expense_ledger_entry(expense_data)
        
        # Update detail with linked_expense_id
        detail['linked_expense_id'] = expense_data['id']

async def delete_linked_expenses(revenue_id: str):
    """Delete all expenses linked to a revenue entry"""
    linked_expenses = await db.expenses.find({'linked_revenue_id': revenue_id}, {'_id': 0}).to_list(100)
    
    for expense in linked_expenses:
        expense_id = expense['id']
        await db.expenses.delete_one({'id': expense_id})
        await db.ledgers.delete_many({'reference_id': expense_id})
        await db.gst_records.delete_many({'reference_id': expense_id})

@api_router.get("/revenue")
async def get_revenues():
    """Get all revenue entries - returns raw data without strict validation"""
    try:
        revenues = await db.revenues.find({}).to_list(1000)
        # Convert ObjectId to string for JSON serialization
        for rev in revenues:
            if '_id' in rev:
                rev['_id'] = str(rev['_id'])
            # Handle datetime conversion
            if isinstance(rev.get('created_at'), str):
                try:
                    rev['created_at'] = datetime.fromisoformat(rev['created_at'])
                except:
                    pass
        return revenues
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching revenues: {str(e)}")

@api_router.post("/revenue", response_model=Revenue)
async def create_revenue(revenue: RevenueCreate):
    revenue_dict = revenue.model_dump()
    
    # Calculate cost, profit, and profit margin
    sale_price = revenue_dict.get('sale_price', 0)
    cost_price_details = revenue_dict.get('cost_price_details', [])
    
    calculations = calculate_cost_profit(sale_price, cost_price_details)
    revenue_dict.update(calculations)
    
    # Auto-set status based on pending amount
    if revenue_dict.get('pending_amount', 0) == 0:
        revenue_dict['status'] = 'Completed'
    else:
        revenue_dict['status'] = 'Pending'
    
    # Create revenue object
    revenue_obj = Revenue(**revenue_dict)
    doc = revenue_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    # Insert revenue
    await db.revenues.insert_one(doc)
    
    # Log activity
    await log_activity("CREATE", "Revenue", f"Created revenue for {revenue_obj.client_name} - ₹{revenue_obj.sale_price or revenue_obj.received_amount}")
    
    # Create linked expenses from cost details
    if cost_price_details:
        linked_expense_ids = await create_linked_expenses(revenue_obj.id, doc)
        # Update the revenue document with linked_expense_ids in cost_price_details
        if linked_expense_ids:
            updated_cost_details = doc.get('cost_price_details', [])
            await db.revenues.update_one(
                {'id': revenue_obj.id},
                {'$set': {'cost_price_details': updated_cost_details}}
            )
    
    # Create ledger entries for partial payments
    partial_payments = revenue_dict.get('partial_payments', [])
    if partial_payments:
        await create_partial_payment_ledgers(revenue_obj.id, revenue_obj.client_name, partial_payments)
    
    # Process vendor partial payments
    if cost_price_details:
        await process_vendor_payments(revenue_obj.id, cost_price_details)
    
    # Create accounting ledger entry if revenue is received/completed
    if revenue_obj.status in ['Received', 'Completed'] and revenue_obj.received_amount > 0:
        await accounting.create_revenue_ledger_entry(doc)
    
    return revenue_obj

@api_router.put("/revenue/{revenue_id}", response_model=Revenue)
async def update_revenue(revenue_id: str, update: RevenueUpdate):
    existing = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Revenue not found")
    
    old_received = existing.get('received_amount', 0)
    old_status = existing.get('status', 'Pending')
    old_cost_details = existing.get('cost_price_details', [])
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Recalculate if sale_price or cost_price_details changed
    if 'sale_price' in update_data or 'cost_price_details' in update_data:
        sale_price = update_data.get('sale_price', existing.get('sale_price', 0))
        cost_details = update_data.get('cost_price_details', existing.get('cost_price_details', []))
        
        calculations = calculate_cost_profit(sale_price, cost_details)
        update_data.update(calculations)
        
        # Update linked expenses
        if 'cost_price_details' in update_data:
            new_cost_details = update_data['cost_price_details']
            await update_linked_expenses(revenue_id, old_cost_details, new_cost_details)
            
            # Handle vendor payment changes
            # For each cost detail, compare old and new vendor payments
            for new_detail in new_cost_details:
                detail_id = new_detail.get('id')
                if detail_id:
                    # Find corresponding old detail
                    old_detail = next((d for d in old_cost_details if d.get('id') == detail_id), None)
                    
                    # Delete old vendor payment ledgers and create new ones
                    if old_detail:
                        await accounting.delete_vendor_payment_ledger_entries(revenue_id, detail_id)
                    
                    # Create new vendor payment ledgers if any
                    vendor_payments = new_detail.get('vendor_payments', [])
                    if vendor_payments:
                        await accounting.create_vendor_payment_ledger_entries(revenue_id, new_detail, vendor_payments)
    
    if update_data:
        await db.revenues.update_one({"id": revenue_id}, {"$set": update_data})
    
    updated = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    # Log activity
    await log_activity("UPDATE", "Revenue", f"Updated revenue for {updated['client_name']}")
    
    # Sync with accounting when status changes to Received or amount changes
    new_received = updated.get('received_amount', 0)
    new_status = updated.get('status', 'Pending')
    
    if (new_status == 'Received' and old_status != 'Received' and new_received > 0):
        # Create new accounting entry (first time marking as received)
        await accounting.create_revenue_ledger_entry(updated)
    elif (new_status == 'Received' and old_status == 'Received' and new_received != old_received):
        # Update existing accounting entry using difference-based approach
        await accounting.update_revenue_ledger_entry(revenue_id, old_received, new_received, updated)
    
    return Revenue(**updated)

@api_router.delete("/revenue/{revenue_id}")
async def delete_revenue(revenue_id: str):
    # Get the revenue entry first to check if it has accounting records
    existing = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Revenue not found")
    
    # Log activity
    await log_activity("DELETE", "Revenue", f"Deleted revenue for {existing['client_name']}")
    
    # Delete all linked expenses first
    await delete_linked_expenses(revenue_id)
    
    # Delete vendor payment ledger entries
    cost_details = existing.get('cost_price_details', [])
    for cost_detail in cost_details:
        detail_id = cost_detail.get('id')
        if detail_id:
            await accounting.delete_vendor_payment_ledger_entries(revenue_id, detail_id)
    
    # Delete from revenues collection
    result = await db.revenues.delete_one({"id": revenue_id})
    
    # Delete all related accounting records
    await db.ledgers.delete_many({"reference_id": revenue_id})
    await db.gst_records.delete_many({"reference_id": revenue_id})
    
    return {"message": "Revenue and related records deleted successfully"}

@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses():
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    for exp in expenses:
        if isinstance(exp.get('created_at'), str):
            exp['created_at'] = datetime.fromisoformat(exp['created_at'])
    return expenses

@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    expense_obj = Expense(**expense.model_dump())
    doc = expense_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.expenses.insert_one(doc)
    
    # Create accounting ledger entry
    await accounting.create_expense_ledger_entry(expense_obj.model_dump())
    
    # If purchase for resale, create GST input record
    if expense_obj.purchase_type == "Purchase for Resale" and expense_obj.gst_rate > 0:
        await accounting.create_input_gst_record(expense_obj.model_dump())
    
    return expense_obj

@api_router.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(expense_id: str, update: ExpenseUpdate):
    existing = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    old_amount = existing.get('amount', 0)
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.expenses.update_one({"id": expense_id}, {"$set": update_data})
    
    updated = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    # Sync with accounting using difference-based approach
    new_amount = updated.get('amount', 0)
    
    if new_amount != old_amount:
        # Update existing ledger entries with the difference
        await accounting.update_expense_ledger_entry(expense_id, old_amount, new_amount, updated)
    
    return Expense(**updated)

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    # Get the expense entry first
    existing = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Delete from expenses collection
    result = await db.expenses.delete_one({"id": expense_id})
    
    # Delete all related accounting records
    await db.ledgers.delete_many({"reference_id": expense_id})
    await db.gst_records.delete_many({"reference_id": expense_id})
    
    return {"message": "Expense and related accounting records deleted successfully"}

@api_router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    revenues = await db.revenues.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(r.get('received_amount', 0) for r in revenues)
    total_expenses = sum(e.get('amount', 0) for e in expenses)
    pending_payments = sum(r.get('pending_amount', 0) for r in revenues if r.get('status') == 'Pending')
    
    return DashboardSummary(
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        pending_payments=pending_payments,
        net_profit=total_revenue - total_expenses
    )

@api_router.get("/dashboard/monthly", response_model=List[MonthlyData])
async def get_monthly_data():
    revenues = await db.revenues.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    
    monthly_rev = {}
    monthly_exp = {}
    
    for r in revenues:
        if r.get('status') == 'Received':
            month = r.get('date', '')[:7]  # YYYY-MM
            monthly_rev[month] = monthly_rev.get(month, 0) + r.get('received_amount', 0)
    
    for e in expenses:
        month = e.get('date', '')[:7]
        monthly_exp[month] = monthly_exp.get(month, 0) + e.get('amount', 0)
    
    all_months = sorted(set(list(monthly_rev.keys()) + list(monthly_exp.keys())))
    result = []
    for month in all_months[-6:]:  # Last 6 months
        result.append(MonthlyData(
            month=month,
            revenue=monthly_rev.get(month, 0),
            expenses=monthly_exp.get(month, 0)
        ))
    
    return result

@api_router.get("/reports", response_model=ReportResponse)
async def get_reports(period: str = "month", year: Optional[int] = None, month: Optional[int] = None):
    revenues = await db.revenues.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    
    # Filter by period
    if period == "month" and year and month:
        period_str = f"{year}-{month:02d}"
        revenues = [r for r in revenues if r.get('date', '').startswith(period_str)]
        expenses = [e for e in expenses if e.get('date', '').startswith(period_str)]
    elif period == "year" and year:
        period_str = str(year)
        revenues = [r for r in revenues if r.get('date', '').startswith(period_str)]
        expenses = [e for e in expenses if e.get('date', '').startswith(period_str)]
    
    total_revenue = sum(r.get('received_amount', 0) for r in revenues if r.get('status') == 'Received')
    total_expenses = sum(e.get('amount', 0) for e in expenses)
    
    # Revenue by source
    rev_by_source = {}
    for r in revenues:
        if r.get('status') == 'Received':
            source = r.get('source', 'Other')
            rev_by_source[source] = rev_by_source.get(source, 0) + r.get('received_amount', 0)
    
    # Expense by category
    exp_by_category = {}
    for e in expenses:
        category = e.get('category', 'Other')
        exp_by_category[category] = exp_by_category.get(category, 0) + e.get('amount', 0)
    
    return ReportResponse(
        period=period_str if 'period_str' in locals() else "all",
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        net_profit=total_revenue - total_expenses,
        revenue_by_source=rev_by_source,
        expense_by_category=exp_by_category
    )

# ===== ACCOUNTING ENDPOINTS =====

@api_router.get("/accounting/chart-of-accounts")
async def get_chart_of_accounts():
    """Get all accounts"""
    accounts = await db.accounts.find({}, {"_id": 0}).sort("type", 1).to_list(1000)
    return {"accounts": accounts}

@api_router.get("/accounting/ledger")
async def get_ledger(account: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get ledger entries"""
    query = {}
    if account:
        query['account'] = account
    if start_date and end_date:
        query['date'] = {'$gte': start_date, '$lte': end_date}
    
    ledger_entries = await db.ledgers.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return {"entries": ledger_entries}

@api_router.get("/accounting/trial-balance")
async def get_trial_balance():
    """Generate trial balance"""
    return await accounting.get_trial_balance()

@api_router.get("/accounting/cash-book")
async def get_cash_book(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get cash book entries"""
    query = {'account': 'Cash'}
    if start_date and end_date:
        query['date'] = {'$gte': start_date, '$lte': end_date}
    
    entries = await db.ledgers.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    # Calculate balance
    opening_balance = 0.0
    closing_balance = 0.0
    for entry in entries:
        if entry['debit'] > 0:
            closing_balance += entry['debit']
        if entry['credit'] > 0:
            closing_balance -= entry['credit']
    
    return {
        "entries": entries,
        "opening_balance": opening_balance,
        "closing_balance": round(closing_balance, 2)
    }

@api_router.get("/accounting/bank-book")
async def get_bank_book(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get bank book entries"""
    query = {'account': {'$regex': 'Bank'}}
    if start_date and end_date:
        query['date'] = {'$gte': start_date, '$lte': end_date}
    
    entries = await db.ledgers.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    # Calculate balance
    opening_balance = 0.0
    closing_balance = 0.0
    for entry in entries:
        if entry['debit'] > 0:
            closing_balance += entry['debit']
        if entry['credit'] > 0:
            closing_balance -= entry['credit']
    
    return {
        "entries": entries,
        "opening_balance": opening_balance,
        "closing_balance": round(closing_balance, 2)
    }

@api_router.get("/accounting/gst-summary")
async def get_gst_summary(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get GST summary"""
    return await accounting.get_gst_summary(start_date, end_date)

@api_router.get("/accounting/gst-invoice/{revenue_id}")
async def get_gst_invoice(revenue_id: str):
    """Get GST invoice data for a revenue entry"""
    revenue = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue not found")
    
    gst_record = await db.gst_records.find_one({"reference_id": revenue_id}, {"_id": 0})
    
    if not gst_record:
        # Generate GST breakdown if not exists
        gst_breakdown = accounting.calculate_gst(revenue['received_amount'], revenue['source'])
        invoice_data = {
            'invoice_number': f"INV-{revenue_id[:8].upper()}",
            'date': revenue['date'],
            'client_name': revenue['client_name'],
            'service_type': revenue['source'],
            'taxable_amount': gst_breakdown['taxable_amount'],
            'cgst': gst_breakdown['cgst'],
            'sgst': gst_breakdown['sgst'],
            'igst': gst_breakdown['igst'],
            'total_gst': gst_breakdown['total_gst'],
            'total_amount': revenue['received_amount'],
            'gst_rate': gst_breakdown['gst_rate']
        }
    else:
        invoice_data = gst_record
    
    return invoice_data

@api_router.post("/accounting/manual-journal")
async def create_manual_journal(entry_data: Dict[str, Any]):
    """Create manual journal entry"""
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    debit_entry = {
        'id': str(uuid.uuid4()),
        'entry_id': entry_id,
        'date': entry_data['date'],
        'account': entry_data['debit_account'],
        'account_type': entry_data['debit_account_type'],
        'debit': entry_data['amount'],
        'credit': 0.0,
        'description': entry_data['narration'],
        'reference_type': 'manual',
        'reference_id': entry_id,
        'created_at': timestamp
    }
    
    credit_entry = {
        'id': str(uuid.uuid4()),
        'entry_id': entry_id,
        'date': entry_data['date'],
        'account': entry_data['credit_account'],
        'account_type': entry_data['credit_account_type'],
        'debit': 0.0,
        'credit': entry_data['amount'],
        'description': entry_data['narration'],
        'reference_type': 'manual',
        'reference_id': entry_id,
        'created_at': timestamp
    }
    
    await db.ledgers.insert_many([debit_entry, credit_entry])
    
    # Update account balances
    await accounting.update_account_balance(entry_data['debit_account'], entry_data['amount'], 'debit')
    await accounting.update_account_balance(entry_data['credit_account'], entry_data['amount'], 'credit')
    
    return {"message": "Journal entry created successfully", "entry_id": entry_id}

# ===== ACTIVITY LOG HELPER =====
async def log_activity(action: str, module: str, description: str, user: str = "admin"):
    """Helper function to log all activities"""
    log = ActivityLog(action=action, module=module, description=description, user=user)
    log_dict = log.model_dump()
    log_dict['timestamp'] = log_dict['timestamp'].isoformat()
    await db.activity_logs.insert_one(log_dict)

# ===== BANK ACCOUNTS ENDPOINTS =====

@api_router.get("/bank-accounts", response_model=List[BankAccountModel])
async def get_bank_accounts():
    accounts = await db.bank_accounts.find({}, {"_id": 0}).to_list(100)
    for acc in accounts:
        if isinstance(acc.get('created_at'), str):
            acc['created_at'] = datetime.fromisoformat(acc['created_at'])
    return accounts

@api_router.post("/bank-accounts", response_model=BankAccountModel)
async def create_bank_account(account: BankAccountCreate):
    account_obj = BankAccountModel(**account.model_dump())
    doc = account_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.bank_accounts.insert_one(doc)
    await log_activity("CREATE", "Bank Account", f"Created bank account: {account.bank_name}")
    return account_obj

@api_router.put("/bank-accounts/{account_id}", response_model=BankAccountModel)
async def update_bank_account(account_id: str, update: BankAccountUpdate):
    existing = await db.bank_accounts.find_one({"id": account_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.bank_accounts.update_one({"id": account_id}, {"$set": update_data})
    
    updated = await db.bank_accounts.find_one({"id": account_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    await log_activity("UPDATE", "Bank Account", f"Updated bank account: {updated['bank_name']}")
    return BankAccountModel(**updated)

@api_router.delete("/bank-accounts/{account_id}")
async def delete_bank_account(account_id: str):
    existing = await db.bank_accounts.find_one({"id": account_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    await db.bank_accounts.delete_one({"id": account_id})
    await log_activity("DELETE", "Bank Account", f"Deleted bank account: {existing['bank_name']}")
    return {"message": "Bank account deleted successfully"}

# ===== VENDOR ENDPOINTS =====

@api_router.get("/vendors", response_model=List[VendorModel])
async def get_vendors():
    vendors = await db.vendors.find({}, {"_id": 0}).to_list(100)
    for vendor in vendors:
        if isinstance(vendor.get('created_at'), str):
            vendor['created_at'] = datetime.fromisoformat(vendor['created_at'])
    return vendors

@api_router.post("/vendors", response_model=VendorModel)
async def create_vendor(vendor: VendorCreate):
    vendor_obj = VendorModel(**vendor.model_dump())
    doc = vendor_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.vendors.insert_one(doc)
    await log_activity("CREATE", "Vendor", f"Created vendor: {vendor.vendor_name}")
    return vendor_obj

@api_router.put("/vendors/{vendor_id}", response_model=VendorModel)
async def update_vendor(vendor_id: str, update: VendorUpdate):
    existing = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.vendors.update_one({"id": vendor_id}, {"$set": update_data})
    
    updated = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    await log_activity("UPDATE", "Vendor", f"Updated vendor: {updated['vendor_name']}")
    return VendorModel(**updated)

@api_router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str):
    existing = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    await db.vendors.delete_one({"id": vendor_id})
    await log_activity("DELETE", "Vendor", f"Deleted vendor: {existing['vendor_name']}")
    return {"message": "Vendor deleted successfully"}

# ===== ACTIVITY LOGS ENDPOINT =====

@api_router.get("/activity-logs")
async def get_activity_logs(limit: int = 100):
    logs = await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

# ===== VENDOR BUSINESS REPORT =====

@api_router.get("/reports/vendor-business")
async def get_vendor_business_report(period: str = "monthly"):
    """Get business done with each vendor"""
    # Aggregate from expenses with linked_revenue_id
    pipeline = [
        {
            "$match": {
                "linked_revenue_id": {"$exists": True, "$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$description",
                "total_amount": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }
        },
        {
            "$sort": {"total_amount": -1}
        }
    ]
    
    results = await db.expenses.aggregate(pipeline).to_list(100)
    
    # Parse vendor names from description
    vendor_report = []
    for result in results:
        desc = result['_id']
        # Extract vendor name from "Auto-generated from Revenue - Client - Vendor: XXX"
        if "Vendor:" in desc:
            vendor_name = desc.split("Vendor:")[-1].strip()
            vendor_report.append({
                "vendor_name": vendor_name,
                "total_business": result['total_amount'],
                "transaction_count": result['transaction_count']
            })
    
    return vendor_report

# ===== ADMIN SETTINGS ENDPOINTS =====

# Pydantic models for settings
class BankAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_holder_name: str
    bank_name: str
    account_number: str
    ifsc_code: str
    branch: str
    upi_id: Optional[str] = ""
    is_default: bool = False

@api_router.get("/admin/settings")
async def get_admin_settings():
    """Get comprehensive admin settings"""
    settings = await db.admin_settings.find_one({}, {"_id": 0})
    if not settings:
        # Return default settings
        return {
            "id": str(uuid.uuid4()),
            # Branding
            "company_name": "Soul Immigration & Travels",
            "company_address": "",
            "company_contact": "",
            "company_email": "",
            "company_tagline": "",
            "logo_path": "",
            "gstin": "",
            # Bank Details (array of accounts)
            "bank_accounts": [],
            # Invoice Customization
            "invoice_prefix": "SOUL",
            "default_tax_percentage": 18.0,
            "invoice_footer": "Thank you for your business!",
            "invoice_terms": "",
            "signature_path": "",
            "show_logo_on_invoice": True,
            # Auto Expense Sync
            "auto_expense_sync": True,
            # Other
            "address": "",
            "phone": "",
            "email": "",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    return settings

@api_router.post("/admin/settings")
async def update_admin_settings(settings: Dict[str, Any]):
    """Update admin settings"""
    settings['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    existing = await db.admin_settings.find_one({})
    if existing:
        await db.admin_settings.update_one({}, {"$set": settings})
    else:
        settings['id'] = str(uuid.uuid4())
        await db.admin_settings.insert_one(settings)
    
    return {"message": "Settings updated successfully", "settings": settings}

@api_router.post("/admin/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload company logo"""
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG, WEBP) are allowed")
    
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"logo_{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return relative path
        return {
            "message": "Logo uploaded successfully",
            "logo_path": f"/uploads/{unique_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload logo: {str(e)}")

@api_router.post("/admin/upload-signature")
async def upload_signature(file: UploadFile = File(...)):
    """Upload digital signature"""
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG, WEBP) are allowed")
    
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"signature_{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return relative path
        return {
            "message": "Signature uploaded successfully",
            "signature_path": f"/uploads/{unique_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload signature: {str(e)}")

@api_router.post("/admin/settings/bank-accounts")
async def add_bank_account(account: BankAccount):
    """Add a new bank account"""
    settings = await db.admin_settings.find_one({})
    
    if not settings:
        # Create default settings with this bank account
        settings = {
            "id": str(uuid.uuid4()),
            "company_name": "Soul Immigration & Travels",
            "bank_accounts": [account.dict()],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admin_settings.insert_one(settings)
    else:
        # If this is marked as default, unset other defaults
        if account.is_default:
            for acc in settings.get('bank_accounts', []):
                acc['is_default'] = False
        
        # Add new account
        bank_accounts = settings.get('bank_accounts', [])
        bank_accounts.append(account.dict())
        await db.admin_settings.update_one(
            {},
            {"$set": {"bank_accounts": bank_accounts, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": "Bank account added successfully", "account": account}

@api_router.put("/admin/settings/bank-accounts/{account_id}")
async def update_bank_account(account_id: str, account_data: Dict[str, Any]):
    """Update a bank account"""
    settings = await db.admin_settings.find_one({})
    
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    bank_accounts = settings.get('bank_accounts', [])
    account_found = False
    
    # If this is marked as default, unset other defaults
    if account_data.get('is_default'):
        for acc in bank_accounts:
            if acc['id'] != account_id:
                acc['is_default'] = False
    
    for i, acc in enumerate(bank_accounts):
        if acc['id'] == account_id:
            bank_accounts[i] = {**acc, **account_data, 'id': account_id}
            account_found = True
            break
    
    if not account_found:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    await db.admin_settings.update_one(
        {},
        {"$set": {"bank_accounts": bank_accounts, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Bank account updated successfully"}

@api_router.delete("/admin/settings/bank-accounts/{account_id}")
async def delete_bank_account(account_id: str):
    """Delete a bank account"""
    settings = await db.admin_settings.find_one({})
    
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    bank_accounts = settings.get('bank_accounts', [])
    original_count = len(bank_accounts)
    bank_accounts = [acc for acc in bank_accounts if acc['id'] != account_id]
    
    # Check if account was actually found and removed
    if len(bank_accounts) == original_count:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    await db.admin_settings.update_one(
        {},
        {"$set": {"bank_accounts": bank_accounts, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Bank account deleted successfully"}

# ===== USER MANAGEMENT ENDPOINTS =====

@api_router.get("/admin/users")
async def get_users():
    """Get all users"""
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(100)
    return {"users": users}

@api_router.post("/admin/users")
async def create_user(user_data: Dict[str, Any]):
    """Create new user"""
    # Check if username exists
    existing = await db.users.find_one({"username": user_data['username']})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = pwd_context.hash(user_data['password'])
    user = {
        'id': str(uuid.uuid4()),
        'username': user_data['username'],
        'hashed_password': hashed_password,
        'role': user_data.get('role', 'viewer'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    return {"message": "User created successfully", "username": user['username']}

@api_router.delete("/admin/users/{username}")
async def delete_user(username: str):
    """Delete user"""
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    
    result = await db.users.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@api_router.put("/admin/users/{username}/password")
async def change_password(username: str, password_data: Dict[str, str]):
    """Change user password"""
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = pwd_context.hash(password_data['new_password'])
    await db.users.update_one({"username": username}, {"$set": {"hashed_password": hashed_password}})
    
    return {"message": "Password updated successfully"}

# ===== DATA MANAGEMENT ENDPOINTS =====

@api_router.delete("/admin/clear-test-data")
async def clear_test_data():
    """Clear all test/demo data from accounting tables"""
    try:
        await db.ledgers.delete_many({})
        await db.gst_records.delete_many({})
        # Reset account balances
        await db.accounts.update_many({}, {"$set": {"balance": 0.0}})
        
        return {"message": "Test data cleared successfully", "cleared": ["ledgers", "gst_records", "account_balances"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/rebuild-accounting")
async def rebuild_accounting_data():
    """Rebuild all accounting entries from existing revenue and expense data"""
    try:
        # Clear existing accounting data
        await db.ledgers.delete_many({})
        await db.gst_records.delete_many({})
        await db.accounts.update_many({}, {"$set": {"balance": 0.0}})
        
        # Rebuild from revenues
        revenues = await db.revenues.find({"status": "Received", "received_amount": {"$gt": 0}}, {"_id": 0}).to_list(1000)
        revenue_count = 0
        for rev in revenues:
            await accounting.create_revenue_ledger_entry(rev)
            revenue_count += 1
        
        # Rebuild from expenses
        expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
        expense_count = 0
        for exp in expenses:
            await accounting.create_expense_ledger_entry(exp)
            if exp.get('purchase_type') == 'Purchase for Resale' and exp.get('gst_rate', 0) > 0:
                await accounting.create_input_gst_record(exp)
            expense_count += 1
        
        return {
            "message": "Accounting data rebuilt successfully",
            "revenues_processed": revenue_count,
            "expenses_processed": expense_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/sync/crm-finance")
async def sync_crm_finance():
    """Sync CRM booked leads with Finance revenue entries"""
    try:
        # Find all booked leads
        booked_leads = await db.leads.find({"status": {"$in": ["Booked", "Converted"]}}).to_list(None)
        
        synced_count = 0
        skipped_count = 0
        
        for lead in booked_leads:
            # Check if revenue already exists
            existing_revenue = await db.revenues.find_one({"lead_id": lead.get("lead_id")})
            
            if not existing_revenue:
                # Create revenue entry
                revenue_data = {
                    "id": str(uuid.uuid4()),
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "client_name": lead["client_name"],
                    "source": lead["lead_type"],
                    "payment_mode": "Pending",
                    "pending_amount": 0.0,
                    "received_amount": 0.0,
                    "status": "Pending",
                    "supplier": "",
                    "notes": f"Synced from CRM lead {lead['lead_id']}",
                    "sale_price": 0.0,
                    "cost_price_details": [],
                    "total_cost_price": 0.0,
                    "profit": 0.0,
                    "profit_margin": 0.0,
                    "partial_payments": [],
                    "lead_id": lead["lead_id"],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.revenues.insert_one(revenue_data)
                
                # Update lead with revenue_id
                await db.leads.update_one(
                    {"_id": lead["_id"]},
                    {"$set": {"revenue_id": revenue_data["id"]}}
                )
                
                synced_count += 1
            else:
                skipped_count += 1
        
        return {
            "success": True,
            "message": "CRM and Finance synced successfully",
            "synced": synced_count,
            "skipped": skipped_count,
            "total_booked_leads": len(booked_leads)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.get("/crm/upcoming-travels-dashboard")
async def get_upcoming_travels_dashboard():
    """Get upcoming travels for next 30 days (for dashboard)"""
    try:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        next_30_days = today + timedelta(days=30)
        
        leads = await db.leads.find({
            "status": {"$in": ["Booked", "Converted"]},
            "travel_date": {
                "$exists": True,
                "$ne": None,
                "$gte": today,
                "$lte": next_30_days
            }
        }).sort("travel_date", 1).to_list(None)
        
        for lead in leads:
            lead["_id"] = str(lead["_id"])
        
        return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Setup CRM routes with DB dependency using app dependency override
from crm.routes import get_crm_controller as crm_get_controller

def get_crm_controller_override():
    return CRMController(db)

app.dependency_overrides[crm_get_controller] = get_crm_controller_override

# Include CRM routes in the API router
from crm import routes as crm_routes
api_router.include_router(crm_routes.router)

# Include the router in the main app
app.include_router(api_router)

# Mount uploads directory for serving files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
