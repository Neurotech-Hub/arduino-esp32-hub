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
import fnmatch
import subprocess

ESP32_CORE_VERSION = "3.0.7"
ESP32_CORE_URL = f"https://github.com/espressif/arduino-esp32/releases/download/{ESP32_CORE_VERSION}/esp32-{ESP32_CORE_VERSION}.zip"
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
    
    # Always remove existing directory to ensure fresh copy
    if os.path.exists(original_dir):
        print("Removing existing working directory...")
        shutil.rmtree(original_dir)
    
    print("Setting up working directory with original core files...")
    temp_dir, zip_path = download_core()
    try:
        # Create original directory
        os.makedirs(original_dir, exist_ok=True)
        
        # Extract directly to original directory (not in a subdirectory)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                # Remove the arduino-esp32-VERSION prefix from paths
                if member.startswith(f'esp32-{ESP32_CORE_VERSION}/'):
                    new_name = member[len(f'esp32-{ESP32_CORE_VERSION}/'):]
                    if new_name:  # Skip the directory itself
                        target_path = os.path.join(original_dir, new_name)
                        
                        # Skip if it's a directory
                        if new_name.endswith('/'):
                            continue
                        
                        # Create parent directories if they don't exist
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # Extract the file
                        source = zip_ref.open(member)
                        target = open(target_path, 'wb')
                        with source, target:
                            shutil.copyfileobj(source, target)
    finally:
        shutil.rmtree(temp_dir)

def create_patches():
    """Create patch files from modified sources."""
    print("Creating patches from modified files...")
    original_dir = os.path.join(WORKING_DIR, "original")
    modified_dir = os.path.join(WORKING_DIR, "modified")
    
    # Clean up existing patches
    if os.path.exists(PATCH_DIR):
        print("Cleaning up existing patches...")
        for f in os.listdir(PATCH_DIR):
            if f.endswith('.patch'):
                os.remove(os.path.join(PATCH_DIR, f))
    
    if not os.path.exists(modified_dir):
        print("No modified files found in working/modified/")
        return
    
    # Create patches directory if it doesn't exist
    os.makedirs(PATCH_DIR, exist_ok=True)
    
    # Walk through modified directory recursively
    for root, _, files in os.walk(modified_dir):
        for file in files:
            if file.endswith(('.cpp', '.h')):
                rel_path = os.path.relpath(root, modified_dir)
                
                modified_file = os.path.join(root, file)
                original_file = os.path.join(original_dir, rel_path, file)
                
                if os.path.exists(original_file):
                    patch_name = f"001-{rel_path.replace('/', '-')}-{file}.patch"
                    patch_path = os.path.join(PATCH_DIR, patch_name)
                    
                    print(f"Processing: {rel_path}/{file}")
                    
                    # Create diff with correct paths
                    temp_patch = patch_path + ".tmp"
                    os.system(f"cd {WORKING_DIR} && diff -u original/{rel_path}/{file} modified/{rel_path}/{file} > {temp_patch}")
                    
                    # Add header and copy content
                    with open(temp_patch, 'r') as src, open(patch_path, 'w') as dst:
                        dst.write(f"# ESP32 Hub Patch for {rel_path}/{file}\n")
                        dst.write(f"# Generated: {datetime.datetime.now()}\n")
                        dst.write(f"# Purpose: Fix BLE memory leaks.\n")
                        dst.write("#\n")
                        content = src.read()
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
    
    # Adjust work_dir to point to the esp32-3.0.7 subdirectory
    work_dir = os.path.join(work_dir, f"esp32-{ESP32_CORE_VERSION}")
    print(f"Adjusted work directory: {work_dir}")
    
    if not os.path.exists(PATCH_DIR):
        print(f"[ERROR] Patch directory not found: {PATCH_DIR}")
        return
    
    patch_files = [f for f in os.listdir(PATCH_DIR) if f.endswith('.patch')]
    print(f"Found {len(patch_files)} patch files to apply")
    
    successful_patches = []
    failed_patches = []
    
    for patch in sorted(patch_files):
        patch_path = os.path.join(PATCH_DIR, patch)
        print(f"\nTrying: {patch}")
        
        # Print patch content for debugging
        print("\nPatch content preview:")
        with open(patch_path, 'r') as f:
            print(''.join(f.readlines()[:10]))
        
        # Check if target file exists
        target_file = os.path.join(work_dir, "libraries/BLE/src/BLE2902.cpp")
        print(f"\nChecking target file: {target_file}")
        print(f"File exists: {os.path.exists(target_file)}")
        
        # Use -p1 to strip one directory level from patch paths
        cmd = f"patch -p1 -d {work_dir} < {patch_path} 2>&1"
        print(f"\nRunning command: {cmd}")
        result = os.popen(cmd).read()
        print(f"Patch result:\n{result}")
        
        if "FAILED" in result or "ERROR" in result:
            print(" [FAILED]")
            print("-" * 40)
            print("Error details:")
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
    
    # Files and directories to exclude
    exclude_patterns = [
        '.*',           # All hidden files/dirs
        'tests',        
        '__pycache__',  
        '*.pyc',        
        '.gitignore',
        '.gitmodules',
        '.pre-commit-config.yaml',
        '.prettierignore',
        '.readthedocs.yaml',
        '.vale.ini',
        '.flake8',
        '.editorconfig',
        '.codespellrc',
        '.clang-format'
    ]
    
    # Create a temporary directory for package structure
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, "esp32-hub")
    
    try:
        # Create the package directory
        os.makedirs(package_dir, exist_ok=True)
        
        # Get path to core files
        core_dir = os.path.join(work_dir, f"esp32-{ESP32_CORE_VERSION}")
        
        # First, copy everything from the core
        for item in os.listdir(core_dir):
            src = os.path.join(core_dir, item)
            dst = os.path.join(package_dir, item)
            
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*exclude_patterns))
            else:
                shutil.copy2(src, dst)
        
        # Then, overwrite with our custom files
        if os.path.exists('boards.txt'):
            shutil.copy2('boards.txt', os.path.join(package_dir, 'boards.txt'))
        
        if os.path.exists('variants'):
            # Remove core variants directory
            shutil.rmtree(os.path.join(package_dir, 'variants'))
            # Copy our variants directory
            shutil.copytree('variants', os.path.join(package_dir, 'variants'))
        
        # Create the ZIP
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
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            setup_working_directory()
            return
        elif sys.argv[1] == "create-patches":
            create_patches()
            return
        elif sys.argv[1] == "verify-patches":
            verify_patches()
            return
        elif sys.argv[1] == "release":
            print("=== Starting Release Process ===")
            print("\n1. Updating tools dependencies...")
            result = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "update_tools.py")], 
                                 check=True)
            if result.returncode != 0:
                print("Error updating tools dependencies")
                sys.exit(1)
            
            print("\n2. Creating package...")
            temp_dir, zip_path = download_core()
            try:
                # Extract directly to temp_dir
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Use temp_dir as work_dir since files are extracted there
                work_dir = temp_dir
                
                # Debug: Print directory structure before applying patches
                print("\nDirectory structure before patches:")
                os.system(f"ls -R {work_dir}")
                
                apply_patches(work_dir)
                package_file = create_package(work_dir)
                update_package_index(package_file)
                
                # Debug: Keep the temp directory for inspection
                print(f"\nTemp directory preserved for inspection: {temp_dir}")
                return
                
            except Exception as e:
                print(f"Error: {e}")
                print(f"\nTemp directory preserved for inspection: {temp_dir}")
                return
                
            finally:
                shutil.rmtree(temp_dir)  # Uncomment cleanup
            return

if __name__ == "__main__":
    main() 