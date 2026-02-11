# 🚇 Portable Subway Telltale — Roosevelt Island (NYC)

A **keychain-sized ambient subway telltale** that provides calm, glanceable information about upcoming subway arrivals at **Roosevelt Island (NYC)**.  Designed as a small, always-with-you object, the device helps users decide *when to leave*, without opening a phone app.



Built with **ESP32-S2 Feather + CircuitPython**  
Course project: *Interactive Devices / Ubiquitous Computing*

<p align="left">
  <img src="assets/outcome.jpg" height="500" style="margin-right:20px;">
</p>



## ✨ Concept

Living on **Roosevelt Island**, I often face a recurring question before leaving home:

**Do I need to rush to the subway now, or do I still have time?**

Instead of opening a transit app, this telltale provides ambient, peripheral feedback. It is designed as a **portable keychain-sized device** in pocket.

The interface prioritizes:
- Glanceability (1-second understanding)
- Redundant cues (color, motion, position)
- Low cognitive load (states instead of raw numbers)



<p align="left">
  <img src="assets/user.jpg" height="500">
</p>


## 📍 Location & Context

- **Station:** Roosevelt Island (B06)
- **Subway Lines:** F / M (automatically detected depending on service)
- **Intended placement:**
  - Near the door at home
  - Eventually as a **portable keychain telltale**

The device is battery-powered and meant to be checked casually while preparing to leave.



## 📊 Information Displayed

The telltale always shows **both directions**:

- **To Manhattan**
- **To Queens**

Each direction displays:
- Estimated minutes until the next train arrives

Two on-board buttons allow interaction:
- **D1** → select *To Manhattan*
- **D2** → select *To Queens*

The **selected direction** determines the main visual state of the device, while the other direction is de-emphasized.

<p align="left">
  <img src="assets/arrive.jpg" width="45%" />
  <img src="assets/gonow_2.jpg" width="45%" />
</p>



## 🔄 Data Source & Pipeline

### Data Source
Real-time arrival predictions from: https://subwayinfo.nyc/api/arrivals?station_id=B06


### On-device Processing
1. Fetch arrival predictions every ~15 seconds
2. Detect which line is active (F preferred, M as fallback)
3. Select the soonest arrival per direction
4. Convert minutes into action-oriented states



## 🧠 State Machine

Arrival times are mapped into three intuitive states:

| State    | Minutes Away | Meaning              | Color        |Animation        |Edge UI          |
|----------|--------------|----------------------|--------------|-----------------|-----------------|
| WAIT     | > 7 min      | You have time        | Grey         |Coffee (idle)    |Slow|
| GO NOW   | 3–7 min      | Leave immediately    | Blue         |Walking          |Medium-speed
| ARRIVE   | 0–2 min      | Train is arriving    | Orange       |Metro (urgent)   |Fast+blink





## 🎨 Visual Language

The interface uses multiple reinforcing cues:

### Color System (inspired by MTA)
- **WAIT:** Grey  
- **GO NOW:** Blue (`#3236A6`)  
- **ARRIVE:** Orange (`#FF6319`)

### Status Text
Large, bold text under the animation:
- `WAIT~`
- `GO NOW!`
- `ARRIVE!`

### Pixel Animations
| State   | Animation |
|--------|-----------|
| WAIT   | Coffee cup steaming |
| GO     | Walking figure |
| ARRIVE | Moving subway train |

### Direction Indicators
- Selected direction: filled colored dot + bright text
- Unselected direction: outlined dot + dimmed text

### Edge Flow Border
A clockwise flow of pixel blocks around the screen:
- Color reflects the current state
- Speed increases as urgency increases
- Communicates the passage of time without numbers



## 🧰 Hardware & Software

### Hardware
- Adafruit ESP32-S2 Feather with TFT display
- On-board buttons (D1 / D2)
- LiPo battery

### Software
- CircuitPython
- displayio
- adafruit_requests
- adafruit_imageload
- Custom sprite animations

## [🖨 Physical Design & Fabrication](Portable-Subway-Telltale/3D_print_model/)


### Enclosure Design
- Modeled in **Autodesk Fusion 360**
- Iterative process:
  1. Measure ESP32 board + battery
  2. Block out internal volume
  3. Adjust battery and board orientation
  4. Design keyring loop
  5. Apply fillets and chamfers
  6. Decide which text to emboss

### Key Design Decisions
- Final size: **5.6 × 4.2 × 1.6 cm**
- Multiple iterations to account for:
  - print tolerances
  - post-processing (sanding)
- Early versions experimented with small embossed text (names, M/Q labels)
  - Rejected due to limited print legibility
- **Telltale 2.0** uses:
  - larger, simpler embossed text
  - cleaner typography
  - improved fit

### Printing
- Printer: **Bambu X1C**
- Material: **PLA**
- Profile: `0.12mm Fine @BBL X1C`
- Print time: ~**38 minutes**

<p align="center">
  <video src="https://github.com/user-attachments/assets/7d5e16f6-8002-4220-ab24-621bf1cb34ab" width="300" controls></video>
</p>

##  Why a Keychain?

- Keys are usually picked up **right before leaving**
- The device naturally fits into that moment of decision
- No need to unlock a phone or open an app
- The form factor encourages **glanceable, low-friction use**

## Why ESP32-S2?
- Compact form factor
- Wi-Fi enabled
- Integrated display
- Ideal for keychain-scale devices


## 📁 Repository Structure
```
PORTABLE SUBWAY TELLTALE/
│── README.md
│── code.py
│
├── animation/
│ ├── coffee_sheet_128x32.bmp
│ ├── walk_sheet_128x32.bmp
│ └── metro_run_sheet_128x32.bmp
│
├───assets
│ └── (Photos)
│
├── icons/
│ ├── subway_grey.png
│ ├── subway_blue.png
│ ├── subway_orange.png
│ └── subway_black.png
│
├── lib/
│ └── (CircuitPython libraries)
│
└── 3D_print_model/
├── top-2.2.stl
├── bottom-2.2.stl
└── Telltale modeling process.mp4

```


## 🔮 Future Work

- Add vibration or subtle audio cues
- Support bus or ferry arrival data

<img width="432" height="592" alt="Telltale Brighter Shot" src="https://github.com/user-attachments/assets/ed0af9a9-f210-437c-b788-a73ba6b33ec3" />

---

## 👋 Author

**Dingran Dai**  
Cornell Tech — MSIS (Urban Tech)  
Interactive Devices / Ubiquitous Computing








