# Enrollment Examples

This directory contains JSON examples for the enrollment/onboarding flow for Digital Energy Programs.

## Files

### Init Requests
- **init-request-simple-consumer.json** - Simple consumer with single meter enrolling in a demand flexibility program
- **init-request-prosumer-solar-battery.json** - Prosumer with solar and battery DERs enrolling in a P2P trading program

### On_Init Responses
- **on-init-response-success.json** - Successful credential verification with no conflicts
- **on-init-response-conflict.json** - Enrollment conflict detected (meter already enrolled)
- **on-init-response-error.json** - Credential verification failed

### Confirm Request
- **confirm-request.json** - Confirm request with enrollment start and end dates

### On_Confirm Response
- **on-confirm-response-success.json** - Successful enrollment with issued credential

### Update Requests (Revocation/Unenrollment)
- **update-request-consent-revocation.json** - Request to revoke a consent credential
- **update-request-unenrollment.json** - Request to unenroll from a program

### On_Update Responses
- **on-update-response-consent-revocation.json** - Confirmation of consent revocation with status list details
- **on-update-response-unenrollment.json** - Confirmation of unenrollment with all credential revocations

## Usage

These examples are embedded in the implementation guide using the `embed_example_json.py` script. The examples are referenced using `<details>` blocks in the markdown file.

To update the embedded examples in the guide, run:
```bash
python3 scripts/embed_example_json.py docs/implementation-guides/v2/Onboarding/IG_Onboarding_users_in_digital_energy_programs.md
```

## Schema

All examples use the `EnergyEnrollment` schema defined at:
- Context: `https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyEnrollment/v0.2/context.jsonld`
- Attributes: `../protocol-specifications-new/schema/EnergyEnrollment/v0.2/attributes.yaml`

## Revocation Mechanism

Consent and enrollment credentials use W3C VC Status Lists (BitstringStatusList) for revocation:

1. **Consent Revocation**: User revokes consent via `update` action → BPP updates status list → Future verifications fail
2. **Unenrollment**: User unenrolls via `update` action → BPP revokes enrollment VC and all consent VCs → All credentials added to status lists

Verifiers must check status lists before accepting credentials. Status lists use bitstrings for efficient and privacy-preserving revocation checks as per [W3C VC Data Model v2.0](https://www.w3.org/TR/vc-data-model-2.0/).

