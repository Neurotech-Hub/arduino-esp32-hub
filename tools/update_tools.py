#!/usr/bin/env python3

import os
import sys
import json
import requests
from urllib.parse import urlparse

ESP32_PACKAGE_URL = "https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json"
PACKAGE_INDEX = "../package_esp32hub_index.json"
CORE_VERSION = "3.0.7"

def fetch_esp32_package_index():
    """Download and parse the official ESP32 package index."""
    print(f"Fetching ESP32 package index from {ESP32_PACKAGE_URL}...")
    try:
        response = requests.get(ESP32_PACKAGE_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ESP32 package index: {e}")
        sys.exit(1)

def find_tools_for_version(package_data, version=CORE_VERSION):
    """Extract complete tool definitions for specific version."""
    print(f"\nFinding tools for version {version}...")
    tools_found = set()
    tools_definitions = []
    
    # Find the platform with matching version
    platform = next(
        (p for p in package_data['packages'][0]['platforms'] 
         if p['version'] == version),
        None
    )
    
    if not platform:
        print(f"Error: Could not find platform version {version}")
        sys.exit(1)
    
    # Get all tool dependencies
    tools_dependencies = []
    for tool_dep in platform['toolsDependencies']:
        if tool_dep['name'] not in tools_found:
            tools_found.add(tool_dep['name'])
            
            # Create modified dependency, preserving original packager if it's "arduino"
            modified_dep = tool_dep.copy()
            if tool_dep['packager'] != 'arduino':
                modified_dep['packager'] = 'esp32-hub'
            tools_dependencies.append(modified_dep)
            
            print(f"Found tool dependency: {tool_dep['name']} v{tool_dep['version']}")
            
            # Only include tool definition if it's not from Arduino
            if tool_dep['packager'] != 'arduino':
                tool_def = next(
                    (tool for tool in package_data['packages'][0].get('tools', [])
                     if tool['name'] == tool_dep['name'] and 
                        tool['version'] == tool_dep['version']),
                    None
                )
                
                if tool_def:
                    tools_definitions.append(tool_def)
                    print(f"  - Found complete definition with {len(tool_def.get('systems', []))} system variants")
                else:
                    print(f"  ! Warning: Could not find complete tool definition")
            
    return tools_dependencies, tools_definitions

def update_package_index(tools_dependencies, tools_definitions):
    """Update tools in the package index."""
    print("\nUpdating package index...")
    
    if os.path.exists(PACKAGE_INDEX):
        with open(PACKAGE_INDEX, 'r') as f:
            package_data = json.load(f)
            
        # Update toolsDependencies
        if 'platforms' in package_data['packages'][0] and package_data['packages'][0]['platforms']:
            package_data['packages'][0]['platforms'][0]['toolsDependencies'] = tools_dependencies
            
        # Update or add tools definitions
        if tools_definitions:
            package_data['packages'][0]['tools'] = tools_definitions
            
        with open(PACKAGE_INDEX, 'w') as f:
            json.dump(package_data, f, indent=4)
        
        print(f"Updated {PACKAGE_INDEX} with:")
        print(f"- {len(tools_dependencies)} tool dependencies")
        print(f"- {len(tools_definitions)} complete tool definitions")
    else:
        print(f"Error: Package index {PACKAGE_INDEX} not found")
        sys.exit(1)

def main():
    # Get script's directory and move up one level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    # Update paths to be relative to repo root
    global PACKAGE_INDEX
    PACKAGE_INDEX = os.path.join(repo_root, "package_esp32hub_index.json")
    
    # Fetch and process
    esp32_package = fetch_esp32_package_index()
    tools_dependencies, tools_definitions = find_tools_for_version(esp32_package)
    update_package_index(tools_dependencies, tools_definitions)
    print("\nSuccess! Package index updated with tool dependencies.")

if __name__ == "__main__":
    main()