from typing import Dict, Any
from app.models.schemas import EntityIngest, EntitySource, Address

def parse_dnb_json(data: Dict[str, Any]) -> EntityIngest:
    """
    Parses a raw D&B API response (or file content) into a normalized EntityIngest object.
    """
    org = data.get("organization", {})
    
    # Extract Address
    primary_addr = org.get("primaryAddress", {})
    address = Address(
        street_number=primary_addr.get("streetNumber"),
        street_name=primary_addr.get("streetName"),
        city=primary_addr.get("addressLocality", {}).get("name"),
        state=primary_addr.get("addressRegion", {}).get("abbreviatedName"),
        postal_code=primary_addr.get("postalCode"),
        country_code=primary_addr.get("addressCountry", {}).get("isoAlpha2Code"),
        full_address=None # Could construct if needed
    )
    
    # Extract Financials (simplistic)
    revenue = None
    if org.get("financials"):
        # Take first financial statement's revenue
        try:
            revenue = org["financials"][0]["yearlyRevenue"][0]["value"]
        except (KeyError, IndexError):
            pass

    # Extract Employees
    employees = None
    if org.get("numberOfEmployees"):
         try:
            employees = org["numberOfEmployees"][0]["value"]
         except (KeyError, IndexError):
            pass

    return EntityIngest(
        name=org.get("primaryName"),
        legal_name=org.get("registeredName"),
        duns=org.get("duns"),
        registration_number=None, # Needs complex parsing from registrationNumbers list
        tax_id=None, # Needs complex parsing
        address=address,
        industry_code=None, # Parsing industryCodes list
        legal_form=org.get("legalForm", {}).get("description"),
        employee_count=employees,
        revenue_usd=revenue,
        source=EntitySource.DNB,
        source_id=org.get("duns"),
        raw_data=data
    )
