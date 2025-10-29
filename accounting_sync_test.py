#!/usr/bin/env python3
"""
Accounting Sync Testing for Revenue/Expense DELETE and UPDATE operations
Tests the sync logic between Revenue/Expense entries and Accounting records (Ledger, GST, Trial Balance)
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://voyage-books-1.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class AccountingSyncTester:
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
                return response.json().get('entries', [])
            return []
        except Exception as e:
            print(f"Error getting ledger entries: {e}")
            return []
    
    def get_gst_records(self):
        """Get all GST records"""
        try:
            response = requests.get(f"{self.base_url}/accounting/gst-summary", headers=self.headers)
            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            print(f"Error getting GST records: {e}")
            return []
    
    def find_entries_by_reference_id(self, entries, reference_id):
        """Find entries with specific reference_id"""
        return [entry for entry in entries if entry.get('reference_id') == reference_id]
    
    def test_scenario_1_revenue_delete_sync(self):
        """
        Scenario 1: Revenue DELETE Sync
        1. Create a new revenue entry with status="Received" and received_amount > 0
        2. Verify ledger entries are created
        3. Delete the revenue entry
        4. Verify all ledger entries with that reference_id are deleted
        5. Verify GST records with that reference_id are deleted
        """
        print("\n🧪 Testing Scenario 1: Revenue DELETE Sync")
        
        # Step 1: Create revenue entry
        revenue_data = {
            "date": "2025-01-15",
            "client_name": "Test Client ABC",
            "source": "Visa",
            "payment_mode": "Bank Transfer",
            "pending_amount": 0.0,
            "received_amount": 50000.0,
            "status": "Received",
            "supplier": "Immigration Services",
            "notes": "Test revenue for accounting sync"
        }
        
        try:
            response = requests.post(f"{self.base_url}/revenue", json=revenue_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Scenario 1 - Create Revenue", False, f"Failed to create revenue: {response.status_code}", response.text)
                return False
            
            revenue = response.json()
            revenue_id = revenue.get('id')
            self.log_result("Scenario 1 - Create Revenue", True, f"Created revenue with ID: {revenue_id}")
            
            # Step 2: Verify ledger entries are created
            ledger_entries = self.get_ledger_entries()
            revenue_ledger_entries = self.find_entries_by_reference_id(ledger_entries, revenue_id)
            
            if len(revenue_ledger_entries) == 0:
                self.log_result("Scenario 1 - Verify Ledger Creation", False, "No ledger entries found for revenue")
                return False
            
            self.log_result("Scenario 1 - Verify Ledger Creation", True, f"Found {len(revenue_ledger_entries)} ledger entries")
            
            # Print BEFORE state
            print(f"   BEFORE DELETE - Ledger entries for revenue {revenue_id}:")
            for entry in revenue_ledger_entries:
                print(f"     - Account: {entry.get('account')}, Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
            
            # Step 3: Delete the revenue entry
            delete_response = requests.delete(f"{self.base_url}/revenue/{revenue_id}", headers=self.headers)
            if delete_response.status_code != 200:
                self.log_result("Scenario 1 - Delete Revenue", False, f"Failed to delete revenue: {delete_response.status_code}")
                return False
            
            self.log_result("Scenario 1 - Delete Revenue", True, f"Successfully deleted revenue {revenue_id}")
            
            # Step 4: Verify all ledger entries with that reference_id are deleted
            updated_ledger_entries = self.get_ledger_entries()
            remaining_revenue_entries = self.find_entries_by_reference_id(updated_ledger_entries, revenue_id)
            
            if len(remaining_revenue_entries) == 0:
                self.log_result("Scenario 1 - Verify Ledger Deletion", True, "All ledger entries successfully deleted")
            else:
                self.log_result("Scenario 1 - Verify Ledger Deletion", False, f"Found {len(remaining_revenue_entries)} remaining ledger entries")
                return False
            
            # Step 5: Verify GST records are deleted
            gst_records = self.get_gst_records()
            remaining_gst_records = self.find_entries_by_reference_id(gst_records, revenue_id)
            
            if len(remaining_gst_records) == 0:
                self.log_result("Scenario 1 - Verify GST Deletion", True, "All GST records successfully deleted")
            else:
                self.log_result("Scenario 1 - Verify GST Deletion", False, f"Found {len(remaining_gst_records)} remaining GST records")
                return False
            
            # Print AFTER state
            print(f"   AFTER DELETE - No entries found for revenue {revenue_id} (as expected)")
            
            return True
            
        except Exception as e:
            self.log_result("Scenario 1 - Exception", False, f"Error: {str(e)}")
            return False
    
    def test_scenario_2_expense_update_sync(self):
        """
        Scenario 2: Expense UPDATE Sync
        1. Create an expense entry with amount=10000
        2. Verify ledger entries are created
        3. Update the expense amount to 20000
        4. Verify ledger entries are updated with new amount (old entries deleted, new created)
        5. Verify amounts match
        """
        print("\n🧪 Testing Scenario 2: Expense UPDATE Sync")
        
        # Step 1: Create expense entry
        expense_data = {
            "date": "2025-01-15",
            "category": "Office Supplies",
            "payment_mode": "Cash",
            "amount": 10000.0,
            "description": "Test expense for accounting sync",
            "purchase_type": "General Expense",
            "supplier_gstin": "",
            "invoice_number": "TEST-001",
            "gst_rate": 0.0
        }
        
        try:
            response = requests.post(f"{self.base_url}/expenses", json=expense_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Scenario 2 - Create Expense", False, f"Failed to create expense: {response.status_code}", response.text)
                return False
            
            expense = response.json()
            expense_id = expense.get('id')
            self.log_result("Scenario 2 - Create Expense", True, f"Created expense with ID: {expense_id}")
            
            # Step 2: Verify ledger entries are created
            ledger_entries = self.get_ledger_entries()
            expense_ledger_entries = self.find_entries_by_reference_id(ledger_entries, expense_id)
            
            if len(expense_ledger_entries) == 0:
                self.log_result("Scenario 2 - Verify Initial Ledger Creation", False, "No ledger entries found for expense")
                return False
            
            self.log_result("Scenario 2 - Verify Initial Ledger Creation", True, f"Found {len(expense_ledger_entries)} ledger entries")
            
            # Print BEFORE state
            print(f"   BEFORE UPDATE - Ledger entries for expense {expense_id} (amount: 10000):")
            for entry in expense_ledger_entries:
                print(f"     - Account: {entry.get('account')}, Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
            
            # Step 3: Update the expense amount to 20000
            update_data = {"amount": 20000.0}
            update_response = requests.put(f"{self.base_url}/expenses/{expense_id}", json=update_data, headers=self.headers)
            if update_response.status_code != 200:
                self.log_result("Scenario 2 - Update Expense", False, f"Failed to update expense: {update_response.status_code}")
                return False
            
            self.log_result("Scenario 2 - Update Expense", True, f"Successfully updated expense {expense_id} amount to 20000")
            
            # Step 4: Verify ledger entries are updated with new amount
            updated_ledger_entries = self.get_ledger_entries()
            updated_expense_entries = self.find_entries_by_reference_id(updated_ledger_entries, expense_id)
            
            if len(updated_expense_entries) == 0:
                self.log_result("Scenario 2 - Verify Updated Ledger Entries", False, "No ledger entries found after update")
                return False
            
            # Print AFTER state
            print(f"   AFTER UPDATE - Ledger entries for expense {expense_id} (amount: 20000):")
            for entry in updated_expense_entries:
                print(f"     - Account: {entry.get('account')}, Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
            
            # Step 5: Verify amounts match (should be 20000 now)
            total_debit = sum(entry.get('debit', 0) for entry in updated_expense_entries)
            total_credit = sum(entry.get('credit', 0) for entry in updated_expense_entries)
            
            # For expenses, the expense account should be debited with 20000
            expense_account_entries = [e for e in updated_expense_entries if 'Office Supplies' in e.get('account', '')]
            if expense_account_entries:
                expense_debit = expense_account_entries[0].get('debit', 0)
                if expense_debit == 20000.0:
                    self.log_result("Scenario 2 - Verify Amount Match", True, f"Expense amount correctly updated to 20000")
                else:
                    self.log_result("Scenario 2 - Verify Amount Match", False, f"Expected 20000, found {expense_debit}")
                    return False
            else:
                self.log_result("Scenario 2 - Verify Amount Match", False, "Could not find expense account entry")
                return False
            
            # Clean up - delete the expense
            requests.delete(f"{self.base_url}/expenses/{expense_id}", headers=self.headers)
            
            return True
            
        except Exception as e:
            self.log_result("Scenario 2 - Exception", False, f"Error: {str(e)}")
            return False
    
    def test_scenario_3_expense_delete_sync(self):
        """
        Scenario 3: Expense DELETE Sync
        1. Create an expense entry
        2. Verify ledger entries exist
        3. Delete the expense
        4. Verify all ledger entries with that reference_id are deleted
        """
        print("\n🧪 Testing Scenario 3: Expense DELETE Sync")
        
        # Step 1: Create expense entry
        expense_data = {
            "date": "2025-01-15",
            "category": "Travel",
            "payment_mode": "Bank Transfer",
            "amount": 15000.0,
            "description": "Test expense for delete sync",
            "purchase_type": "General Expense",
            "supplier_gstin": "",
            "invoice_number": "DEL-001",
            "gst_rate": 0.0
        }
        
        try:
            response = requests.post(f"{self.base_url}/expenses", json=expense_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Scenario 3 - Create Expense", False, f"Failed to create expense: {response.status_code}", response.text)
                return False
            
            expense = response.json()
            expense_id = expense.get('id')
            self.log_result("Scenario 3 - Create Expense", True, f"Created expense with ID: {expense_id}")
            
            # Step 2: Verify ledger entries exist
            ledger_entries = self.get_ledger_entries()
            expense_ledger_entries = self.find_entries_by_reference_id(ledger_entries, expense_id)
            
            if len(expense_ledger_entries) == 0:
                self.log_result("Scenario 3 - Verify Ledger Creation", False, "No ledger entries found for expense")
                return False
            
            self.log_result("Scenario 3 - Verify Ledger Creation", True, f"Found {len(expense_ledger_entries)} ledger entries")
            
            # Print BEFORE state
            print(f"   BEFORE DELETE - Ledger entries for expense {expense_id}:")
            for entry in expense_ledger_entries:
                print(f"     - Account: {entry.get('account')}, Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
            
            # Step 3: Delete the expense
            delete_response = requests.delete(f"{self.base_url}/expenses/{expense_id}", headers=self.headers)
            if delete_response.status_code != 200:
                self.log_result("Scenario 3 - Delete Expense", False, f"Failed to delete expense: {delete_response.status_code}")
                return False
            
            self.log_result("Scenario 3 - Delete Expense", True, f"Successfully deleted expense {expense_id}")
            
            # Step 4: Verify all ledger entries with that reference_id are deleted
            updated_ledger_entries = self.get_ledger_entries()
            remaining_expense_entries = self.find_entries_by_reference_id(updated_ledger_entries, expense_id)
            
            if len(remaining_expense_entries) == 0:
                self.log_result("Scenario 3 - Verify Ledger Deletion", True, "All ledger entries successfully deleted")
            else:
                self.log_result("Scenario 3 - Verify Ledger Deletion", False, f"Found {len(remaining_expense_entries)} remaining ledger entries")
                return False
            
            # Print AFTER state
            print(f"   AFTER DELETE - No entries found for expense {expense_id} (as expected)")
            
            return True
            
        except Exception as e:
            self.log_result("Scenario 3 - Exception", False, f"Error: {str(e)}")
            return False
    
    def test_scenario_4_expense_gst_update_delete(self):
        """
        Scenario 4: Expense with GST UPDATE
        1. Create expense with purchase_type="Purchase for Resale", gst_rate=18
        2. Verify both ledger AND GST records created
        3. Update amount
        4. Verify both ledger AND GST records updated
        5. Delete expense
        6. Verify both deleted
        """
        print("\n🧪 Testing Scenario 4: Expense with GST UPDATE and DELETE")
        
        # Step 1: Create expense with GST
        expense_data = {
            "date": "2025-01-15",
            "category": "Inventory",
            "payment_mode": "Bank Transfer",
            "amount": 25000.0,
            "description": "Test expense with GST for sync",
            "purchase_type": "Purchase for Resale",
            "supplier_gstin": "29ABCDE1234F1Z5",
            "invoice_number": "GST-001",
            "gst_rate": 18.0
        }
        
        try:
            response = requests.post(f"{self.base_url}/expenses", json=expense_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Scenario 4 - Create GST Expense", False, f"Failed to create expense: {response.status_code}", response.text)
                return False
            
            expense = response.json()
            expense_id = expense.get('id')
            self.log_result("Scenario 4 - Create GST Expense", True, f"Created GST expense with ID: {expense_id}")
            
            # Step 2: Verify both ledger AND GST records created
            ledger_entries = self.get_ledger_entries()
            expense_ledger_entries = self.find_entries_by_reference_id(ledger_entries, expense_id)
            
            gst_records = self.get_gst_records()
            expense_gst_records = self.find_entries_by_reference_id(gst_records, expense_id)
            
            if len(expense_ledger_entries) == 0:
                self.log_result("Scenario 4 - Verify Initial Ledger Creation", False, "No ledger entries found for GST expense")
                return False
            
            if len(expense_gst_records) == 0:
                self.log_result("Scenario 4 - Verify Initial GST Creation", False, "No GST records found for GST expense")
                return False
            
            self.log_result("Scenario 4 - Verify Initial Records", True, f"Found {len(expense_ledger_entries)} ledger entries and {len(expense_gst_records)} GST records")
            
            # Print BEFORE state
            print(f"   BEFORE UPDATE - Ledger entries for GST expense {expense_id} (amount: 25000):")
            for entry in expense_ledger_entries:
                print(f"     - Account: {entry.get('account')}, Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
            
            print(f"   BEFORE UPDATE - GST records for expense {expense_id}:")
            for record in expense_gst_records:
                print(f"     - GST Type: {record.get('gst_type')}, Amount: {record.get('amount', 0)}")
            
            # Step 3: Update amount
            update_data = {"amount": 35000.0}
            update_response = requests.put(f"{self.base_url}/expenses/{expense_id}", json=update_data, headers=self.headers)
            if update_response.status_code != 200:
                self.log_result("Scenario 4 - Update GST Expense", False, f"Failed to update expense: {update_response.status_code}")
                return False
            
            self.log_result("Scenario 4 - Update GST Expense", True, f"Successfully updated GST expense {expense_id} amount to 35000")
            
            # Step 4: Verify both ledger AND GST records updated
            updated_ledger_entries = self.get_ledger_entries()
            updated_expense_ledger = self.find_entries_by_reference_id(updated_ledger_entries, expense_id)
            
            updated_gst_records = self.get_gst_records()
            updated_expense_gst = self.find_entries_by_reference_id(updated_gst_records, expense_id)
            
            if len(updated_expense_ledger) == 0:
                self.log_result("Scenario 4 - Verify Updated Ledger", False, "No ledger entries found after update")
                return False
            
            if len(updated_expense_gst) == 0:
                self.log_result("Scenario 4 - Verify Updated GST", False, "No GST records found after update")
                return False
            
            # Print AFTER UPDATE state
            print(f"   AFTER UPDATE - Ledger entries for GST expense {expense_id} (amount: 35000):")
            for entry in updated_expense_ledger:
                print(f"     - Account: {entry.get('account')}, Debit: {entry.get('debit', 0)}, Credit: {entry.get('credit', 0)}")
            
            print(f"   AFTER UPDATE - GST records for expense {expense_id}:")
            for record in updated_expense_gst:
                print(f"     - GST Type: {record.get('gst_type')}, Amount: {record.get('amount', 0)}")
            
            # Verify amounts are updated
            inventory_entries = [e for e in updated_expense_ledger if 'Inventory' in e.get('account', '')]
            if inventory_entries:
                inventory_debit = inventory_entries[0].get('debit', 0)
                if inventory_debit == 35000.0:
                    self.log_result("Scenario 4 - Verify Updated Amount", True, f"Expense amount correctly updated to 35000")
                else:
                    self.log_result("Scenario 4 - Verify Updated Amount", False, f"Expected 35000, found {inventory_debit}")
                    return False
            
            # Step 5: Delete expense
            delete_response = requests.delete(f"{self.base_url}/expenses/{expense_id}", headers=self.headers)
            if delete_response.status_code != 200:
                self.log_result("Scenario 4 - Delete GST Expense", False, f"Failed to delete expense: {delete_response.status_code}")
                return False
            
            self.log_result("Scenario 4 - Delete GST Expense", True, f"Successfully deleted GST expense {expense_id}")
            
            # Step 6: Verify both deleted
            final_ledger_entries = self.get_ledger_entries()
            final_expense_ledger = self.find_entries_by_reference_id(final_ledger_entries, expense_id)
            
            final_gst_records = self.get_gst_records()
            final_expense_gst = self.find_entries_by_reference_id(final_gst_records, expense_id)
            
            if len(final_expense_ledger) == 0 and len(final_expense_gst) == 0:
                self.log_result("Scenario 4 - Verify Final Deletion", True, "All ledger and GST records successfully deleted")
            else:
                self.log_result("Scenario 4 - Verify Final Deletion", False, f"Found {len(final_expense_ledger)} ledger and {len(final_expense_gst)} GST records remaining")
                return False
            
            # Print AFTER DELETE state
            print(f"   AFTER DELETE - No entries found for expense {expense_id} (as expected)")
            
            return True
            
        except Exception as e:
            self.log_result("Scenario 4 - Exception", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all accounting sync tests"""
        print("🚀 Starting Accounting Sync Tests...")
        print("=" * 80)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        print("\n📋 Testing Revenue/Expense to Accounting Sync Logic...")
        
        # Run all test scenarios
        scenario_1_result = self.test_scenario_1_revenue_delete_sync()
        scenario_2_result = self.test_scenario_2_expense_update_sync()
        scenario_3_result = self.test_scenario_3_expense_delete_sync()
        scenario_4_result = self.test_scenario_4_expense_gst_update_delete()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

def main():
    """Main test execution"""
    tester = AccountingSyncTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All accounting sync tests passed!")
        return 0
    else:
        print("\n💥 Some accounting sync tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())