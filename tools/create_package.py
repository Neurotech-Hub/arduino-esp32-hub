#!/usr/bin/env python3

import os
import sys
import shutil
import tempfile
import urllib.request
import zipfile
import hashlib
import json
import datetime

ESP32_CORE_VERSION = "3.0.7"
ESP32_CORE_URL = f"https://github.com/espressif/arduino-esp32/archive/refs/tags/{ESP32_CORE_VERSION}.zip"
PATCH_DIR = f"../patches/{ESP32_CORE_VERSION}"
PACKAGE_NAME = f"esp32-hub-{ESP32_CORE_VERSION}.zip"
PACKAGE_INDEX = "../package_esp32hub_index.json"
WORKING_DIR = "../working"

def download_core():
    """Download the ESP32 Arduino core."""
    print(f"Downloading ESP32 core version {ESP32_CORE_VERSION}...")
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "esp32-core.zip")
    
    urllib.request.urlretrieve(ESP32_CORE_URL, zip_path)
    return temp_dir, zip_path

def setup_working_directory():
    """Download and setup original core files in working directory."""
    original_dir = os.path.join(WORKING_DIR, "original")
    if not os.path.exists(original_dir):
        print("Setting up working directory with original core files...")
        temp_dir, zip_path = download_core()
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(original_dir)
        finally:
            shutil.rmtree(temp_dir)
    else:
        print("Working directory already exists.")

def create_patches():
    """Create patch files from modified sources."""
    print("Creating patches from modified files...")
    original_dir = os.path.join(WORKING_DIR, "original", f"arduino-esp32-{ESP32_CORE_VERSION}")
    modified_dir = os.path.join(WORKING_DIR, "modified")
    
    if not os.path.exists(modified_dir):
        print("No modified files found in working/modified/")
        return
    
    # Create patches directory if it doesn't exist
    os.makedirs(PATCH_DIR, exist_ok=True)
    
    # Walk through modified directory recursively
    for root, _, files in os.walk(modified_dir):
        for file in files:
            if file.endswith(('.cpp', '.h')):
                # Get relative path from modified dir
                rel_path = os.path.relpath(root, modified_dir)
                
                # Construct paths
                modified_file = os.path.join(root, file)
                original_file = os.path.join(original_dir, rel_path, file)
                
                if os.path.exists(original_file):
                    # Create patch name preserving directory structure
                    patch_name = f"001-{rel_path.replace('/', '-')}-{file}.patch"
                    patch_path = os.path.join(PATCH_DIR, patch_name)
                    
                    print(f"Processing: {rel_path}/{file}")
                    
                    # Create diff using relative paths
                    temp_patch = patch_path + ".tmp"
                    os.system(f"cd {WORKING_DIR} && diff -u original/arduino-esp32-{ESP32_CORE_VERSION}/{rel_path}/{file} modified/{rel_path}/{file} > {temp_patch}")
                    
                    # Add header and copy content
                    with open(temp_patch, 'r') as src, open(patch_path, 'w') as dst:
                        dst.write(f"# ESP32 Hub Patch for {rel_path}/{file}\n")
                        dst.write(f"# Generated: {datetime.datetime.now()}\n")
                        dst.write(f"# Purpose: Fix BLE memory leaks.\n")
                        dst.write("#\n")
                        # Replace paths in diff output to be relative
                        content = src.read()
                        content = content.replace(f"{original_dir}/", "")
                        content = content.replace(f"{modified_dir}/", "")
                        dst.write(content)
                    
                    # Remove temp file
                    os.remove(temp_patch)
                    print(f"[SUCCESS] Created patch: {patch_path}")
                else:
                    print(f"[WARNING] Original file not found: {original_file}")

def apply_patches(work_dir):
    """Apply patches to the core."""
    print("\n=== Patch Application ===")
    print(f"Working directory: {os.path.basename(work_dir)}")
    
    if not os.path.exists(PATCH_DIR):
        print(f"[ERROR] Patch directory not found: {PATCH_DIR}")
        return
    
    patch_files = [f for f in os.listdir(PATCH_DIR) if f.endswith('.patch')]
    print(f"Found {len(patch_files)} patch files to apply")
    
    successful_patches = []
    failed_patches = []
    
    for patch in sorted(patch_files):
        patch_path = os.path.join(PATCH_DIR, patch)
        print(f"\nTrying: {patch}", end="")
        
        # Capture patch command output
        cmd = f"patch -p1 -d {work_dir} < {patch_path} 2>&1"
        result = os.popen(cmd).read()
        
        if "FAILED" in result or "ERROR" in result:
            print(" [FAILED]")
            print("-" * 40)
            print("Error details:")
            # Only print relevant error lines
            for line in result.split('\n'):
                if any(x in line for x in ['FAILED', 'ERROR', 'offset', 'reject']):
                    print(f"  {line.strip()}")
            print("-" * 40)
            failed_patches.append(patch)
        else:
            print(" [OK]")
            successful_patches.append(patch)
    
    # Summary report
    print("\n=== Patch Summary ===")
    print(f"Succeeded: {len(successful_patches)}")
    print(f"Failed: {len(failed_patches)}")
    
    if failed_patches:
        print("\nFailed patches:")
        for patch in failed_patches:
            print(f"  - {patch}")
    
    return len(successful_patches) > 0

def create_package(work_dir):
    """Create the final package ZIP file."""
    print("Creating package...")
    output_file = PACKAGE_NAME
    
    # Create a temporary directory for package structure
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, "esp32-hub")
    
    try:
        # Create the package directory first
        os.makedirs(package_dir, exist_ok=True)
        
        # Copy all files except boards.txt and variants
        for item in os.listdir(work_dir):
            src = os.path.join(work_dir, item)
            dst = os.path.join(package_dir, item)
            
            if item not in ['boards.txt', 'variants']:
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # Copy our custom boards.txt
        shutil.copy2('boards.txt', os.path.join(package_dir, 'boards.txt'))
        
        # Copy our variants directory
        shutil.copytree('variants', os.path.join(package_dir, 'variants'))
        
        # Create the ZIP with correct structure
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
    
    finally:
        shutil.rmtree(temp_dir)
    
    print(f"\nPackage created: {output_file}")
    print("Verifying ZIP structure...")
    
    # Verify ZIP structure
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        files = zip_ref.namelist()
        root_dirs = set(f.split('/')[0] for f in files)
        if len(root_dirs) != 1 or 'esp32-hub' not in root_dirs:
            print("ERROR: ZIP does not have single 'esp32-hub' root directory!")
            return None
        
        required_files = ['esp32-hub/boards.txt', 'esp32-hub/platform.txt']
        required_dirs = ['esp32-hub/cores', 'esp32-hub/variants', 'esp32-hub/tools']
        
        for f in required_files:
            if f not in files:
                print(f"ERROR: Missing required file: {f}")
                return None
        
        for d in required_dirs:
            if not any(f.startswith(d + '/') for f in files):
                print(f"ERROR: Missing required directory: {d}")
                return None
        
        print("ZIP structure verified successfully!")
    
    return output_file

def update_package_index(package_file):
    """Update the package index with the new ZIP information."""
    size = os.path.getsize(package_file)
    
    with open(package_file, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    # Update package index JSON
    with open(PACKAGE_INDEX, 'r') as f:
        package_data = json.load(f)
    
    # Update the platform info
    platform = package_data['packages'][0]['platforms'][0]
    platform['size'] = str(size)
    platform['checksum'] = f"SHA-256:{checksum}"
    
    # Write updated package index
    with open(PACKAGE_INDEX, 'w') as f:
        json.dump(package_data, f, indent=2)
    
    print(f"Package size: {size}")
    print(f"SHA-256: {checksum}")

def verify_patches():
    """Verify all patches have proper headers."""
    if not os.path.exists(PATCH_DIR):
        print("No patches directory found.")
        return
    
    patch_files = os.listdir(PATCH_DIR)
    for patch in sorted(patch_files):
        if patch.endswith('.patch'):
            patch_path = os.path.join(PATCH_DIR, patch)
            with open(patch_path, 'r') as f:
                first_line = f.readline().strip()
                if not first_line.startswith('# ESP32 Hub Patch'):
                    print(f"Warning: {patch} is missing header comment")
                else:
                    print(f"Verified: {patch}")

def main():
    # Get script's directory and move up one level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    # Update paths to be relative to repo root
    global PATCH_DIR, PACKAGE_INDEX, WORKING_DIR
    PATCH_DIR = os.path.join(repo_root, "patches", ESP32_CORE_VERSION)
    PACKAGE_INDEX = os.path.join(repo_root, "package_esp32hub_index.json")
    WORKING_DIR = os.path.join(repo_root, "working")
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_working_directory()
        return
    elif len(sys.argv) > 1 and sys.argv[1] == "create-patches":
        create_patches()
        return
    elif len(sys.argv) > 1 and sys.argv[1] == "verify-patches":
        verify_patches()
        return
    
    temp_dir, zip_path = download_core()
    try:
        work_dir = os.path.join(temp_dir, f"arduino-esp32-{ESP32_CORE_VERSION}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        apply_patches(work_dir)
        package_file = create_package(work_dir)
        update_package_index(package_file)
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main() 