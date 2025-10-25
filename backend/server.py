from fastapi import FastAPI, APIRouter, HTTPException, Depends
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

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    username: str

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExpenseCreate(BaseModel):
    date: str
    category: str
    payment_mode: str
    amount: float
    description: Optional[str] = ""

class ExpenseUpdate(BaseModel):
    date: Optional[str] = None
    category: Optional[str] = None
    payment_mode: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None

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
        admin_user = User(username="admin", hashed_password=hashed_password)
        doc = admin_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logging.info("Admin user created with username: admin, password: admin123")

@app.on_event("startup")
async def startup_event():
    await init_admin()

# Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    if not user or not pwd_context.verify(request.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({"username": user['username']}, SECRET_KEY, algorithm=ALGORITHM)
    return LoginResponse(token=token, username=user['username'])

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
    return revenue_obj

@api_router.put("/revenue/{revenue_id}", response_model=Revenue)
async def update_revenue(revenue_id: str, update: RevenueUpdate):
    existing = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Revenue not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.revenues.update_one({"id": revenue_id}, {"$set": update_data})
    
    updated = await db.revenues.find_one({"id": revenue_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
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

# Include the router in the main app
app.include_router(api_router)

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
