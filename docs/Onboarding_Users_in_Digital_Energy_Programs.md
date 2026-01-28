# **Technical Specification: Multi-Channel Onboarding of Users into Digital Energy Programs**

Version: 1.0 (Draft – Normative)

---

## **Status of This Memo**

This document defines the **technical specification** for onboarding users into Digital Energy Programs through multiple channels.
This is a **standards-track** document.

---

## **Table of Contents**

1. Scope
2. Normative References
3. Definitions
4. Architectural Overview
5. Identity & Authentication Specification
6. Asset Model Specification
7. Program Owner Specification (BPP Role)
8. Enrolment Channel Specification
9. Beckn-Based Enrollment Flow Specification
10. Enrollment Criteria Specification
11. Credential Specification
12. Registries
13. Security Considerations
14. Privacy Considerations
15. Compliance Requirements
16. Appendix (Message Structures)

---

# **1. Scope**

This specification defines the **protocols, message structures, identifiers, interactions, and requirements** for enrolling users into digital energy programs using:

* **Utility Portals**
* **Certified Enrolment Agency Portals**
* **Network Participant Applications** using an **Onboarding SDK**

The specification covers:

* Identity and authentication
* Meter and DER association
* Program discovery and eligibility verification
* Consent acquisition
* Credential issuance
* Multi-utility onboarding
* Multi-persona handling
* Beckn protocol interactions for search → select → init → confirm

This document is globally applicable and does not depend on any specific national identity scheme, tariff structure, or regulatory regime.

---

# **2. Normative References**

The following specifications are normative:

* **Beckn Protocol 1.x / 2.0** — Discovery, Ordering, Fulfillment flows
* **W3C DID Core**
* **W3C Verifiable Credentials (VC Data Model)**
* **OpenID Connect Core**
* **RFC 6749 – OAuth 2.0**
* **RFC 8259 – JSON**
* **ISO/IEC 30141 – IoT Reference Architecture**
* **DEG Vision Document** (Identity, Verifiability, Interoperability principles)

---

# **3. Definitions**

### **3.1 User Identifier**

One of:

* National ID (e.g., Social Security Number, Aadhaar, SIN, BankID, etc.)
* Program-level Meter Identifier (UMID)
* Utility Customer Identifier

### **3.2 Enrolment Agency (EA)**

A utility-certified entity authorized to conduct onboarding flows.

### **3.3 Program Owner**

Entity operating a digital energy program.
In Beckn terms, Program Owner implements a **BPP**.

### **3.4 Network Participant**

Any BAP, BPP, NFO, EV app, DER app, or aggregator application integrating via the SDK.

### **3.5 Behind-the-Meter (BTM) Appliances**

Appliances consuming or producing energy through a user-side meter.

---

# **4. Architectural Overview**

The onboarding architecture comprises:

## **4.1 Identity Layer**

* OIDC-based unified Identity Provider (IdP)
* Federation with national ID or utility ID providers
* All login returns a `subject_id`

## **4.2 Asset Layer**

Defines relationships:

* User ↔ Utility ↔ Accounts ↔ Meters ↔ Sites ↔ DERs (EV, solar, battery)

## **4.3 Program Layer**

Each Program Owner exposes:

* Beckn Discovery endpoint
* Beckn Select + Init + Confirm to communicate eligibility and enrollment requirements
* Issuance of Program Enrollment Credential

## **4.4 Channel Layer**

Three approved channels:

1. Utility Portal
2. Certified Enrolment Agency Portal
3. Network Participant App (via SDK)

## **4.5 Credential Layer**

All enrollment outcomes must issue:

* **Program Enrollment Credential** as a Verifiable Credential

---

# **5. Identity & Authentication Specification**

### **5.1 Identity Provider (IdP) Requirements**

The IdP MUST:

1. Support OIDC Authorization Code Flow
2. Support at least three identifiers:

   * `national_id`
   * `meter_id` (UMID)
   * `utility_customer_id`
3. Issue ID Tokens containing:

```json
{
  "sub": "<subject_id>",
  "id_type": "national|meter|utility",
  "meter_ids": ["<umid>"],
  "utility_customer_ids": ["<>"],
  "acr": "assurance_level",
  "iss": "https://idp.example.com"
}
```

### **5.2 Authentication Assurance**

The IdP MUST support:

* MFA (OTP, email, authenticator app, or national ID provider’s MFA)
* Federation with external trusted ID schemes

---

# **6. Asset Model Specification**

Every ecosystem MUST support the following data model:

### **6.1 Entities**

**User**

* `subject_id`
* Contact info

**Utility**

* `utility_id`
* Service areas (CIM regions)

**Meter**

* `umid` (universal meter identity)
* `utility_meter_id`
* `utility_id`
* `site_id`

**DER**

* `der_id`
* `der_type` (EV, solarPV, battery, heat pump, V2G-EV)
* `primary_meter` (umid)
* `secondary_utility` for cross-utility usage

**Program**

* `program_id`
* Owned by Program Owner (BPP)

---

# **7. Program Owner Specification (BPP Role)**

### **7.1 Program Discovery**

Program Owners MUST expose:

* `POST /search` (Beckn Search)
  Returns metadata:
* Supported personas
* Supported utilities
* Enrollment prerequisites

### **7.2 Eligibility Evaluation**

The **Init** API MUST return:

```json
{
  "enrollment_criteria": {
    "documents_required": [...],
    "proof_required": [...],
    "consents_required": [...],
    "cross_utility_checks": [...],
    "der_certification_required": true|false
  },
  "next_steps": "collect_documents"
}
```

### **7.3 Enrollment Decision**

The **Confirm** API MUST:

* Approve or reject enrollment
* Issue Program Enrollment Credential

---

# **8. Enrolment Channel Specification**

Three channels MUST use identical Beckn interactions.

### **8.1 Utility Portal**

* MUST redirect to IdP for login
* MUST invoke `search → select → init → confirm` on Program Owner’s BPP
* MUST store final Program Enrollment Credential for user

### **8.2 Certified Enrolment Agency Portal**

* MUST redirect to IdP
* MUST call Program Owner BPP
* MUST include EA identity header:

```
X-Enrollment-Agency-ID: <ea_id>
```

### **8.3 Network Participant App with SDK**

* MUST embed onboarding SDK
* MUST NOT directly call BPP
* SDK MUST perform all Beckn operations
* SDK MUST NOT override Enrollment decisions

---

# **9. Beckn-Based Enrollment Flow Specification**

### **9.1 Sequence**

1. `search` – Program discovery
2. `on_search` – Program Owner BPP responds
3. `select` – User selects program
4. `on_select` – Program Owner returns preliminary eligibility
5. `init` – User submits identifiers, meters, DERs
6. `on_init` – Program Owner returns:

   * Required consents
   * Required proofs
   * Cross-utility checks
7. `confirm` – User submits consents + proofs
8. `on_confirm` – Program Owner issues enrollment credential

### **9.2 Required Fields**

**init.request**

```json
{
  "subject_id": "did:example:123",
  "meters": ["umid-123", "umid-456"],
  "ders": ["der-ev-001"],
  "cross_utility_info": ["utilityB"],
  "persona_type": "consumer_multimeter"
}
```

---

# **10. Enrollment Criteria Specification**

Program Owners MUST publish criteria **via Beckn Select/Init**, not via registries.

Criteria MUST be returned as structured data:

```json
{
  "criteria": {
    "identity": ["national_id|meter_id|utility_id"],
    "meter_association": true,
    "der_certification": true,
    "utility_ownership_verification": true,
    "cross_utility_consent_required": true,
    "v2g_control_consent_required": false
  }
}
```

---

# **11. Credential Specification**

### **11.1 Program Enrollment Credential (VC)**

Required fields:

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1", "https://dedi.global/energy-program/v1"],
  "type": ["VerifiableCredential", "ProgramEnrollmentCredential"],
  "issuer": "<program_owner_did>",
  "credentialSubject": {
    "subject_id": "<user>",
    "program_id": "<program>",
    "meters": ["<umid>"],
    "ders": ["<der_id>"],
    "roles": ["consumer|prosumer|v2g-participant"],
    "constraints": {...}
  }
}
```

Must support **StatusList revocation**.

---

# **12. Registries**

Program discovery and criteria are **not registries**.

The following registries **MUST** exist on `dedi.global`:

### **12.1 Utility Registry**

Contains:

* Utility ID
* Public keys
* Service areas

### **12.2 Enrolment Agency Registry**

Contains:

* EA ID
* Certification details
* Supported utilities
* Public signing keys

### **12.3 Schema Registry**

Contains:

* Program Enrollment Credential schema
* Meter/DER schemas
* Consent schema

Registries MUST be publicly accessible and versioned.

---

# **13. Security Considerations**

* All Beckn messages MUST be signed (non-repudiation).
* IdP must enforce MFA where legally required.
* DER control consents MUST be explicit.
* Cross-utility interactions MUST use mutual TLS.

---

# **14. Privacy Considerations**

* Programs MUST request minimum necessary data.
* National IDs must not be stored by Program Owners without legal basis.
* Cross-utility data sharing requires explicit consent.
* Users must be able to revoke participation at any time.

---

# **15. Compliance Requirements**

Entities MUST comply with:

* Data protection laws (GDPR, CCPA, PDPA, etc.)
* Grid/utility regulatory frameworks
* Beckn protocol compliance
* Credential issuance standards
* Deg Vision principles (identity, verifiability, interoperability)

---

# **16. Appendix: Message Structure Examples**

## **16.1 Beckn init**

```json
{
  "context": { "action": "init" },
  "message": {
    "order": {
      "provider": { "id": "program-owner-bpp" },
      "items": [{ "id": "program-id" }],
      "fulfillments": [{
        "customer": { "id": "<subject_id>" },
        "instrument": {
          "meters": ["umid-1"],
          "ders": ["der-1"]
        }
      }]
    }
  }
}
```

## **16.2 Beckn on_confirm**

```json
{
  "message": {
    "order": {
      "provider": { "id": "program-owner-bpp" },
      "id": "enrollment-12345",
      "state": "CONFIRMED",
      "documents": [{
        "type": "ProgramEnrollmentCredential",
        "url": "https://utility.example.com/credential/123"
      }]
    }
  }
}
```
