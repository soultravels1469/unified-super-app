#!/usr/bin/env python3
"""
Backend API Testing for Difference-Based Sync Logic
Tests Revenue and Expense UPDATE operations to verify difference-based sync instead of delete-recreate
"""

import requests
import json
import os
import sys
from pathlib import Path
import uuid
from PIL import Image
import io
import time

# Configuration
BACKEND_URL = "https://travelledger-2.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class DifferenceSyncTester:
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
    
    def create_test_image(self, filename, size=(100, 100)):
        """Create a test image file"""
        try:
            # Create a simple test image
            img = Image.new('RGB', size, color='red')
            img_path = Path(f"/tmp/{filename}")
            img.save(img_path, 'PNG')
            return str(img_path)
        except Exception as e:
            print(f"Error creating test image: {e}")
            return None
    
    def test_get_admin_settings_default(self):
        """Test GET /api/admin/settings - Default values when no settings exist"""
        try:
            response = requests.get(f"{self.base_url}/admin/settings", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required default fields
                required_fields = [
                    'company_name', 'company_address', 'company_contact', 'company_email',
                    'bank_accounts', 'invoice_prefix', 'default_tax_percentage',
                    'invoice_footer', 'show_logo_on_invoice'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("GET Admin Settings (Default)", True, 
                                  f"Retrieved default settings with all required fields")
                    return data
                else:
                    self.log_result("GET Admin Settings (Default)", False, 
                                  f"Missing required fields: {missing_fields}", data)
                    return None
            else:
                self.log_result("GET Admin Settings (Default)", False, 
                              f"Failed with status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("GET Admin Settings (Default)", False, f"Error: {str(e)}")
            return None
    
    def test_post_admin_settings(self):
        """Test POST /api/admin/settings - Save complete settings"""
        try:
            test_settings = {
                "company_name": "Soul Immigration & Travels Ltd",
                "company_address": "123 Business Street, City, State 12345",
                "company_contact": "+91-9876543210",
                "company_email": "info@soulimmigration.com",
                "company_tagline": "Your Gateway to Global Opportunities",
                "gstin": "29ABCDE1234F1Z5",
                "invoice_prefix": "SOUL",
                "default_tax_percentage": 18.0,
                "invoice_footer": "Thank you for choosing Soul Immigration!",
                "invoice_terms": "Payment due within 30 days",
                "show_logo_on_invoice": True
            }
            
            response = requests.post(f"{self.base_url}/admin/settings", 
                                   json=test_settings, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Settings updated successfully':
                    self.log_result("POST Admin Settings", True, "Settings saved successfully")
                    return True
                else:
                    self.log_result("POST Admin Settings", False, "Unexpected response", data)
                    return False
            else:
                self.log_result("POST Admin Settings", False, 
                              f"Failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("POST Admin Settings", False, f"Error: {str(e)}")
            return False
    
    def test_upload_logo(self):
        """Test POST /api/admin/upload-logo - Upload logo file"""
        try:
            # Create test image
            test_image_path = self.create_test_image("test_logo.png")
            if not test_image_path:
                self.log_result("Upload Logo", False, "Failed to create test image")
                return None
            
            # Upload file
            with open(test_image_path, 'rb') as f:
                files = {'file': ('test_logo.png', f, 'image/png')}
                headers_no_content_type = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
                
                response = requests.post(f"{self.base_url}/admin/upload-logo", 
                                       files=files, headers=headers_no_content_type)
            
            # Clean up test file
            os.unlink(test_image_path)
            
            if response.status_code == 200:
                data = response.json()
                logo_path = data.get('logo_path')
                
                if logo_path and logo_path.startswith('/uploads/logo_'):
                    # Verify file exists on server
                    file_url = f"https://travelledger-2.preview.emergentagent.com{logo_path}"
                    file_check = requests.get(file_url)
                    
                    if file_check.status_code == 200:
                        self.log_result("Upload Logo", True, f"Logo uploaded and accessible at {logo_path}")
                        return logo_path
                    else:
                        self.log_result("Upload Logo", False, f"Logo uploaded but not accessible at {logo_path}")
                        return None
                else:
                    self.log_result("Upload Logo", False, "Invalid logo path returned", data)
                    return None
            else:
                self.log_result("Upload Logo", False, 
                              f"Upload failed with status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Upload Logo", False, f"Error: {str(e)}")
            return None
    
    def test_upload_signature(self):
        """Test POST /api/admin/upload-signature - Upload signature file"""
        try:
            # Create test image
            test_image_path = self.create_test_image("test_signature.png", (200, 80))
            if not test_image_path:
                self.log_result("Upload Signature", False, "Failed to create test image")
                return None
            
            # Upload file
            with open(test_image_path, 'rb') as f:
                files = {'file': ('test_signature.png', f, 'image/png')}
                headers_no_content_type = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
                
                response = requests.post(f"{self.base_url}/admin/upload-signature", 
                                       files=files, headers=headers_no_content_type)
            
            # Clean up test file
            os.unlink(test_image_path)
            
            if response.status_code == 200:
                data = response.json()
                signature_path = data.get('signature_path')
                
                if signature_path and signature_path.startswith('/uploads/signature_'):
                    # Verify file exists on server
                    file_url = f"https://travelledger-2.preview.emergentagent.com{signature_path}"
                    file_check = requests.get(file_url)
                    
                    if file_check.status_code == 200:
                        self.log_result("Upload Signature", True, f"Signature uploaded and accessible at {signature_path}")
                        return signature_path
                    else:
                        self.log_result("Upload Signature", False, f"Signature uploaded but not accessible at {signature_path}")
                        return None
                else:
                    self.log_result("Upload Signature", False, "Invalid signature path returned", data)
                    return None
            else:
                self.log_result("Upload Signature", False, 
                              f"Upload failed with status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Upload Signature", False, f"Error: {str(e)}")
            return None
    
    def test_upload_invalid_file(self):
        """Test uploading invalid file type"""
        try:
            # Create a text file instead of image
            test_file_path = "/tmp/test_invalid.txt"
            with open(test_file_path, 'w') as f:
                f.write("This is not an image file")
            
            # Try to upload as logo
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_invalid.txt', f, 'text/plain')}
                headers_no_content_type = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
                
                response = requests.post(f"{self.base_url}/admin/upload-logo", 
                                       files=files, headers=headers_no_content_type)
            
            # Clean up test file
            os.unlink(test_file_path)
            
            if response.status_code == 400:
                self.log_result("Upload Invalid File", True, "Correctly rejected invalid file type")
                return True
            else:
                self.log_result("Upload Invalid File", False, 
                              f"Should have rejected invalid file, got status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Upload Invalid File", False, f"Error: {str(e)}")
            return False
    
    def test_add_bank_account(self):
        """Test POST /api/admin/settings/bank-accounts - Add bank account"""
        try:
            bank_account = {
                "account_holder_name": "Soul Immigration & Travels",
                "bank_name": "State Bank of India",
                "account_number": "1234567890123456",
                "ifsc_code": "SBIN0001234",
                "branch": "Main Branch",
                "upi_id": "soulimmigration@sbi",
                "is_default": True
            }
            
            response = requests.post(f"{self.base_url}/admin/settings/bank-accounts", 
                                   json=bank_account, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                account_data = data.get('account', {})
                
                if account_data.get('id') and account_data.get('account_number') == bank_account['account_number']:
                    self.log_result("Add Bank Account", True, f"Bank account added with ID: {account_data.get('id')}")
                    return account_data.get('id')
                else:
                    self.log_result("Add Bank Account", False, "Invalid account data returned", data)
                    return None
            else:
                self.log_result("Add Bank Account", False, 
                              f"Failed with status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Add Bank Account", False, f"Error: {str(e)}")
            return None
    
    def test_update_bank_account(self, account_id):
        """Test PUT /api/admin/settings/bank-accounts/{account_id} - Update bank account"""
        if not account_id:
            self.log_result("Update Bank Account", False, "No account ID provided")
            return False
            
        try:
            update_data = {
                "account_holder_name": "Soul Immigration & Travels Ltd",
                "branch": "Updated Branch Name",
                "upi_id": "updated@sbi",
                "is_default": False
            }
            
            response = requests.put(f"{self.base_url}/admin/settings/bank-accounts/{account_id}", 
                                  json=update_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Bank account updated successfully':
                    self.log_result("Update Bank Account", True, f"Bank account {account_id} updated successfully")
                    return True
                else:
                    self.log_result("Update Bank Account", False, "Unexpected response", data)
                    return False
            else:
                self.log_result("Update Bank Account", False, 
                              f"Failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Bank Account", False, f"Error: {str(e)}")
            return False
    
    def test_update_nonexistent_bank_account(self):
        """Test updating non-existent bank account - should return 404"""
        try:
            fake_id = str(uuid.uuid4())
            update_data = {"branch": "Should not work"}
            
            response = requests.put(f"{self.base_url}/admin/settings/bank-accounts/{fake_id}", 
                                  json=update_data, headers=self.headers)
            
            if response.status_code == 404:
                self.log_result("Update Non-existent Bank Account", True, "Correctly returned 404 for non-existent account")
                return True
            else:
                self.log_result("Update Non-existent Bank Account", False, 
                              f"Should have returned 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Update Non-existent Bank Account", False, f"Error: {str(e)}")
            return False
    
    def test_delete_bank_account(self, account_id):
        """Test DELETE /api/admin/settings/bank-accounts/{account_id} - Delete bank account"""
        if not account_id:
            self.log_result("Delete Bank Account", False, "No account ID provided")
            return False
            
        try:
            response = requests.delete(f"{self.base_url}/admin/settings/bank-accounts/{account_id}", 
                                     headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Bank account deleted successfully':
                    self.log_result("Delete Bank Account", True, f"Bank account {account_id} deleted successfully")
                    return True
                else:
                    self.log_result("Delete Bank Account", False, "Unexpected response", data)
                    return False
            else:
                self.log_result("Delete Bank Account", False, 
                              f"Failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Delete Bank Account", False, f"Error: {str(e)}")
            return False
    
    def test_delete_nonexistent_bank_account(self):
        """Test deleting non-existent bank account - should return 404"""
        try:
            fake_id = str(uuid.uuid4())
            
            response = requests.delete(f"{self.base_url}/admin/settings/bank-accounts/{fake_id}", 
                                     headers=self.headers)
            
            if response.status_code == 404:
                self.log_result("Delete Non-existent Bank Account", True, "Correctly returned 404 for non-existent account")
                return True
            else:
                self.log_result("Delete Non-existent Bank Account", False, 
                              f"Should have returned 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Delete Non-existent Bank Account", False, f"Error: {str(e)}")
            return False
    
    def test_get_settings_after_updates(self):
        """Test GET /api/admin/settings after making updates"""
        try:
            response = requests.get(f"{self.base_url}/admin/settings", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if our updates are reflected
                if (data.get('company_name') == 'Soul Immigration & Travels Ltd' and 
                    data.get('company_address') == '123 Business Street, City, State 12345'):
                    self.log_result("GET Settings After Updates", True, "Settings correctly reflect updates")
                    return True
                else:
                    self.log_result("GET Settings After Updates", False, "Settings do not reflect updates", data)
                    return False
            else:
                self.log_result("GET Settings After Updates", False, 
                              f"Failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("GET Settings After Updates", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin settings tests"""
        print("🚀 Starting Admin Settings API Tests...")
        print("=" * 60)
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        print("\n📋 Testing Admin Settings Endpoints...")
        
        # Test GET settings (default)
        self.test_get_admin_settings_default()
        
        # Test POST settings
        self.test_post_admin_settings()
        
        # Test file uploads
        logo_path = self.test_upload_logo()
        signature_path = self.test_upload_signature()
        
        # Test invalid file upload
        self.test_upload_invalid_file()
        
        # Test bank account operations
        account_id = self.test_add_bank_account()
        self.test_update_bank_account(account_id)
        self.test_update_nonexistent_bank_account()
        
        # Test GET settings after updates
        self.test_get_settings_after_updates()
        
        # Test delete operations (do this last)
        self.test_delete_bank_account(account_id)
        self.test_delete_nonexistent_bank_account()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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
    try:
        # Check if PIL is available for image creation
        from PIL import Image
    except ImportError:
        print("❌ PIL (Pillow) not available. Installing...")
        os.system("pip install Pillow")
        from PIL import Image
    
    tester = AdminSettingsAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())