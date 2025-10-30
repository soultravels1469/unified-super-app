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
