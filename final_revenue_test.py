#!/usr/bin/env python3
"""
Final Revenue Endpoint Test - Accounting for Legacy Data
Tests the revenue endpoint fix with proper handling of legacy data
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://budget-tracker-582.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class FinalRevenueTest:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {}
        
    def login(self):
        """Login and get JWT token"""
        try:
            login_data = {
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
                print(f"✅ Logged in as {data.get('username')}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def test_revenue_endpoint_with_legacy_data(self):
        """Test 1: GET /api/revenue - verify it handles legacy data correctly"""
        print("\n🔍 TEST 1: GET /api/revenue with legacy data handling")
        
        try:
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ FAIL: GET /api/revenue failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            try:
                revenues = response.json()
            except json.JSONDecodeError as e:
                print(f"❌ FAIL: Invalid JSON response: {str(e)}")
                return False
            
            if not isinstance(revenues, list):
                print(f"❌ FAIL: Expected list, got {type(revenues)}")
                return False
            
            print(f"✅ PASS: Successfully retrieved {len(revenues)} revenue entries")
            
            # Analyze legacy vs new data
            legacy_entries = 0
            new_entries = 0
            
            for revenue in revenues:
                if isinstance(revenue, dict):
                    if '_id' in revenue and 'id' not in revenue:
                        legacy_entries += 1
                    elif 'id' in revenue:
                        new_entries += 1
            
            print(f"📊 Data Analysis: {new_entries} new format, {legacy_entries} legacy format")
            print(f"✅ PASS: Endpoint handles both legacy and new data formats without errors")
            
            return revenues
            
        except Exception as e:
            print(f"❌ FAIL: Error testing revenue endpoint: {str(e)}")
            return False
    
    def test_create_lead_and_auto_revenue(self):
        """Test 2 & 3: Create lead, mark as Booked, verify auto-revenue creation"""
        print("\n🔍 TEST 2 & 3: Create lead and verify auto-revenue creation")
        
        try:
            # Create unique client name
            timestamp = datetime.now().strftime("%H%M%S")
            client_name = f"Final Test Client {timestamp}"
            
            # Step 1: Create lead
            lead_data = {
                "client_name": client_name,
                "primary_phone": f"+91-999{timestamp}",
                "email": f"finaltest{timestamp}@example.com",
                "lead_type": "Visa",
                "source": "Walk-in",
                "status": "New"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ FAIL: Create lead failed with status {response.status_code}")
                return False
            
            response_data = response.json()
            if not response_data.get('success'):
                print(f"❌ FAIL: Lead creation success is False")
                return False
            
            lead = response_data.get('lead')
            lead_id = lead.get('_id')
            lead_code = lead.get('lead_id')
            
            print(f"✅ PASS: Lead created with ID: {lead_code}")
            
            # Step 2: Mark as Booked
            update_data = {"status": "Booked"}
            response = requests.put(f"{self.base_url}/crm/leads/{lead_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ FAIL: Update lead failed with status {response.status_code}")
                return False
            
            updated_response = response.json()
            if not updated_response.get('success'):
                print(f"❌ FAIL: Lead update success is False")
                return False
            
            print(f"✅ PASS: Lead {lead_code} marked as Booked")
            
            # Step 3: Wait and verify auto-revenue creation
            time.sleep(3)  # Allow time for auto-creation
            
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            if response.status_code != 200:
                print(f"❌ FAIL: Get revenues after booking failed")
                return False
            
            revenues = response.json()
            
            # Find the auto-created revenue
            auto_revenue = None
            for revenue in revenues:
                if (isinstance(revenue, dict) and 
                    revenue.get('client_name') == client_name and 
                    revenue.get('lead_id') == lead_code):
                    auto_revenue = revenue
                    break
            
            if not auto_revenue:
                print(f"❌ FAIL: Auto-created revenue not found for lead {lead_code}")
                return False
            
            print(f"✅ PASS: Auto-revenue created with ID: {auto_revenue.get('id')}")
            
            # Verify revenue fields
            expected_fields = {
                'client_name': client_name,
                'source': 'Visa',  # Should match lead_type
                'status': 'Pending',
                'payment_mode': 'Pending',
                'lead_id': lead_code
            }
            
            field_errors = []
            for field, expected_value in expected_fields.items():
                actual_value = auto_revenue.get(field)
                if actual_value != expected_value:
                    field_errors.append(f"{field}: expected '{expected_value}', got '{actual_value}'")
            
            if field_errors:
                print(f"❌ FAIL: Revenue field validation errors:")
                for error in field_errors:
                    print(f"   - {error}")
                return False
            
            print(f"✅ PASS: All revenue fields are correct")
            
            return {
                'lead_code': lead_code,
                'revenue_id': auto_revenue.get('id'),
                'client_name': client_name
            }
            
        except Exception as e:
            print(f"❌ FAIL: Error in lead/revenue creation test: {str(e)}")
            return False
    
    def test_revenue_endpoint_after_creation(self, initial_count, test_info):
        """Test 4: Verify revenue endpoint still works after new entry"""
        print("\n🔍 TEST 4: GET /api/revenue after new entry creation")
        
        try:
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ FAIL: GET /api/revenue failed after creation: {response.status_code}")
                return False
            
            try:
                revenues = response.json()
            except json.JSONDecodeError as e:
                print(f"❌ FAIL: JSON decode error after creation: {str(e)}")
                return False
            
            if not isinstance(revenues, list):
                print(f"❌ FAIL: Expected list after creation, got {type(revenues)}")
                return False
            
            new_count = len(revenues)
            
            if new_count <= initial_count:
                print(f"❌ FAIL: Revenue count did not increase (was {initial_count}, now {new_count})")
                return False
            
            print(f"✅ PASS: Revenue count increased from {initial_count} to {new_count}")
            
            # Verify our new entry is in the list
            found_new_entry = False
            for revenue in revenues:
                if (isinstance(revenue, dict) and 
                    revenue.get('id') == test_info['revenue_id']):
                    found_new_entry = True
                    break
            
            if not found_new_entry:
                print(f"❌ FAIL: New revenue entry not found in updated list")
                return False
            
            print(f"✅ PASS: New revenue entry confirmed in updated list")
            
            # Verify endpoint still handles all entries correctly
            valid_entries = 0
            for revenue in revenues:
                if isinstance(revenue, dict) and (revenue.get('id') or revenue.get('_id')):
                    valid_entries += 1
            
            if valid_entries != new_count:
                print(f"❌ FAIL: Some entries are invalid ({valid_entries}/{new_count} valid)")
                return False
            
            print(f"✅ PASS: All {valid_entries} revenue entries are accessible")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL: Error testing revenue endpoint after creation: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all revenue endpoint tests"""
        print("=" * 80)
        print("🚀 FINAL REVENUE ENDPOINT FIX VERIFICATION")
        print("=" * 80)
        
        if not self.login():
            print("❌ Cannot proceed without login")
            return False
        
        # Test 1: GET /api/revenue with legacy data
        initial_revenues = self.test_revenue_endpoint_with_legacy_data()
        if not initial_revenues:
            return False
        
        initial_count = len(initial_revenues)
        
        # Test 2 & 3: Create lead and verify auto-revenue
        test_info = self.test_create_lead_and_auto_revenue()
        if not test_info:
            return False
        
        # Test 4: Verify endpoint still works after new entry
        final_test = self.test_revenue_endpoint_after_creation(initial_count, test_info)
        if not final_test:
            return False
        
        # Summary
        print("\n" + "=" * 80)
        print("🎉 ALL REVENUE ENDPOINT TESTS PASSED!")
        print("=" * 80)
        print(f"✅ Revenue endpoint handles legacy data correctly")
        print(f"✅ Lead → Revenue auto-creation working")
        print(f"✅ New revenue entry: {test_info['revenue_id']}")
        print(f"✅ Endpoint remains stable after new entries")
        print("=" * 80)
        
        return True

def main():
    """Main test execution"""
    tester = FinalRevenueTest()
    
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 REVENUE ENDPOINT FIX VERIFICATION COMPLETE!")
        return 0
    else:
        print("\n💥 REVENUE ENDPOINT TESTS FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())