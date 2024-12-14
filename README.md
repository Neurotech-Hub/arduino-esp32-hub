# Arduino ESP32 Hub

Custom variants and patches for the ESP32 Arduino core, maintained by Neurotech Hub.

## Installation

1. Add the following URL to Arduino IDE's Additional Board Manager URLs:   ```
   https://raw.githubusercontent.com/Neurotech-Hub/arduino-esp32-hub/main/package_esp32hub_index.json   ```

2. Open the Boards Manager in Arduino IDE
3. Search for "ESP32 Hub"
4. Install the package

### Development
1. Ensure cached versions of packages and package_*.json are deleted (e.g., `/Users/mattgaidica/Library/Arduino15`).
2. Restart Arduino IDE.
3. Install the ESP32 Hub package from Boards Manager.

## Development

### Complete Workflow

1. Initial setup (only needed once):
   ```bash
   python3 tools/create_package.py setup
   ```
   This downloads the original ESP32 core files to `working/original/`

2. Make modifications:
   - Copy files you want to modify from `working/original/arduino-esp32-3.0.7/` to `working/modified/`
   - Maintain the same directory structure
   - Make your modifications in the `working/modified/` files

3. Create patches:
   ```bash
   # Optional: clean existing patches
   rm -rf patches/3.0.7/*.patch
   
   # Create new patches
   python3 tools/create_package.py create-patches
   ```
   This creates .patch files in `patches/3.0.7/` by comparing original and modified files

4. Update tools dependencies:
   ```bash
   # Install required Python package
   pip install requests

   # Update tool dependencies from ESP32 core
   python3 tools/update_tools.py
   ```
   This fetches and updates the toolsDependencies in package_esp32hub_index.json

5. Build and release:
   ```bash
   # Option 1: Build package only
   python3 tools/create_package.py

   # Option 2: Update tools and build package
   python3 tools/create_package.py release
   ```
   This will:
   - Download a fresh copy of the ESP32 core
   - Apply your patches
   - Create the package ZIP
   - Update package_esp32hub_index.json with new size and checksum

   Then create a GitHub Release:
   - Go to GitHub > Releases > "Create a new release"
   - Tag version: v3.0.7
   - Release title: ESP32 Hub v3.0.7
   - Upload the generated esp32-hub-3.0.7.zip file
   - Publish release

6. Verify:
   - Check that all patches applied successfully
   - Test the package in Arduino IDE
   - Commit and push changes to GitHub

### File Structure
```
arduino-esp32-hub/
├── working/
│   ├── original/          # Original ESP32 core files
│   └── modified/         # Your modified files
├── patches/
│   └── 3.0.7/           # Generated patch files
├── package_esp32hub_index.json
└── tools/
    ├── create_package.py # Package creation tool
    └── update_tools.py   # Tools dependency updater
```

## License
This project contains modifications to the ESP32 Arduino core, which is licensed under LGPL-2.1. 
