#!/usr/bin/env python3
"""
Debug Revenue Endpoint - Check what's causing the invalid entry
"""

import requests
import json

# Configuration
BACKEND_URL = "https://budget-tracker-582.preview.emergentagent.com/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login():
    """Login and get JWT token"""
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        print(f"✅ Logged in as {data.get('username')}")
        return headers
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def debug_revenues():
    """Debug revenue entries"""
    headers = login()
    if not headers:
        return
    
    response = requests.get(f"{BACKEND_URL}/revenue", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ GET /api/revenue failed: {response.status_code}")
        print(response.text)
        return
    
    try:
        revenues = response.json()
        print(f"✅ Retrieved {len(revenues)} revenue entries")
        
        # Check each entry
        for i, revenue in enumerate(revenues):
            print(f"\n--- Entry {i} ---")
            if not isinstance(revenue, dict):
                print(f"❌ Entry {i}: Not a dict - {type(revenue)}")
                print(f"   Content: {revenue}")
                continue
            
            if not revenue.get('id'):
                print(f"❌ Entry {i}: Missing 'id' field")
                print(f"   Keys: {list(revenue.keys())}")
                print(f"   Content: {revenue}")
                continue
            
            # Check for legacy issues
            issues = []
            if 'service_type' in revenue and 'source' not in revenue:
                issues.append("Has 'service_type' but missing 'source'")
            
            if not revenue.get('client_name'):
                issues.append("Missing 'client_name'")
            
            if issues:
                print(f"⚠️  Entry {i}: Issues - {', '.join(issues)}")
                print(f"   ID: {revenue.get('id')}")
                print(f"   Keys: {list(revenue.keys())}")
            else:
                print(f"✅ Entry {i}: OK - ID: {revenue.get('id')}, Client: {revenue.get('client_name')}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response text: {response.text[:500]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_revenues()