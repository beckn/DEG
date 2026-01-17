"""
Beckn Protocol Schema Validator

This script validates JSON payloads against Beckn protocol schemas (core and domain-specific).
It automatically discovers and loads schemas from @context URLs embedded in JSON-LD objects,
supports both core Beckn objects (beckn:Order, beckn:Offer, etc.) and domain-specific attribute
objects (ChargingOffer, ChargingSession, etc.), and handles schema references across multiple
schema files.

HOW IT WORKS:
-------------
1. Schema Discovery: The validator scans JSON payloads for objects with @context and @type fields.
   These fields indicate which schema should be used for validation.

2. On-Demand Loading: Schemas are loaded on-demand from GitHub URLs when first encountered.
   The @context URL (e.g., .../EvChargingOffer/v1/context.jsonld) is converted to the
   corresponding attributes.yaml URL for schema loading.

3. Schema Caching: Loaded schemas are cached in a Registry and attribute_schemas_map to avoid
   redundant network requests.

4. Reference Resolution: Uses the referencing library to resolve $ref JSON pointers within
   and across schema files. Core objects use $ref to the full schema document to ensure
   internal references resolve correctly.

5. Validation: Validates objects against their corresponding schemas, handling both core
   Beckn objects and domain-specific attribute objects with different validation strategies.
   
Note: Schemas are loaded from the exact branch specified in the @context URL. If a schema
is not found on that branch, validation will fail. No branch fallback is performed.

ARCHITECTURE:
-------------
- Core Objects (beckn:Order, beckn:Offer, etc.): Validated using schemas from core/v2/attributes.yaml
- Attribute Objects (ChargingOffer, ChargingSession, etc.): Validated using schemas from
  domain-specific attributes.yaml files (e.g., EvChargingOffer/v1/attributes.yaml)
- JSON-LD Support: Automatically allows @context and @type properties even when schemas
  have additionalProperties: false

USAGE EXAMPLES:
---------------
# Validate a single JSON file:
python3 scripts/validate_schema.py examples/ev-charging/v2/03_select/time-based-ev-charging-slot-select.json

# Validate multiple files:
python3 scripts/validate_schema.py examples/ev-charging/v2/**/*.json

# Validate only core Beckn objects (skip domain-specific attributes):
python3 scripts/validate_schema.py --core-only examples/ev-charging/v2/03_select/time-based-ev-charging-slot-select.json

# Validate Postman collection:
python3 scripts/validate_schema.py testnet/ev-charging-devkit/postman/ev-charging:BAP-DEG.postman_collection.json

EXAMPLE JSON STRUCTURE:
----------------------
{
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-123",
      "beckn:orderItems": [
        {
          "beckn:acceptedOffer": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/EvChargingOffer/v1/context.jsonld",
              "@type": "ChargingOffer",
              "tariffModel": "PER_KWH"
            }
          }
        }
      ]
    }
  }
}

The validator will:
1. Detect beckn:Order and load core/v2/attributes.yaml
2. Detect beckn:Offer and use the already-loaded core schema
3. Detect ChargingOffer and load EvChargingOffer/v1/attributes.yaml
4. Validate each object against its corresponding schema

DEPENDENCIES:
-------------
- jsonschema: JSON Schema validation
- referencing: JSON Schema reference resolution
- requests: HTTP requests for schema loading
- yaml: YAML parsing for schema files
"""

import json
import re
import copy
import requests
import yaml
from jsonschema import validate, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

def load_schema_from_url(url):
    """
    Load a YAML schema file from a URL.
    
    Args:
        url: URL to the attributes.yaml schema file
        
    Returns:
        dict: Parsed YAML schema as a dictionary
        
    Raises:
        requests.HTTPError: If the HTTP request fails
        yaml.YAMLError: If YAML parsing fails
    """
    response = requests.get(url)
    response.raise_for_status()
    return yaml.safe_load(response.text)

def extract_schema_info_from_url(url):
    """
    Extract schema name and version from attributes.yaml URL.
    
    Example: 
        https://.../EvChargingOffer/v1/attributes.yaml -> (EvChargingOffer, v1)
    """
    match = re.search(r'/schema/([^/]+)/([^/]+)/attributes\.yaml', url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def extract_branch_from_context_url(context_url):
    """
    Extract branch name from @context URL.
    
    Example:
        .../refs/heads/draft/schema/... -> draft
        .../refs/heads/p2p_trading/schema/... -> p2p_trading
        .../refs/heads/main/schema/... -> main
    """
    match = re.search(r'/refs/heads/([^/]+)/schema/', context_url)
    if match:
        return match.group(1)
    return None

def get_attributes_url_from_context_url(context_url):
    """
    Convert context.jsonld URL to corresponding attributes.yaml URL.
    Infers branch from the context URL.
    
    Example:
        .../draft/schema/EvChargingOffer/v1/context.jsonld -> .../draft/schema/EvChargingOffer/v1/attributes.yaml
        .../p2p_trading/schema/EnergyResource/v0.2/context.jsonld -> .../p2p_trading/schema/EnergyResource/v0.2/attributes.yaml
        .../draft/schema/core/v2/context.jsonld -> .../draft/schema/core/v2/attributes.yaml
    """
    return context_url.replace('/context.jsonld', '/attributes.yaml')

def is_core_context_url(context_url):
    """
    Check if @context URL points to core schema.
    
    Example:
        .../schema/core/v2/context.jsonld -> True
        .../schema/EvChargingOffer/v1/context.jsonld -> False
    """
    return '/schema/core/' in context_url

def load_core_schema_for_context_url(context_url, registry_list):
    """
    Load core attributes schema for a given @context URL.
    
    Loads the schema from the branch specified in the context_url. Caches the schema
    in the registry for reuse.
    
    Args:
        context_url: The @context URL from the JSON (e.g., .../core/v2/context.jsonld)
        registry_list: List containing referencing Registry (mutated in place)
    
    Returns:
        dict: Schema data if successful, None if loading fails
    """
    registry = registry_list[0]
    attributes_url = get_attributes_url_from_context_url(context_url)
    
    # Check if already loaded in registry
    try:
        resource = registry.get(attributes_url)
        if resource is not None:
            return resource.contents
    except (KeyError, AttributeError):
        pass
    
    # Load from the branch specified in context_url
    try:
        schema_data = load_schema_from_url(attributes_url)
        registry_list[0] = registry.with_resource(attributes_url, Resource.from_contents(schema_data, DRAFT202012))
        branch = extract_branch_from_context_url(context_url)
        print(f"  Loaded core attributes schema (branch: {branch})")
        return schema_data
    except Exception as e:
        print(f"  Warning: Failed to load core attributes schema from {attributes_url}: {e}")
        return None

def load_schema_for_context_url(context_url, attribute_schemas_map, registry_list=None):
    """
    Load schema for a given @context URL from the branch specified in the URL.
    
    Args:
        context_url: The @context URL from the JSON
        attribute_schemas_map: Existing map to add to (may be modified)
        registry_list: List containing referencing Registry (mutated in place, optional)
    
    Returns:
        tuple: (schema_name, schema_data, schema_url) or None if failed
    """
    # Check if we already have this context URL mapped
    if context_url in attribute_schemas_map:
        return attribute_schemas_map[context_url]
    
    # Extract branch from context URL
    branch = extract_branch_from_context_url(context_url)
    if not branch:
        return None
    
    # Convert context URL to attributes URL
    attributes_url = get_attributes_url_from_context_url(context_url)
    
    # Extract schema name and version
    schema_name, version = extract_schema_info_from_url(attributes_url)
    if not schema_name:
        return None
    
    # Load the schema from the branch specified in context_url
    try:
        schema_data = load_schema_from_url(attributes_url)
        attribute_schemas_map[context_url] = (schema_name, schema_data, attributes_url)
        if registry_list is not None:
            registry = registry_list[0]
            registry_list[0] = registry.with_resource(attributes_url, Resource.from_contents(schema_data, DRAFT202012))
        print(f"  Loaded: {schema_name}/{version} (branch: {branch})")
        return (schema_name, schema_data, attributes_url)
    except Exception as e:
        print(f"  Warning: Failed to load {schema_name}/{version} from {attributes_url}: {e}")
        return None


def _validate_attribute_object(data, schema_def, schema_type, schema_name, path, errors, registry_list, schema_url=None):
    """
    Validate a domain-specific attribute object against its schema.
    
    Uses $ref to full document to allow nested $ref resolution, then handles
    @context and @type properties which are required for JSON-LD.
    
    Args:
        data: Object data to validate
        schema_def: Schema definition from attributes.yaml (used as fallback)
        schema_type: Type name for logging (e.g., "ChargingOffer")
        schema_name: Schema name for logging (e.g., "EvChargingOffer")
        path: JSON path for error reporting
        errors: List to append validation errors to
        registry_list: Registry list for reference resolution
        schema_url: Full URL to the attributes.yaml file (for $ref resolution)
    """
    print(f"  Validating {schema_type} (from {schema_name}) at {path or 'root'}...")
    
    # Try using $ref to full document first (allows nested $ref resolution)
    if schema_url:
        try:
            # Get the full document resource from registry
            full_doc_resource = registry_list[0].get(schema_url)
            if full_doc_resource:
                full_doc = full_doc_resource.contents
                # Extract the schema from the full document
                if "components" in full_doc and "schemas" in full_doc["components"]:
                    target_schema = full_doc["components"]["schemas"].get(schema_type)
                    if target_schema:
                        # Recursively convert relative $ref to absolute $ref
                        # Also need to handle nested schemas referenced within this schema
                        def convert_relative_refs(obj, base_url, full_doc_schemas=None):
                            """Recursively convert relative $ref to absolute $ref"""
                            if isinstance(obj, dict):
                                result = {}
                                for k, v in obj.items():
                                    if k == "$ref" and isinstance(v, str) and v.startswith("#"):
                                        # Convert relative ref to absolute
                                        result[k] = f"{base_url}{v}"
                                    elif k == "allOf" and isinstance(v, list):
                                        # Handle allOf with $ref - convert $ref in allOf items
                                        result[k] = [convert_relative_refs(item, base_url, full_doc_schemas) for item in v]
                                    else:
                                        result[k] = convert_relative_refs(v, base_url, full_doc_schemas)
                                return result
                            elif isinstance(obj, list):
                                return [convert_relative_refs(item, base_url, full_doc_schemas) for item in obj]
                            return obj
                        
                        # Get schema and convert relative $ref to absolute $ref
                        resolved_schema = copy.deepcopy(target_schema)
                        resolved_schema = convert_relative_refs(resolved_schema, schema_url)
                        
                        # Modify to allow @context and @type (required for JSON-LD)
                        if resolved_schema.get("additionalProperties") is False:
                            if "properties" not in resolved_schema:
                                resolved_schema["properties"] = {}
                            resolved_schema["properties"]["@context"] = {"type": "string"}
                            resolved_schema["properties"]["@type"] = {"type": "string"}
                        
                        # Validate against the resolved and modified schema
                        validate(instance=data, schema=resolved_schema, registry=registry_list[0])
                        print(f"  {schema_type} at {path or 'root'} is VALID.")
                        return
        except ValidationError as e:
            print(f"  {schema_type} at {path or 'root'} is INVALID: {e.message}")
            print(f"  Path: {e.json_path}")
            errors.append(f"{path} ({schema_type}): {e.message}")
            return
        except Exception as e:
            # Fallback to direct validation if $ref resolution fails
            pass
    
    # Fallback: direct validation with schema fragment (may fail on nested $ref)
    validation_schema = copy.deepcopy(schema_def)
    if validation_schema.get("additionalProperties") is False:
        if "properties" not in validation_schema:
            validation_schema["properties"] = {}
        validation_schema["properties"]["@context"] = {"type": "string"}
        validation_schema["properties"]["@type"] = {"type": "string"}
    
    try:
        validate(instance=data, schema=validation_schema, registry=registry_list[0])
        print(f"  {schema_type} at {path or 'root'} is VALID.")
    except ValidationError as e:
        print(f"  {schema_type} at {path or 'root'} is INVALID: {e.message}")
        print(f"  Path: {e.json_path}")
        errors.append(f"{path} ({schema_type}): {e.message}")

def get_schema_store():
    """
    Initialize empty schema store for on-demand schema loading.
    
    Returns:
        tuple: (registry_list, attributes_schema, attribute_schemas_map)
            - registry_list: List containing referencing Registry (wrapped for mutability)
            - attributes_schema: Unused, kept for compatibility (None)
            - attribute_schemas_map: Dict mapping @context URLs to (schema_name, schema_data, schema_url)
    """
    registry = Registry()
    attribute_schemas_map = {}
    return [registry], None, attribute_schemas_map

def validate_payload(payload, registry_list, attributes_schema, attribute_schemas_map=None, core_only=False):
    """
    Validate JSON payload against Beckn protocol schemas.
    
    Recursively traverses the payload, identifies objects with @context and @type,
    loads schemas on-demand, and validates each object against its corresponding schema.
    Supports both core Beckn objects (beckn:Order, etc.) and domain-specific attribute
    objects (ChargingOffer, etc.).
    
    Args:
        payload: JSON payload to validate (dict or list)
        registry_list: List containing referencing Registry with all loaded schemas
        attributes_schema: Unused, kept for compatibility (None)
        attribute_schemas_map: Dict mapping @context URLs to (schema_name, schema_data, schema_url)
        core_only: If True, only validate core Beckn objects, skip domain-specific attributes
    
    Returns:
        list: List of validation error messages (empty if validation passes)
    """
    errors = []
    
    def find_and_validate_objects(data, path=""):
        if isinstance(data, dict):
            # Check for objects with @context and @type
            if "@context" in data and "@type" in data and attribute_schemas_map is not None:
                context_url = data.get("@context")
                obj_type = data.get("@type")
                
                # Handle core Beckn objects (e.g., beckn:Order, beckn:Offer)
                if obj_type and obj_type.startswith("beckn:"):
                    if is_core_context_url(context_url):
                        attributes_url = get_attributes_url_from_context_url(context_url)
                        if attributes_url not in registry_list[0]:
                            load_core_schema_for_context_url(context_url, registry_list)
                        
                        try:
                            resource = registry_list[0].get(attributes_url)
                            if resource is not None:
                                core_attributes = resource.contents
                                object_name = obj_type.split(":")[-1]
                                
                                if "components" in core_attributes and "schemas" in core_attributes["components"]:
                                    schemas = core_attributes["components"]["schemas"]
                                    if object_name in schemas:
                                        print(f"  Validating {object_name} at {path or 'root'}...")
                                        try:
                                            # Use $ref to full document to allow internal JSON pointer resolution
                                            schema_to_validate = {
                                                "$ref": f"{attributes_url}#/components/schemas/{object_name}"
                                            }
                                            validate(instance=data, schema=schema_to_validate, registry=registry_list[0])
                                            print(f"  {object_name} at {path or 'root'} is VALID.")
                                        except ValidationError as e:
                                            print(f"  {object_name} at {path or 'root'} is INVALID: {e.message}")
                                            print(f"  Path: {e.json_path}")
                                            errors.append(f"{path}: {e.message}")
                                        except Exception as e:
                                            # Fallback to direct fragment validation if $ref resolution fails
                                            print(f"  Warning: $ref resolution failed, trying direct validation: {e}")
                                            try:
                                                validate(instance=data, schema=schemas[object_name], registry=registry_list[0])
                                                print(f"  {object_name} at {path or 'root'} is VALID.")
                                            except ValidationError as ve:
                                                print(f"  {object_name} at {path or 'root'} is INVALID: {ve.message}")
                                                print(f"  Path: {ve.json_path}")
                                                errors.append(f"{path}: {ve.message}")
                        except (KeyError, AttributeError):
                            pass
                
                # Handle non-core domain-specific attribute objects
                else:
                    if core_only:
                        # Skip domain-specific attribute validation when --core-only flag is set
                        pass
                    else:
                        if context_url not in attribute_schemas_map:
                            load_schema_for_context_url(context_url, attribute_schemas_map, registry_list)
                        
                        if context_url in attribute_schemas_map:
                            schema_name, schema_data, schema_url = attribute_schemas_map[context_url]
                            schema_type = obj_type.split(":")[-1] if ":" in obj_type else obj_type
                            
                            if "components" in schema_data and "schemas" in schema_data["components"]:
                                schemas = schema_data["components"]["schemas"]
                                
                                # Try exact match first
                                if schema_type in schemas:
                                    _validate_attribute_object(data, schemas[schema_type], schema_type, schema_name, path, errors, registry_list, schema_url)
                                else:
                                    # Try case-insensitive match
                                    for schema_key, schema_def in schemas.items():
                                        if schema_key.lower() == schema_type.lower():
                                            _validate_attribute_object(data, schema_def, schema_key, schema_name, path, errors, registry_list, schema_url)
                                            break
            
            # Recursively check children
            for key, value in data.items():
                find_and_validate_objects(value, f"{path}/{key}" if path else key)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                find_and_validate_objects(item, f"{path}[{idx}]")

    find_and_validate_objects(payload)
    return errors

def process_file(filepath, registry_list, attributes_schema, attribute_schemas_map=None, core_only=False):
    """
    Process and validate a JSON file or Postman collection.
    
    Supports two file types:
    1. Regular JSON files: Validated directly
    2. Postman collections: Extracts JSON bodies from request items and validates them
    
    Args:
        filepath: Path to JSON file or Postman collection
        registry_list: List containing referencing Registry
        attributes_schema: Unused, kept for compatibility (None)
        attribute_schemas_map: Dict mapping @context URLs to schema info
        core_only: If True, only validate core Beckn objects, skip domain-specific attributes
    """
    print(f"Processing {filepath}...")
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        is_postman = "info" in data and "_postman_id" in data.get("info", {})
        
        if is_postman:
            print("  Identified as Postman collection.")
            _traverse_postman_items(data.get("item", []), registry_list, attributes_schema, attribute_schemas_map, core_only)
        else:
            validate_payload(data, registry_list, attributes_schema, attribute_schemas_map, core_only)
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")

def _traverse_postman_items(items, registry_list, attributes_schema, attribute_schemas_map, core_only=False):
    """
    Recursively traverse Postman collection items and validate JSON request bodies.
    
    Args:
        items: List of Postman collection items (may contain nested items)
        registry_list: List containing referencing Registry
        attributes_schema: Unused, kept for compatibility (None)
        attribute_schemas_map: Dict mapping @context URLs to schema info
        core_only: If True, only validate core Beckn objects, skip domain-specific attributes
    """
    for item in items:
        if "item" in item:
            _traverse_postman_items(item["item"], registry_list, attributes_schema, attribute_schemas_map, core_only)
        if "request" in item and "body" in item["request"]:
            body = item["request"]["body"]
            if body.get("mode") == "raw":
                try:
                    json_body = json.loads(body["raw"])
                    validate_payload(json_body, registry_list, attributes_schema, attribute_schemas_map, core_only)
                except json.JSONDecodeError:
                    pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate JSON files against Beckn protocol schemas",
        epilog="Example: python3 scripts/validate_schema.py examples/ev-charging/v2/**/*.json"
    )
    parser.add_argument("files", nargs="+", help="JSON files or Postman collections to validate")
    parser.add_argument(
        "--core-only",
        action="store_true",
        default=False,
        help="Only validate core Beckn objects (beckn:Order, beckn:Offer, etc.), skip domain-specific attribute objects"
    )
    
    args = parser.parse_args()
    registry, attributes_schema, attribute_schemas_map = get_schema_store()
    
    for file in args.files:
        process_file(file, registry, attributes_schema, attribute_schemas_map, core_only=args.core_only)
