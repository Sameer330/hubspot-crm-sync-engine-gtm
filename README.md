# 🔄 Autonomous HubSpot CRM Sync & Deduplication Engine

> **Production-grade CRM synchronization and deduplication infrastructure in Python.** Interfaces with HubSpot REST API v3 to ingest inbound leads, enforce deterministic company and contact deduplication, orchestrate enterprise deal creation, and establish bi-directional multi-object associations in real time.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![HubSpot API v3](https://img.shields.io/badge/HubSpot_API-v3_REST-FF7A59?style=flat-square&logo=hubspot&logoColor=white)](https://developers.hubspot.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![HTTPX](https://img.shields.io/badge/HTTPX-Async_Client-5A67D8?style=flat-square)](https://www.python-httpx.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

## 🎯 The Business Problem: CRM Data Rot & Revenue Fragmentation

In high-growth B2B companies, the CRM is the central source of truth for revenue operations. However, unchecked inbound flows and manual sales rep entries trigger severe **data degradation**:

* **Duplicate Account Proliferation:** When different sales reps or marketing campaigns ingest leads from the same account (e.g., `sarah.chen@linear.app` and `eng-team@linear.app`), disconnected company records are created. Deal context, historical touchpoints, and executive notes become fragmented across duplicate entities.
* **The Cost of Dirty CRM Data:** According to Gartner, dirty CRM data costs B2B enterprises an average of **$12.9M annually** in lost productivity, misattributed sales commissions, and misrouted high-value enterprise accounts.
* **Enterprise Tool Markup:** Standalone data deduplication and sync platforms like **Syncari**, **LeanData**, and **Ringlead** charge high-growth startups **$25,000 to $70,000+ per year** for basic deduplication and association workflows.

This project delivers an autonomous, asynchronous CRM deduplication and sync engine that prevents duplicate record creation, updates existing contact lifecycle stages atomically, creates enterprise deals, and guarantees referential integrity across HubSpot's Contact, Company, and Deal objects.

---

## 🏗️ System Architecture

```
                 [ Inbound Lead Payload ]
                 (Contact, Company, Deal)
                            │
                            ▼
           [ CRMSyncEngine.sync_lead(...) ]
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    [ Search Company ]           [ Search Contact ]
   (domain == "linear.app")    (email == "sarah.chen@linear.app")
              │                           │
       Exists?                     Exists?
      ┌───┴───┐                   ┌───┴───┐
     YES      NO                 YES      NO
      │        │                  │        │
  Reuse ID  Create Company    Update      Create Contact
            (HTTP 201)        Lifecycle   (HTTP 201)
                              Stage       (is_duplicate=False)
                              (PATCH)
                              (is_duplicate=True)
              │                           │
              └─────────────┬─────────────┘
                            │
                            ▼
        [ Multi-Object Association Engine ]
        - Contacts ↔ Companies (PUT v3 Association)
                            │
                            ▼
             [ Enterprise Deal Creation ]
             - Name: "Linear - Enterprise Dedicated Cluster"
             - Amount: $75,000
             - Pipeline Stage: appointmentscheduled
                            │
                            ▼
        [ Deal Referential Associations ]
        - Deals ↔ Contacts (deal_to_contact)
        - Deals ↔ Companies (deal_to_company)
                            │
                            ▼
             [ Return SyncResult Contract ]
```

---

## 📐 Data Contracts & Object Schemas (`models.py`)

The engine enforces strict type safety and schema validation using **Pydantic v2** and typed string enums matching HubSpot's internal REST API v3 definitions:

### 1. Lifecycle Stage & Deal Stage Enums
```python
class LifecycleStage(str, Enum):
    LEAD = "lead"
    MQL = "marketingqualifiedlead"
    SQL = "salesqualifiedlead"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"

class DealStage(str, Enum):
    APPOINTMENT_SCHEDULED = "appointmentscheduled"
    QUALIFIED_TO_BUY = "qualifiedtobuy"
    PRESENTATION_SCHEDULED = "presentationscheduled"
    DECISION_MAKER_BOUGHT_IN = "decisionmakerboughtin"
    CONTRACT_SENT = "contractsent"
    CLOSED_WON = "closedwon"
    CLOSED_LOST = "closedlost"
```

### 2. Standardized Sync Result Contract
Every sync operation returns an immutable `SyncResult` providing telemetry for downstream analytics and revenue routers:
```python
class SyncResult(BaseModel):
    action: SyncAction           # CREATED | UPDATED | SKIPPED
    contact_id: str             # HubSpot Contact ID
    company_id: str             # HubSpot Company ID
    deal_id: Optional[str]      # HubSpot Deal ID (if deal created)
    is_duplicate: bool          # True if lead already existed in CRM
```

---

## ⚡ Production Verification: First Sync vs. Deduplication Run

The engine was tested against a live HubSpot CRM production environment.

### Run 1: First Inbound Lead Sync (Creation)
When a new lead arrives (`sarah.chen@linear.app` at `linear.app`), the engine creates the company, creates the contact, associates them, and provisions an enterprise deal:

```text
--- Running Live Sync ---
Sync Result: 
  action=<SyncAction.CREATED: 'created'> 
  contact_id='600066650859' 
  company_id='369701937875' 
  deal_id='371583102674' 
  is_duplicate=False
```

### Run 2: Re-ingesting the Same Lead (Deduplication & Atomic Update)
When the same lead is submitted again, the engine's search filter detects existing records by domain and email. It **prevents duplicate entity creation**, atomically updates the contact's lifecycle stage, and links the deal to the existing records:

```text
--- Running Live Sync ---
Sync Result: 
  action=<SyncAction.UPDATED: 'updated'> 
  contact_id='600066650859' 
  company_id='369701937875' 
  deal_id='371863570167' 
  is_duplicate=True
```
* **Company Records Created:** 1 (reused existing `369701937875`)
* **Contact Records Created:** 1 (reused existing `600066650859`)
* **Duplicate Leakage:** **0%**

---

## 🛠️ HubSpot v3 REST API Integration Details

### 1. Granular Scopes Requirement
HubSpot permanently migrated to **Service Keys** enforcing strict object-level permissions:
* `crm.objects.contacts.read` & `crm.objects.contacts.write`
* `crm.objects.companies.read` & `crm.objects.companies.write`
* `crm.objects.deals.read` & `crm.objects.deals.write`

### 2. Multi-Object Association Endpoints
HubSpot associations are maintained using idempotent HTTP `PUT` requests:
```http
PUT /crm/v3/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}/{assoc_type}
```
* `contacts` ➔ `companies` (`contact_to_company`)
* `deals` ➔ `contacts` (`deal_to_contact`)
* `deals` ➔ `companies` (`deal_to_company`)

### 3. Test Data Lifecycle Management (`delete.py`)
To enable automated testing and CI/CD teardown without cluttering the CRM, the engine includes a dedicated deletion service verifying HTTP `204 No Content`:
```python
async def delete(self, object_type: str, object_id: str) -> bool:
    response = await self.client.delete(
        f"{self.base_url}/crm/v3/objects/{object_type}/{object_id}",
        headers=self.__headers,
    )
    return response.status_code == 204
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
* Python 3.11+
* HubSpot Account with a configured Service Key

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Sameer330/hubspot-crm-sync-engine-gtm.git
cd hubspot-crm-sync-engine-gtm

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```env
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 4. Run Live Sync Engine
```bash
python sync_engine.py
```

---

## 📂 Project Structure

```
hubspot-crm-sync-engine/
├── models.py              # Pydantic schemas (CRMContact, CRMCompany, CRMDeal, SyncResult)
├── hubspot_client.py      # Async HTTPX client for HubSpot REST API v3
├── sync_engine.py         # Autonomous deduplication & multi-object sync orchestration
├── delete.py              # Test data lifecycle & CRM record cleanup utility
├── ping.py                # Health check & Service Key authentication verification
├── requirements.txt       # Production dependencies (httpx, pydantic, python-dotenv)
├── .env.example           # Template for environment credentials
└── README.md              # System documentation & architectural reference
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
