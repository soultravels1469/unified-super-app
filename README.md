# Soul Immigration & Travels - Unified Business Dashboard

A comprehensive full-stack business management system with integrated accounting, GST tracking, invoice generation, and role-based access control.

## 🚀 Tech Stack

**Frontend:**
- React.js
- Tailwind CSS
- Recharts (for analytics)
- jsPDF (for invoice generation)
- xlsx (for data export)

**Backend:**
- FastAPI (Python)
- Motor (Async MongoDB driver)
- JWT Authentication
- Pydantic for data validation

**Database:**
- MongoDB

---

## 👥 User Roles & Access Control

### 1. **Admin Role** (username: `admin`, password: `admin123`)

**Full System Access** - Complete control over all features

#### Main Operations
✅ Dashboard - View all analytics and charts  
✅ Revenue Management - Add, Edit, Delete revenue entries  
✅ Tour Packages - Manage package bookings  
✅ Tickets - Manage ticket bookings  
✅ Visas - Manage visa services  
✅ Expenses - Add, Edit, Delete expense entries  
✅ Pending Payments - View, Edit partial payments, Mark as paid  
✅ Reports - Generate monthly/yearly reports  

#### Accounting Section
✅ Chart of Accounts - View all accounts  
✅ Trial Balance - View and verify balances  
✅ Cash/Bank Book - View all cash and bank transactions  
✅ GST Summary - View output and input GST  
✅ Invoice Generator - Create, Edit, Download invoices  

#### Admin-Only Features
✅ Admin Settings - Configure company details, GSTIN, logo, bank details  
✅ User Management - Create, Delete users, Reset passwords  
✅ Data Management - Export data, Clear test data, Rebuild accounting  
✅ System Configuration - All administrative controls  

---

### 2. **Viewer Role** (username: `viewer`, password: `viewer123`)

**Read-Only Access** - Perfect for CA (Chartered Accountant) or Auditor

#### View-Only Access To:
✅ Dashboard - View all analytics and charts  
✅ Revenue Entries - View only, cannot add/edit/delete  
✅ Tour Packages - View only  
✅ Tickets - View only  
✅ Visas - View only  
✅ Expenses - View only  
✅ Pending Payments - View only, cannot edit or mark as paid  
✅ Reports - View and export reports  

#### Accounting Section (View-Only)
✅ Chart of Accounts - View all accounts  
✅ Trial Balance - View balances  
✅ Cash/Bank Book - View transactions  
✅ GST Summary - View GST records  
✅ Invoice Generator - View invoices only  

#### Restricted Access
❌ Cannot Add/Edit/Delete any revenue entries  
❌ Cannot Add/Edit/Delete any expense entries  
❌ Cannot Edit partial payments  
❌ Cannot Mark payments as paid  
❌ No access to Admin Settings  
❌ No access to User Management  
❌ No access to Data Management  
❌ Cannot create or edit invoices  

---

## 📊 Feature Overview

### Dashboard
- **4 Key Metrics**: Total Revenue, Total Expenses, Pending Payments, Net Profit
- **Revenue vs Expenses Trend** - Bar chart with monthly comparison
- **Profit/Loss Trend** - Line chart showing business performance
- **Expense Breakdown** - Pie chart by category
- **Revenue by Source** - Pie chart (Visa, Ticket, Package)
- Monthly/Yearly view with date filters

### Revenue Management
- Add revenue entries with auto-calculation
- **Total Amount** field that auto-updates Received & Pending
- Source types: Visa, Ticket, Package, Other
- Payment modes: Cash, UPI, Bank Transfer, Card, Cheque
- Supplier tracking
- Status: Pending/Received (auto-set based on amounts)
- Monthly grouping view

### Expense Management
- Add expense entries with categorization
- **Purchase Type Tagging**:
  - General Expense
  - Purchase for Resale (triggers GST input recording)
  - Office Use
- GST rate selection for purchases (0%, 5%, 12%, 18%)
- Supplier GSTIN and invoice number tracking
- Monthly filtered view

### Pending Payments
- **Search by Client Name** - Real-time filtering
- **Edit Partial Payments** - Record incremental payments
- Month-wise filtering
- Auto-sync with accounting ledger
- Mark as Paid functionality

### Accounting System
- **Double-Entry Bookkeeping** - Automatic ledger creation
- **Chart of Accounts** - Pre-configured account structure
- **Trial Balance** - Real-time balance verification
- **Cash/Bank Book** - Separate tracking for cash and bank
- **GST Tracking**:
  - Output GST (Sales): CGST + SGST breakdown
  - Input GST (Purchases): For "Purchase for Resale" expenses
  - Net GST Payable calculation

### Invoice System
- Generate GST-compliant invoices
- **Edit before download**: Client name, date, invoice number, service type
- Auto-populate company logo and bank details
- PDF download with professional format
- Complete GST breakdown (CGST/SGST)

### Data Management (Admin Only)
- **Export Functionality**:
  - Export Revenue (Excel)
  - Export Expenses (Excel)
  - Export Ledger (Excel)
  - Export Trial Balance (Excel)
  - Export GST Records (Excel)
- **Admin Utilities**:
  - Clear Test Data (Remove all accounting records)
  - Rebuild Accounting (Recreate from revenue/expense data)

---

## 🔄 Automatic Data Synchronization

The system maintains **single source of truth** with automatic sync:

1. **Revenue Entry** (Status: Received) →
   - Creates 4 ledger entries (Debit: Bank/Cash, Credit: Revenue, Credit: CGST, Credit: SGST)
   - Creates GST output record
   - Updates account balances
   - Reflects in Trial Balance

2. **Expense Entry** →
   - Creates 2 ledger entries (Debit: Expense, Credit: Bank/Cash)
   - Updates account balances
   - If "Purchase for Resale": Creates GST input record

3. **Ticket Entry** →
   - Same as Revenue with 5% GST

4. **Partial Payment Edit** →
   - Updates received and pending amounts
   - Creates new ledger entry for additional payment
   - Syncs to accounting section

5. **Revenue/Expense Update** →
   - Deletes old ledger entries
   - Creates new ledger entries
   - Recalculates balances

---

## 🗄️ Database Collections

```javascript
revenues {
  id, date, client_name, source, payment_mode,
  total_amount, received_amount, pending_amount,
  status, supplier, notes, created_at
}

expenses {
  id, date, category, payment_mode, amount,
  purchase_type, supplier_gstin, invoice_number,
  gst_rate, description, created_at
}

accounts {
  id, name, type, code, balance, created_at
}

ledgers {
  id, entry_id, date, account, account_type,
  debit, credit, description, reference_type,
  reference_id, created_at
}

gst_records {
  id, date, type, invoice_number, client_name,
  service_type, taxable_amount, cgst, sgst,
  igst, total_gst, total_amount, gst_rate,
  reference_id, created_at
}

admin_settings {
  id, company_name, gstin, logo_url, bank_name,
  account_number, ifsc_code, branch, address,
  phone, email, updated_at
}

users {
  id, username, hashed_password, role, created_at
}
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB 5.0+

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=soul_immigration_finance
CORS_ORIGINS=*
SECRET_KEY=your-secret-key-here
EOF

# Run backend (development)
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Configure environment variables
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Run frontend (development)
yarn start
```

### Access the Application

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001/api`
- API Docs: `http://localhost:8001/docs`

---

## 🔐 Default Login Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Full system control

### Viewer Account (CA Access)
- **Username**: `viewer`
- **Password**: `viewer123`
- **Access**: Read-only access to all data

**⚠️ IMPORTANT**: Change these passwords in production!

---

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - User login

### Revenue Management
- `GET /api/revenue` - Get all revenues
- `POST /api/revenue` - Create revenue entry
- `PUT /api/revenue/{id}` - Update revenue entry
- `DELETE /api/revenue/{id}` - Delete revenue entry

### Expense Management
- `GET /api/expenses` - Get all expenses
- `POST /api/expenses` - Create expense entry
- `PUT /api/expenses/{id}` - Update expense entry
- `DELETE /api/expenses/{id}` - Delete expense entry

### Dashboard & Reports
- `GET /api/dashboard/summary` - Get summary stats
- `GET /api/dashboard/monthly` - Get monthly data
- `GET /api/reports` - Generate reports (with filters)

### Accounting
- `GET /api/accounting/chart-of-accounts` - Get all accounts
- `GET /api/accounting/ledger` - Get ledger entries
- `GET /api/accounting/trial-balance` - Get trial balance
- `GET /api/accounting/cash-book` - Get cash book
- `GET /api/accounting/bank-book` - Get bank book
- `GET /api/accounting/gst-summary` - Get GST summary
- `GET /api/accounting/gst-invoice/{revenue_id}` - Get invoice data
- `POST /api/accounting/manual-journal` - Create manual journal entry

### Admin (Admin Role Only)
- `GET /api/admin/settings` - Get admin settings
- `POST /api/admin/settings` - Update admin settings
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create new user
- `DELETE /api/admin/users/{username}` - Delete user
- `PUT /api/admin/users/{username}/password` - Change password
- `DELETE /api/admin/clear-test-data` - Clear accounting test data
- `POST /api/admin/rebuild-accounting` - Rebuild accounting from data

---

## 🎨 GST Configuration

### GST Rates by Service
- **Visa Services**: 18% (CGST 9% + SGST 9%)
- **Ticket Booking**: 5% (CGST 2.5% + SGST 2.5%)
- **Tour Packages**: 5% (CGST 2.5% + SGST 2.5%)
- **Other Services**: 18% (CGST 9% + SGST 9%)

### GST Calculation
For a revenue of ₹100,000 (Visa):
- Taxable Amount: ₹84,745.76
- CGST @ 9%: ₹7,627.12
- SGST @ 9%: ₹7,627.12
- Total GST: ₹15,254.24
- Total Amount: ₹100,000

---

## 📤 Export Formats

All exports are in **Excel (.xlsx)** format with current date:
- `Revenue_Export_2025-10-27.xlsx`
- `Expenses_Export_2025-10-27.xlsx`
- `Ledger_Export_2025-10-27.xlsx`
- `Trial_Balance_Export_2025-10-27.xlsx`
- `GST_Records_Export_2025-10-27.xlsx`

---

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth
- **Password Hashing** - bcrypt for password storage
- **Role-Based Access Control** - Admin/Viewer roles
- **CORS Protection** - Configurable origins
- **Input Validation** - Pydantic models
- **SQL Injection Protection** - MongoDB (NoSQL)

---

## 🚀 Deployment (Render)

### Backend Deployment
1. Push code to GitHub
2. Create Web Service on Render
3. Connect GitHub repository
4. Set environment variables:
   - `MONGO_URL`: Your MongoDB connection string
   - `DB_NAME`: soul_immigration_finance
   - `SECRET_KEY`: Generate secure key
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

### Frontend Deployment
1. Create Static Site on Render
2. Connect same GitHub repository
3. Set environment variable:
   - `REACT_APP_BACKEND_URL`: Your backend URL
4. Build command: `yarn install && yarn build`
5. Publish directory: `build`

---

## 📈 Business Metrics

The system tracks:
- **Total Revenue** - All received payments
- **Total Expenses** - All expenditures
- **Pending Payments** - Outstanding amounts
- **Net Profit** - Revenue - Expenses
- **Profit Margin** - (Net Profit / Total Revenue) × 100
- **Cash Flow** - Monthly net profit tracking
- **Revenue by Source** - Visa, Ticket, Package breakdown
- **Expense by Category** - Category-wise analysis

---

## 🧪 Testing Utilities

### Admin Tools (Admin Only)

**Clear Test Data**
- Removes all ledgers and GST records
- Resets account balances to zero
- Keeps revenue and expense data intact
- Use for testing or data cleanup

**Rebuild Accounting**
- Scans all revenue and expense entries
- Recreates ledger entries from scratch
- Regenerates GST records
- Use for data recovery or after bulk imports

---

## 🔧 Troubleshooting

### Issue: Trial Balance Not Balanced
**Solution**: Use "Rebuild Accounting" in Data Management

### Issue: GST Not Showing for Expenses
**Solution**: Ensure expense is marked as "Purchase for Resale" with GST rate

### Issue: Invoice Not Showing Company Logo
**Solution**: Update Logo URL in Admin Settings

### Issue: Viewer Can Edit Data
**Solution**: Check user role in User Management, ensure role is "viewer"

---

## 📞 Support

For technical issues:
1. Check API logs: `tail -f /var/log/supervisor/backend.*.log`
2. Check frontend logs: Browser Console (F12)
3. Verify MongoDB connection
4. Ensure all environment variables are set

---

## 📝 License

Proprietary - Soul Immigration & Travels

---

## 🎯 Roadmap

Future enhancements:
- [ ] Multi-branch support
- [ ] Automated bank reconciliation
- [ ] Payment reminders (WhatsApp/Email)
- [ ] TDS calculation module
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Backup/Restore automation
- [ ] Multi-currency support

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintained by**: Soul Immigration & Travels Tech Team
