import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('HUBSPOT_ACCESS_TOKEN')

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = httpx.get(
    "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
    headers=headers
)

print("HTTP Status:", response.status_code)

if response.status_code == 200:
    print('Hubspot connection successful')
    print(f'portal data - {response.json()}')
else:
    print('Connection failed', response.text)