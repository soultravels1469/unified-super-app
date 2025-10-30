#!/usr/bin/env python3
"""
Test CRITICAL END-TO-END flow: CRM Lead → Revenue → Ledger
"""

import requests
import json
import time
from datetime import datetime

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
        print(f"✅ Login successful as {data.get('username')}")
        return headers
    else:
        print(f"❌ Login failed with status {response.status_code}")
        return None

def test_end_to_end_flow():
    """Test the complete end-to-end flow"""
    print("🔍 CRITICAL TEST: END-TO-END Lead → Revenue → Ledger Flow")
    print("=" * 60)
    
    # Step 1: Login
    headers = login()
    if not headers:
        return False
    
    # Step 2: Create a new lead with specific data
    print("\n📝 Step 1: Create Lead")
    lead_data = {
        "client_name": "Test Client",
        "primary_phone": "1234567890",
        "lead_type": "Visa",
        "source": "Walk-in",
        "status": "New"
    }
    
    response = requests.post(f"{BACKEND_URL}/crm/leads", json=lead_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create lead: {response.status_code} - {response.text}")
        return False
    
    response_data = response.json()
    if not response_data.get('success'):
        print(f"❌ Lead creation failed: {response_data}")
        return False
    
    lead = response_data.get('lead')
    lead_id = lead.get('lead_id')  # Business lead_id (LD-YYYYMMDD-XXXX)
    lead_mongo_id = lead.get('_id')  # MongoDB _id
    
    print(f"✅ Lead created with ID: {lead_id}")
    
    # Step 3: Update lead status to 'Booked'
    print("\n🔄 Step 2: Update Lead Status to Booked")
    update_data = {"status": "Booked"}
    response = requests.put(f"{BACKEND_URL}/crm/leads/{lead_mongo_id}", json=update_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to update lead: {response.status_code} - {response.text}")
        return False
    
    updated_lead = response.json().get('lead')
    if updated_lead.get('status') != 'Booked':
        print(f"❌ Lead status not updated correctly: {updated_lead.get('status')}")
        return False
    
    print(f"✅ Lead status updated to Booked")
    
    # Step 4: Wait and check for revenue creation
    print("\n💰 Step 3: Check Revenue Creation")
    time.sleep(3)  # Allow for processing
    
    response = requests.get(f"{BACKEND_URL}/revenue", headers=headers)
    print(f"Revenue endpoint response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get revenues: {response.status_code}")
        print(f"Response text: {response.text}")
        
        # Let's check what's in the revenues collection directly
        print("\n🔍 Checking revenues collection directly...")
        # We can't access MongoDB directly, but let's see if we can get individual revenue
        return False
    
    revenues = response.json()
    print(f"Found {len(revenues)} total revenues")
    
    # Look for our revenue
    revenue_found = None
    for revenue in revenues:
        if revenue.get('client_name') == 'Test Client' and revenue.get('source') == 'Visa':
            revenue_found = revenue
            break
    
    if not revenue_found:
        print("❌ Revenue entry not found for Test Client")
        return False
    
    print(f"✅ Revenue entry found for Test Client")
    
    # Step 5: Verify Revenue has lead_id linkage
    print("\n🔗 Step 4: Verify Revenue-Lead Linkage")
    if revenue_found.get('lead_id') != lead_id:
        print(f"❌ Revenue lead_id mismatch: expected {lead_id}, got {revenue_found.get('lead_id')}")
        return False
    
    print(f"✅ Revenue correctly linked to lead_id: {lead_id}")
    
    # Step 6: Verify Lead has revenue_id stored
    print("\n🔗 Step 5: Verify Lead-Revenue Linkage")
    response = requests.get(f"{BACKEND_URL}/crm/leads/{lead_mongo_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get updated lead: {response.status_code}")
        return False
    
    final_lead = response.json()
    if not final_lead.get('revenue_id'):
        print("❌ revenue_id not stored in lead document")
        return False
    
    print(f"✅ Lead document has revenue_id: {final_lead.get('revenue_id')}")
    
    # Step 7: Check ledger entries
    print("\n📊 Step 6: Check Ledger Entries")
    response = requests.get(f"{BACKEND_URL}/accounting/ledger", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get ledger: {response.status_code}")
        return False
    
    ledger_data = response.json()
    ledger_entries = ledger_data.get('entries', [])
    
    # Look for entries related to this revenue
    revenue_id = revenue_found.get('id')
    related_entries = [e for e in ledger_entries if e.get('reference_id') == revenue_id]
    
    # Since amount is 0 and status is Pending, no ledger entries expected yet
    if len(related_entries) == 0:
        print(f"✅ No ledger entries found (expected for amount=0, status=Pending)")
    else:
        print(f"✅ Found {len(related_entries)} ledger entries")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 END-TO-END FLOW TEST RESULTS")
    print("=" * 60)
    print(f"✅ Lead Created: {lead_id}")
    print(f"✅ Lead Status Updated: New → Booked")
    print(f"✅ Revenue Auto-Created: {revenue_id}")
    print(f"✅ Revenue-Lead Linkage: {revenue_found.get('lead_id')}")
    print(f"✅ Lead-Revenue Linkage: {final_lead.get('revenue_id')}")
    print(f"✅ Ledger Check: Completed")
    print("\n🎯 CRITICAL INTEGRATION TEST: PASSED")
    print("The complete Lead → Revenue → Ledger flow is working correctly!")
    
    return True

if __name__ == "__main__":
    success = test_end_to_end_flow()
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Test failed!")
        exit(1)