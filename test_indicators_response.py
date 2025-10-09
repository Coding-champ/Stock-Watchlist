"""
Test script to check if indicators are being returned correctly
"""
import requests
import json

url = "http://localhost:8000/api/chart-data/MSFT"
params = {
    "period": "1y",
    "indicators": "sma_20,bollinger"
}

print("Testing chart data endpoint...")
print(f"URL: {url}")
print(f"Params: {params}")
print("-" * 50)

try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nKeys in response: {list(data.keys())}")
        
        if 'indicators' in data:
            print(f"Indicators present: {list(data['indicators'].keys())}")
            
            # Check SMA_20
            if 'sma_20' in data['indicators']:
                sma_values = data['indicators']['sma_20']
                print(f"\nSMA_20: Type={type(sma_values)}, Length={len(sma_values) if isinstance(sma_values, list) else 'N/A'}")
                if isinstance(sma_values, list) and len(sma_values) > 0:
                    print(f"First 5 values: {sma_values[:5]}")
                else:
                    print(f"Value: {sma_values}")
            
            # Check Bollinger
            if 'bollinger' in data['indicators']:
                bb = data['indicators']['bollinger']
                print(f"\nBollinger Bands present: {list(bb.keys())}")
                if 'upper' in bb:
                    bb_upper = bb['upper']
                    print(f"Upper Band: Type={type(bb_upper)}, Length={len(bb_upper) if isinstance(bb_upper, list) else 'N/A'}")
                    if isinstance(bb_upper, list) and len(bb_upper) > 0:
                        print(f"First 5 values: {bb_upper[:5]}")
                    else:
                        print(f"Value: {bb_upper}")
        else:
            print("No 'indicators' key in response!")
            print(f"Response data: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
