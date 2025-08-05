#!/usr/bin/env python3
"""
Test script to debug the Canadian Employment Equity API
"""
import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api_endpoint():
    """Test the API with various parameters to see what works"""
    
    url = "https://disclosure.esdc.gc.ca/dp-pd/eec-csj/Chercher-Search"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://disclosure.esdc.gc.ca",
        "Referer": "https://disclosure.esdc.gc.ca/dp-pd/eec-csj/eec-csj.jsp?lang=eng&activity=968&jurisdiction=10",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    # Test different combinations
    test_cases = [
        {"activity": "968", "jurisdiction": "10", "description": "Original parameters"},
        {"activity": "968", "jurisdiction": "", "description": "No jurisdiction"},
        {"activity": "", "jurisdiction": "10", "description": "No activity"},
        {"activity": "", "jurisdiction": "", "description": "No filters"},
        {"activity": "968", "jurisdiction": "06", "description": "Ontario"},
        {"activity": "968", "jurisdiction": "05", "description": "Quebec"},
        {"activity": "969", "jurisdiction": "10", "description": "Different activity"},
        {"activity": "970", "jurisdiction": "10", "description": "Another activity"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['description']} ---")
        
        payload = {
            "lang": "eng",
            "activity": test_case["activity"],
            "jurisdiction": test_case["jurisdiction"],
            "searchTerm": "",
            "offset": 0,
            "limit": 10,
            "sort": "organizationName",
            "order": "asc"
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=30, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                total = result.get("recordsTotal", 0)
                data_count = len(result.get("data", []))
                print(f"Status: SUCCESS")
                print(f"Records Total: {total}")
                print(f"Data Count: {data_count}")
                
                if data_count > 0:
                    print("Sample record:")
                    print(json.dumps(result["data"][0], indent=2))
                    return True  # Found working parameters
            else:
                print(f"Status: FAILED - HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"Status: ERROR - {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing Canadian Employment Equity API...")
    success = test_api_endpoint()
    
    if not success:
        print("\n❌ No working parameter combinations found.")
        print("The API might be temporarily unavailable or the parameters may have changed.")
    else:
        print("\n✅ Found working parameter combination!")