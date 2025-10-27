#!/usr/bin/env python3
"""
Comprehensive end-to-end test for Admin Settings
"""

import requests
import json
from PIL import Image

BACKEND_URL = "https://travelledger-2.preview.emergentagent.com/api"

def comprehensive_admin_settings_test():
    """Test complete admin settings workflow"""
    
    # Login
    login_data = {"username": "admin", "password": "admin123"}
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_response.json().get('token')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🔄 Testing complete Admin Settings workflow...")
    
    # 1. Get initial settings
    response = requests.get(f"{BACKEND_URL}/admin/settings", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get initial settings")
        return False
    
    initial_settings = response.json()
    print(f"✅ Retrieved initial settings with {len(initial_settings)} fields")
    
    # 2. Upload logo
    img = Image.new('RGB', (150, 75), color='blue')
    img_path = "/tmp/company_logo.png"
    img.save(img_path, 'PNG')
    
    with open(img_path, 'rb') as f:
        files = {'file': ('company_logo.png', f, 'image/png')}
        headers_no_content_type = {k: v for k, v in headers.items() if k != 'Content-Type'}
        
        response = requests.post(f"{BACKEND_URL}/admin/upload-logo", 
                               files=files, headers=headers_no_content_type)
    
    if response.status_code != 200:
        print("❌ Failed to upload logo")
        return False
    
    logo_path = response.json().get('logo_path')
    print(f"✅ Logo uploaded: {logo_path}")
    
    # 3. Upload signature
    sig_img = Image.new('RGB', (200, 60), color='green')
    sig_path = "/tmp/signature.png"
    sig_img.save(sig_path, 'PNG')
    
    with open(sig_path, 'rb') as f:
        files = {'file': ('signature.png', f, 'image/png')}
        
        response = requests.post(f"{BACKEND_URL}/admin/upload-signature", 
                               files=files, headers=headers_no_content_type)
    
    if response.status_code != 200:
        print("❌ Failed to upload signature")
        return False
    
    signature_path = response.json().get('signature_path')
    print(f"✅ Signature uploaded: {signature_path}")
    
    # 4. Add multiple bank accounts
    bank_accounts = [
        {
            "account_holder_name": "Soul Immigration & Travels",
            "bank_name": "State Bank of India",
            "account_number": "1234567890123456",
            "ifsc_code": "SBIN0001234",
            "branch": "Main Branch",
            "upi_id": "soulimmigration@sbi",
            "is_default": True
        },
        {
            "account_holder_name": "Soul Immigration & Travels",
            "bank_name": "HDFC Bank",
            "account_number": "9876543210987654",
            "ifsc_code": "HDFC0001234",
            "branch": "Business Branch",
            "upi_id": "soulimmigration@hdfc",
            "is_default": False
        }
    ]
    
    account_ids = []
    for i, account in enumerate(bank_accounts):
        response = requests.post(f"{BACKEND_URL}/admin/settings/bank-accounts", 
                               json=account, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to add bank account {i+1}")
            return False
        
        account_id = response.json().get('account', {}).get('id')
        account_ids.append(account_id)
        print(f"✅ Added bank account {i+1}: {account['bank_name']}")
    
    # 5. Update comprehensive settings
    comprehensive_settings = {
        "company_name": "Soul Immigration & Travels Pvt Ltd",
        "company_address": "123 Business Complex, Immigration Street, Mumbai, Maharashtra 400001",
        "company_contact": "+91-9876543210",
        "company_email": "contact@soulimmigration.com",
        "company_tagline": "Your Gateway to Global Opportunities",
        "logo_path": logo_path,
        "gstin": "27ABCDE1234F1Z5",
        "invoice_prefix": "SOUL-INV",
        "default_tax_percentage": 18.0,
        "invoice_footer": "Thank you for choosing Soul Immigration & Travels!",
        "invoice_terms": "Payment due within 30 days. Late payments may incur additional charges.",
        "signature_path": signature_path,
        "show_logo_on_invoice": True
    }
    
    response = requests.post(f"{BACKEND_URL}/admin/settings", 
                           json=comprehensive_settings, headers=headers)
    
    if response.status_code != 200:
        print("❌ Failed to update comprehensive settings")
        return False
    
    print("✅ Updated comprehensive settings")
    
    # 6. Verify final settings
    response = requests.get(f"{BACKEND_URL}/admin/settings", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get final settings")
        return False
    
    final_settings = response.json()
    
    # Verify key fields
    checks = [
        (final_settings.get('company_name') == comprehensive_settings['company_name'], "Company name"),
        (final_settings.get('logo_path') == logo_path, "Logo path"),
        (final_settings.get('signature_path') == signature_path, "Signature path"),
        (len(final_settings.get('bank_accounts', [])) == 2, "Bank accounts count"),
        (final_settings.get('invoice_prefix') == 'SOUL-INV', "Invoice prefix"),
        (final_settings.get('default_tax_percentage') == 18.0, "Tax percentage")
    ]
    
    all_passed = True
    for check, name in checks:
        if check:
            print(f"✅ {name} verified")
        else:
            print(f"❌ {name} verification failed")
            all_passed = False
    
    # 7. Test file accessibility
    for file_path in [logo_path, signature_path]:
        file_url = f"https://travelledger-2.preview.emergentagent.com{file_path}"
        file_response = requests.get(file_url)
        
        if file_response.status_code == 200:
            print(f"✅ File accessible: {file_path}")
        else:
            print(f"❌ File not accessible: {file_path}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = comprehensive_admin_settings_test()
    
    if success:
        print("\n🎉 Comprehensive Admin Settings test PASSED!")
    else:
        print("\n💥 Comprehensive Admin Settings test FAILED!")