#!/usr/bin/env python3
"""
Debug specific issues found in backend testing
"""

import requests
import json

BACKEND_URL = "https://travelledger-2.preview.emergentagent.com/api"

def test_post_settings_debug():
    """Debug the POST settings 500 error"""
    
    # Login first
    login_data = {"username": "admin", "password": "admin123"}
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json().get('token')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Try minimal settings first
    minimal_settings = {
        "company_name": "Test Company"
    }
    
    print("Testing minimal settings...")
    response = requests.post(f"{BACKEND_URL}/admin/settings", json=minimal_settings, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print("✅ Minimal settings worked")

def test_invalid_file_debug():
    """Debug the invalid file upload issue"""
    
    # Login first
    login_data = {"username": "admin", "password": "admin123"}
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create a text file
    test_file_path = "/tmp/test_invalid.txt"
    with open(test_file_path, 'w') as f:
        f.write("This is not an image file")
    
    # Try to upload as logo
    with open(test_file_path, 'rb') as f:
        files = {'file': ('test_invalid.txt', f, 'text/plain')}
        
        response = requests.post(f"{BACKEND_URL}/admin/upload-logo", files=files, headers=headers)
        print(f"Invalid file upload status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    print("🔍 Debugging backend issues...")
    test_post_settings_debug()
    print("\n" + "="*50)
    test_invalid_file_debug()