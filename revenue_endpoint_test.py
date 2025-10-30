#!/usr/bin/env python3
"""
Quick Revenue Endpoint Fix Test
Tests the specific revenue endpoint fix as requested:
1. GET /api/revenue - verify it returns data without errors (even with legacy data)
2. Create a test lead and mark as Booked
3. Verify revenue entry auto-created with correct fields
4. GET /api/revenue again to confirm new entry appears
"""

import requests
import json
import os
import sys
from pathlib import Path
import uuid
import time
from datetime import datetime, timedelta, timezone

# Configuration
BACKEND_URL = "https://budget-tracker-582.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class RevenueEndpointTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
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
                self.log_result("Admin Login", True, f"Successfully logged in as {data.get('username')}")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False
    
    def test_revenue_endpoint_get(self):
        """Test 1: GET /api/revenue - verify it returns data without errors"""
        try:
            print("\n🔍 TEST 1: GET /api/revenue endpoint")
            
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("GET Revenue Endpoint", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            try:
                revenues = response.json()
            except json.JSONDecodeError as e:
                self.log_result("GET Revenue JSON Parse", False, f"Invalid JSON response: {str(e)}")
                return False
            
            if not isinstance(revenues, list):
                self.log_result("GET Revenue Response Type", False, f"Expected list, got {type(revenues)}")
                return False
            
            self.log_result("GET Revenue Endpoint", True, f"✅ Successfully retrieved {len(revenues)} revenue entries")
            
            # Check if we have any legacy data issues
            legacy_issues = []
            for i, revenue in enumerate(revenues):
                if not isinstance(revenue, dict):
                    legacy_issues.append(f"Entry {i}: Not a dict")
                    continue
                
                # Check for common legacy data issues
                if 'service_type' in revenue and 'source' not in revenue:
                    legacy_issues.append(f"Entry {i}: Has 'service_type' but missing 'source'")
                
                if not revenue.get('id'):
                    legacy_issues.append(f"Entry {i}: Missing 'id' field")
            
            if legacy_issues:
                self.log_result("Legacy Data Issues", True, f"Found {len(legacy_issues)} legacy data issues but endpoint still works", legacy_issues[:5])  # Show first 5
            else:
                self.log_result("Legacy Data Check", True, "No legacy data issues found")
            
            return revenues
            
        except Exception as e:
            self.log_result("GET Revenue Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_create_lead_and_book(self):
        """Test 2: Create a test lead and mark as Booked"""
        try:
            print("\n🔍 TEST 2: Create test lead and mark as Booked")
            
            # Step 1: Create lead with status='New'
            lead_data = {
                "client_name": "Revenue Test Client",
                "primary_phone": "+91-9999888777",
                "email": "revenuetest@example.com",
                "lead_type": "Visa",
                "source": "Walk-in",
                "status": "New"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Test Lead", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            response_data = response.json()
            if not response_data.get('success'):
                self.log_result("Create Test Lead", False, "Response success is False", response_data)
                return False
            
            lead = response_data.get('lead')
            lead_id = lead.get('_id')
            lead_code = lead.get('lead_id')
            
            self.log_result("Create Test Lead", True, f"✅ Lead created with ID: {lead_code}")
            
            # Step 2: Update lead status to 'Booked'
            update_data = {"status": "Booked"}
            response = requests.put(f"{self.base_url}/crm/leads/{lead_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Mark Lead as Booked", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            updated_response = response.json()
            if not updated_response.get('success'):
                self.log_result("Mark Lead as Booked", False, "Update response success is False", updated_response)
                return False
            
            updated_lead = updated_response.get('lead')
            if updated_lead.get('status') != 'Booked':
                self.log_result("Lead Status Verification", False, f"Expected Booked, got {updated_lead.get('status')}")
                return False
            
            self.log_result("Mark Lead as Booked", True, f"✅ Lead {lead_code} marked as Booked")
            
            return {
                "lead": updated_lead,
                "lead_id": lead_id,
                "lead_code": lead_code,
                "client_name": lead_data['client_name'],
                "lead_type": lead_data['lead_type']
            }
            
        except Exception as e:
            self.log_result("Create and Book Lead", False, f"Error: {str(e)}")
            return False
    
    def test_verify_auto_revenue_creation(self, lead_info):
        """Test 3: Verify revenue entry auto-created with correct fields"""
        try:
            print("\n🔍 TEST 3: Verify auto-revenue creation")
            
            if not lead_info:
                self.log_result("Auto-Revenue Verification", False, "No lead info provided")
                return False
            
            # Wait a moment for auto-creation to complete
            time.sleep(2)
            
            # Get revenues to find the auto-created one
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Get Revenues for Verification", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            revenues = response.json()
            
            # Find revenue with matching client_name and lead_id
            auto_revenue = None
            for revenue in revenues:
                if (revenue.get('client_name') == lead_info['client_name'] and 
                    revenue.get('lead_id') == lead_info['lead_code']):
                    auto_revenue = revenue
                    break
            
            if not auto_revenue:
                self.log_result("Auto-Revenue Creation", False, f"Revenue entry not found for lead {lead_info['lead_code']}")
                return False
            
            self.log_result("Auto-Revenue Found", True, f"✅ Auto-created revenue found with ID: {auto_revenue.get('id')}")
            
            # Validate revenue fields
            validations = [
                ("client_name", auto_revenue.get('client_name'), lead_info['client_name']),
                ("source", auto_revenue.get('source'), lead_info['lead_type']),
                ("status", auto_revenue.get('status'), "Pending"),
                ("payment_mode", auto_revenue.get('payment_mode'), "Pending"),
                ("lead_id", auto_revenue.get('lead_id'), lead_info['lead_code'])
            ]
            
            validation_errors = []
            for field, actual, expected in validations:
                if actual != expected:
                    validation_errors.append(f"{field}: expected '{expected}', got '{actual}'")
            
            if validation_errors:
                self.log_result("Revenue Field Validation", False, "Field validation failed", validation_errors)
                return False
            
            self.log_result("Revenue Field Validation", True, "✅ All revenue fields are correct")
            
            # Check if revenue has proper structure
            required_fields = ['id', 'date', 'client_name', 'source', 'payment_mode', 'status', 'lead_id']
            missing_fields = []
            for field in required_fields:
                if field not in auto_revenue or auto_revenue[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_result("Revenue Structure Check", False, f"Missing required fields: {missing_fields}")
                return False
            
            self.log_result("Revenue Structure Check", True, "✅ Revenue has all required fields")
            
            return auto_revenue
            
        except Exception as e:
            self.log_result("Auto-Revenue Verification", False, f"Error: {str(e)}")
            return False
    
    def test_revenue_endpoint_after_creation(self, original_count):
        """Test 4: GET /api/revenue again to confirm new entry appears"""
        try:
            print("\n🔍 TEST 4: GET /api/revenue after auto-creation")
            
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("GET Revenue After Creation", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            try:
                revenues = response.json()
            except json.JSONDecodeError as e:
                self.log_result("GET Revenue JSON Parse After", False, f"Invalid JSON response: {str(e)}")
                return False
            
            if not isinstance(revenues, list):
                self.log_result("GET Revenue Response Type After", False, f"Expected list, got {type(revenues)}")
                return False
            
            new_count = len(revenues)
            
            if new_count <= original_count:
                self.log_result("Revenue Count Increase", False, f"Expected count > {original_count}, got {new_count}")
                return False
            
            self.log_result("GET Revenue After Creation", True, f"✅ Successfully retrieved {new_count} revenue entries (increased from {original_count})")
            
            # Verify the endpoint is still working properly after the new entry
            try:
                # Try to access each revenue entry to ensure no serialization issues
                valid_entries = 0
                invalid_entries = []
                
                for i, revenue in enumerate(revenues):
                    if isinstance(revenue, dict) and revenue.get('id'):
                        valid_entries += 1
                    else:
                        invalid_entries.append(i)
                
                if invalid_entries:
                    self.log_result("Revenue Entries Validation", False, f"Found {len(invalid_entries)} invalid entries at positions: {invalid_entries[:5]}")
                    return False
                
                self.log_result("Revenue Entries Validation", True, f"✅ All {valid_entries} revenue entries are valid")
                
            except Exception as e:
                self.log_result("Revenue Entries Validation", False, f"Error validating entries: {str(e)}")
                return False
            
            return revenues
            
        except Exception as e:
            self.log_result("GET Revenue After Creation", False, f"Error: {str(e)}")
            return False
    
    def run_revenue_endpoint_tests(self):
        """Run all revenue endpoint tests"""
        print("=" * 80)
        print("🚀 STARTING REVENUE ENDPOINT FIX TESTS")
        print("=" * 80)
        
        if not self.login():
            print("❌ Login failed - cannot proceed with tests")
            return False
        
        # Test 1: GET /api/revenue - verify it works with legacy data
        initial_revenues = self.test_revenue_endpoint_get()
        if not initial_revenues:
            return False
        
        original_count = len(initial_revenues) if isinstance(initial_revenues, list) else 0
        
        # Test 2: Create test lead and mark as Booked
        lead_info = self.test_create_lead_and_book()
        if not lead_info:
            return False
        
        # Test 3: Verify revenue entry auto-created
        auto_revenue = self.test_verify_auto_revenue_creation(lead_info)
        if not auto_revenue:
            return False
        
        # Test 4: GET /api/revenue again to confirm new entry
        final_revenues = self.test_revenue_endpoint_after_creation(original_count)
        if not final_revenues:
            return False
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 REVENUE ENDPOINT TEST RESULTS")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        print(f"✅ Passed: {passed_tests}/{total_tests} tests")
        
        if passed_tests == total_tests:
            print("🎉 ALL REVENUE ENDPOINT TESTS PASSED!")
            print(f"📈 Revenue count increased from {original_count} to {len(final_revenues)}")
            print(f"🔗 Auto-created revenue ID: {auto_revenue.get('id')}")
            return True
        else:
            failed_tests = [result for result in self.test_results if not result['success']]
            print(f"❌ Failed tests: {len(failed_tests)}")
            for failed in failed_tests:
                print(f"   - {failed['test']}: {failed['message']}")
            return False

def main():
    """Main test execution for Revenue Endpoint Fix"""
    tester = RevenueEndpointTester()
    
    success = tester.run_revenue_endpoint_tests()
    
    if success:
        print("\n🎉 REVENUE ENDPOINT FIX VERIFICATION COMPLETE - ALL TESTS PASSED!")
        return 0
    else:
        print("\n💥 REVENUE ENDPOINT TESTS FAILED - NEEDS INVESTIGATION")
        return 1

if __name__ == "__main__":
    sys.exit(main())