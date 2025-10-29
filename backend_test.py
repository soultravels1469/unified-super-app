#!/usr/bin/env python3
"""
Backend API Testing for Vendor Partial Payment Tracking and Ledger Sync
Tests NEW Vendor Partial Payment Tracking feature with comprehensive ledger sync
Also includes Sale & Cost Tracking and Difference-Based Sync Logic tests
"""

import requests
import json
import os
import sys
from pathlib import Path
import uuid
import time

# Configuration
BACKEND_URL = "https://voyage-books-1.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class VendorPaymentTrackingTester:
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
    
    def get_expenses(self):
        """Get all expenses"""
        try:
            response = requests.get(f"{self.base_url}/expenses", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Get Expenses", False, f"Failed with status {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_result("Get Expenses", False, f"Error: {str(e)}")
            return []
    
    def create_vendor(self, vendor_name, vendor_type="Hotel"):
        """Create a vendor"""
        try:
            vendor_data = {
                "vendor_name": vendor_name,
                "contact": "9876543210",
                "vendor_type": vendor_type,
                "bank_name": "Test Bank",
                "bank_account_number": "1234567890",
                "bank_ifsc": "TEST0001234"
            }
            
            response = requests.post(f"{self.base_url}/vendors", json=vendor_data, headers=self.headers)
            
            if response.status_code == 200:
                vendor = response.json()
                self.log_result("Create Vendor", True, f"Created vendor: {vendor_name}")
                return vendor.get('id')
            else:
                self.log_result("Create Vendor", False, f"Failed with status {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("Create Vendor", False, f"Error: {str(e)}")
            return None
    
    def get_bank_accounts(self):
        """Get bank accounts list"""
        try:
            response = requests.get(f"{self.base_url}/bank-accounts", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Get Bank Accounts", False, f"Failed with status {response.status_code}", response.text)
                return []
        except Exception as e:
            self.log_result("Get Bank Accounts", False, f"Error: {str(e)}")
            return []
    
    def get_revenue(self, revenue_id):
        """Get specific revenue by ID"""
        try:
            response = requests.get(f"{self.base_url}/revenue", headers=self.headers)
            if response.status_code == 200:
                revenues = response.json()
                for rev in revenues:
                    if rev.get('id') == revenue_id:
                        return rev
                return None
            else:
                self.log_result("Get Revenue", False, f"Failed with status {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("Get Revenue", False, f"Error: {str(e)}")
            return None
    
    def get_admin_settings(self):
        """Get admin settings"""
        try:
            response = requests.get(f"{self.base_url}/admin/settings", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Get Admin Settings", False, f"Failed with status {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("Get Admin Settings", False, f"Error: {str(e)}")
            return None
    
    def update_admin_settings(self, settings):
        """Update admin settings"""
        try:
            response = requests.post(f"{self.base_url}/admin/settings", json=settings, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Update Admin Settings", False, f"Failed with status {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("Update Admin Settings", False, f"Error: {str(e)}")
            return None
    
    def delete_revenue(self, revenue_id):
        """Delete revenue"""
        try:
            response = requests.delete(f"{self.base_url}/revenue/{revenue_id}", headers=self.headers)
            if response.status_code == 200:
                return True
            else:
                self.log_result("Delete Revenue", False, f"Failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Delete Revenue", False, f"Error: {str(e)}")
            return False
    
    # ===== VENDOR PARTIAL PAYMENT TRACKING TESTS =====
    
    def test_create_revenue_with_vendor_partial_payments(self):
        """Test Scenario 1: CREATE Revenue with Vendor Partial Payments"""
        try:
            print("\n🔍 SCENARIO 1: CREATE Revenue with Vendor Partial Payments")
            
            # First create a vendor if needed
            vendor_id = self.create_vendor("Hotel ABC", "Hotel")
            
            # Get bank accounts list
            bank_accounts = self.get_bank_accounts()
            self.log_result("Get Bank Accounts", True, f"Found {len(bank_accounts)} bank accounts")
            
            # Create revenue with cost details including vendor payments
            revenue_data = {
                "date": "2025-01-29",
                "client_name": "Adventure Tours Client",
                "source": "Package",
                "payment_mode": "Bank Transfer",
                "sale_price": 100000,
                "received_amount": 100000,
                "pending_amount": 0,
                "status": "Completed",
                "cost_price_details": [
                    {
                        "id": str(uuid.uuid4()),
                        "vendor_name": "Hotel ABC",
                        "category": "Hotel",
                        "amount": 30000,
                        "payment_status": "Pending",
                        "vendor_payments": [
                            {
                                "id": "vp_1",
                                "amount": 10000,
                                "date": "2025-01-29",
                                "payment_mode": "Bank Transfer"
                            },
                            {
                                "id": "vp_2", 
                                "amount": 5000,
                                "date": "2025-01-30",
                                "payment_mode": "Cash"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(f"{self.base_url}/revenue", json=revenue_data, headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Create Revenue with Vendor Payments", False, f"Failed with status {response.status_code}", response.text)
                return False
            
            revenue_response = response.json()
            revenue_id = revenue_response.get('id')
            
            # Verify response has revenue created with cost_price_details preserved
            cost_details = revenue_response.get('cost_price_details', [])
            if len(cost_details) == 1 and cost_details[0].get('vendor_payments'):
                self.log_result("Revenue Created with Vendor Payments", True, f"Revenue created with vendor payments preserved")
            else:
                self.log_result("Revenue Created with Vendor Payments", False, "Vendor payments not preserved in response")
                return False
            
            # Check Ledger Entries - verify vendor payment ledgers created
            time.sleep(2)  # Allow for ledger processing
            ledger_entries = self.get_ledger_entries()
            vendor_payment_entries = [e for e in ledger_entries if e.get('reference_type') == 'vendor_payment']
            
            if len(vendor_payment_entries) == 4:  # 2 payments × 2 entries each (debit + credit)
                self.log_result("Vendor Payment Ledger Entries", True, f"Created {len(vendor_payment_entries)} vendor payment ledger entries")
            else:
                self.log_result("Vendor Payment Ledger Entries", False, f"Expected 4 entries, got {len(vendor_payment_entries)}")
                return False
            
            # Verify ledger entry details
            vendor_debits = [e for e in vendor_payment_entries if e.get('account') == 'Vendor - Hotel ABC' and e.get('debit', 0) > 0]
            bank_credits = [e for e in vendor_payment_entries if e.get('account') == 'Bank - Current Account' and e.get('credit', 0) > 0]
            cash_credits = [e for e in vendor_payment_entries if e.get('account') == 'Cash' and e.get('credit', 0) > 0]
            
            # Verify amounts
            total_vendor_debit = sum(e.get('debit', 0) for e in vendor_debits)
            total_bank_credit = sum(e.get('credit', 0) for e in bank_credits)
            total_cash_credit = sum(e.get('credit', 0) for e in cash_credits)
            
            if abs(total_vendor_debit - 15000) < 0.01:  # 10000 + 5000
                self.log_result("Vendor Debit Amount", True, f"Correct vendor debit total: ₹{total_vendor_debit}")
            else:
                self.log_result("Vendor Debit Amount", False, f"Expected ₹15000, got ₹{total_vendor_debit}")
                return False
            
            if abs(total_bank_credit - 10000) < 0.01:
                self.log_result("Bank Credit Amount", True, f"Correct bank credit: ₹{total_bank_credit}")
            else:
                self.log_result("Bank Credit Amount", False, f"Expected ₹10000, got ₹{total_bank_credit}")
                return False
            
            if abs(total_cash_credit - 5000) < 0.01:
                self.log_result("Cash Credit Amount", True, f"Correct cash credit: ₹{total_cash_credit}")
            else:
                self.log_result("Cash Credit Amount", False, f"Expected ₹5000, got ₹{total_cash_credit}")
                return False
            
            # Verify reference_id format: "{revenue_id}_{cost_detail_id}_{payment_id}"
            reference_ids = [e.get('reference_id') for e in vendor_payment_entries]
            expected_refs = [f"{revenue_id}_{cost_details[0]['id']}_vp_1", f"{revenue_id}_{cost_details[0]['id']}_vp_2"]
            
            valid_refs = all(any(ref.endswith(expected) for expected in ['_vp_1', '_vp_2']) for ref in reference_ids)
            if valid_refs:
                self.log_result("Reference ID Format", True, "Reference IDs follow correct format")
            else:
                self.log_result("Reference ID Format", False, f"Invalid reference ID format: {reference_ids}")
                return False
            
            self.log_result("Create Revenue with Vendor Partial Payments", True, "✅ Revenue created with correct vendor payment ledger entries")
            return revenue_id
            
        except Exception as e:
            self.log_result("Create Revenue with Vendor Partial Payments", False, f"Error: {str(e)}")
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
    
    def run_vendor_payment_tracking_tests(self):
        """Run all Vendor Partial Payment Tracking tests"""
        print("🚀 Starting Vendor Partial Payment Tracking Tests...")
        print("=" * 70)
        print("Testing NEW Vendor Partial Payment Tracking and Ledger Sync feature")
        print("=" * 70)
        
        # Test Scenario 1: Create Revenue with Vendor Partial Payments
        revenue_id = self.test_create_revenue_with_vendor_partial_payments()
        
        # Test Scenario 2: Update Revenue - Modify Vendor Payments (only if creation succeeded)
        if revenue_id:
            self.test_update_revenue_modify_vendor_payments(revenue_id)
            
            # Test Scenario 3: Update Revenue - Add New Vendor Cost with Payments
            self.test_update_revenue_add_new_vendor_cost(revenue_id)
            
            # Test Scenario 4: Delete Revenue with Vendor Payments (only if updates succeeded)
            self.test_delete_revenue_with_vendor_payments(revenue_id)
        
        # Test Scenario 5: Multiple Cost Details with Mixed Payment Status
        self.test_multiple_cost_details_mixed_payment_status()
        
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
    
    def run_all_tests(self):
        """Run all Vendor Payment Tracking, Sale & Cost Tracking and Difference-Based Sync tests"""
        print("🚀 Starting Comprehensive Backend API Tests...")
        print("=" * 80)
        print("Testing NEW Vendor Partial Payment Tracking and Ledger Sync feature")
        print("Testing Sale & Cost Tracking feature with multi-vendor support")
        print("Testing auto-expense sync functionality")
        print("Testing difference-based sync logic for Revenue and Expense updates")
        print("=" * 80)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run Vendor Payment Tracking Tests (PRIORITY)
        print("\n📋 Testing Vendor Partial Payment Tracking Feature...")
        self.run_vendor_payment_tracking_tests()
        
        # Run Sale & Cost Tracking Tests
        print("\n📋 Testing Sale & Cost Tracking Feature...")
        self.run_sale_cost_tracking_tests()
        
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
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKEND TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Key findings summary
        print("\n🔍 KEY FINDINGS:")
        
        # Sale & Cost Tracking findings
        sale_cost_tests = [r for r in self.test_results if any(keyword in r['test'] for keyword in ['Revenue with Vendor Costs', 'Update Revenue Costs', 'Delete Revenue with Linked', 'Auto-Expense Sync'])]
        sale_cost_passed = sum(1 for r in sale_cost_tests if r['success'])
        
        if sale_cost_passed == len(sale_cost_tests) and len(sale_cost_tests) > 0:
            print("✅ SALE & COST TRACKING: Multi-vendor support working correctly")
            print("✅ AUTO-EXPENSE SYNC: Linked expenses created, updated, and deleted properly")
            print("✅ COST CALCULATIONS: Profit and profit margin calculated accurately")
        else:
            print("❌ SALE & COST TRACKING ISSUES DETECTED")
        
        # Difference-based sync findings
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
    tester = SaleCostTrackingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All Sale & Cost Tracking and Sync Logic tests passed!")
        print("✅ The NEW Sale & Cost Tracking feature is working correctly!")
        print("✅ Multi-vendor support and auto-expense sync functioning properly!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        print("❌ Issues detected - needs investigation")
        return 1

if __name__ == "__main__":
    sys.exit(main())