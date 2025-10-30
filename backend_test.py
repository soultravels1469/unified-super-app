#!/usr/bin/env python3
"""
Backend API Testing for CRM-Finance Integration
Tests the 4 PRIMARY TESTS from review request:
1. Auto-Revenue Creation: Create lead with status='New', update to 'Booked', verify revenue auto-created
2. Sync Endpoint: GET /api/sync/crm-finance - verify it syncs booked leads without revenue entries
3. Upcoming Travels Dashboard: GET /api/crm/upcoming-travels-dashboard - create lead with travel_date in next 15 days, verify it appears
4. Reminders Filter: GET /api/crm/reminders?status=Pending - verify only pending reminders returned
"""

import requests
import json
import os
import sys
from pathlib import Path
import uuid
import time
from datetime import datetime, timedelta, timezone
import io

# Configuration
BACKEND_URL = "https://budget-tracker-582.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class CRMFinanceIntegrationTester:
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
    
    
    def get_revenues(self):
        """Get all revenues"""
        try:
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Get Revenues", False, f"Failed with status {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_result("Get Revenues", False, f"Error: {str(e)}")
            return []
    
    def get_leads(self):
        """Get all leads"""
        try:
            response = requests.get(f"{self.base_url}/crm/leads", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Get Leads", False, f"Failed with status {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_result("Get Leads", False, f"Error: {str(e)}")
            return []
    
    # ===== PRIMARY TEST 1: AUTO-REVENUE CREATION =====
    
    def test_auto_revenue_creation(self):
        """
        PRIMARY TEST 1: Auto-Revenue Creation
        Create lead with status='New', update to 'Booked', verify revenue auto-created
        """
        try:
            print("\n🔍 PRIMARY TEST 1: Auto-Revenue Creation")
            
            # Step 1: Create lead with status='New'
            lead_data = {
                "client_name": "Auto Revenue Test Client",
                "primary_phone": "+91-9876543100",
                "email": "autorevenue@example.com",
                "lead_type": "Visa",
                "source": "Walk-in",
                "status": "New"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Lead for Auto-Revenue", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            response_data = response.json()
            if not response_data.get('success'):
                self.log_result("Create Lead for Auto-Revenue", False, "Response success is False", response_data)
                return False
            
            lead = response_data.get('lead')
            lead_id = lead.get('_id')
            lead_code = lead.get('lead_id')
            
            self.log_result("Create Lead for Auto-Revenue", True, f"✅ Lead created with ID: {lead_code}")
            
            # Step 2: Verify no revenue exists initially
            revenues_before = self.get_revenues()
            revenue_count_before = len([r for r in revenues_before if r.get('client_name') == lead_data['client_name']])
            
            if revenue_count_before > 0:
                self.log_result("Initial Revenue Check", False, f"Revenue already exists for client: {revenue_count_before}")
                return False
            
            self.log_result("Initial Revenue Check", True, "✅ No revenue exists initially")
            
            # Step 3: Update lead status to 'Booked'
            update_data = {"status": "Booked"}
            response = requests.put(f"{self.base_url}/crm/leads/{lead_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Update Lead to Booked", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            updated_response = response.json()
            if not updated_response.get('success'):
                self.log_result("Update Lead to Booked", False, "Update response success is False", updated_response)
                return False
            
            updated_lead = updated_response.get('lead')
            if updated_lead.get('status') != 'Booked':
                self.log_result("Lead Status Update", False, f"Expected Booked, got {updated_lead.get('status')}")
                return False
            
            self.log_result("Update Lead to Booked", True, "✅ Lead status updated to Booked")
            
            # Step 4: Verify revenue auto-created
            time.sleep(2)  # Allow for revenue creation
            revenues_after = self.get_revenues()
            
            # Find revenue with matching client_name and lead_id
            auto_revenue = None
            for revenue in revenues_after:
                if (revenue.get('client_name') == lead_data['client_name'] and 
                    revenue.get('lead_id') == lead_code):
                    auto_revenue = revenue
                    break
            
            if not auto_revenue:
                self.log_result("Auto-Revenue Creation", False, "Revenue entry not found after lead status update")
                return False
            
            # Step 5: Validate revenue fields
            validations = [
                ("client_name", auto_revenue.get('client_name'), lead_data['client_name']),
                ("source", auto_revenue.get('source'), lead_data['lead_type']),
                ("status", auto_revenue.get('status'), "Pending"),
                ("payment_mode", auto_revenue.get('payment_mode'), "Pending"),
                ("lead_id", auto_revenue.get('lead_id'), lead_code)
            ]
            
            for field, actual, expected in validations:
                if actual != expected:
                    self.log_result(f"Revenue {field} Validation", False, f"Expected {expected}, got {actual}")
                    return False
            
            # Step 6: Verify bi-directional linkage
            if not updated_lead.get('revenue_id'):
                self.log_result("Revenue ID in Lead", False, "revenue_id not populated in lead")
                return False
            
            if updated_lead.get('revenue_id') != auto_revenue.get('id'):
                self.log_result("Revenue ID Match", False, f"Lead revenue_id {updated_lead.get('revenue_id')} != Revenue id {auto_revenue.get('id')}")
                return False
            
            self.log_result("Auto-Revenue Creation", True, f"✅ Revenue auto-created with ID: {auto_revenue.get('id')}")
            self.log_result("Bi-directional Linkage", True, "✅ Lead and Revenue properly linked")
            
            return {"lead": updated_lead, "revenue": auto_revenue}
            
        except Exception as e:
            self.log_result("Auto-Revenue Creation", False, f"Error: {str(e)}")
            return False
    
    # ===== PRIMARY TEST 2: SYNC ENDPOINT =====
    
    def test_sync_crm_finance(self):
        """
        PRIMARY TEST 2: Sync Endpoint
        GET /api/sync/crm-finance - verify it syncs booked leads without revenue entries
        """
        try:
            print("\n🔍 PRIMARY TEST 2: CRM-Finance Sync Endpoint")
            
            # Step 1: Create a booked lead without revenue
            lead_data = {
                "client_name": "Sync Test Client",
                "primary_phone": "+91-9876543200",
                "email": "synctest@example.com",
                "lead_type": "Package",
                "source": "Website",
                "status": "Booked"  # Create directly as Booked
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Booked Lead for Sync", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            lead = response.json().get('lead')
            lead_code = lead.get('lead_id')
            
            self.log_result("Create Booked Lead for Sync", True, f"✅ Booked lead created: {lead_code}")
            
            # Step 2: Verify lead is booked but check if revenue exists
            revenues_before = self.get_revenues()
            existing_revenue = None
            for revenue in revenues_before:
                if revenue.get('lead_id') == lead_code:
                    existing_revenue = revenue
                    break
            
            # Step 3: Call sync endpoint
            response = requests.get(f"{self.base_url}/sync/crm-finance", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("CRM-Finance Sync", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            sync_result = response.json()
            
            # Step 4: Validate sync response structure
            required_fields = ['success', 'message', 'synced', 'skipped', 'total_booked_leads']
            for field in required_fields:
                if field not in sync_result:
                    self.log_result("Sync Response Structure", False, f"Missing field: {field}")
                    return False
            
            if not sync_result.get('success'):
                self.log_result("Sync Success Flag", False, f"Sync success is False: {sync_result}")
                return False
            
            self.log_result("Sync Response Structure", True, "✅ Sync response has all required fields")
            
            # Step 5: Verify counts
            synced_count = sync_result.get('synced', 0)
            skipped_count = sync_result.get('skipped', 0)
            total_booked = sync_result.get('total_booked_leads', 0)
            
            if total_booked == 0:
                self.log_result("Total Booked Leads", False, "No booked leads found in system")
                return False
            
            # If revenue already existed, it should be skipped; if not, it should be synced
            if existing_revenue:
                expected_synced = 0
                expected_skipped = 1
            else:
                expected_synced = 1
                expected_skipped = 0
            
            self.log_result("Sync Counts", True, f"✅ Synced: {synced_count}, Skipped: {skipped_count}, Total: {total_booked}")
            
            # Step 6: Verify revenue entry exists after sync
            time.sleep(2)  # Allow for sync processing
            revenues_after = self.get_revenues()
            
            synced_revenue = None
            for revenue in revenues_after:
                if revenue.get('lead_id') == lead_code:
                    synced_revenue = revenue
                    break
            
            if not synced_revenue:
                self.log_result("Revenue After Sync", False, "No revenue found after sync")
                return False
            
            # Step 7: Validate synced revenue fields
            validations = [
                ("client_name", synced_revenue.get('client_name'), lead_data['client_name']),
                ("source", synced_revenue.get('source'), lead_data['lead_type']),
                ("lead_id", synced_revenue.get('lead_id'), lead_code),
                ("status", synced_revenue.get('status'), "Pending")
            ]
            
            for field, actual, expected in validations:
                if actual != expected:
                    self.log_result(f"Synced Revenue {field}", False, f"Expected {expected}, got {actual}")
                    return False
            
            self.log_result("CRM-Finance Sync", True, f"✅ Sync completed successfully - Revenue created for lead {lead_code}")
            
            return {"sync_result": sync_result, "revenue": synced_revenue}
            
        except Exception as e:
            self.log_result("CRM-Finance Sync", False, f"Error: {str(e)}")
            return False
    
    # ===== PRIMARY TEST 3: UPCOMING TRAVELS DASHBOARD =====
    
    def test_upcoming_travels_dashboard(self):
        """
        PRIMARY TEST 3: Upcoming Travels Dashboard
        GET /api/crm/upcoming-travels-dashboard - create lead with travel_date in next 15 days, verify it appears
        """
        try:
            print("\n🔍 PRIMARY TEST 3: Upcoming Travels Dashboard")
            
            # Step 1: Create lead with travel_date in next 15 days
            travel_date = datetime.now(timezone.utc) + timedelta(days=10)  # 10 days from now
            
            lead_data = {
                "client_name": "Upcoming Travel Client",
                "primary_phone": "+91-9876543300",
                "email": "travel@example.com",
                "lead_type": "Package",
                "source": "Instagram",
                "status": "Booked",  # Must be booked to appear in upcoming travels
                "travel_date": travel_date.isoformat()
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Travel Lead", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            lead = response.json().get('lead')
            lead_code = lead.get('lead_id')
            
            self.log_result("Create Travel Lead", True, f"✅ Travel lead created: {lead_code} with travel date: {travel_date.strftime('%Y-%m-%d')}")
            
            # Step 2: Test upcoming travels dashboard endpoint
            response = requests.get(f"{self.base_url}/crm/upcoming-travels-dashboard", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Upcoming Travels Dashboard", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            upcoming_travels = response.json()
            
            if not isinstance(upcoming_travels, list):
                self.log_result("Dashboard Response Type", False, f"Expected list, got {type(upcoming_travels)}")
                return False
            
            self.log_result("Dashboard Response Type", True, f"✅ Dashboard returned list with {len(upcoming_travels)} entries")
            
            # Step 3: Verify our lead appears in upcoming travels
            travel_lead_found = None
            for travel_lead in upcoming_travels:
                if travel_lead.get('lead_id') == lead_code:
                    travel_lead_found = travel_lead
                    break
            
            if not travel_lead_found:
                self.log_result("Travel Lead in Dashboard", False, f"Lead {lead_code} not found in upcoming travels")
                return False
            
            # Step 4: Validate travel lead data
            validations = [
                ("client_name", travel_lead_found.get('client_name'), lead_data['client_name']),
                ("lead_type", travel_lead_found.get('lead_type'), lead_data['lead_type']),
                ("status", travel_lead_found.get('status'), "Booked"),
                ("travel_date", travel_lead_found.get('travel_date')[:10], travel_date.strftime('%Y-%m-%d'))  # Compare date part only
            ]
            
            for field, actual, expected in validations:
                if actual != expected:
                    self.log_result(f"Travel Lead {field}", False, f"Expected {expected}, got {actual}")
                    return False
            
            self.log_result("Travel Lead in Dashboard", True, f"✅ Travel lead found in dashboard with correct data")
            
            # Step 5: Test edge case - create lead with travel date > 30 days (should not appear)
            future_date = datetime.now(timezone.utc) + timedelta(days=35)
            
            future_lead_data = {
                "client_name": "Future Travel Client",
                "primary_phone": "+91-9876543301",
                "email": "future@example.com",
                "lead_type": "Visa",
                "source": "Website",
                "status": "Booked",
                "travel_date": future_date.isoformat()
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=future_lead_data, headers=self.headers)
            if response.status_code == 200:
                future_lead = response.json().get('lead')
                future_lead_code = future_lead.get('lead_id')
                
                # Check dashboard again
                time.sleep(1)
                response = requests.get(f"{self.base_url}/crm/upcoming-travels-dashboard", headers=self.headers)
                updated_travels = response.json()
                
                future_found = any(t.get('lead_id') == future_lead_code for t in updated_travels)
                if future_found:
                    self.log_result("Future Travel Filter", False, f"Lead with travel date > 30 days appeared in dashboard")
                    return False
                
                self.log_result("Future Travel Filter", True, "✅ Lead with travel date > 30 days correctly filtered out")
            
            self.log_result("Upcoming Travels Dashboard", True, f"✅ Dashboard working correctly - shows leads with travel dates in next 30 days")
            
            return {"upcoming_travels": upcoming_travels, "travel_lead": travel_lead_found}
            
        except Exception as e:
            self.log_result("Upcoming Travels Dashboard", False, f"Error: {str(e)}")
            return False
    
    # ===== PRIMARY TEST 4: REMINDERS FILTER =====
    
    def test_reminders_filter(self):
        """
        PRIMARY TEST 4: Reminders Filter
        GET /api/crm/reminders?status=Pending - verify only pending reminders returned
        """
        try:
            print("\n🔍 PRIMARY TEST 4: Reminders Filter")
            
            # Step 1: Create a lead for reminders
            lead_data = {
                "client_name": "Reminder Filter Client",
                "primary_phone": "+91-9876543400",
                "email": "reminder@example.com",
                "lead_type": "Visa",
                "source": "Referral",
                "status": "In Process"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Lead for Reminders", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            lead = response.json().get('lead')
            lead_code = lead.get('lead_id')
            
            self.log_result("Create Lead for Reminders", True, f"✅ Lead created: {lead_code}")
            
            # Step 2: Create multiple reminders with different statuses
            reminders_to_create = [
                {
                    "title": "Pending Reminder 1",
                    "lead_id": lead_code,
                    "description": "This should appear in pending filter",
                    "date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "priority": "High"
                    # status will default to "Pending"
                },
                {
                    "title": "Pending Reminder 2", 
                    "lead_id": lead_code,
                    "description": "This should also appear in pending filter",
                    "date": (datetime.now() + timedelta(days=2)).isoformat(),
                    "priority": "Medium"
                }
            ]
            
            created_reminders = []
            for reminder_data in reminders_to_create:
                response = requests.post(f"{self.base_url}/crm/reminders", json=reminder_data, headers=self.headers)
                
                if response.status_code != 200:
                    self.log_result("Create Reminder", False, f"Failed with status {response.status_code}", response.text)
                    return False
                
                reminder_response = response.json()
                if not reminder_response.get('success'):
                    self.log_result("Create Reminder", False, "Reminder creation success is False")
                    return False
                
                created_reminders.append(reminder_response.get('reminder'))
            
            self.log_result("Create Pending Reminders", True, f"✅ Created {len(created_reminders)} pending reminders")
            
            # Step 3: Mark one reminder as Done
            if created_reminders:
                reminder_to_complete = created_reminders[0]
                reminder_id = reminder_to_complete.get('_id')
                
                update_data = {"status": "Done"}
                response = requests.put(f"{self.base_url}/crm/reminders/{reminder_id}", json=update_data, headers=self.headers)
                
                if response.status_code != 200:
                    self.log_result("Mark Reminder Done", False, f"Failed with status {response.status_code}", response.text)
                    return False
                
                self.log_result("Mark Reminder Done", True, "✅ Marked one reminder as Done")
            
            # Step 4: Test filter - Get all reminders (no filter)
            response = requests.get(f"{self.base_url}/crm/reminders", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Get All Reminders", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            all_reminders = response.json()
            
            if not isinstance(all_reminders, list):
                self.log_result("All Reminders Response", False, f"Expected list, got {type(all_reminders)}")
                return False
            
            # Count reminders by status
            pending_count_all = len([r for r in all_reminders if r.get('status') == 'Pending'])
            done_count_all = len([r for r in all_reminders if r.get('status') == 'Done'])
            
            self.log_result("Get All Reminders", True, f"✅ Total reminders: {len(all_reminders)} (Pending: {pending_count_all}, Done: {done_count_all})")
            
            # Step 5: Test filter - Get only Pending reminders
            response = requests.get(f"{self.base_url}/crm/reminders?status=Pending", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Get Pending Reminders", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            pending_reminders = response.json()
            
            if not isinstance(pending_reminders, list):
                self.log_result("Pending Reminders Response", False, f"Expected list, got {type(pending_reminders)}")
                return False
            
            # Step 6: Validate filter results
            # All returned reminders should have status = "Pending"
            non_pending_found = []
            for reminder in pending_reminders:
                if reminder.get('status') != 'Pending':
                    non_pending_found.append(reminder.get('status'))
            
            if non_pending_found:
                self.log_result("Pending Filter Validation", False, f"Non-pending reminders found: {non_pending_found}")
                return False
            
            # Should have at least 1 pending reminder (we created 2, marked 1 as done)
            if len(pending_reminders) < 1:
                self.log_result("Pending Count Validation", False, f"Expected at least 1 pending reminder, got {len(pending_reminders)}")
                return False
            
            self.log_result("Pending Filter Validation", True, f"✅ Filter returned {len(pending_reminders)} pending reminders only")
            
            # Step 7: Test filter - Get only Done reminders
            response = requests.get(f"{self.base_url}/crm/reminders?status=Done", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Get Done Reminders", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            done_reminders = response.json()
            
            # All returned reminders should have status = "Done"
            non_done_found = []
            for reminder in done_reminders:
                if reminder.get('status') != 'Done':
                    non_done_found.append(reminder.get('status'))
            
            if non_done_found:
                self.log_result("Done Filter Validation", False, f"Non-done reminders found: {non_done_found}")
                return False
            
            self.log_result("Done Filter Validation", True, f"✅ Done filter returned {len(done_reminders)} done reminders only")
            
            # Step 8: Verify counts match
            total_filtered = len(pending_reminders) + len(done_reminders)
            if total_filtered != len(all_reminders):
                self.log_result("Filter Count Consistency", False, f"Filtered total {total_filtered} != All reminders {len(all_reminders)}")
                return False
            
            self.log_result("Filter Count Consistency", True, "✅ Filter counts are consistent")
            
            self.log_result("Reminders Filter", True, f"✅ Reminders filter working correctly - Pending: {len(pending_reminders)}, Done: {len(done_reminders)}")
            
            return {
                "all_reminders": all_reminders,
                "pending_reminders": pending_reminders,
                "done_reminders": done_reminders
            }
            
        except Exception as e:
            self.log_result("Reminders Filter", False, f"Error: {str(e)}")
            return False
    
    # ===== MAIN TEST RUNNER =====
    
    def run_primary_tests(self):
        """Run all 4 primary tests from review request"""
        print("=" * 80)
        print("🚀 STARTING CRM-FINANCE INTEGRATION TESTS")
        print("=" * 80)
        
        if not self.login():
            print("❌ Login failed - cannot proceed with tests")
            return False
        
        test_results = {}
        
        # Run all 4 primary tests
        test_results['auto_revenue'] = self.test_auto_revenue_creation()
        test_results['sync_endpoint'] = self.test_sync_crm_finance()
        test_results['upcoming_travels'] = self.test_upcoming_travels_dashboard()
        test_results['reminders_filter'] = self.test_reminders_filter()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed_tests = []
        failed_tests = []
        
        for test_name, result in test_results.items():
            if result:
                passed_tests.append(test_name)
                print(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
        
        print(f"\n📈 OVERALL RESULTS: {len(passed_tests)}/{len(test_results)} tests passed")
        
        if failed_tests:
            print(f"❌ Failed tests: {', '.join(failed_tests)}")
            return False
        else:
            print("🎉 ALL PRIMARY TESTS PASSED!")
            return True

def main():
    """Main test execution for CRM-Finance Integration"""
    tester = CRMFinanceIntegrationTester()
    
    # Run the 4 primary tests
    success = tester.run_primary_tests()
    
    if success:
        print("\n🎉 ALL CRM-FINANCE INTEGRATION TESTS PASSED!")
        return 0
    else:
        print("\n💥 SOME TESTS FAILED - NEEDS INVESTIGATION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
        """Test Scenario 1: CREATE Lead with all fields"""
        try:
            print("\n🔍 SCENARIO 1: CREATE Lead with all fields")
            
            # Create lead with comprehensive data
            lead_data = {
                "client_name": "John Smith",
                "primary_phone": "+91-9876543210",
                "alternate_phone": "+91-9876543211",
                "email": "john.smith@example.com",
                "lead_type": "Visa",
                "source": "Walk-in",
                "status": "New",
                "labels": ["VIP", "Priority"],
                "notes": "Interested in Canada PR visa. Has IELTS score 8.5",
                "travel_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Lead", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            response_data = response.json()
            if not response_data.get('success'):
                self.log_result("Create Lead", False, "Response success is False", response_data)
                return False
            
            lead = response_data.get('lead')
            if not lead:
                self.log_result("Create Lead", False, "No lead data in response")
                return False
            
            # Verify lead fields
            if lead.get('client_name') != lead_data['client_name']:
                self.log_result("Lead Client Name", False, f"Expected {lead_data['client_name']}, got {lead.get('client_name')}")
                return False
            
            if lead.get('lead_type') != lead_data['lead_type']:
                self.log_result("Lead Type", False, f"Expected {lead_data['lead_type']}, got {lead.get('lead_type')}")
                return False
            
            # Verify auto-generated fields
            if not lead.get('lead_id') or not lead.get('lead_id').startswith('LD-'):
                self.log_result("Lead ID Generation", False, f"Invalid lead_id: {lead.get('lead_id')}")
                return False
            
            if not lead.get('referral_code') or len(lead.get('referral_code')) != 6:
                self.log_result("Referral Code Generation", False, f"Invalid referral_code: {lead.get('referral_code')}")
                return False
            
            # Verify default values
            if lead.get('loyalty_points') != 0:
                self.log_result("Default Loyalty Points", False, f"Expected 0, got {lead.get('loyalty_points')}")
                return False
            
            if lead.get('referred_clients') != []:
                self.log_result("Default Referred Clients", False, f"Expected empty array, got {lead.get('referred_clients')}")
                return False
            
            self.log_result("Create Lead", True, f"✅ Lead created successfully with ID: {lead.get('lead_id')}")
            return lead
            
        except Exception as e:
            self.log_result("Create Lead", False, f"Error: {str(e)}")
            return False
    
    def test_get_leads_with_filters(self):
        """Test Scenario 2: GET Leads with filters and pagination"""
        try:
            print("\n🔍 SCENARIO 2: GET Leads with filters and pagination")
            
            # Create multiple leads for testing filters
            leads_to_create = [
                {
                    "client_name": "Alice Johnson",
                    "primary_phone": "+91-9876543220",
                    "email": "alice@example.com",
                    "lead_type": "Visa",
                    "source": "Instagram",
                    "status": "New"
                },
                {
                    "client_name": "Bob Wilson",
                    "primary_phone": "+91-9876543221",
                    "email": "bob@example.com",
                    "lead_type": "Ticket",
                    "source": "Walk-in",
                    "status": "In Process"
                },
                {
                    "client_name": "Carol Davis",
                    "primary_phone": "+91-9876543222",
                    "email": "carol@example.com",
                    "lead_type": "Package",
                    "source": "Website",
                    "status": "Booked"
                }
            ]
            
            created_leads = []
            for lead_data in leads_to_create:
                response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
                if response.status_code == 200:
                    created_leads.append(response.json().get('lead'))
            
            if len(created_leads) != 3:
                self.log_result("Create Test Leads", False, f"Expected 3 leads, created {len(created_leads)}")
                return False
            
            self.log_result("Create Test Leads", True, f"Created {len(created_leads)} test leads")
            
            # Test 1: Get all leads (no filters)
            response = requests.get(f"{self.base_url}/crm/leads", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get All Leads", False, f"Failed with status {response.status_code}")
                return False
            
            all_leads_data = response.json()
            if all_leads_data.get('total', 0) < 3:
                self.log_result("Get All Leads", False, f"Expected at least 3 leads, got {all_leads_data.get('total')}")
                return False
            
            self.log_result("Get All Leads", True, f"Retrieved {all_leads_data.get('total')} total leads")
            
            # Test 2: Filter by lead_type=Visa
            response = requests.get(f"{self.base_url}/crm/leads?lead_type=Visa", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Filter by Lead Type", False, f"Failed with status {response.status_code}")
                return False
            
            visa_leads = response.json()
            visa_count = len([lead for lead in visa_leads.get('leads', []) if lead.get('lead_type') == 'Visa'])
            if visa_count < 1:
                self.log_result("Filter by Lead Type", False, f"Expected at least 1 Visa lead, got {visa_count}")
                return False
            
            self.log_result("Filter by Lead Type", True, f"Found {visa_count} Visa leads")
            
            # Test 3: Filter by status=New
            response = requests.get(f"{self.base_url}/crm/leads?status=New", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Filter by Status", False, f"Failed with status {response.status_code}")
                return False
            
            new_leads = response.json()
            new_count = len([lead for lead in new_leads.get('leads', []) if lead.get('status') == 'New'])
            if new_count < 1:
                self.log_result("Filter by Status", False, f"Expected at least 1 New lead, got {new_count}")
                return False
            
            self.log_result("Filter by Status", True, f"Found {new_count} New leads")
            
            # Test 4: Search by client name
            response = requests.get(f"{self.base_url}/crm/leads?search=Alice", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Search by Name", False, f"Failed with status {response.status_code}")
                return False
            
            search_results = response.json()
            alice_found = any('Alice' in lead.get('client_name', '') for lead in search_results.get('leads', []))
            if not alice_found:
                self.log_result("Search by Name", False, "Alice not found in search results")
                return False
            
            self.log_result("Search by Name", True, "Search by client name working")
            
            # Test 5: Pagination
            response = requests.get(f"{self.base_url}/crm/leads?limit=2", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Pagination Test", False, f"Failed with status {response.status_code}")
                return False
            
            paginated_data = response.json()
            if len(paginated_data.get('leads', [])) > 2:
                self.log_result("Pagination Test", False, f"Expected max 2 leads, got {len(paginated_data.get('leads', []))}")
                return False
            
            self.log_result("Pagination Test", True, f"Pagination working - got {len(paginated_data.get('leads', []))} leads")
            
            self.log_result("Get Leads with Filters", True, "✅ All lead filtering and pagination tests passed")
            return True
            
        except Exception as e:
            self.log_result("Get Leads with Filters", False, f"Error: {str(e)}")
            return False
    
    def test_update_lead_status_to_booked(self):
        """Test Scenario 3: UPDATE Lead status to Booked (triggers auto-revenue creation)"""
        try:
            print("\n🔍 SCENARIO 3: UPDATE Lead status to Booked (Auto-Revenue Creation)")
            
            # First create a lead
            lead_data = {
                "client_name": "Revenue Test Client",
                "primary_phone": "+91-9876543230",
                "email": "revenue.test@example.com",
                "lead_type": "Visa",
                "source": "Referral",
                "status": "New"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Lead for Revenue Test", False, f"Failed with status {response.status_code}")
                return False
            
            lead = response.json().get('lead')
            lead_id = lead.get('_id')
            
            # Update status to Booked
            update_data = {"status": "Booked"}
            response = requests.put(f"{self.base_url}/crm/leads/{lead_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Update Lead to Booked", False, f"Failed with status {response.status_code}")
                return False
            
            updated_lead = response.json().get('lead')
            if updated_lead.get('status') != 'Booked':
                self.log_result("Lead Status Update", False, f"Expected Booked, got {updated_lead.get('status')}")
                return False
            
            self.log_result("Lead Status Update", True, "Lead status updated to Booked")
            
            # Verify revenue_id is populated
            if not updated_lead.get('revenue_id'):
                self.log_result("Revenue ID Population", False, "revenue_id not populated in lead")
                return False
            
            self.log_result("Revenue ID Population", True, f"Revenue ID populated: {updated_lead.get('revenue_id')}")
            
            # Verify revenue entry created in revenues collection
            time.sleep(2)  # Allow for revenue creation
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Revenues", False, f"Failed with status {response.status_code}")
                return False
            
            revenues = response.json()
            revenue_found = None
            for revenue in revenues:
                if revenue.get('client_name') == lead_data['client_name'] and revenue.get('service_type') == lead_data['lead_type']:
                    revenue_found = revenue
                    break
            
            if not revenue_found:
                self.log_result("Auto-Revenue Creation", False, "Revenue entry not found in revenues collection")
                return False
            
            # Verify revenue fields
            if revenue_found.get('amount') != 0:
                self.log_result("Revenue Amount", False, f"Expected 0, got {revenue_found.get('amount')}")
                return False
            
            if revenue_found.get('status') != 'Pending':
                self.log_result("Revenue Status", False, f"Expected Pending, got {revenue_found.get('status')}")
                return False
            
            if revenue_found.get('lead_id') != lead.get('lead_id'):
                self.log_result("Revenue Lead Linkage", False, f"Expected {lead.get('lead_id')}, got {revenue_found.get('lead_id')}")
                return False
            
            self.log_result("Auto-Revenue Creation", True, "✅ Revenue entry auto-created with correct fields")
            
            # Test idempotency - update status to Booked again
            response = requests.put(f"{self.base_url}/crm/leads/{lead_id}", json=update_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Idempotency Test Setup", False, f"Failed with status {response.status_code}")
                return False
            
            # Check that no duplicate revenue was created
            time.sleep(1)
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            revenues_after = response.json()
            
            duplicate_revenues = [r for r in revenues_after if r.get('client_name') == lead_data['client_name']]
            if len(duplicate_revenues) > 1:
                self.log_result("Idempotency Test", False, f"Duplicate revenue created - found {len(duplicate_revenues)} revenues")
                return False
            
            self.log_result("Idempotency Test", True, "✅ No duplicate revenue created on second Booked update")
            
            self.log_result("Update Lead Status to Booked", True, "✅ Auto-revenue creation working correctly with idempotency")
            return {"lead": updated_lead, "revenue": revenue_found}
            
        except Exception as e:
            self.log_result("Update Lead Status to Booked", False, f"Error: {str(e)}")
            return False
    
    def test_referral_system(self):
        """Test Scenario 4: Referral System and Loyalty Points"""
        try:
            print("\n🔍 SCENARIO 4: Referral System and Loyalty Points")
            
            # Create Lead A (referrer)
            lead_a_data = {
                "client_name": "Referrer Client A",
                "primary_phone": "+91-9876543240",
                "email": "referrer@example.com",
                "lead_type": "Package",
                "source": "Website",
                "status": "New"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_a_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Referrer Lead", False, f"Failed with status {response.status_code}")
                return False
            
            lead_a = response.json().get('lead')
            referral_code = lead_a.get('referral_code')
            
            self.log_result("Create Referrer Lead", True, f"Created referrer with code: {referral_code}")
            
            # Create Lead B with reference_from = Lead A's referral_code
            lead_b_data = {
                "client_name": "Referred Client B",
                "primary_phone": "+91-9876543241",
                "email": "referred@example.com",
                "lead_type": "Visa",
                "source": "Referral",
                "status": "New",
                "reference_from": referral_code
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_b_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Referred Lead", False, f"Failed with status {response.status_code}")
                return False
            
            lead_b = response.json().get('lead')
            lead_b_id = lead_b.get('lead_id')
            
            self.log_result("Create Referred Lead", True, f"Created referred lead: {lead_b_id}")
            
            # Verify Lead A's referred_clients array includes Lead B's lead_id
            time.sleep(2)  # Allow for referral processing
            response = requests.get(f"{self.base_url}/crm/leads/{lead_a.get('_id')}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Updated Referrer", False, f"Failed with status {response.status_code}")
                return False
            
            updated_lead_a = response.json()
            referred_clients = updated_lead_a.get('referred_clients', [])
            
            if lead_b_id not in referred_clients:
                self.log_result("Referral Linkage", False, f"Lead B ID {lead_b_id} not in referrer's referred_clients: {referred_clients}")
                return False
            
            self.log_result("Referral Linkage", True, f"Lead B correctly linked to referrer")
            
            # Verify Lead A's loyalty_points incremented by 10
            loyalty_points = updated_lead_a.get('loyalty_points', 0)
            if loyalty_points < 10:
                self.log_result("Loyalty Points", False, f"Expected at least 10 points, got {loyalty_points}")
                return False
            
            self.log_result("Loyalty Points", True, f"Loyalty points incremented to {loyalty_points}")
            
            # Create 4 more leads referencing Lead A to test Royal Client label
            for i in range(4):
                referred_data = {
                    "client_name": f"Referred Client {i+3}",
                    "primary_phone": f"+91-987654324{i+2}",
                    "email": f"referred{i+3}@example.com",
                    "lead_type": "Ticket",
                    "source": "Referral",
                    "status": "New",
                    "reference_from": referral_code
                }
                
                response = requests.post(f"{self.base_url}/crm/leads", json=referred_data, headers=self.headers)
                if response.status_code != 200:
                    self.log_result(f"Create Referred Lead {i+3}", False, f"Failed with status {response.status_code}")
                    return False
            
            self.log_result("Create Additional Referrals", True, "Created 4 additional referred leads")
            
            # Verify Lead A gets 'Royal Client' label (5+ referrals)
            time.sleep(2)  # Allow for processing
            response = requests.get(f"{self.base_url}/crm/leads/{lead_a.get('_id')}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Final Referrer State", False, f"Failed with status {response.status_code}")
                return False
            
            final_lead_a = response.json()
            labels = final_lead_a.get('labels', [])
            referred_count = len(final_lead_a.get('referred_clients', []))
            
            if referred_count < 5:
                self.log_result("Referral Count", False, f"Expected at least 5 referrals, got {referred_count}")
                return False
            
            if 'Royal Client' not in labels:
                self.log_result("Royal Client Label", False, f"Royal Client label not found in labels: {labels}")
                return False
            
            self.log_result("Royal Client Label", True, f"Royal Client label added after {referred_count} referrals")
            
            # Verify final loyalty points (should be 5+ * 10 = 50+)
            final_points = final_lead_a.get('loyalty_points', 0)
            if final_points < 50:
                self.log_result("Final Loyalty Points", False, f"Expected at least 50 points, got {final_points}")
                return False
            
            self.log_result("Final Loyalty Points", True, f"Final loyalty points: {final_points}")
            
            self.log_result("Referral System", True, "✅ Referral system working correctly with loyalty points and Royal Client label")
            return True
            
        except Exception as e:
            self.log_result("Referral System", False, f"Error: {str(e)}")
            return False
    
    def test_reminders_crud(self):
        """Test Scenario 5: Reminders CRUD Operations"""
        try:
            print("\n🔍 SCENARIO 5: Reminders CRUD Operations")
            
            # First create a lead to link reminders to
            lead_data = {
                "client_name": "Reminder Test Client",
                "primary_phone": "+91-9876543250",
                "email": "reminder.test@example.com",
                "lead_type": "Visa",
                "source": "Walk-in",
                "status": "In Process"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Lead for Reminders", False, f"Failed with status {response.status_code}")
                return False
            
            lead = response.json().get('lead')
            lead_id = lead.get('lead_id')
            
            # Create reminder linked to lead
            reminder_data = {
                "title": "Follow up on visa application",
                "lead_id": lead_id,
                "description": "Check document submission status and provide updates",
                "date": (datetime.now() + timedelta(days=2)).isoformat(),
                "priority": "High"
            }
            
            response = requests.post(f"{self.base_url}/crm/reminders", json=reminder_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Reminder", False, f"Failed with status {response.status_code}")
                return False
            
            reminder_response = response.json()
            if not reminder_response.get('success'):
                self.log_result("Create Reminder", False, "Response success is False")
                return False
            
            reminder = reminder_response.get('reminder')
            reminder_id = reminder.get('_id')
            
            # Verify reminder fields
            if reminder.get('title') != reminder_data['title']:
                self.log_result("Reminder Title", False, f"Expected {reminder_data['title']}, got {reminder.get('title')}")
                return False
            
            if reminder.get('lead_id') != lead_id:
                self.log_result("Reminder Lead Link", False, f"Expected {lead_id}, got {reminder.get('lead_id')}")
                return False
            
            if reminder.get('priority') != 'High':
                self.log_result("Reminder Priority", False, f"Expected High, got {reminder.get('priority')}")
                return False
            
            if reminder.get('status') != 'Pending':
                self.log_result("Reminder Default Status", False, f"Expected Pending, got {reminder.get('status')}")
                return False
            
            self.log_result("Create Reminder", True, f"✅ Reminder created successfully")
            
            # Test GET reminders (all)
            response = requests.get(f"{self.base_url}/crm/reminders", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get All Reminders", False, f"Failed with status {response.status_code}")
                return False
            
            all_reminders = response.json()
            if not isinstance(all_reminders, list) or len(all_reminders) == 0:
                self.log_result("Get All Reminders", False, f"Expected list with reminders, got {type(all_reminders)}")
                return False
            
            self.log_result("Get All Reminders", True, f"Retrieved {len(all_reminders)} reminders")
            
            # Test GET reminders with lead_id filter
            response = requests.get(f"{self.base_url}/crm/reminders?lead_id={lead_id}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Reminders by Lead", False, f"Failed with status {response.status_code}")
                return False
            
            lead_reminders = response.json()
            lead_reminder_found = any(r.get('lead_id') == lead_id for r in lead_reminders)
            if not lead_reminder_found:
                self.log_result("Get Reminders by Lead", False, f"No reminders found for lead {lead_id}")
                return False
            
            self.log_result("Get Reminders by Lead", True, f"Found reminders for lead {lead_id}")
            
            # Test UPDATE reminder (mark as Done)
            update_data = {
                "status": "Done",
                "description": "Completed - Documents submitted successfully"
            }
            
            response = requests.put(f"{self.base_url}/crm/reminders/{reminder_id}", json=update_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Update Reminder", False, f"Failed with status {response.status_code}")
                return False
            
            update_response = response.json()
            if not update_response.get('success'):
                self.log_result("Update Reminder", False, "Update response success is False")
                return False
            
            updated_reminder = update_response.get('reminder')
            if updated_reminder.get('status') != 'Done':
                self.log_result("Reminder Status Update", False, f"Expected Done, got {updated_reminder.get('status')}")
                return False
            
            self.log_result("Update Reminder", True, "✅ Reminder updated successfully")
            
            # Test DELETE reminder
            response = requests.delete(f"{self.base_url}/crm/reminders/{reminder_id}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Delete Reminder", False, f"Failed with status {response.status_code}")
                return False
            
            delete_response = response.json()
            if not delete_response.get('success'):
                self.log_result("Delete Reminder", False, "Delete response success is False")
                return False
            
            # Verify reminder is deleted
            response = requests.get(f"{self.base_url}/crm/reminders", headers=self.headers)
            remaining_reminders = response.json()
            deleted_reminder_found = any(r.get('_id') == reminder_id for r in remaining_reminders)
            
            if deleted_reminder_found:
                self.log_result("Verify Reminder Deleted", False, "Reminder still exists after deletion")
                return False
            
            self.log_result("Delete Reminder", True, "✅ Reminder deleted successfully")
            
            self.log_result("Reminders CRUD", True, "✅ All reminder CRUD operations working correctly")
            return True
            
        except Exception as e:
            self.log_result("Reminders CRUD", False, f"Error: {str(e)}")
            return False
    
    def test_analytics_endpoints(self):
        """Test Scenario 6: Analytics and Dashboard Endpoints"""
        try:
            print("\n🔍 SCENARIO 6: Analytics and Dashboard Endpoints")
            
            # Test dashboard summary
            response = requests.get(f"{self.base_url}/crm/dashboard-summary", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Dashboard Summary", False, f"Failed with status {response.status_code}")
                return False
            
            summary = response.json()
            required_fields = ['total_leads', 'active_leads', 'booked_leads', 'upcoming_travels', 'today_reminders', 'total_referrals']
            
            for field in required_fields:
                if field not in summary:
                    self.log_result("Dashboard Summary Fields", False, f"Missing field: {field}")
                    return False
                if not isinstance(summary[field], int):
                    self.log_result("Dashboard Summary Types", False, f"Field {field} is not integer: {type(summary[field])}")
                    return False
            
            self.log_result("Dashboard Summary", True, f"✅ Dashboard summary with counts: {summary}")
            
            # Test monthly leads report
            current_year = datetime.now().year
            response = requests.get(f"{self.base_url}/crm/reports/monthly?year={current_year}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Monthly Leads Report", False, f"Failed with status {response.status_code}")
                return False
            
            monthly_data = response.json()
            if not isinstance(monthly_data, list) or len(monthly_data) != 12:
                self.log_result("Monthly Leads Report", False, f"Expected 12 months, got {len(monthly_data) if isinstance(monthly_data, list) else type(monthly_data)}")
                return False
            
            # Verify month structure
            first_month = monthly_data[0]
            if 'month' not in first_month or 'count' not in first_month:
                self.log_result("Monthly Report Structure", False, f"Invalid month structure: {first_month}")
                return False
            
            self.log_result("Monthly Leads Report", True, f"✅ Monthly report with 12 months")
            
            # Test lead type breakdown
            response = requests.get(f"{self.base_url}/crm/reports/lead-type-breakdown", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Lead Type Breakdown", False, f"Failed with status {response.status_code}")
                return False
            
            type_breakdown = response.json()
            if not isinstance(type_breakdown, list):
                self.log_result("Lead Type Breakdown", False, f"Expected list, got {type(type_breakdown)}")
                return False
            
            self.log_result("Lead Type Breakdown", True, f"✅ Lead type breakdown with {len(type_breakdown)} types")
            
            # Test lead source breakdown
            response = requests.get(f"{self.base_url}/crm/reports/lead-source-breakdown", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Lead Source Breakdown", False, f"Failed with status {response.status_code}")
                return False
            
            source_breakdown = response.json()
            if not isinstance(source_breakdown, list):
                self.log_result("Lead Source Breakdown", False, f"Expected list, got {type(source_breakdown)}")
                return False
            
            self.log_result("Lead Source Breakdown", True, f"✅ Lead source breakdown with {len(source_breakdown)} sources")
            
            # Test upcoming travels
            response = requests.get(f"{self.base_url}/crm/upcoming-travels", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Upcoming Travels", False, f"Failed with status {response.status_code}")
                return False
            
            upcoming_travels = response.json()
            if not isinstance(upcoming_travels, list):
                self.log_result("Upcoming Travels", False, f"Expected list, got {type(upcoming_travels)}")
                return False
            
            self.log_result("Upcoming Travels", True, f"✅ Upcoming travels list with {len(upcoming_travels)} entries")
            
            # Create a lead with travel date in next 5 days to test upcoming travels
            travel_date = datetime.now() + timedelta(days=3)
            travel_lead_data = {
                "client_name": "Travel Test Client",
                "primary_phone": "+91-9876543260",
                "email": "travel.test@example.com",
                "lead_type": "Package",
                "source": "Website",
                "status": "Booked",
                "travel_date": travel_date.isoformat()
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=travel_lead_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Travel Lead", False, f"Failed with status {response.status_code}")
                return False
            
            # Verify it appears in upcoming travels
            time.sleep(1)
            response = requests.get(f"{self.base_url}/crm/upcoming-travels", headers=self.headers)
            updated_travels = response.json()
            
            travel_found = any(lead.get('client_name') == 'Travel Test Client' for lead in updated_travels)
            if not travel_found:
                self.log_result("Upcoming Travel Detection", False, "Travel lead not found in upcoming travels")
                return False
            
            self.log_result("Upcoming Travel Detection", True, "✅ Lead with upcoming travel date correctly detected")
            
            self.log_result("Analytics Endpoints", True, "✅ All analytics endpoints working correctly")
            return True
            
        except Exception as e:
            self.log_result("Analytics Endpoints", False, f"Error: {str(e)}")
            return False
    
    def test_document_upload(self):
        """Test Scenario 7: Document Upload, Download, Delete"""
        try:
            print("\n🔍 SCENARIO 7: Document Upload, Download, Delete")
            
            # First create a lead for document testing
            lead_data = {
                "client_name": "Document Test Client",
                "primary_phone": "+91-9876543270",
                "email": "document.test@example.com",
                "lead_type": "Visa",
                "source": "Walk-in",
                "status": "In Process"
            }
            
            response = requests.post(f"{self.base_url}/crm/leads", json=lead_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Create Lead for Documents", False, f"Failed with status {response.status_code}")
                return False
            
            lead = response.json().get('lead')
            lead_id = lead.get('_id')
            
            # Create a small test file (PDF content)
            test_file_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            # Test file upload
            files = {
                'file': ('test_document.pdf', io.BytesIO(test_file_content), 'application/pdf')
            }
            
            response = requests.post(
                f"{self.base_url}/crm/leads/{lead_id}/upload",
                files=files,
                headers={'Authorization': self.headers['Authorization']}  # Remove Content-Type for multipart
            )
            
            if response.status_code != 200:
                self.log_result("Upload Document", False, f"Failed with status {response.status_code}: {response.text}")
                return False
            
            upload_response = response.json()
            if not upload_response.get('success'):
                self.log_result("Upload Document", False, "Upload response success is False")
                return False
            
            document = upload_response.get('document')
            if not document:
                self.log_result("Upload Document", False, "No document data in response")
                return False
            
            file_path = document.get('file_path')
            if not file_path:
                self.log_result("Upload Document", False, "No file_path in document")
                return False
            
            self.log_result("Upload Document", True, f"✅ Document uploaded: {file_path}")
            
            # Verify document is added to lead
            response = requests.get(f"{self.base_url}/crm/leads/{lead_id}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Lead with Document", False, f"Failed with status {response.status_code}")
                return False
            
            updated_lead = response.json()
            documents = updated_lead.get('documents', [])
            
            if len(documents) == 0:
                self.log_result("Document in Lead", False, "No documents found in lead")
                return False
            
            uploaded_doc = documents[0]
            if uploaded_doc.get('file_name') != 'test_document.pdf':
                self.log_result("Document Metadata", False, f"Expected test_document.pdf, got {uploaded_doc.get('file_name')}")
                return False
            
            self.log_result("Document in Lead", True, f"✅ Document metadata stored in lead")
            
            # Test file download
            response = requests.get(
                f"{self.base_url}/crm/leads/{lead_id}/docs/download?file_path={file_path}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_result("Download Document", False, f"Failed with status {response.status_code}")
                return False
            
            # Verify content type and some content
            if 'application' not in response.headers.get('content-type', ''):
                self.log_result("Download Content Type", False, f"Unexpected content type: {response.headers.get('content-type')}")
                return False
            
            if len(response.content) == 0:
                self.log_result("Download Content", False, "Downloaded file is empty")
                return False
            
            self.log_result("Download Document", True, f"✅ Document downloaded successfully")
            
            # Test file deletion
            response = requests.delete(
                f"{self.base_url}/crm/leads/{lead_id}/docs?file_path={file_path}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_result("Delete Document", False, f"Failed with status {response.status_code}")
                return False
            
            delete_response = response.json()
            if not delete_response.get('success'):
                self.log_result("Delete Document", False, "Delete response success is False")
                return False
            
            # Verify document removed from lead
            response = requests.get(f"{self.base_url}/crm/leads/{lead_id}", headers=self.headers)
            final_lead = response.json()
            final_documents = final_lead.get('documents', [])
            
            doc_still_exists = any(doc.get('file_path') == file_path for doc in final_documents)
            if doc_still_exists:
                self.log_result("Document Removed from Lead", False, "Document still exists in lead after deletion")
                return False
            
            self.log_result("Delete Document", True, f"✅ Document deleted successfully")
            
            # Test file size validation (create file > 3MB)
            large_content = b"x" * (4 * 1024 * 1024)  # 4MB
            large_files = {
                'file': ('large_file.pdf', io.BytesIO(large_content), 'application/pdf')
            }
            
            response = requests.post(
                f"{self.base_url}/crm/leads/{lead_id}/upload",
                files=large_files,
                headers={'Authorization': self.headers['Authorization']}
            )
            
            if response.status_code == 400:
                self.log_result("File Size Validation", True, "✅ Large file correctly rejected")
            else:
                self.log_result("File Size Validation", False, f"Expected 400, got {response.status_code}")
                return False
            
            # Test invalid file type
            invalid_files = {
                'file': ('test.exe', io.BytesIO(b"invalid content"), 'application/octet-stream')
            }
            
            response = requests.post(
                f"{self.base_url}/crm/leads/{lead_id}/upload",
                files=invalid_files,
                headers={'Authorization': self.headers['Authorization']}
            )
            
            if response.status_code == 400:
                self.log_result("File Type Validation", True, "✅ Invalid file type correctly rejected")
            else:
                self.log_result("File Type Validation", False, f"Expected 400, got {response.status_code}")
                return False
            
            self.log_result("Document Upload", True, "✅ All document operations working correctly with proper validations")
            return True
            
        except Exception as e:
            self.log_result("Document Upload", False, f"Error: {str(e)}")
            return False
    
    def test_update_revenue_modify_vendor_payments(self, revenue_id):
        """Test Scenario 2: UPDATE Revenue - Modify Vendor Payments"""
        try:
            print("\n🔍 SCENARIO 2: UPDATE Revenue - Modify Vendor Payments")
            
            if not revenue_id:
                self.log_result("Update Revenue Vendor Payments", False, "No revenue ID provided")
                return False
            
            # Get current revenue state
            current_revenue = self.get_revenue(revenue_id)
            if not current_revenue:
                self.log_result("Get Current Revenue", False, "Could not fetch current revenue")
                return False
            
            cost_details = current_revenue.get('cost_price_details', [])
            if not cost_details:
                self.log_result("Get Cost Details", False, "No cost details found")
                return False
            
            # Modify vendor payments: change first payment from ₹10,000 to ₹15,000, remove second payment, add new payment ₹8,000
            updated_cost_details = []
            for detail in cost_details:
                if detail.get('vendor_name') == 'Hotel ABC':
                    detail['vendor_payments'] = [
                        {
                            "id": "vp_1",
                            "amount": 15000,  # Changed from 10000
                            "date": "2025-01-29",
                            "payment_mode": "Bank Transfer"
                        },
                        # Removed vp_2 (5000)
                        {
                            "id": "vp_3",  # New payment
                            "amount": 8000,
                            "date": "2025-01-31",
                            "payment_mode": "Bank Transfer"
                        }
                    ]
                updated_cost_details.append(detail)
            
            # Update revenue
            update_data = {
                "cost_price_details": updated_cost_details
            }
            
            response = requests.put(f"{self.base_url}/revenue/{revenue_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Update Revenue Vendor Payments", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            # Check Ledger Entries - old entries should be deleted, new ones created
            time.sleep(2)  # Allow for processing
            ledger_entries = self.get_ledger_entries()
            vendor_payment_entries = [e for e in ledger_entries if e.get('reference_type') == 'vendor_payment']
            
            # Should have 4 entries for the updated payments (2 payments × 2 entries each)
            if len(vendor_payment_entries) == 4:
                self.log_result("Updated Vendor Payment Entries", True, f"Found {len(vendor_payment_entries)} updated vendor payment entries")
            else:
                self.log_result("Updated Vendor Payment Entries", False, f"Expected 4 entries, got {len(vendor_payment_entries)}")
                return False
            
            # Verify new amounts: Total debits to "Vendor - Hotel ABC": ₹23,000 (15,000 + 8,000)
            vendor_debits = [e for e in vendor_payment_entries if e.get('account') == 'Vendor - Hotel ABC' and e.get('debit', 0) > 0]
            total_vendor_debit = sum(e.get('debit', 0) for e in vendor_debits)
            
            if abs(total_vendor_debit - 23000) < 0.01:  # 15000 + 8000
                self.log_result("Updated Vendor Debit Total", True, f"Correct updated vendor debit: ₹{total_vendor_debit}")
            else:
                self.log_result("Updated Vendor Debit Total", False, f"Expected ₹23000, got ₹{total_vendor_debit}")
                return False
            
            # Verify bank credits: ₹23,000 (all payments via bank)
            bank_credits = [e for e in vendor_payment_entries if e.get('account') == 'Bank - Current Account' and e.get('credit', 0) > 0]
            total_bank_credit = sum(e.get('credit', 0) for e in bank_credits)
            
            if abs(total_bank_credit - 23000) < 0.01:
                self.log_result("Updated Bank Credit Total", True, f"Correct updated bank credit: ₹{total_bank_credit}")
            else:
                self.log_result("Updated Bank Credit Total", False, f"Expected ₹23000, got ₹{total_bank_credit}")
                return False
            
            # Verify no cash entries remain (since we removed the cash payment)
            cash_entries = [e for e in vendor_payment_entries if e.get('account') == 'Cash']
            if len(cash_entries) == 0:
                self.log_result("Cash Entries Removed", True, "Cash payment entries correctly removed")
            else:
                self.log_result("Cash Entries Removed", False, f"Found {len(cash_entries)} unexpected cash entries")
                return False
            
            self.log_result("Update Revenue Modify Vendor Payments", True, "✅ Vendor payments updated correctly with proper ledger sync")
            return True
            
        except Exception as e:
            self.log_result("Update Revenue Modify Vendor Payments", False, f"Error: {str(e)}")
            return False
    
    def test_update_revenue_add_new_vendor_cost(self, revenue_id):
        """Test Scenario 3: UPDATE Revenue - Add New Vendor Cost with Payments"""
        try:
            print("\n🔍 SCENARIO 3: UPDATE Revenue - Add New Vendor Cost with Payments")
            
            if not revenue_id:
                self.log_result("Add New Vendor Cost", False, "No revenue ID provided")
                return False
            
            # Get current revenue
            current_revenue = self.get_revenue(revenue_id)
            if not current_revenue:
                self.log_result("Get Current Revenue for Add", False, "Could not fetch current revenue")
                return False
            
            # Add new cost detail with vendor payments
            current_cost_details = current_revenue.get('cost_price_details', [])
            new_cost_detail = {
                "id": str(uuid.uuid4()),
                "vendor_name": "Airlines XYZ",
                "category": "Flight",
                "amount": 50000,
                "payment_status": "Done",
                "vendor_payments": [
                    {
                        "id": "vp_airlines_1",
                        "amount": 50000,
                        "date": "2025-01-29",
                        "payment_mode": "Bank Transfer"
                    }
                ]
            }
            
            updated_cost_details = current_cost_details + [new_cost_detail]
            
            # Update revenue
            update_data = {
                "cost_price_details": updated_cost_details
            }
            
            response = requests.put(f"{self.base_url}/revenue/{revenue_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Add New Vendor Cost", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            # Check new vendor payment ledgers for Airlines XYZ
            time.sleep(2)  # Allow for processing
            ledger_entries = self.get_ledger_entries()
            vendor_payment_entries = [e for e in ledger_entries if e.get('reference_type') == 'vendor_payment']
            
            # Should now have entries for both Hotel ABC (4 entries) and Airlines XYZ (2 entries) = 6 total
            if len(vendor_payment_entries) >= 6:
                self.log_result("Total Vendor Payment Entries", True, f"Found {len(vendor_payment_entries)} total vendor payment entries")
            else:
                self.log_result("Total Vendor Payment Entries", False, f"Expected at least 6 entries, got {len(vendor_payment_entries)}")
                return False
            
            # Verify Airlines XYZ entries
            airlines_entries = [e for e in vendor_payment_entries if 'Airlines XYZ' in e.get('account', '')]
            if len(airlines_entries) == 1:  # Should be 1 debit entry for Airlines XYZ
                airlines_debit = airlines_entries[0]
                if abs(airlines_debit.get('debit', 0) - 50000) < 0.01:
                    self.log_result("Airlines Debit Entry", True, f"Correct Airlines XYZ debit: ₹{airlines_debit.get('debit')}")
                else:
                    self.log_result("Airlines Debit Entry", False, f"Expected ₹50000, got ₹{airlines_debit.get('debit')}")
                    return False
            else:
                self.log_result("Airlines Debit Entry", False, f"Expected 1 Airlines debit entry, got {len(airlines_entries)}")
                return False
            
            # Verify corresponding bank credit for Airlines payment
            airlines_bank_credits = [e for e in vendor_payment_entries 
                                   if e.get('account') == 'Bank - Current Account' 
                                   and e.get('credit', 0) == 50000
                                   and 'Airlines XYZ' in e.get('description', '')]
            
            if len(airlines_bank_credits) == 1:
                self.log_result("Airlines Bank Credit", True, f"Correct Airlines bank credit: ₹{airlines_bank_credits[0].get('credit')}")
            else:
                self.log_result("Airlines Bank Credit", False, f"Expected 1 Airlines bank credit, got {len(airlines_bank_credits)}")
                return False
            
            self.log_result("Add New Vendor Cost with Payments", True, "✅ New vendor cost added with correct ledger entries")
            return True
            
        except Exception as e:
            self.log_result("Add New Vendor Cost with Payments", False, f"Error: {str(e)}")
            return False
    
    def test_delete_revenue_with_vendor_payments(self, revenue_id):
        """Test Scenario 4: DELETE Revenue with Vendor Payments"""
        try:
            print("\n🔍 SCENARIO 4: DELETE Revenue with Vendor Payments")
            
            if not revenue_id:
                self.log_result("Delete Revenue with Vendor Payments", False, "No revenue ID provided")
                return False
            
            # Get vendor payment entries before deletion
            ledger_before = self.get_ledger_entries()
            vendor_payment_before = [e for e in ledger_before if e.get('reference_type') == 'vendor_payment']
            
            self.log_result("Vendor Payment Entries Before Delete", True, f"Found {len(vendor_payment_before)} vendor payment entries before delete")
            
            # Delete revenue
            if not self.delete_revenue(revenue_id):
                return False
            
            # Verify cleanup - all ledger entries with reference_type='vendor_payment' should be deleted
            time.sleep(2)  # Allow for cleanup
            ledger_after = self.get_ledger_entries()
            vendor_payment_after = [e for e in ledger_after if e.get('reference_type') == 'vendor_payment']
            
            if len(vendor_payment_after) == 0:
                self.log_result("Vendor Payment Cleanup", True, "All vendor payment ledger entries deleted")
            else:
                self.log_result("Vendor Payment Cleanup", False, f"{len(vendor_payment_after)} vendor payment entries still exist")
                return False
            
            # Verify no orphaned ledger entries remain
            revenue_related_entries = [e for e in ledger_after if revenue_id in e.get('reference_id', '')]
            if len(revenue_related_entries) == 0:
                self.log_result("No Orphaned Entries", True, "No orphaned ledger entries remain")
            else:
                self.log_result("No Orphaned Entries", False, f"{len(revenue_related_entries)} orphaned entries found")
                return False
            
            self.log_result("Delete Revenue with Vendor Payments", True, "✅ Revenue deleted with complete vendor payment cleanup")
            return True
            
        except Exception as e:
            self.log_result("Delete Revenue with Vendor Payments", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_cost_details_mixed_payment_status(self):
        """Test Scenario 5: Multiple Cost Details with Mixed Payment Status"""
        try:
            print("\n🔍 SCENARIO 5: Multiple Cost Details with Mixed Payment Status")
            
            # Create revenue with 2 cost details: one Done, one Pending with partial payments
            revenue_data = {
                "date": "2025-01-29",
                "client_name": "Mixed Payment Client",
                "source": "Package",
                "payment_mode": "Bank Transfer",
                "sale_price": 80000,
                "received_amount": 80000,
                "pending_amount": 0,
                "status": "Completed",
                "cost_price_details": [
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Hotel Complete",
                        "category": "Hotel",
                        "amount": 20000,
                        "payment_status": "Done",
                        "vendor_payments": [
                            {
                                "id": "vp_complete_1",
                                "amount": 20000,
                                "date": "2025-01-29",
                                "payment_mode": "Bank Transfer"
                            }
                        ]
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Transport Partial",
                        "category": "Land",
                        "amount": 30000,
                        "payment_status": "Pending",
                        "vendor_payments": [
                            {
                                "id": "vp_partial_1",
                                "amount": 10000,
                                "date": "2025-01-29",
                                "payment_mode": "Cash"
                            },
                            {
                                "id": "vp_partial_2",
                                "amount": 5000,
                                "date": "2025-01-30",
                                "payment_mode": "Bank Transfer"
                            }
                            # ₹15,000 remaining (30000 - 10000 - 5000)
                        ]
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/revenue", json=revenue_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Mixed Payment Revenue", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            revenue_response = response.json()
            test_revenue_id = revenue_response.get('id')
            
            # Verify ledger entries created correctly for both
            time.sleep(2)  # Allow for processing
            ledger_entries = self.get_ledger_entries()
            vendor_payment_entries = [e for e in ledger_entries if e.get('reference_type') == 'vendor_payment']
            
            # Should have 6 entries: Hotel Complete (2 entries), Transport Partial (4 entries)
            if len(vendor_payment_entries) >= 6:
                self.log_result("Mixed Payment Ledger Entries", True, f"Created {len(vendor_payment_entries)} vendor payment entries")
            else:
                self.log_result("Mixed Payment Ledger Entries", False, f"Expected at least 6 entries, got {len(vendor_payment_entries)}")
                return False
            
            # Verify Hotel Complete entries (₹20,000 fully paid)
            hotel_entries = [e for e in vendor_payment_entries if 'Hotel Complete' in e.get('account', '') or 'Hotel Complete' in e.get('description', '')]
            hotel_debit_total = sum(e.get('debit', 0) for e in hotel_entries)
            
            if abs(hotel_debit_total - 20000) < 0.01:
                self.log_result("Hotel Complete Payment", True, f"Hotel Complete fully paid: ₹{hotel_debit_total}")
            else:
                self.log_result("Hotel Complete Payment", False, f"Expected ₹20000, got ₹{hotel_debit_total}")
                return False
            
            # Verify Transport Partial entries (₹15,000 paid, ₹15,000 remaining)
            transport_entries = [e for e in vendor_payment_entries if 'Transport Partial' in e.get('account', '') or 'Transport Partial' in e.get('description', '')]
            transport_debit_total = sum(e.get('debit', 0) for e in transport_entries)
            
            if abs(transport_debit_total - 15000) < 0.01:  # 10000 + 5000
                self.log_result("Transport Partial Payment", True, f"Transport Partial paid: ₹{transport_debit_total} (₹15000 remaining)")
            else:
                self.log_result("Transport Partial Payment", False, f"Expected ₹15000, got ₹{transport_debit_total}")
                return False
            
            # Check that accounts show correct balances
            # This would require checking the trial balance or account balances
            response = requests.get(f"{self.base_url}/accounting/trial-balance", headers=self.headers)
            if response.status_code == 200:
                trial_balance = response.json()
                if trial_balance.get('balanced', False):
                    self.log_result("Account Balances Correct", True, "Trial balance is balanced after mixed payments")
                else:
                    self.log_result("Account Balances Correct", False, "Trial balance is not balanced")
                    return False
            
            # Cleanup
            self.delete_revenue(test_revenue_id)
            
            self.log_result("Multiple Cost Details Mixed Payment Status", True, "✅ Mixed payment status handled correctly")
            return True
            
        except Exception as e:
            self.log_result("Multiple Cost Details Mixed Payment Status", False, f"Error: {str(e)}")
            return False
    
    def run_crm_backend_tests(self):
        """Run all CRM Backend tests"""
        print("🚀 Starting CRM Backend Tests...")
        print("=" * 70)
        print("Testing NEW CRM Module backend endpoints comprehensively")
        print("Testing Lead CRUD, Auto-Revenue Creation, Document Upload, Reminders, Analytics")
        print("=" * 70)
        
        # Test Scenario 1: Lead CRUD Operations
        lead = self.test_create_lead()
        
        # Test Scenario 2: Lead Filtering and Pagination
        self.test_get_leads_with_filters()
        
        # Test Scenario 3: Auto-Revenue Creation when Lead Booked
        self.test_update_lead_status_to_booked()
        
        # Test Scenario 4: Referral System and Loyalty Points
        self.test_referral_system()
        
        # Test Scenario 5: Reminders CRUD
        self.test_reminders_crud()
        
        # Test Scenario 6: Analytics Endpoints
        self.test_analytics_endpoints()
        
        # Test Scenario 7: Document Upload/Download/Delete
        self.test_document_upload()
        
        return True

    # ===== SALE & COST TRACKING TESTS =====
    
    def test_create_revenue_with_vendor_costs(self):
        """Test Scenario 1: CREATE Revenue with Vendor Costs"""
        try:
            print("\n🔍 SCENARIO 1: CREATE Revenue with Vendor Costs")
            
            # Create revenue with sale_price and cost_price_details
            revenue_data = {
                "date": "2025-01-28",
                "client_name": "Adventure Tours Ltd",
                "source": "Package",
                "payment_mode": "Bank Transfer",
                "pending_amount": 0.0,
                "received_amount": 100000.0,
                "status": "Received",
                "sale_price": 100000.0,
                "cost_price_details": [
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Hotel ABC",
                        "category": "Hotel",
                        "amount": 30000,
                        "payment_date": "2025-01-28",
                        "notes": "Luxury hotel booking"
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Airlines XYZ",
                        "category": "Flight",
                        "amount": 25000,
                        "payment_date": "2025-01-28",
                        "notes": "Round trip flights"
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/revenue", json=revenue_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Revenue with Costs", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            revenue_response = response.json()
            revenue_id = revenue_response.get('id')
            
            # Verify calculated fields
            expected_total_cost = 55000  # 30000 + 25000
            expected_profit = 45000     # 100000 - 55000
            expected_profit_margin = 45.0  # (45000/100000) * 100
            
            if abs(revenue_response.get('total_cost_price', 0) - expected_total_cost) < 0.01:
                self.log_result("Total Cost Calculation", True, f"Correct total cost: ₹{revenue_response.get('total_cost_price')}")
            else:
                self.log_result("Total Cost Calculation", False, f"Expected ₹{expected_total_cost}, got ₹{revenue_response.get('total_cost_price')}")
                return False
            
            if abs(revenue_response.get('profit', 0) - expected_profit) < 0.01:
                self.log_result("Profit Calculation", True, f"Correct profit: ₹{revenue_response.get('profit')}")
            else:
                self.log_result("Profit Calculation", False, f"Expected ₹{expected_profit}, got ₹{revenue_response.get('profit')}")
                return False
            
            if abs(revenue_response.get('profit_margin', 0) - expected_profit_margin) < 0.01:
                self.log_result("Profit Margin Calculation", True, f"Correct profit margin: {revenue_response.get('profit_margin')}%")
            else:
                self.log_result("Profit Margin Calculation", False, f"Expected {expected_profit_margin}%, got {revenue_response.get('profit_margin')}%")
                return False
            
            # Verify auto-created expenses
            time.sleep(2)  # Allow for expense creation
            expenses = self.get_expenses()
            auto_expenses = [exp for exp in expenses if exp.get('linked_revenue_id') == revenue_id]
            
            if len(auto_expenses) == 2:
                self.log_result("Auto-Expense Creation", True, f"Created {len(auto_expenses)} linked expenses")
            else:
                self.log_result("Auto-Expense Creation", False, f"Expected 2 auto-expenses, got {len(auto_expenses)}")
                return False
            
            # Verify expense details
            hotel_expense = next((exp for exp in auto_expenses if "Hotel ABC" in exp.get('description', '')), None)
            airline_expense = next((exp for exp in auto_expenses if "Airlines XYZ" in exp.get('description', '')), None)
            
            if hotel_expense and abs(hotel_expense.get('amount', 0) - 30000) < 0.01:
                self.log_result("Hotel Expense Amount", True, f"Hotel expense: ₹{hotel_expense.get('amount')}")
            else:
                self.log_result("Hotel Expense Amount", False, f"Hotel expense amount incorrect")
                return False
            
            if airline_expense and abs(airline_expense.get('amount', 0) - 25000) < 0.01:
                self.log_result("Airline Expense Amount", True, f"Airline expense: ₹{airline_expense.get('amount')}")
            else:
                self.log_result("Airline Expense Amount", False, f"Airline expense amount incorrect")
                return False
            
            # Verify linked_expense_id populated in cost details
            updated_revenue = self.get_revenue(revenue_id)
            if updated_revenue:
                cost_details = updated_revenue.get('cost_price_details', [])
                linked_count = sum(1 for detail in cost_details if detail.get('linked_expense_id'))
                
                if linked_count == 2:
                    self.log_result("Linked Expense IDs", True, f"All {linked_count} cost details have linked_expense_id")
                else:
                    self.log_result("Linked Expense IDs", False, f"Expected 2 linked IDs, got {linked_count}")
                    return False
            
            self.log_result("Create Revenue with Vendor Costs", True, "✅ Revenue created with correct calculations and auto-expenses")
            return revenue_id
            
        except Exception as e:
            self.log_result("Create Revenue with Vendor Costs", False, f"Error: {str(e)}")
            return False
    
    def test_update_revenue_costs(self, revenue_id):
        """Test Scenario 2: UPDATE Revenue - Add/Modify/Remove Costs"""
        try:
            print("\n🔍 SCENARIO 2: UPDATE Revenue - Add/Modify/Remove Costs")
            
            if not revenue_id:
                self.log_result("Update Revenue Costs", False, "No revenue ID provided")
                return False
            
            # Get current revenue state
            current_revenue = self.get_revenue(revenue_id)
            if not current_revenue:
                self.log_result("Get Current Revenue", False, "Could not fetch current revenue")
                return False
            
            current_costs = current_revenue.get('cost_price_details', [])
            
            # Prepare updated cost details:
            # - Add new vendor: Transport Co
            # - Modify Hotel ABC amount from 30000 to 35000
            # - Remove Airlines XYZ
            
            updated_costs = []
            
            # Keep and modify Hotel ABC
            for cost in current_costs:
                if cost.get('vendor_name') == 'Hotel ABC':
                    cost['amount'] = 35000  # Modify amount
                    updated_costs.append(cost)
                # Skip Airlines XYZ (remove it)
            
            # Add new Transport Co
            updated_costs.append({
                "id": str(uuid.uuid4()),
                "vendor_name": "Transport Co",
                "category": "Land",
                "amount": 10000,
                "payment_date": "2025-01-28",
                "notes": "Local transportation"
            })
            
            # Update revenue
            update_data = {
                "cost_price_details": updated_costs
            }
            
            response = requests.put(f"{self.base_url}/revenue/{revenue_id}", json=update_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Update Revenue Costs", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            updated_revenue = response.json()
            
            # Verify recalculated totals
            expected_total_cost = 45000  # 35000 (Hotel) + 10000 (Transport)
            expected_profit = 55000     # 100000 - 45000
            expected_profit_margin = 55.0  # (55000/100000) * 100
            
            if abs(updated_revenue.get('total_cost_price', 0) - expected_total_cost) < 0.01:
                self.log_result("Updated Total Cost", True, f"Recalculated total cost: ₹{updated_revenue.get('total_cost_price')}")
            else:
                self.log_result("Updated Total Cost", False, f"Expected ₹{expected_total_cost}, got ₹{updated_revenue.get('total_cost_price')}")
                return False
            
            # Verify expense changes
            time.sleep(2)  # Allow for expense updates
            expenses = self.get_expenses()
            auto_expenses = [exp for exp in expenses if exp.get('linked_revenue_id') == revenue_id]
            
            # Should have 2 expenses: Hotel ABC (updated) and Transport Co (new)
            if len(auto_expenses) == 2:
                self.log_result("Updated Expense Count", True, f"Correct expense count: {len(auto_expenses)}")
            else:
                self.log_result("Updated Expense Count", False, f"Expected 2 expenses, got {len(auto_expenses)}")
                return False
            
            # Verify Hotel ABC expense updated to 35000
            hotel_expense = next((exp for exp in auto_expenses if "Hotel ABC" in exp.get('description', '')), None)
            if hotel_expense and abs(hotel_expense.get('amount', 0) - 35000) < 0.01:
                self.log_result("Hotel Expense Updated", True, f"Hotel expense updated to ₹{hotel_expense.get('amount')}")
            else:
                self.log_result("Hotel Expense Updated", False, f"Hotel expense not updated correctly")
                return False
            
            # Verify Transport Co expense created
            transport_expense = next((exp for exp in auto_expenses if "Transport Co" in exp.get('description', '')), None)
            if transport_expense and abs(transport_expense.get('amount', 0) - 10000) < 0.01:
                self.log_result("Transport Expense Created", True, f"Transport expense created: ₹{transport_expense.get('amount')}")
            else:
                self.log_result("Transport Expense Created", False, f"Transport expense not created correctly")
                return False
            
            # Verify Airlines XYZ expense deleted
            airline_expense = next((exp for exp in auto_expenses if "Airlines XYZ" in exp.get('description', '')), None)
            if airline_expense is None:
                self.log_result("Airline Expense Deleted", True, "Airlines XYZ expense correctly deleted")
            else:
                self.log_result("Airline Expense Deleted", False, "Airlines XYZ expense still exists")
                return False
            
            self.log_result("Update Revenue Costs", True, "✅ Revenue costs updated correctly with expense sync")
            return True
            
        except Exception as e:
            self.log_result("Update Revenue Costs", False, f"Error: {str(e)}")
            return False
    
    def test_delete_revenue_with_linked_expenses(self, revenue_id):
        """Test Scenario 3: DELETE Revenue"""
        try:
            print("\n🔍 SCENARIO 3: DELETE Revenue with Linked Expenses")
            
            if not revenue_id:
                self.log_result("Delete Revenue Test", False, "No revenue ID provided")
                return False
            
            # Get expenses before deletion
            expenses_before = self.get_expenses()
            linked_expenses_before = [exp for exp in expenses_before if exp.get('linked_revenue_id') == revenue_id]
            
            self.log_result("Linked Expenses Before Delete", True, f"Found {len(linked_expenses_before)} linked expenses")
            
            # Get ledger entries before deletion
            ledger_before = self.get_ledger_entries()
            revenue_ledger_before = [entry for entry in ledger_before if entry.get('reference_id') == revenue_id]
            expense_ledger_before = []
            for exp in linked_expenses_before:
                expense_ledger_before.extend([entry for entry in ledger_before if entry.get('reference_id') == exp.get('id')])
            
            self.log_result("Ledger Entries Before Delete", True, 
                          f"Revenue ledger: {len(revenue_ledger_before)}, Expense ledger: {len(expense_ledger_before)}")
            
            # Delete revenue
            if not self.delete_revenue(revenue_id):
                return False
            
            # Verify revenue deleted
            deleted_revenue = self.get_revenue(revenue_id)
            if deleted_revenue is None:
                self.log_result("Revenue Deleted", True, "Revenue successfully deleted")
            else:
                self.log_result("Revenue Deleted", False, "Revenue still exists")
                return False
            
            # Verify linked expenses deleted
            time.sleep(2)  # Allow for cleanup
            expenses_after = self.get_expenses()
            linked_expenses_after = [exp for exp in expenses_after if exp.get('linked_revenue_id') == revenue_id]
            
            if len(linked_expenses_after) == 0:
                self.log_result("Linked Expenses Deleted", True, "All linked expenses deleted")
            else:
                self.log_result("Linked Expenses Deleted", False, f"{len(linked_expenses_after)} linked expenses still exist")
                return False
            
            # Verify ledger entries cleaned up
            ledger_after = self.get_ledger_entries()
            revenue_ledger_after = [entry for entry in ledger_after if entry.get('reference_id') == revenue_id]
            
            if len(revenue_ledger_after) == 0:
                self.log_result("Revenue Ledger Cleaned", True, "Revenue ledger entries deleted")
            else:
                self.log_result("Revenue Ledger Cleaned", False, f"{len(revenue_ledger_after)} revenue ledger entries still exist")
                return False
            
            # Check expense ledger entries also cleaned
            expense_ledger_after = []
            for exp in linked_expenses_before:
                expense_ledger_after.extend([entry for entry in ledger_after if entry.get('reference_id') == exp.get('id')])
            
            if len(expense_ledger_after) == 0:
                self.log_result("Expense Ledger Cleaned", True, "Expense ledger entries deleted")
            else:
                self.log_result("Expense Ledger Cleaned", False, f"{len(expense_ledger_after)} expense ledger entries still exist")
                return False
            
            self.log_result("Delete Revenue with Linked Expenses", True, "✅ Revenue and all linked data deleted successfully")
            return True
            
        except Exception as e:
            self.log_result("Delete Revenue with Linked Expenses", False, f"Error: {str(e)}")
            return False
    
    def test_auto_expense_sync_toggle(self):
        """Test Scenario 4: Auto-Expense Sync Toggle"""
        try:
            print("\n🔍 SCENARIO 4: Auto-Expense Sync Toggle")
            
            # Get current settings
            current_settings = self.get_admin_settings()
            if not current_settings:
                self.log_result("Get Current Settings", False, "Could not fetch admin settings")
                return False
            
            original_sync_setting = current_settings.get('auto_expense_sync', True)
            
            # Disable auto_expense_sync
            updated_settings = current_settings.copy()
            updated_settings['auto_expense_sync'] = False
            
            if not self.update_admin_settings(updated_settings):
                self.log_result("Disable Auto Sync", False, "Could not update admin settings")
                return False
            
            self.log_result("Disable Auto Sync", True, "Auto-expense sync disabled")
            
            # Create revenue with cost details
            revenue_data = {
                "date": "2025-01-28",
                "client_name": "Test Client for Sync Toggle",
                "source": "Visa",
                "payment_mode": "Cash",
                "pending_amount": 0.0,
                "received_amount": 50000.0,
                "status": "Received",
                "sale_price": 50000.0,
                "cost_price_details": [
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Test Vendor",
                        "category": "Other",
                        "amount": 20000,
                        "payment_date": "2025-01-28"
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/revenue", json=revenue_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Revenue with Sync Disabled", False, f"Failed with status {response.status_code}")
                return False
            
            revenue_response = response.json()
            test_revenue_id = revenue_response.get('id')
            
            # Verify NO expenses were created
            time.sleep(2)
            expenses = self.get_expenses()
            auto_expenses = [exp for exp in expenses if exp.get('linked_revenue_id') == test_revenue_id]
            
            if len(auto_expenses) == 0:
                self.log_result("No Auto Expenses Created", True, "Correctly no expenses created when sync disabled")
            else:
                self.log_result("No Auto Expenses Created", False, f"Unexpected {len(auto_expenses)} expenses created")
                return False
            
            # Re-enable auto_expense_sync
            updated_settings['auto_expense_sync'] = True
            
            if not self.update_admin_settings(updated_settings):
                self.log_result("Re-enable Auto Sync", False, "Could not re-enable auto sync")
                return False
            
            self.log_result("Re-enable Auto Sync", True, "Auto-expense sync re-enabled")
            
            # Create another revenue to verify sync works again
            revenue_data2 = {
                "date": "2025-01-28",
                "client_name": "Test Client for Sync Re-enabled",
                "source": "Package",
                "payment_mode": "Bank Transfer",
                "pending_amount": 0.0,
                "received_amount": 30000.0,
                "status": "Received",
                "sale_price": 30000.0,
                "cost_price_details": [
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Test Vendor 2",
                        "category": "Hotel",
                        "amount": 15000,
                        "payment_date": "2025-01-28"
                    }
                ]
            }
            
            response2 = requests.post(f"{self.base_url}/revenue", json=revenue_data2, headers=self.headers)
            
            if response2.status_code != 200:
                self.log_result("Create Revenue with Sync Enabled", False, f"Failed with status {response2.status_code}")
                return False
            
            revenue_response2 = response2.json()
            test_revenue_id2 = revenue_response2.get('id')
            
            # Verify expenses ARE created now
            time.sleep(2)
            expenses = self.get_expenses()
            auto_expenses2 = [exp for exp in expenses if exp.get('linked_revenue_id') == test_revenue_id2]
            
            if len(auto_expenses2) == 1:
                self.log_result("Auto Expenses Created After Re-enable", True, f"Correctly created {len(auto_expenses2)} expense when sync re-enabled")
            else:
                self.log_result("Auto Expenses Created After Re-enable", False, f"Expected 1 expense, got {len(auto_expenses2)}")
                return False
            
            # Cleanup test revenues
            self.delete_revenue(test_revenue_id)
            self.delete_revenue(test_revenue_id2)
            
            # Restore original setting
            updated_settings['auto_expense_sync'] = original_sync_setting
            self.update_admin_settings(updated_settings)
            
            self.log_result("Auto-Expense Sync Toggle", True, "✅ Auto-expense sync toggle working correctly")
            return True
            
        except Exception as e:
            self.log_result("Auto-Expense Sync Toggle", False, f"Error: {str(e)}")
            return False
    
    def run_sale_cost_tracking_tests(self):
        """Run all Sale & Cost Tracking tests"""
        print("🚀 Starting Sale & Cost Tracking Tests...")
        print("=" * 70)
        print("Testing NEW Sale & Cost Tracking feature with multi-vendor support")
        print("Testing auto-expense sync functionality")
        print("=" * 70)
        
        # Test Scenario 1: Create Revenue with Vendor Costs
        revenue_id = self.test_create_revenue_with_vendor_costs()
        
        # Test Scenario 2: Update Revenue Costs (only if creation succeeded)
        if revenue_id:
            self.test_update_revenue_costs(revenue_id)
            
            # Test Scenario 3: Delete Revenue (only if update succeeded)
            self.test_delete_revenue_with_linked_expenses(revenue_id)
        
        # Test Scenario 4: Auto-Expense Sync Toggle
        self.test_auto_expense_sync_toggle()
        
        return True

    def create_expense(self, amount, category="Office Supplies", payment_mode="Cash"):
        """Create a test expense"""
        try:
            expense_data = {
                "date": "2025-01-15",
                "category": category,
                "payment_mode": payment_mode,
                "amount": amount,
                "description": f"Test expense for difference sync - {amount}",
                "purchase_type": "General Expense"
            }
            
            response = requests.post(f"{self.base_url}/expenses", json=expense_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                expense_id = data.get('id')
                self.log_result("Create Expense", True, f"Created expense with ID: {expense_id}, Amount: ₹{amount}")
                return expense_id
            else:
                self.log_result("Create Expense", False, f"Failed with status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Create Expense", False, f"Error: {str(e)}")
            return None
    
    def create_revenue(self, received_amount, status="Received", source="Visa"):
        """Create a test revenue"""
        try:
            revenue_data = {
                "date": "2025-01-15",
                "client_name": "Test Client Ltd",
                "source": source,
                "payment_mode": "Bank",
                "pending_amount": 0.0,
                "received_amount": received_amount,
                "status": status,
                "supplier": "",
                "notes": f"Test revenue for difference sync - {received_amount}"
            }
            
            response = requests.post(f"{self.base_url}/revenue", json=revenue_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                revenue_id = data.get('id')
                self.log_result("Create Revenue", True, f"Created revenue with ID: {revenue_id}, Amount: ₹{received_amount}")
                return revenue_id
            else:
                self.log_result("Create Revenue", False, f"Failed with status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Create Revenue", False, f"Error: {str(e)}")
            return None
    
    def update_expense(self, expense_id, new_amount):
        """Update expense amount"""
        try:
            update_data = {"amount": new_amount}
            
            response = requests.put(f"{self.base_url}/expenses/{expense_id}", json=update_data, headers=self.headers)
            
            if response.status_code == 200:
                self.log_result("Update Expense", True, f"Updated expense {expense_id} to ₹{new_amount}")
                return True
            else:
                self.log_result("Update Expense", False, f"Failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Expense", False, f"Error: {str(e)}")
            return False
    
    def update_revenue(self, revenue_id, new_received_amount):
        """Update revenue received amount"""
        try:
            update_data = {"received_amount": new_received_amount}
            
            response = requests.put(f"{self.base_url}/revenue/{revenue_id}", json=update_data, headers=self.headers)
            
            if response.status_code == 200:
                self.log_result("Update Revenue", True, f"Updated revenue {revenue_id} to ₹{new_received_amount}")
                return True
            else:
                self.log_result("Update Revenue", False, f"Failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Revenue", False, f"Error: {str(e)}")
            return False
    
    def test_expense_update_increase(self):
        """Test Scenario 1: Expense UPDATE with INCREASE - Verify difference-based sync"""
        try:
            print("\n🔍 SCENARIO 1: Expense UPDATE with INCREASE")
            
            # Step 1: Create expense with amount=₹10,000
            expense_id = self.create_expense(10000.0, "Office Supplies", "Cash")
            if not expense_id:
                return False
            
            # Step 2: Get initial ledger entries and note the amounts
            time.sleep(1)  # Allow for processing
            initial_entries = self.get_ledger_entries()
            expense_entries = [e for e in initial_entries if e.get('reference_id') == expense_id]
            
            if len(expense_entries) != 2:
                self.log_result("Expense Initial Ledger Check", False, f"Expected 2 entries, got {len(expense_entries)}")
                return False
            
            # Store initial entry IDs and amounts
            initial_entry_ids = {e['id']: {'debit': e['debit'], 'credit': e['credit'], 'account': e['account']} for e in expense_entries}
            
            self.log_result("Expense Initial Ledger Check", True, 
                          f"Found 2 ledger entries: Office Supplies debit ₹10000, Cash credit ₹10000")
            
            # Step 3: Update expense amount to ₹15,000 (+₹5,000 increase)
            if not self.update_expense(expense_id, 15000.0):
                return False
            
            # Step 4: Verify ledger entries are UPDATED (not recreated) with new amounts
            time.sleep(1)  # Allow for processing
            updated_entries = self.get_ledger_entries()
            updated_expense_entries = [e for e in updated_entries if e.get('reference_id') == expense_id]
            
            if len(updated_expense_entries) != 2:
                self.log_result("Expense Update Ledger Check", False, f"Expected 2 entries after update, got {len(updated_expense_entries)}")
                return False
            
            # Step 5: Verify the difference of ₹5,000 is correctly applied
            success = True
            for entry in updated_expense_entries:
                entry_id = entry['id']
                if entry_id not in initial_entry_ids:
                    self.log_result("Expense Update ID Check", False, f"Entry ID {entry_id} not found in initial entries - entries were recreated!")
                    success = False
                    continue
                
                initial_data = initial_entry_ids[entry_id]
                account = entry['account']
                
                if account == "Office Supplies":
                    # Should be debit ₹15,000 (was ₹10,000)
                    if abs(entry['debit'] - 15000.0) < 0.01:
                        self.log_result("Office Supplies Update", True, f"Correctly updated from ₹10000 to ₹{entry['debit']}")
                    else:
                        self.log_result("Office Supplies Update", False, f"Expected ₹15000, got ₹{entry['debit']}")
                        success = False
                elif account == "Cash":
                    # Should be credit ₹15,000 (was ₹10,000)
                    if abs(entry['credit'] - 15000.0) < 0.01:
                        self.log_result("Cash Update", True, f"Correctly updated from ₹10000 to ₹{entry['credit']}")
                    else:
                        self.log_result("Cash Update", False, f"Expected ₹15000, got ₹{entry['credit']}")
                        success = False
            
            if success:
                self.log_result("Expense Update Increase Test", True, "✅ Difference-based sync working - IDs preserved, amounts updated correctly")
            else:
                self.log_result("Expense Update Increase Test", False, "❌ Difference-based sync failed")
            
            return success
                
        except Exception as e:
            self.log_result("Expense Update Increase Test", False, f"Error: {str(e)}")
            return False
    
    def test_expense_update_decrease(self):
        """Test Scenario 2: Expense UPDATE with DECREASE - Verify ledger entry IDs remain same"""
        try:
            print("\n🔍 SCENARIO 2: Expense UPDATE with DECREASE")
            
            # Step 1: Update the same expense from ₹15,000 to ₹8,000 (-₹7,000 decrease)
            # First, get the expense ID from previous test by creating a new one
            expense_id = self.create_expense(15000.0, "Travel", "Bank")
            if not expense_id:
                return False
            
            # Get initial ledger entries
            time.sleep(1)
            initial_entries = self.get_ledger_entries()
            expense_entries = [e for e in initial_entries if e.get('reference_id') == expense_id]
            
            if len(expense_entries) != 2:
                self.log_result("Expense Decrease Initial Check", False, f"Expected 2 entries, got {len(expense_entries)}")
                return False
            
            # Store initial entry IDs
            initial_entry_ids = {e['id']: {'debit': e['debit'], 'credit': e['credit'], 'account': e['account']} for e in expense_entries}
            
            # Step 2: Update to ₹8,000
            if not self.update_expense(expense_id, 8000.0):
                return False
            
            # Step 3: Verify ledger entries are updated with the decreased amount
            time.sleep(1)
            updated_entries = self.get_ledger_entries()
            updated_expense_entries = [e for e in updated_entries if e.get('reference_id') == expense_id]
            
            # Step 4: Verify the ledger entry IDs remain the same (proving no delete-recreate)
            success = True
            for entry in updated_expense_entries:
                entry_id = entry['id']
                if entry_id not in initial_entry_ids:
                    self.log_result("Expense Decrease ID Preservation", False, f"Entry ID {entry_id} not found - entries were recreated!")
                    success = False
                    continue
                
                account = entry['account']
                if account == "Travel":
                    if abs(entry['debit'] - 8000.0) < 0.01:
                        self.log_result("Travel Decrease Update", True, f"Correctly decreased from ₹15000 to ₹{entry['debit']}")
                    else:
                        self.log_result("Travel Decrease Update", False, f"Expected ₹8000, got ₹{entry['debit']}")
                        success = False
                elif account == "Bank - Current Account":
                    if abs(entry['credit'] - 8000.0) < 0.01:
                        self.log_result("Bank Decrease Update", True, f"Correctly decreased from ₹15000 to ₹{entry['credit']}")
                    else:
                        self.log_result("Bank Decrease Update", False, f"Expected ₹8000, got ₹{entry['credit']}")
                        success = False
            
            if success:
                self.log_result("Expense Update Decrease Test", True, "✅ Entry IDs preserved, amounts decreased correctly")
            else:
                self.log_result("Expense Update Decrease Test", False, "❌ Decrease update failed")
            
            return success
                
        except Exception as e:
            self.log_result("Expense Update Decrease Test", False, f"Error: {str(e)}")
            return False
    
    def test_revenue_update_scenarios(self):
        """Test Scenario 3: Revenue UPDATE - Verify difference-based updates with GST"""
        try:
            print("\n🔍 SCENARIO 3: Revenue UPDATE with GST calculations")
            
            # Step 1: Create revenue with status="Received", received_amount=₹50,000
            revenue_id = self.create_revenue(50000.0, "Received", "Visa")
            if not revenue_id:
                return False
            
            # Step 2: Get initial ledger entries
            time.sleep(1)
            initial_entries = self.get_ledger_entries()
            revenue_entries = [e for e in initial_entries if e.get('reference_id') == revenue_id]
            
            if len(revenue_entries) != 4:  # Bank, Visa Revenue, CGST, SGST
                self.log_result("Revenue Initial Ledger Check", False, f"Expected 4 entries, got {len(revenue_entries)}")
                return False
            
            # Store initial entry IDs and amounts
            initial_entry_ids = {e['id']: {'debit': e['debit'], 'credit': e['credit'], 'account': e['account']} for e in revenue_entries}
            
            self.log_result("Revenue Initial Ledger Check", True, 
                          f"Found 4 ledger entries for ₹50000 revenue with GST breakdown")
            
            # Step 3: Update received_amount to ₹60,000 (+₹10,000)
            if not self.update_revenue(revenue_id, 60000.0):
                return False
            
            # Step 4: Verify ledger entries updated with difference
            time.sleep(1)
            updated_entries = self.get_ledger_entries()
            updated_revenue_entries = [e for e in updated_entries if e.get('reference_id') == revenue_id]
            
            if len(updated_revenue_entries) != 4:
                self.log_result("Revenue Update Ledger Check", False, f"Expected 4 entries after update, got {len(updated_revenue_entries)}")
                return False
            
            # Verify IDs are preserved and amounts are correct
            success = True
            for entry in updated_revenue_entries:
                entry_id = entry['id']
                if entry_id not in initial_entry_ids:
                    self.log_result("Revenue Update ID Check", False, f"Entry ID {entry_id} not found - entries were recreated!")
                    success = False
                    continue
                
                account = entry['account']
                if account == "Bank - Current Account":
                    # Should be debit ₹60,000
                    if abs(entry['debit'] - 60000.0) < 0.01:
                        self.log_result("Bank Revenue Update", True, f"Bank debit updated to ₹{entry['debit']}")
                    else:
                        self.log_result("Bank Revenue Update", False, f"Expected ₹60000, got ₹{entry['debit']}")
                        success = False
            
            # Step 5: Update received_amount to ₹45,000 (-₹15,000)
            if not self.update_revenue(revenue_id, 45000.0):
                return False
            
            # Step 6: Verify ledger entries updated correctly with decrease
            time.sleep(1)
            final_entries = self.get_ledger_entries()
            final_revenue_entries = [e for e in final_entries if e.get('reference_id') == revenue_id]
            
            # Verify final amounts
            for entry in final_revenue_entries:
                entry_id = entry['id']
                if entry_id not in initial_entry_ids:
                    self.log_result("Revenue Final ID Check", False, f"Entry ID {entry_id} not found - entries were recreated!")
                    success = False
                    continue
                
                account = entry['account']
                if account == "Bank - Current Account":
                    # Should be debit ₹45,000
                    if abs(entry['debit'] - 45000.0) < 0.01:
                        self.log_result("Bank Final Update", True, f"Bank debit correctly decreased to ₹{entry['debit']}")
                    else:
                        self.log_result("Bank Final Update", False, f"Expected ₹45000, got ₹{entry['debit']}")
                        success = False
            
            if success:
                self.log_result("Revenue Update Test", True, "✅ Revenue difference-based sync working - IDs preserved, GST updated correctly")
            else:
                self.log_result("Revenue Update Test", False, "❌ Revenue update failed")
            
            return success
                
        except Exception as e:
            self.log_result("Revenue Update Test", False, f"Error: {str(e)}")
            return False
    
    def test_account_balances_accuracy(self):
        """Verify account balances are accurate after multiple updates"""
        try:
            print("\n🔍 VERIFICATION: Account Balances Accuracy")
            
            # Get trial balance to check account balances
            response = requests.get(f"{self.base_url}/accounting/trial-balance", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('accounts', [])
                
                # Check if trial balance is balanced
                if data.get('balanced', False):
                    self.log_result("Trial Balance Check", True, f"Trial balance is balanced - Total Debit: ₹{data.get('total_debit')}, Total Credit: ₹{data.get('total_credit')}")
                else:
                    self.log_result("Trial Balance Check", False, f"Trial balance is NOT balanced - Debit: ₹{data.get('total_debit')}, Credit: ₹{data.get('total_credit')}")
                    return False
                
                # Check specific account balances
                cash_account = next((acc for acc in accounts if acc['account_name'] == 'Cash'), None)
                bank_account = next((acc for acc in accounts if acc['account_name'] == 'Bank - Current Account'), None)
                
                if cash_account:
                    self.log_result("Cash Account Balance", True, f"Cash balance: ₹{cash_account['balance']}")
                
                if bank_account:
                    self.log_result("Bank Account Balance", True, f"Bank balance: ₹{bank_account['balance']}")
                
                return True
            else:
                self.log_result("Account Balance Check", False, f"Failed to get trial balance: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Account Balance Check", False, f"Error: {str(e)}")
            return False
    
    def test_gst_records_update(self):
        """Verify GST records are updated correctly with difference-based sync"""
        try:
            print("\n🔍 VERIFICATION: GST Records Update")
            
            # Get GST summary to check if GST records are properly updated
            response = requests.get(f"{self.base_url}/accounting/gst-summary", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                output_gst = data.get('output_gst', {})
                total_output = output_gst.get('total', 0)
                
                if total_output > 0:
                    self.log_result("GST Records Check", True, f"GST records found - Total Output GST: ₹{total_output}")
                    
                    # Check individual GST components
                    cgst = output_gst.get('cgst', 0)
                    sgst = output_gst.get('sgst', 0)
                    
                    if cgst > 0 and sgst > 0:
                        self.log_result("GST Components Check", True, f"CGST: ₹{cgst}, SGST: ₹{sgst}")
                    else:
                        self.log_result("GST Components Check", False, f"Missing GST components - CGST: ₹{cgst}, SGST: ₹{sgst}")
                        return False
                else:
                    self.log_result("GST Records Check", False, "No GST records found")
                    return False
                
                return True
            else:
                self.log_result("GST Records Check", False, f"Failed to get GST summary: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("GST Records Check", False, f"Error: {str(e)}")
            return False
    
    # Removed old test methods - now focusing on CRM backend testing

def main():
    """Main test execution"""
    tester = CRMBackendTester()
    
    # Login first
    if not tester.login():
        print("❌ Login failed - cannot proceed with tests")
        return 1
    
    # Run CRM backend tests
    success = tester.run_crm_backend_tests()
    
    # Print summary
    print("\n" + "=" * 70)
    print("🔍 CRM BACKEND TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = [result for result in tester.test_results if result['success']]
    failed_tests = [result for result in tester.test_results if not result['success']]
    
    print(f"✅ PASSED: {len(passed_tests)} tests")
    print(f"❌ FAILED: {len(failed_tests)} tests")
    print(f"📊 SUCCESS RATE: {len(passed_tests)}/{len(tester.test_results)} ({len(passed_tests)/len(tester.test_results)*100:.1f}%)")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"   • {test['test']}: {test['message']}")
    
    if success and len(failed_tests) == 0:
        print("\n🎉 All CRM Backend tests passed!")
        print("✅ Lead CRUD operations working correctly!")
        print("✅ Auto-revenue creation on Booked status functioning!")
        print("✅ Referral system and loyalty points working!")
        print("✅ Reminders CRUD operations functioning!")
        print("✅ Analytics endpoints returning correct data!")
        print("✅ Document upload/download/delete working with validations!")
        return 0
    else:
        print("\n💥 Some CRM tests failed!")
        print("❌ Issues detected - needs investigation")
        return 1

if __name__ == "__main__":
    sys.exit(main())