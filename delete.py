from hubspot_client import HubspotClient
import asyncio

class DeleteTestData:
    client: HubspotClient

    def __init__(self, client: HubspotClient | None = None):
        self.client = client or HubspotClient()

    async def delete_object_type_by_id(self, object_type: str, object_id: str) -> bool:
        response = await self.client.delete(
            object_type=object_type,
            object_id=object_id,
        )
        return response

# use this to delete using APIs
# OR simply delete in your Hubspot CRM interface
# here -> https://app.hubspot.com
if __name__ == '__main__':
    async def main():
        delete_test_data = DeleteTestData()

    #     delete_company = await delete_test_data.delete_object_type_by_id(
    #         object_type='companies',
    #         object_id=''
    #     )
    #     print("Deleted company:", delete_company)

    #     delete_contact = await delete_test_data.delete_object_type_by_id(
    #         object_type='contacts',
    #         object_id=''
    #     )
    #     print("Deleted contact:", delete_contact)

    #     delete_deal = await delete_test_data.delete_object_type_by_id(
    #         object_type='deals',
    #         object_id=''
    #     )
    #     print("Deleted deal:", delete_deal)
    asyncio.run(main())