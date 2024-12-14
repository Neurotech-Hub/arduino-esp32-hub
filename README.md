# Arduino ESP32 Hub

Custom variants and patches for the ESP32 Arduino core, maintained by Neurotech Hub.

## Installation

1. Add the following URL to Arduino IDE's Additional Board Manager URLs:   ```
   https://raw.githubusercontent.com/Neurotech-Hub/arduino-esp32-hub/main/package_esp32hub_index.json   ```

2. Open the Boards Manager in Arduino IDE
3. Search for "ESP32 Hub"
4. Install the package

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

4. Build the package:
   ```bash
   python3 tools/create_package.py
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

5. Verify:
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
    └── create_package.py
```

## License
This project contains modifications to the ESP32 Arduino core, which is licensed under LGPL-2.1. 
