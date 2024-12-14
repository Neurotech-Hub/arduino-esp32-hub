#!/usr/bin/env python3

import os
import sys
import shutil
import tempfile
import urllib.request
import zipfile
import hashlib
import json

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
    original_dir = os.path.join(WORKING_DIR, "original")
    modified_dir = os.path.join(WORKING_DIR, "modified")
    
    if not os.path.exists(modified_dir):
        print("No modified files found in working/modified/")
        return
    
    # Create patches directory if it doesn't exist
    os.makedirs(PATCH_DIR, exist_ok=True)
    
    # Walk through modified directory
    for root, _, files in os.walk(modified_dir):
        for file in files:
            if file.endswith(('.cpp', '.h')):
                # Get relative path from working dir
                rel_path = os.path.relpath(root, modified_dir)
                original_file = os.path.join(original_dir, rel_path, file)
                modified_file = os.path.join(root, file)
                
                if os.path.exists(original_file):
                    patch_name = f"001-{rel_path.replace('/', '-')}-{file}.patch"
                    patch_path = os.path.join(PATCH_DIR, patch_name)
                    
                    # Create patch using diff
                    os.system(f"diff -u {original_file} {modified_file} > {patch_path}")
                    print(f"Created patch: {patch_path}")

def apply_patches(work_dir):
    """Apply patches to the core."""
    print("Applying patches...")
    if not os.path.exists(PATCH_DIR):
        print("No patches directory found.")
        return
        
    patch_files = os.listdir(PATCH_DIR)
    for patch in sorted(patch_files):  # Sort to ensure consistent order
        if patch.endswith('.patch'):
            patch_path = os.path.join(PATCH_DIR, patch)
            result = os.system(f"patch -p1 -d {work_dir} < {patch_path}")
            if result != 0:
                print(f"Warning: Patch {patch} may have failed")

def create_package(work_dir):
    """Create the final package ZIP file."""
    print("Creating package...")
    output_file = PACKAGE_NAME
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(work_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, work_dir)
                zipf.write(file_path, arcname)
    
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

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_working_directory()
        return
    elif len(sys.argv) > 1 and sys.argv[1] == "create-patches":
        create_patches()
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