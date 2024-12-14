#!/usr/bin/env python3

import os
import re
import shutil
import argparse
import json

DEFAULT_ESP32_VARIANTS = os.path.expanduser("~/Library/Arduino15/packages/esp32/hardware/esp32/3.0.7/variants")

def get_board_names_and_titles(boards_file):
    """Extract board identifiers and their display names from boards.txt."""
    boards = {}
    
    with open(boards_file, 'r') as f:
        for line in f:
            # Look for lines like "esp32c2.name=ESP32C2 Dev Module"
            match = re.match(r'^([^.]+)\.name=(.+)$', line.strip())
            if match:
                board_id = match.group(1)
                board_name = match.group(2)
                # Skip esp32_family as it's a generic placeholder
                if board_id != 'esp32_family':
                    boards[board_id] = board_name
    
    return boards

def get_variant_folders(variants_dir):
    """Get list of variant folders."""
    if not os.path.exists(variants_dir):
        return set()
    
    return {name for name in os.listdir(variants_dir) 
            if os.path.isdir(os.path.join(variants_dir, name))}

def sync_variants(source_variants, dest_variants, missing_variants):
    """Copy missing variant folders from ESP32 core."""
    synced = []
    not_found = []
    
    if not os.path.exists(source_variants):
        print(f"\nWarning: ESP32 variants directory not found at: {source_variants}")
        return synced, not_found
    
    print("\nSyncing variants from ESP32 core...")
    for variant in missing_variants:
        source_path = os.path.join(source_variants, variant)
        dest_path = os.path.join(dest_variants, variant)
        
        if os.path.exists(source_path):
            try:
                shutil.copytree(source_path, dest_path)
                synced.append(variant)
                print(f"  + Copied {variant}")
            except Exception as e:
                print(f"  ! Error copying {variant}: {e}")
        else:
            not_found.append(variant)
    
    return synced, not_found

def generate_boards_json(boards, variant_folders):
    """Generate boards section for package index JSON."""
    board_entries = []
    
    for board_id, board_name in sorted(boards.items()):
        if board_id in variant_folders:
            board_entries.append({
                "name": board_name
            })
    
    return board_entries

def update_package_index(boards_json):
    """Update the package index file with new boards section."""
    try:
        with open("package_esp32hub_index.json", 'r') as f:
            package_data = json.load(f)
            
        # Update boards section
        package_data["packages"][0]["platforms"][0]["boards"] = boards_json
        
        with open("package_esp32hub_index.json", 'w') as f:
            json.dump(package_data, f, indent=4)
            
        print("\nUpdated package_esp32hub_index.json")
    except Exception as e:
        print(f"\nError updating package index: {e}")
        print("\nGenerated boards JSON for manual update:")
        print(json.dumps(boards_json, indent=4))

def main():
    parser = argparse.ArgumentParser(description='Check and sync Arduino ESP32 variants')
    parser.add_argument('--variants', default=DEFAULT_ESP32_VARIANTS,
                      help='Path to ESP32 core variants directory')
    parser.add_argument('--generate-json', action='store_true',
                      help='Generate full package index JSON')
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    boards_file = os.path.join(repo_root, 'boards.txt')
    variants_dir = os.path.join(repo_root, 'variants')
    
    # Create variants directory if it doesn't exist
    os.makedirs(variants_dir, exist_ok=True)
    
    # Get board IDs and variant folders
    boards = get_board_names_and_titles(boards_file)
    variant_folders = get_variant_folders(variants_dir)
    
    # Find mismatches
    missing_variants = set(boards.keys()) - variant_folders
    extra_variants = variant_folders - set(boards.keys())
    
    # Try to sync missing variants from ESP32 core
    synced, not_found = sync_variants(args.variants, variants_dir, missing_variants)
    
    # Update missing variants list after sync
    if synced:
        missing_variants = missing_variants - set(synced)
        variant_folders = variant_folders.union(set(synced))
    
    # Always show supported boards
    print("\nSupported Boards:")
    print("================")
    for board_id, board_name in sorted(boards.items()):
        if board_id in variant_folders:
            print(f"  + {board_name} ({board_id})")
    
    # Generate boards JSON
    boards_json = generate_boards_json(boards, variant_folders)
    
    # Try to update package index or print JSON
    update_package_index(boards_json)
    
    # Report findings
    print("\nBoards vs Variants Analysis")
    print("==========================")
    print(f"\nFound {len(boards)} boards and {len(variant_folders)} variant folders")
    
    if synced:
        print(f"\nSynced {len(synced)} variants from ESP32 core:")
        for variant in sorted(synced):
            print(f"  + {variant}")
    
    if missing_variants:
        print("\nBoards still missing variant folders:")
        for board in sorted(missing_variants):
            status = "(not found in ESP32 core)" if board in not_found else ""
            print(f"  - {board} {status}")
    
    if extra_variants:
        print("\nVariant folders without corresponding boards:")
        for variant in sorted(extra_variants):
            print(f"  - {variant}")
            
    if not missing_variants and not extra_variants:
        print("\nAll boards have matching variant folders!")

if __name__ == "__main__":
    main() 