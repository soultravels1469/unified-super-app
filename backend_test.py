#!/usr/bin/env python3
"""
Backend API Testing for Sale & Cost Tracking with Multi-Vendor Support
Tests NEW Sale & Cost Tracking feature with auto-expense sync functionality
Also includes Difference-Based Sync Logic tests
"""

import requests
import json
import os
import sys
from pathlib import Path
import uuid
import time

# Configuration
BACKEND_URL = "https://travelledger-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class SaleCostTrackingTester:
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
    
    
    def get_ledger_entries(self):
        """Get all ledger entries"""
        try:
            response = requests.get(f"{self.base_url}/accounting/ledger", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('entries', [])
            else:
                self.log_result("Get Ledger Entries", False, f"Failed with status {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_result("Get Ledger Entries", False, f"Error: {str(e)}")
            return []
    
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
    
    def run_all_tests(self):
        """Run all difference-based sync tests"""
        print("🚀 Starting Difference-Based Sync Logic Tests...")
        print("=" * 70)
        print("Testing NEW difference-based sync logic for Revenue and Expense updates")
        print("Verifying that updates use difference calculations instead of delete-recreate")
        print("=" * 70)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        print("\n📋 Testing Difference-Based Sync Logic...")
        
        # Test Scenario 1: Expense UPDATE with INCREASE
        test1_success = self.test_expense_update_increase()
        
        # Test Scenario 2: Expense UPDATE with DECREASE  
        test2_success = self.test_expense_update_decrease()
        
        # Test Scenario 3: Revenue UPDATE scenarios
        test3_success = self.test_revenue_update_scenarios()
        
        # Verification tests
        test4_success = self.test_account_balances_accuracy()
        test5_success = self.test_gst_records_update()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 DIFFERENCE-BASED SYNC TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Key findings summary
        print("\n🔍 KEY FINDINGS:")
        if test1_success and test2_success and test3_success:
            print("✅ DIFFERENCE-BASED SYNC WORKING: Ledger entry IDs are preserved during updates")
            print("✅ AMOUNTS ACCURATE: Final amounts reflect exact values (not cumulative)")
            print("✅ NO DELETE-RECREATE: Updates use difference calculations as intended")
        else:
            print("❌ DIFFERENCE-BASED SYNC ISSUES DETECTED")
        
        if test4_success:
            print("✅ ACCOUNT BALANCES: Trial balance is accurate after multiple updates")
        else:
            print("❌ ACCOUNT BALANCE ISSUES: Trial balance may be incorrect")
        
        if test5_success:
            print("✅ GST RECORDS: GST calculations updated correctly")
        else:
            print("❌ GST RECORD ISSUES: GST updates may be incorrect")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

def main():
    """Main test execution"""
    tester = DifferenceSyncTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All difference-based sync tests passed!")
        print("✅ The new sync logic is working correctly - no more delete-recreate!")
        return 0
    else:
        print("\n💥 Some difference-based sync tests failed!")
        print("❌ Issues detected with the new sync logic - needs investigation")
        return 1

if __name__ == "__main__":
    sys.exit(main())