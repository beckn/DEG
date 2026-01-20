#!/usr/bin/env python3
"""
Beckn Postman Collection Generator

This script builds Postman collections from the example JSON flows in this repo for a
given devkit (e.g., ev-charging) and role (BAP or BPP). It wires in context macros so
requests route correctly within the devkit testnets, and can optionally validate the
resulting collection against Beckn schemas.

WHAT IT DOES
------------
1) Discovers example JSON files under a devkit-specific examples directory
2) Builds Postman items for each API flow, adding environment macros for BAP/BPP IDs and URIs
3) Writes a Postman collection JSON to the requested output directory
4) Optionally validates the generated collection using the local `validate_schema.py`

KEY FUNCTIONS
-------------
- `generate_collection(...)`: Core builder; converts example flows to Postman items
- `build_item(...)`: Creates a Postman item with request, headers, and body
- `attach_env_macros(...)`: Injects {{bap_id}}, {{bap_uri}}, {{bpp_id}}, {{bpp_uri}}
  placeholders so the same collection works across environments
- `main()`: CLI entry point (parses args, resolves paths, runs generation, optional validation)

CLI USAGE
---------
python3 scripts/generate_postman_collection.py \\
  --devkit ev-charging \\
  --role BAP \\
  --output-dir testnet/ev-charging-devkit/postman \\
  --examples examples/ev-charging/v2 \\
  --name ev-charging:BAP-DEG \\
  --description \"EV Charging BAP flows\" \\
  --validate

Arguments:
- --devkit        Devkit key (e.g., ev-charging)
- --role          Role in the flows (BAP or BPP)
- --output-dir    Where to write the Postman collection
- --examples      Root path to example JSONs (defaults from devkit config)
- --name          Collection name (default: <devkit>:<role>-DEG)
- --description   Collection description (optional)
- --validate      Run schema validation on the generated collection using validate_schema.py

OUTPUT
------
Writes a Postman collection JSON with environment macros for IDs/URIs, suitable for
importing into Postman or running via newman with environment files.
"""

import json
import os
import re
import uuid
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import validation functions from validate_schema
try:
    # Try importing as module (if scripts directory is in path)
    from validate_schema import get_schema_store, process_file
except ImportError:
    # If running as a script, import from same directory
    import importlib.util
    validate_schema_path = Path(__file__).parent / "validate_schema.py"
    if validate_schema_path.exists():
        spec = importlib.util.spec_from_file_location("validate_schema", validate_schema_path)
        validate_schema = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validate_schema)
        get_schema_store = validate_schema.get_schema_store
        process_file = validate_schema.process_file
    else:
        get_schema_store = None
        process_file = None


# Configuration for different devkits
DEVKIT_CONFIGS = {
    "ev-charging": {
        "domain": "beckn.one:deg:ev-charging:2.0.0",
        "bap_id": "ev-charging.sandbox1.com",
        "bap_uri": "http://onix-bap:8081/bap/receiver",
        "bpp_id": "ev-charging.sandbox2.com",
        "bpp_uri": "http://onix-bpp:8082/bpp/receiver",
        "bap_adapter_url": "http://localhost:8081/bap/caller",
        "bpp_adapter_url": "http://localhost:8082/bpp/caller",
        "examples_path": "examples/ev-charging/v2",
        # "output_path": "testnet/ev-charging-devkit/postman",
        "structure": "folders"  # Folder-based structure
    },
    "p2p-trading": {
        "domain": "beckn.one:deg:p2p-trading:2.0.0",
        "bap_id": "p2p-trading-sandbox1.com",
        "bap_uri": "http://onix-bap:8081/bap/receiver",
        "bpp_id": "p2p-trading-sandbox2.com",
        "bpp_uri": "http://onix-bpp:8082/bpp/receiver",
        "bap_adapter_url": "http://localhost:8081/bap/caller",
        "bpp_adapter_url": "http://localhost:8082/bpp/caller",
        "examples_path": "examples/p2p-trading/v2",
        # "output_path": "testnet/p2p-energy-trading-devkit/postman",
        "structure": "flat"  # Flat file structure
    },
    "p2p-enrollment": {
        "domain": "beckn.one:deg:p2p-enrollment:2.0.0",
        "bap_id": "p2p-enrollment-sandbox1.com",
        "bap_uri": "http://onix-bap:8081/bap/receiver",
        "bpp_id": "p2p-enrollment-sandbox2.com",
        "bpp_uri": "http://onix-bpp:8082/bpp/receiver",
        "bap_adapter_url": "http://localhost:8081/bap/caller",
        "bpp_adapter_url": "http://localhost:8082/bpp/caller",
        "examples_path": "examples/enrollment/v2",
        # "output_path": "testnet/p2p-enrollment-devkit/postman",
        "structure": "flat"  # Flat file structure (like p2p-trading)
    },
    "p2p-trading-interdiscom": {
        "domain": "beckn.one:deg:p2p-trading:2.0.0",
        "bap_id": "p2p-trading-sandbox1.com",
        "bap_uri": "http://onix-bap:8081/bap/receiver",
        "bpp_id": "p2p-trading-sandbox2.com",
        "bpp_uri": "http://onix-bpp:8082/bpp/receiver",
        "bap_adapter_url": "http://localhost:8081/bap/caller",
        "bpp_adapter_url": "http://localhost:8082/bpp/caller",
        "examples_path": "examples/p2p-trading-interdiscom/v2",
        # "output_path": "testnet/p2p-trading-interdiscom-devkit/postman",
        "structure": "flat"  # Flat file structure (like p2p-trading)
    }
}

# Role-based file name filters (regex patterns)
ROLE_FILTERS = {
    "BAP": [
        r".*-request.*\.json$",  # P2P trading/enrollment: *-request*.json (includes suffixes like -otp, -oauth2)
        r"^\d+_(discover|select|init|confirm|status|update|track|rating|support|cancel)\.json$",  # EV charging: numbered folders
        r"^(discover|select|init|confirm|status|update|track|rating|support|cancel).*\.json$"  # General pattern
    ],
    "BPP": [
        r"^(?!cascaded-).*-response.*\.json$",  # P2P trading/enrollment: *-response*.json (excludes cascaded-)
        r"^\d+_on_(discover|select|init|confirm|update|track|status|rating|support|cancel).*\.json$",  # EV charging: on_* folders
        r"^on[-_](discover|select|init|confirm|update|track|status|rating|support|cancel).*\.json$",  # General pattern (on- or on_)
        r"^publish-.*\.json$"  # BPP-initiated publish action to CDS
    ],
    "UtilityBPP": [
        r"^cascaded-.*\.json$"  # Cascaded requests/responses
    ]
}

# All BAP-initiated actions (including status)
BAP_ACTIONS = {
    "discover": "discover",
    "select": "select",
    "init": "init",
    "confirm": "confirm",
    "status": "status",
    "update": "update",
    "track": "track",
    "rating": "rating",
    "support": "support",
    "cancel": "cancel",
}

# BPP-initiated actions (not callbacks, but BPP initiating requests to CDS, etc.)
BPP_INITIATED_ACTIONS = {
    "publish": "publish",
}

# BPP response actions
BPP_ACTIONS = {
    "on_discover": "on_discover",
    "on_select": "on_select",
    "on_init": "on_init",
    "on_confirm": "on_confirm",
    "on_status": "on_status",
    "on_update": "on_update",
    "on_track": "on_track",
    "on_rating": "on_rating",
    "on_support": "on_support",
    "on_cancel": "on_cancel",
}

# Pre-request script for ISO timestamp generation
PRE_REQUEST_SCRIPT = """// Pure JS pre-request script to replace moment()
// 1) ISO 8601 timestamp without needing moment
const isoTimestamp = new Date().toISOString();
pm.collectionVariables.set('iso_date', isoTimestamp);
"""


def matches_role_filter(filename: str, role: str) -> bool:
    """
    Check if filename matches role-based filter patterns.
    
    Args:
        filename: Name of the file
        role: Role (BAP, BPP, or UtilityBPP)
    
    Returns:
        True if filename matches role filters
    """
    if role not in ROLE_FILTERS:
        return False
    
    for pattern in ROLE_FILTERS[role]:
        if re.match(pattern, filename, re.IGNORECASE):
            return True
    return False


def extract_action_from_filename(filename: str, role: str) -> Optional[str]:
    """
    Extract action name from filename based on role.
    
    Examples:
        "discover-request.json" (BAP) -> "discover"
        "discover-response.json" (BPP) -> "on_discover"
        "cascaded-init-request.json" (UtilityBPP) -> "init"
        "init-request-otp.json" (BAP) -> "init"
        "on-init-response-oauth2.json" (BPP) -> "on_init"
    """
    # Remove .json extension
    name = filename.replace('.json', '')
    
    # Handle P2P trading/enrollment flat structure - strict role-based matching
    if role == "BAP":
        # BAP only matches *-request*.json (not *-response*.json)
        # Pattern: action-request or action-request-suffix
        if '-request' in name and '-response' not in name:
            # Extract action from before -request
            match = re.match(r'^(cascaded-)?([a-z]+)-request', name, re.IGNORECASE)
            if match:
                is_cascaded = match.group(1) is not None
                action = match.group(2)
                if action in BAP_ACTIONS:
                    return action
    
    elif role == "BPP":
        # BPP matches *-response*.json (not *-request*.json) AND publish-*.json
        # Patterns: action-response, on-action-response, action-response-suffix, publish-*

        # First check for BPP-initiated actions (like publish-catalog.json)
        if name.startswith('publish-'):
            match = re.match(r'^(publish)-', name, re.IGNORECASE)
            if match:
                action = match.group(1).lower()
                if action in BPP_INITIATED_ACTIONS:
                    return action

        if '-response' in name and '-request' not in name:
            # First try: on-action-response pattern (e.g., on-init-response-oauth2)
            match = re.match(r'^(cascaded-)?(on[-_])?([a-z]+)-response', name, re.IGNORECASE)
            if match:
                is_cascaded = match.group(1) is not None
                has_on_prefix = match.group(2) is not None
                action = match.group(3)

                if has_on_prefix:
                    # Already has on_ prefix (e.g., on-init-response -> on_init)
                    bpp_action = f"on_{action}"
                    if bpp_action in BPP_ACTIONS:
                        return bpp_action
                else:
                    # No on_ prefix, convert to BPP action (e.g., discover-response -> on_discover)
                    if action in BAP_ACTIONS:
                        return f"on_{action}"
    
    elif role == "UtilityBPP":
        # UtilityBPP matches cascaded-*-request*.json
        if name.startswith('cascaded-') and '-request' in name:
            match = re.match(r'^cascaded-([a-z]+)-request', name, re.IGNORECASE)
            if match:
                action = match.group(1)
                if action in BAP_ACTIONS:
                    return action
    
    return None


def extract_action_from_folder(folder_name: str, role: str) -> Optional[str]:
    """
    Extract action name from folder name (for folder-based structure).
    
    Examples:
        "01_discover" (BAP) -> "discover"
        "02_on_discover" (BPP) -> "on_discover"
        "08_02_on_status" (BPP) -> "on_status"
        "03_select" (BAP) -> "select"
    """
    # Remove leading numbers and underscores
    # Handles both: \d+_action and \d+_\d+_action patterns
    match = re.match(r'^\d+(?:_\d+)?_(.+)$', folder_name)
    if match:
        action = match.group(1)
        
        if role == "BAP":
            # BAP uses regular actions
            if action in BAP_ACTIONS:
                return action
        elif role == "BPP":
            # BPP uses on_* actions
            if action in BPP_ACTIONS:
                return action
        elif role == "UtilityBPP":
            # UtilityBPP uses cascaded actions (same as BAP actions)
            if action in BAP_ACTIONS:
                return action
    
    return None


def get_request_name(filename: str) -> str:
    """
    Use filename directly as request name (remove .json extension).
    
    Examples:
        "discovery-along-route.json" -> "discovery-along-route"
        "time-based-ev-charging-slot-select.json" -> "time-based-ev-charging-slot-select"
        "discover-request.json" -> "discover-request"
    """
    return filename.replace('.json', '')


def load_example_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load and parse JSON example file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            print(f"  Warning: {filepath.name} is not a JSON object, skipping")
            return None
        
        if "context" not in data or "message" not in data:
            print(f"  Warning: {filepath.name} missing 'context' or 'message', skipping")
            return None
        
        return data
    except json.JSONDecodeError as e:
        print(f"  Error: {filepath.name} is not valid JSON: {e}, skipping")
        return None
    except Exception as e:
        print(f"  Error reading {filepath.name}: {e}, skipping")
        return None


def replace_context_macros(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace hardcoded context values with Postman macros.
    
    Preserves message payload as-is, only modifies context.
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    
    for key, value in data.items():
        if key == "context" and isinstance(value, dict):
            # Replace context fields with macros
            new_context = {}
            for ctx_key, ctx_value in value.items():
                if ctx_key == "version":
                    new_context[ctx_key] = "{{version}}"
                elif ctx_key == "domain":
                    # Handle wildcard domains
                    if isinstance(ctx_value, str) and "*" in ctx_value:
                        new_context[ctx_key] = "{{domain}}"
                    else:
                        new_context[ctx_key] = "{{domain}}"
                elif ctx_key == "bap_id":
                    new_context[ctx_key] = "{{bap_id}}"
                elif ctx_key == "bap_uri":
                    new_context[ctx_key] = "{{bap_uri}}"
                elif ctx_key == "bpp_id":
                    new_context[ctx_key] = "{{bpp_id}}"
                elif ctx_key == "bpp_uri":
                    new_context[ctx_key] = "{{bpp_uri}}"
                elif ctx_key == "transaction_id":
                    new_context[ctx_key] = "{{transaction_id}}"
                elif ctx_key == "message_id":
                    new_context[ctx_key] = "{{$guid}}"
                elif ctx_key == "timestamp":
                    new_context[ctx_key] = "{{iso_date}}"
                elif ctx_key == "ttl":
                    # Keep TTL as constant
                    new_context[ctx_key] = ctx_value
                elif ctx_key == "schema_context":
                    # Preserve schema_context array as-is
                    new_context[ctx_key] = ctx_value
                elif ctx_key == "action":
                    # Keep action as-is (needed for routing)
                    new_context[ctx_key] = ctx_value
                else:
                    # Preserve other context fields (e.g., location)
                    new_context[ctx_key] = replace_context_macros(ctx_value) if isinstance(ctx_value, (dict, list)) else ctx_value
            
            result[key] = new_context
        elif isinstance(value, (dict, list)):
            # Recursively process nested structures in message
            result[key] = replace_context_macros(value)
        else:
            # Preserve other fields as-is
            result[key] = value
    
    return result


def create_postman_request(
    json_data: Dict[str, Any],
    action: str,
    endpoint: str,
    request_name: str,
    role: str,
    adapter_url_var: str
) -> Dict[str, Any]:
    """
    Create a Postman request object from JSON data.
    
    Args:
        json_data: The JSON payload
        action: Action name (e.g., "discover", "on_discover")
        endpoint: API endpoint path
        request_name: Name for the request
        role: Role (BAP, BPP, UtilityBPP)
        adapter_url_var: Variable name for adapter URL (e.g., "bap_adapter_url")
    """
    # Replace macros in the JSON
    request_body = replace_context_macros(json_data)
    
    # Format JSON with proper indentation
    body_raw = json.dumps(request_body, indent=2)
    
    return {
        "name": request_name,
        "request": {
            "method": "POST",
            "header": [],
            "body": {
                "mode": "raw",
                "raw": body_raw,
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            },
            "url": {
                "raw": f"{{{{{adapter_url_var}}}}}/{endpoint}",
                "host": [f"{{{{{adapter_url_var}}}}}"],
                "path": [endpoint]
            },
            "description": f"{action.capitalize()} request: {request_name}"
        },
        "response": []
    }


def scan_examples_directory(examples_dir: Path, structure: str, role: str) -> Dict[str, List[Tuple[Path, str]]]:
    """
    Scan examples directory and group JSON files by action.
    
    Args:
        examples_dir: Path to examples directory
        structure: "folders" or "flat"
        role: "BAP", "BPP", or "UtilityBPP"
    
    Returns: {action: [(filepath, request_name)]}
    """
    actions_map = {}
    
    if not examples_dir.exists():
        print(f"Error: Examples directory not found: {examples_dir}")
        return actions_map
    
    if structure == "folders":
        # Folder-based structure (ev-charging)
        for item in examples_dir.iterdir():
            if not item.is_dir():
                continue
            
            action = extract_action_from_folder(item.name, role)
            if action is None:
                continue
            
            # Find all JSON files in this folder
            json_files = list(item.glob("*.json"))
            for json_file in json_files:
                # For folder-based structure, we trust the folder name for role filtering
                # But we can still check filename as secondary filter
                request_name = get_request_name(json_file.name)
                if action not in actions_map:
                    actions_map[action] = []
                actions_map[action].append((json_file, request_name))
        
        for action, files in actions_map.items():
            print(f"Found {len(files)} example(s) for action '{action}'")
    
    else:
        # Flat structure (p2p-trading)
        json_files = list(examples_dir.glob("*.json"))
        for json_file in json_files:
            # Check if file matches role filter
            if not matches_role_filter(json_file.name, role):
                continue
            
            action = extract_action_from_filename(json_file.name, role)
            if action is None:
                continue
            
            request_name = get_request_name(json_file.name)
            if action not in actions_map:
                actions_map[action] = []
            actions_map[action].append((json_file, request_name))
        
        for action, files in actions_map.items():
            print(f"Found {len(files)} example(s) for action '{action}'")
    
    return actions_map


def get_collection_variables(devkit: str, role: str) -> List[Dict[str, str]]:
    """Get collection variables based on devkit and role."""
    config = DEVKIT_CONFIGS[devkit]
    
    variables = [
        {"key": "domain", "value": config["domain"]},
        {"key": "version", "value": "2.0.0"},
        {"key": "bap_id", "value": config["bap_id"]},
        {"key": "bap_uri", "value": config["bap_uri"]},
        {"key": "bpp_id", "value": config["bpp_id"]},
        {"key": "bpp_uri", "value": config["bpp_uri"]},
        {"key": "transaction_id", "value": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002"},
        {"key": "iso_date", "value": ""}
    ]
    
    # Add adapter URLs based on role
    if role == "BAP":
        variables.append({"key": "bap_adapter_url", "value": config["bap_adapter_url"]})
    elif role == "BPP":
        variables.append({"key": "bpp_adapter_url", "value": config["bpp_adapter_url"]})
    elif role == "UtilityBPP":
        variables.append({"key": "bpp_adapter_url", "value": config["bpp_adapter_url"]})
        variables.append({"key": "bap_adapter_url", "value": config["bap_adapter_url"]})
    
    return variables


def generate_collection(
    examples_dir: Path,
    output_path: Path,
    devkit: str,
    role: str,
    collection_name: Optional[str] = None,
    collection_description: Optional[str] = None
) -> None:
    """
    Generate Postman collection from examples.
    
    Args:
        examples_dir: Path to examples directory
        output_path: Output path for collection
        devkit: "ev-charging" or "p2p-trading"
        role: "BAP", "BPP", or "UtilityBPP"
        collection_name: Optional collection name (auto-generated if None)
        collection_description: Optional description (auto-generated if None)
    """
    config = DEVKIT_CONFIGS[devkit]
    structure = config["structure"]
    
    # Determine action mapping and adapter URL based on role
    if role == "BAP":
        action_mapping = BAP_ACTIONS
        adapter_url_var = "bap_adapter_url"
    elif role == "BPP":
        # BPP uses both callback actions and BPP-initiated actions (like publish to CDS)
        action_mapping = {**BPP_ACTIONS, **BPP_INITIATED_ACTIONS}
        adapter_url_var = "bpp_adapter_url"
    elif role == "UtilityBPP":
        action_mapping = BAP_ACTIONS  # UtilityBPP uses BAP actions
        adapter_url_var = "bpp_adapter_url"
    else:
        raise ValueError(f"Unknown role: {role}")
    
    # Auto-generate collection name and description if not provided
    if collection_name is None:
        collection_name = f"{devkit}:{role}-DEG"
    
    if collection_description is None:
        role_desc = {
            "BAP": "Buyer Application Platform",
            "BPP": "Buyer Provider Platform",
            "UtilityBPP": "Utility BPP (Transmission/Grid Provider Platform)"
        }
        devkit_desc = devkit
        collection_description = f"Postman collection for {role_desc[role]} implementing {devkit_desc} APIs based on Beckn Protocol v2"
    
    print(f"Scanning examples directory: {examples_dir}")
    print(f"Devkit: {devkit}, Role: {role}, Structure: {structure}")
    
    actions_map = scan_examples_directory(examples_dir, structure, role)
    
    if not actions_map:
        print("No valid examples found. Exiting.")
        return
    
    # Build collection items (folders)
    collection_items = []
    
    # Process each action in order (include all BAP actions, even if no examples)
    all_actions = sorted(set(list(actions_map.keys()) + list(action_mapping.keys())))
    
    for action in all_actions:
        if action not in action_mapping:
            continue
        
        endpoint = action_mapping[action]
        files_list = actions_map.get(action, [])
        
        # Create folder for this action
        action_items = []
        
        for json_file, request_name in sorted(files_list):
            print(f"  Processing: {json_file.name}")
            
            # Load JSON
            json_data = load_example_json(json_file)
            if json_data is None:
                continue
            
            # Create Postman request
            request = create_postman_request(
                json_data, action, endpoint, request_name, role, adapter_url_var
            )
            action_items.append(request)
        
        # Only create folder if it has requests
        if action_items:
            folder = {
                "name": action,
                "item": action_items
            }
            collection_items.append(folder)
            print(f"  Created folder '{action}' with {len(action_items)} request(s)")
    
    # Build collection
    collection = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": collection_name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": collection_description
        },
        "item": collection_items,
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": PRE_REQUEST_SCRIPT.split("\n")
                }
            }
        ],
        "variable": get_collection_variables(devkit, role)
    }
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Generated Postman collection: {output_path}")
    print(f"  Total folders: {len(collection_items)}")
    print(f"  Total requests: {sum(len(item['item']) for item in collection_items)}")
    
    return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Postman collection from example JSONs for a a predefined devkit and role"
    )
    parser.add_argument(
        "--devkit",
        type=str,
        choices=["ev-charging", "p2p-trading", "p2p-enrollment", "p2p-trading-interdiscom"],
        required=True,
        help="Devkit type: 'ev-charging', 'p2p-trading', 'p2p-enrollment', or 'p2p-trading-interdiscom'"
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=["BAP", "BPP", "UtilityBPP"],
        required=True,
        help="Role: 'BAP', 'BPP', or 'UtilityBPP'"
    )
    parser.add_argument(
        "--examples",
        type=str,
        default=None,
        help="Path to examples directory (default: uses devkit config)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        dest="output_dir",
        help="Output directory for Postman collection (required)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Collection name (default: auto-generated from devkit and role)"
    )
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Collection description (default: auto-generated)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate generated collection against schema (default: True)"
    )
    parser.add_argument(
        "--no-validate",
        dest="validate",
        action="store_false",
        help="Skip schema validation"
    )
    
    args = parser.parse_args()
    
    # Get devkit configuration
    config = DEVKIT_CONFIGS[args.devkit]
    
    # Convert to Path objects
    repo_root_dir = Path(__file__).parent.parent
    
    # Use provided paths or defaults from config
    examples_dir = repo_root_dir / (args.examples or config["examples_path"])
    
    # Generate collection name if not provided
    if args.name is None:
        collection_name = f"{args.devkit}:{args.role}-DEG"
    else:
        collection_name = args.name
    
    # Construct output filename from collection name
    filename = f"{collection_name}.postman_collection.json"
    output_path = repo_root_dir / args.output_dir / filename
    
    print("=" * 60)
    print(f"Postman Collection Generator")
    print(f"Devkit: {args.devkit}, Role: {args.role}")
    print("=" * 60)
    print()
    
    output_path = generate_collection(
        examples_dir=examples_dir,
        output_path=output_path,
        devkit=args.devkit,
        role=args.role,
        collection_name=collection_name,
        collection_description=args.description
    )
    
    # Validate collection if requested
    if args.validate:
        if get_schema_store is None or process_file is None:
            print("\n⚠ Warning: Schema validation module not available, skipping validation")
        else:
            print("\n" + "=" * 60)
            print("Validating Postman collection against schema...")
            print("=" * 60)
            try:
                schema_store, attributes_schema, attribute_schemas_map = get_schema_store()
                process_file(str(output_path), schema_store, attributes_schema, attribute_schemas_map)
                print("\n✓ Schema validation completed")
            except Exception as e:
                print(f"\n⚠ Warning: Schema validation failed: {e}")
                import traceback
                traceback.print_exc()
                print("  Collection was still generated successfully")


if __name__ == "__main__":
    main()

