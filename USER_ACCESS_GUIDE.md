# User Access Control - Quick Reference Guide

## 🎭 Role Comparison Matrix

| Feature / Section | Admin | Viewer (CA) |
|-------------------|-------|-------------|
| **Dashboard** |
| View Analytics | ✅ | ✅ |
| View Charts | ✅ | ✅ |
| **Revenue Management** |
| View Revenue Entries | ✅ | ✅ |
| Add Revenue | ✅ | ❌ |
| Edit Revenue | ✅ | ❌ |
| Delete Revenue | ✅ | ❌ |
| **Tour Packages** |
| View Packages | ✅ | ✅ |
| Add Package | ✅ | ❌ |
| Edit Package | ✅ | ❌ |
| Delete Package | ✅ | ❌ |
| **Tickets** |
| View Tickets | ✅ | ✅ |
| Add Ticket | ✅ | ❌ |
| Edit Ticket | ✅ | ❌ |
| Delete Ticket | ✅ | ❌ |
| **Visas** |
| View Visas | ✅ | ✅ |
| Add Visa | ✅ | ❌ |
| Edit Visa | ✅ | ❌ |
| Delete Visa | ✅ | ❌ |
| **Expenses** |
| View Expenses | ✅ | ✅ |
| Add Expense | ✅ | ❌ |
| Edit Expense | ✅ | ❌ |
| Delete Expense | ✅ | ❌ |
| **Pending Payments** |
| View Pending Payments | ✅ | ✅ |
| Search by Client | ✅ | ✅ |
| Edit Partial Payment | ✅ | ❌ |
| Mark as Paid | ✅ | ❌ |
| **Reports** |
| View Reports | ✅ | ✅ |
| Generate Reports | ✅ | ✅ |
| Filter by Date | ✅ | ✅ |
| **Accounting Section** |
| Chart of Accounts | ✅ View | ✅ View |
| Trial Balance | ✅ View | ✅ View |
| Cash/Bank Book | ✅ View | ✅ View |
| GST Summary | ✅ View | ✅ View |
| Manual Journal Entry | ✅ | ❌ |
| **Invoice Generator** |
| View Invoices | ✅ | ✅ |
| Generate Invoice | ✅ | ❌ |
| Edit Invoice | ✅ | ❌ |
| Download PDF | ✅ | ✅ |
| **Admin Settings** |
| Access Page | ✅ | ❌ |
| Edit Company Details | ✅ | ❌ |
| Edit Bank Details | ✅ | ❌ |
| Upload Logo | ✅ | ❌ |
| **User Management** |
| Access Page | ✅ | ❌ |
| Create Users | ✅ | ❌ |
| Delete Users | ✅ | ❌ |
| Reset Passwords | ✅ | ❌ |
| **Data Management** |
| Access Page | ✅ | ❌ |
| Export Data | ✅ | ❌ |
| Clear Test Data | ✅ | ❌ |
| Rebuild Accounting | ✅ | ❌ |

---

## 🔑 Login Credentials

### Admin User
```
Username: admin
Password: admin123
Role: Administrator
Access Level: Full Control
```

**Permissions:**
- ✅ All CRUD operations (Create, Read, Update, Delete)
- ✅ Complete system administration
- ✅ User management
- ✅ Data export/import
- ✅ System configuration

**Use Cases:**
- Daily business operations
- Financial management
- System configuration
- User account management
- Data maintenance

---

### Viewer User (CA Access)
```
Username: viewer
Password: viewer123
Role: Viewer (Chartered Accountant)
Access Level: Read-Only
```

**Permissions:**
- ✅ View all business data
- ✅ View all reports
- ✅ View accounting records
- ✅ Export/view invoices
- ❌ Cannot modify any data
- ❌ No admin access
- ❌ Cannot create/edit/delete entries

**Use Cases:**
- Financial auditing
- Tax filing preparation
- Compliance review
- Performance analysis
- External accountant access

---

## 🚦 Access Control Rules

### Navigation Visibility

**Admin sees:**
```
Main Section:
├── Dashboard
├── Revenue
├── Tour Packages
├── Tickets
├── Visas
├── Expenses
├── Pending Payments
└── Reports

Accounting Section:
├── Chart of Accounts
├── Trial Balance
├── Cash/Bank Book
├── GST Summary
└── Invoices

Admin Section (Collapsible):
├── Settings
├── User Management
└── Data Management
```

**Viewer sees:**
```
Main Section:
├── Dashboard (View only)
├── Revenue (View only)
├── Tour Packages (View only)
├── Tickets (View only)
├── Visas (View only)
├── Expenses (View only)
├── Pending Payments (View only)
└── Reports (View only)

Accounting Section:
├── Chart of Accounts (View only)
├── Trial Balance (View only)
├── Cash/Bank Book (View only)
├── GST Summary (View only)
└── Invoices (View only)

❌ No Admin Section visible
```

---

## 🔐 Security Implementation

### Authentication Flow
1. User enters username and password
2. Backend validates credentials
3. JWT token generated with role information
4. Token stored in localStorage
5. Role checked on every page load
6. UI elements hidden/disabled based on role

### Role Verification
- **Frontend**: UI elements conditionally rendered
- **Backend**: API endpoints check user role
- **Database**: Role stored in user document

### Password Security
- Passwords hashed using bcrypt
- No plain text storage
- Secure password reset flow

---

## 👤 Creating New Users (Admin Only)

### Steps:
1. Navigate to Admin → User Management
2. Click "Add User"
3. Enter details:
   - Username (required)
   - Password (minimum 6 characters)
   - Role (Admin or Viewer)
4. Click "Create User"

### Password Requirements:
- Minimum 6 characters
- No special character requirements (can be added if needed)

### Deleting Users:
- Navigate to User Management
- Click trash icon next to user
- Confirm deletion
- ⚠️ Cannot delete "admin" user (protected)

### Resetting Passwords:
- Click key icon next to user
- Enter new password
- Confirm reset

---

## 📋 Access Control Best Practices

### For Business Owners (Admin):
✅ Change default admin password immediately
✅ Create individual accounts for each team member
✅ Use Viewer role for external accountants/auditors
✅ Regularly review user access in User Management
✅ Disable/delete accounts when employees leave

### For Accountants (Viewer):
✅ Log in with viewer credentials
✅ Review all financial data
✅ Export reports for tax filing
✅ Verify trial balance regularly
✅ Check GST records for compliance
✅ Report any discrepancies to admin

---

## 🔄 Role Change Process

To change a user's role:
1. Admin logs in
2. Navigate to Admin → User Management
3. Delete the user
4. Create new user with same username but different role

**Note**: Currently, role modification requires user recreation. Future updates may add direct role editing.

---

## 🛡️ Security Recommendations

### Password Policy:
- [ ] Change default passwords immediately
- [ ] Use strong passwords (8+ characters, mixed case, numbers, symbols)
- [ ] Don't share passwords
- [ ] Reset passwords every 90 days (recommended)

### Access Management:
- [ ] Grant minimum required access
- [ ] Use Viewer role for read-only needs
- [ ] Regularly audit user list
- [ ] Remove inactive users
- [ ] Monitor login activity

### Data Protection:
- [ ] Use HTTPS in production
- [ ] Enable MongoDB authentication
- [ ] Regular database backups
- [ ] Secure environment variables
- [ ] Monitor API logs

---

## ⚠️ Important Notes

1. **Default Credentials**: Must be changed in production environment
2. **Viewer Limitations**: Cannot create, edit, or delete any data
3. **Admin Protection**: Default "admin" user cannot be deleted
4. **Token Expiry**: JWT tokens don't expire (add expiry in production)
5. **Session Management**: Users remain logged in until manual logout
6. **Role Enforcement**: Enforced both in frontend and backend

---

## 📞 Troubleshooting Access Issues

### Problem: User Can't Login
**Check:**
- Correct username and password
- User exists in User Management
- Database connection is active
- Backend server is running

### Problem: Viewer Can Edit Data
**Solution:**
- Check user role in User Management
- Verify role is set to "viewer"
- If issue persists, recreate user account

### Problem: Admin Menu Not Showing
**Solution:**
- Verify logged in as admin (not viewer)
- Check sidebar - scroll down to Admin section
- Click Admin section title to expand

### Problem: Can't Create New User
**Solution:**
- Verify logged in as admin
- Check username doesn't already exist
- Ensure password is at least 6 characters
- Check backend logs for errors

---

**Last Updated**: October 2025  
**Document Version**: 1.0
