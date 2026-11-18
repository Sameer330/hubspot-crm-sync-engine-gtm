import os
import httpx
import asyncio
import json
from models import CRMContact, CRMCompany, CRMDeal
from dotenv import load_dotenv

load_dotenv()

class HubspotClient():
    base_url: str
    client: httpx.AsyncClient

    __headers = dict

    def __init__(self, token: str | None = None):
        self.base_url = 'https://api.hubapi.com'
        self.client = httpx.AsyncClient()

        api_token = token or os.getenv('HUBSPOT_ACCESS_TOKEN')

        self.__headers =  {
            'User-Agent': 'hubspot-crm-sync-engine',
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
        }

    async def search_contact(self, email: str) -> dict | None:
        response = await self.client.post(
            f'{self.base_url}/crm/v3/objects/contacts/search',
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": f"{email}"
                            }
                        ]
                    }
                ],
                "properties": ["email", "firstname", "lastname", "lifecyclestage"]
            },
            headers=self.__headers,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('total', 0) > 0:
                return data['results'][0]
        
        return None

    async def search_company(self, domain: str) -> dict | None:
        response = await self.client.post(
            f'{self.base_url}/crm/v3/objects/companies/search',
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "domain",
                                "operator": "EQ",
                                "value": f"{domain}"
                            }
                        ]
                    }
                ],
                "properties": ["name", "domain"],
            },
            headers=self.__headers,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('total', 0) > 0:
                return data['results'][0]

        return None

    async def create_contact(self, contact: CRMContact) -> str:
        properties = {
            'email': contact.email,
            'firstname': contact.first_name,
            'lastname': contact.last_name,
            'lifecyclestage': contact.lifecycle_stage.value,
        }
        if contact.phone:
            properties['phone'] = contact.phone
        if contact.job_title:
            properties['jobtitle'] = contact.job_title

        response = await self.client.post(
            f'{self.base_url}/crm/v3/objects/contacts',
            json={'properties': properties},
            headers=self.__headers,
        )

        id = response.json()['id']
        return id

    async def update_contact(self, contact_id: str, properties: dict) -> bool:
        response = await self.client.patch(
            f'{self.base_url}/crm/v3/objects/contacts/{contact_id}',
            json={'properties': properties},
            headers=self.__headers,
        )

        return response.status_code in (200, 201)

    async def create_company(self, company: CRMCompany) -> str:
        properties = {
            'name': company.name,
            'domain': company.domain,
        }
        if company.industry:
            properties['industry'] = company.industry
        if company.employee_count:
            properties['numberofemployees'] = str(company.employee_count)

        response = await self.client.post(
            f'{self.base_url}/crm/v3/objects/companies',
            json={'properties': properties},
            headers=self.__headers,
        )
        print(response)

        return response.json()['id']

    async def create_deal(self, deal: CRMDeal) -> str:
        properties = {
            'dealname': deal.deal_name,
            'amount': str(deal.amount),
            'dealstage': deal.pipeline_stage.value,
        }

        response = await self.client.post(
            f'{self.base_url}/crm/v3/objects/deals',
            json={'properties': properties},
            headers=self.__headers,
        )

        return response.json()['id']

    async def associate(self, from_type: str, from_id: str, to_type: str, to_id: str, assoc_type: str) -> bool:
        response = await self.client.put(
            f'{self.base_url}/crm/v3/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}/{assoc_type}',
            headers=self.__headers,
        )

        return response.status_code in (200, 201)

    # only for testing - to delete objects from CRM
    async def delete(self, object_type: str, object_id: str):
        response = await self.client.delete(
            f'{self.base_url}/crm/v3/objects/{object_type}/{object_id}',
            headers=self.__headers,
        )
        return response.status_code == 204

async def main():
    hubspot_client = HubspotClient()
    
    contact = await hubspot_client.search_contact(email='bh@hubspot.com')
    print('--- Contact ---')
    print(json.dumps(contact, indent=2))
    
    company = await hubspot_client.search_company(domain='hubspot.com')
    print('\n--- Company ---')
    print(json.dumps(company, indent=2))

if __name__ == '__main__':
    asyncio.run(main())