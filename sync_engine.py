from hubspot_client import HubspotClient
from models import CRMContact, CRMCompany, CRMDeal, SyncResult, SyncAction
import asyncio
import json

class CRMSyncEngine:
    client: HubspotClient

    def __init__(self, client: HubspotClient | None = None):
        self.client = client or HubspotClient()

    async def sync_lead(
            self,
            contact: CRMContact,
            company: CRMCompany,
            deal: CRMDeal | None = None,
    ) -> SyncResult:
        existing_company = await self.client.search_company(company.domain)

        action =  SyncAction.CREATED
        is_duplicate = False

        company_id = ''

        if existing_company:
            company_id = existing_company['id']
        else:
            company_id = await self.client.create_company(company=company)

        existing_contact = await self.client.search_contact(email=contact.email)

        contact_id = ''
        if existing_contact:
            contact_id = existing_contact['id']
            update_lifecycle = await self.client.update_contact(
                contact_id=contact_id,
                properties={'lifecyclestage': contact.lifecycle_stage.value}
            )

            action = SyncAction.UPDATED
            is_duplicate = True
        else:
            contact_id = await self.client.create_contact(contact=contact)

            action = SyncAction.CREATED
            is_duplicate = False

        contact_to_company = await self.client.associate(
            from_type='contacts',
            from_id=contact_id,
            to_type='companies',
            to_id=company_id,
            assoc_type='contact_to_company',
        )
        
        deal_id = None

        if deal:
            deal_id = await self.client.create_deal(deal=deal)

            deal_to_contact = await self.client.associate(
                from_type='deals',
                from_id=deal_id,
                to_type='contacts',
                to_id=contact_id,
                assoc_type='deal_to_contact',
            )

            deal_to_company = await self.client.associate(
                from_type='deals',
                from_id=deal_id,
                to_type='companies',
                to_id=company_id,
                assoc_type='deal_to_company',
            )

        return SyncResult(
            action=action,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            is_duplicate=is_duplicate,
        )

if __name__ == '__main__':
    from models import LifecycleStage, DealStage

    async def main():
        engine = CRMSyncEngine()

        test_contact = CRMContact(
            email="sarah.chen@linear.app",
            first_name="Sarah",
            last_name="Chen",
            job_title="VP of Engineering",
            lifecycle_stage=LifecycleStage.SQL
        )

        test_company = CRMCompany(
            name="Linear",
            domain="linear.app",
            industry="COMPUTER_SOFTWARE",
            employee_count=120
        )

        test_deal = CRMDeal(
            deal_name="Linear - Enterprise Dedicated Cluster",
            amount=75000.0,
            pipeline_stage=DealStage.APPOINTMENT_SCHEDULED
        )

        print("\n--- Running Live Sync ---")

        result = await engine.sync_lead(test_contact, test_company, test_deal)

        print("Sync Result:", json.dumps(result, indent=2))

    asyncio.run(main())