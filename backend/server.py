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
from datetime import datetime, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from accounting_service import AccountingService
import shutil
import base64

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

class Revenue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    client_name: str
    source: str  # Visa, Ticket, Package
    payment_mode: str
    pending_amount: float
    received_amount: float
    status: str  # Pending/Received
    supplier: Optional[str] = ""
    notes: Optional[str] = ""
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

@api_router.get("/revenue", response_model=List[Revenue])
async def get_revenues():
    revenues = await db.revenues.find({}, {"_id": 0}).to_list(1000)
    for rev in revenues:
        if isinstance(rev.get('created_at'), str):
            rev['created_at'] = datetime.fromisoformat(rev['created_at'])
    return revenues

@api_router.post("/revenue", response_model=Revenue)
async def create_revenue(revenue: RevenueCreate):
    revenue_obj = Revenue(**revenue.model_dump())
    doc = revenue_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.revenues.insert_one(doc)
    
    # Create accounting ledger entry if revenue is received
    if revenue_obj.status == 'Received' and revenue_obj.received_amount > 0:
        await accounting.create_revenue_ledger_entry(revenue_obj.model_dump())
    
    return revenue_obj

@api_router.put("/revenue/{revenue_id}", response_model=Revenue)
async def update_revenue(revenue_id: str, update: RevenueUpdate):
    existing = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Revenue not found")
    
    old_received = existing.get('received_amount', 0)
    old_status = existing.get('status', 'Pending')
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.revenues.update_one({"id": revenue_id}, {"$set": update_data})
    
    updated = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    # Sync with accounting when status changes to Received or amount changes
    new_received = updated.get('received_amount', 0)
    new_status = updated.get('status', 'Pending')
    
    if (new_status == 'Received' and old_status != 'Received' and new_received > 0):
        # Create new accounting entry
        await accounting.create_revenue_ledger_entry(updated)
    elif (new_status == 'Received' and old_status == 'Received' and new_received != old_received):
        # Update existing accounting entry by removing old and creating new
        await db.ledgers.delete_many({"reference_id": revenue_id})
        await db.gst_records.delete_many({"reference_id": revenue_id})
        if new_received > 0:
            await accounting.create_revenue_ledger_entry(updated)
    
    return Revenue(**updated)

@api_router.delete("/revenue/{revenue_id}")
async def delete_revenue(revenue_id: str):
    result = await db.revenues.delete_one({"id": revenue_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Revenue not found")
    return {"message": "Revenue deleted successfully"}

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
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.expenses.update_one({"id": expense_id}, {"$set": update_data})
    
    updated = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Expense(**updated)

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    result = await db.expenses.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

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
