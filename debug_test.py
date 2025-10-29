#!/usr/bin/env python3
"""
Debug test for Sale & Cost Tracking feature
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = "https://budget-tracker-582.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login():
    """Login and get JWT token"""
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        print(f"✅ Logged in as {data.get('username')}")
        return headers
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def debug_revenue_creation():
    """Debug revenue creation with cost details"""
    headers = login()
    if not headers:
        return
    
    print("\n🔍 Testing Revenue Creation with Cost Details...")
    
    # Create revenue with cost details
    revenue_data = {
        "date": "2025-01-28",
        "client_name": "Debug Test Client",
        "source": "Package",
        "payment_mode": "Bank Transfer",
        "pending_amount": 0.0,
        "received_amount": 50000.0,
        "status": "Received",
        "sale_price": 50000.0,
        "cost_price_details": [
            {
                "id": str(uuid.uuid4()),
                "vendor_name": "Debug Hotel",
                "category": "Hotel",
                "amount": 20000,
                "payment_date": "2025-01-28",
                "notes": "Debug test hotel"
            }
        ]
    }
    
    print(f"📤 Sending revenue data: {json.dumps(revenue_data, indent=2)}")
    
    response = requests.post(f"{BACKEND_URL}/revenue", json=revenue_data, headers=headers)
    
    print(f"📥 Response status: {response.status_code}")
    
    if response.status_code == 200:
        revenue_response = response.json()
        print(f"📥 Revenue response: {json.dumps(revenue_response, indent=2)}")
        
        revenue_id = revenue_response.get('id')
        
        # Wait a moment for expense creation
        import time
        time.sleep(2)
        
        # Check expenses
        print("\n🔍 Checking created expenses...")
        expenses_response = requests.get(f"{BACKEND_URL}/expenses", headers=headers)
        
        if expenses_response.status_code == 200:
            expenses = expenses_response.json()
            print(f"📊 Total expenses in system: {len(expenses)}")
            
            # Check for any expenses with our revenue ID
            linked_expenses = [exp for exp in expenses if exp.get('linked_revenue_id') == revenue_id]
            print(f"📊 Found {len(linked_expenses)} linked expenses for revenue {revenue_id}")
            
            # Check for any expenses created recently
            recent_expenses = [exp for exp in expenses if 'Debug Test Client' in exp.get('description', '')]
            print(f"📊 Found {len(recent_expenses)} expenses mentioning 'Debug Test Client'")
            
            for exp in recent_expenses:
                print(f"   - Expense ID: {exp.get('id')}")
                print(f"   - Amount: ₹{exp.get('amount')}")
                print(f"   - Description: {exp.get('description')}")
                print(f"   - Linked Revenue ID: {exp.get('linked_revenue_id')}")
                print(f"   - Created At: {exp.get('created_at')}")
        
        # Check admin settings
        print("\n🔍 Checking admin settings...")
        settings_response = requests.get(f"{BACKEND_URL}/admin/settings", headers=headers)
        
        if settings_response.status_code == 200:
            settings = settings_response.json()
            auto_sync = settings.get('auto_expense_sync', True)
            print(f"📊 Auto-expense sync enabled: {auto_sync}")
        
        # Clean up
        print(f"\n🧹 Cleaning up test revenue...")
        delete_response = requests.delete(f"{BACKEND_URL}/revenue/{revenue_id}", headers=headers)
        print(f"🗑️ Delete response: {delete_response.status_code}")
        
    else:
        print(f"❌ Revenue creation failed: {response.text}")

if __name__ == "__main__":
    debug_revenue_creation()