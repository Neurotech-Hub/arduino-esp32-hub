# Arduino ESP32 Hub

Custom variants and patches for the ESP32 Arduino core, maintained by Neurotech Hub.

## Installation

1. Add the following URL to Arduino IDE's Additional Board Manager URLs:   ```
   https://raw.githubusercontent.com/Neurotech-Hub/arduino-esp32-hub/main/package_esp32hub_index.json   ```

2. Open the Boards Manager in Arduino IDE
3. Search for "ESP32 Hub"
4. Install the package

## Development

The patches are organized by ESP32 core versions in the `patches` directory. To build the package:

1. Install Python requirements
2. Run the package creation script:   ```bash
   python tools/create_package.py   ```

## License

This project contains modifications to the ESP32 Arduino core, which is licensed under LGPL-2.1. 