# Setup Guide — Portable Subway Telltale

This guide explains how to reproduce and run the **Portable Subway Telltale** on an ESP32-S2 Feather using CircuitPython.



## 1. Hardware Requirements

- Adafruit **ESP32-S2 Feather with TFT display**
- USB-C cable
- LiPo battery (optional, for portable use)



## 2. Software Requirements

- **CircuitPython** (ESP32-S2 compatible version)
- **Mu Editor** or any editor that can edit files on the CIRCUITPY drive



## 3. Flash CircuitPython

1. Download the CircuitPython firmware for **ESP32-S2 Feather** from:
   https://circuitpython.org/board/adafruit_feather_esp32s2/

2. Put the board into bootloader mode and flash the firmware.

3. After flashing, a drive named **CIRCUITPY** should appear on your computer.



## 4. Copy Project Files to CIRCUITPY

Copy the following files and folders to the **root of the CIRCUITPY drive**:

```
CIRCUITPY/
├── code.py
├── animation/
├── icons/
└── lib/
```

> ⚠️ The `lib/` folder is required.  
> Missing libraries will cause import errors at runtime.



## 5. Required Libraries

The following CircuitPython libraries must exist inside the `lib/` folder:

- `adafruit_requests.mpy`
- `adafruit_connection_manager.mpy`
- `adafruit_display_text/`
- `adafruit_display_shapes/`
- `adafruit_imageload/`

These libraries are included in this repository under the `lib/` directory and can be copied directly.



## 6. Configure Wi-Fi Credentials

Open `code.py` and update the Wi-Fi credentials at the top of the file:

```python
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
```