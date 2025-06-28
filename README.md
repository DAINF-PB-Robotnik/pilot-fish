# Pilot Fish

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An autonomous Raspberry Pi 4 rover that **follows** a colored object (“fish”) in an aquarium using computer vision with Python, and **avoids** obstacles via 8 ultrasonic sensors on an Arduino Mega.
Movement is commanded through an H-bridge and PWM.

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)
- [Prerequisites](#prerequisites)  
- [3D Models & Bill of Materials](#3d-models--bill-of-materials)    
- [Installation](#installation)  
- [Configuration](#configuration)  
- [File Structure](#file-structure)  
- [Usage](#usage)  
- [Photo Dataset](#photo-dataset)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Overview

`Pilot_Fish`:

1. Captures frames from Picamera2.  
2. Tracks a colored “fish” via HSV→contour, computes centroid.  
3. Divides view into a 3×3 grid and compensates for any camera rotation with `rotate_index()`.  
4. Reads **8** HC-SR04 sensors over USB (ttyACM0) from an Arduino Mega at 0.2 s intervals.  
5. If the sensor **in the fish’s heading** is below the proximity limit, enters **avoidance**:  
   - Picks the clearest sensor (distance ≥ limit) as the escape direction.  
   - If no direction is clear, **stops** globally.  
6. Otherwise, if the fish’s path is clear, resumes **fish-follow**: grid→Direction mapping.  
7. Renders grid, rotated labels (`rotate_labels()`), contour, centroid and FPS on screen.  
8. Motor control via `Direction.drive()` (Braitenberg) or simple H-bridge commands.

All parameters (pins, HSV, sensor mapping, weights, limits, camera) live in **config.yaml**.

---

## Features

- **Fish-following** in a 3×3 grid, with camera-rotation compensation  
- **Obstacle avoidance** in fish’s heading via best-escape Braitenberg  
- **8-sensor array** on Arduino Mega → serial reader in Python  
- **Dynamic logging** of sensor labels & distances (e.g. `F=12.3 cm | R=45.6 cm`)  
- **Config-driven**: every pin, limit, weight, label and mapping in YAML  
- **Systemd service** for auto-start on boot  

---

## Prerequisites

Before you begin, ensure you have the following hardware and software:

### Hardware

- **Raspberry Pi 4** with camera connector  
- **Picamera v2** (or HQ Camera)  
- **2 × H-bridge drivers** (e.g. L298N)  
- **4 × DC motors** (JGA25-370 DC 12V 100 RPM, ≥ 2 kg·cm torque)  
- **Arduino Mega** (any Mega-series)  
- **8 × HC-SR04 ultrasonic sensors**  
- **Power supply** (12 V for motors, 5 V / 3 A for Pi)  
- **Jumper wires**, mounting hardware, chassis, wheels

### Software

- **Raspberry Pi OS** (Bullseye or newer)  
- **Python 3.7+**  
- System packages:
  - `python3-venv`  
  - `python3-pip`  
  - `python3-opencv`  
- Python libraries (installed via `pip install -r requirements.txt`):
  - `picamera2`  
  - `opencv-python`  
  - `RPi.GPIO`  
  - `pyyaml`  
  - `colorama`  
  - `pyserial`  
- **Git** (to clone this repo)  
- **systemd** (for the `start.service` unit)  

---

## 3D Models & Bill of Materials

All custom parts live in the [`3D/`](3D/) folder, in both CAD (STEP, FCStd) and mesh (STL) formats.

| Model / Hardware       | File / Spec                      | Description                       | Qty |
|------------------------|----------------------------------|-----------------------------------|-----|
| **Chassis Base**       | `3D/parts/chassis.stl`           | Main chassis platform             | 1   |
| **Sensor Bracket**     | `3D/parts/sensor_mount.stl`      | Ultrasonic sensor mount           | 8   |
| **Motor Mount Plate**  | `3D/parts/motor_mount.stl`       | DC motor mounting plate           | 4   |
| **Full Assembly**      | `3D/assemblies/assembly.step`    | Complete assembly for CAD import  | 1   |
| **M2.5×6 mm screws**    | Stainless steel                  | Fasten 3D-printed parts           | 16  |
| **M2.5 nuts**          | Stainless steel                  | Securing screws                   | 16  |
| **DC Motors**          | JGA25-370 DC 12V 100 RPM, ≥2 kg·cm| Drive wheels                      | 4   |
| **H-bridge driver**    | L298N or equivalent              | Motor control via PWM             | 2   |
| **Arduino Mega**       | Any Mega-series                  | Reads 8× HC-SR04 via serial       | 1   |
| **HC-SR04 sensor**     | Ultrasonic distance sensor       | Obstacle detection                | 8   |

---

## Installation

Follow these steps to install and configure **Pilot-Fish** in either **contour** or **YOLO** mode. All you need is the unified `install.sh` script.

1. **Clone the repository**

   ```bash
   git clone https://github.com/DAINF-PB-Robotnik/pilot-fish.git
   cd pilot-fish
   ```

2. **Make the installer executable**

   ```bash
   chmod +x install.sh
   ```

3. **Run the installer**\
   Choose either **contour** (color-based) or **yolo** (neural-network) mode:

   ```bash
   sudo ./install.sh contour
   ```
   **— OR —**
   ```bash
   sudo ./install.sh yolo
   ```

   This will:

   - Install system packages (Python 3, OpenCV, libcamera-utils, Atlas, HDF5, Qt, etc.)
   - Create a dedicated virtual environment (`.venv_contour` or `.venv_yolo`)
   - Install Python dependencies from `code/<mode>/requirements.txt`
   - Generate and enable a `fish.service` systemd unit to launch your chosen mode on boot

5. **Verify and manage the service**

   - Check status:
     ```bash
     systemctl status fish.service
     ```
   - Watch live logs:
     ```bash
     journalctl -u fish.service -f
     ```
   - Manually stop or start:
     ```bash
     sudo systemctl stop  fish.service
     sudo systemctl start fish.service
     ```

---

## Quick One-Line Installs

### Contour mode:
```bash
git clone https://github.com/DAINF-PB-Robotnik/pilot-fish.git && cd pilot-fish && chmod +x install.sh && sudo ./install.sh contour
```
### YOLO mode:
```bash
git clone https://github.com/DAINF-PB-Robotnik/pilot-fish.git && cd pilot-fish && chmod +x install.sh && sudo ./install.sh yolo
```



## Configuration

Edit **`config.yaml`** to adjust:

```yaml
# Serial for Arduino Mega
serial:
  port:      "/dev/ttyACM0"
  baudrate:  115200
  timeout_s: 1.0

# Polling for serial sensors
sensor_read:
  num_sensors: 8
  interval_s:  0.2
  labels:      ["F","FR","R","BR","B","BL","L","FL"]

# Grid → sensor index map
sensor_map:
  - [7, 0, 1]
  - [6, null, 2]
  - [5, 4, 3]

# Braitenberg parameters
braitenberg:
  base_speed:      50
  weights_left:   [ -0.5, -0.3,  0.0,  0.3,  0.5,  0.3,  0.0, -0.3 ]
  weights_right:  [  0.5,  0.3,  0.0, -0.3, -0.5, -0.3,  0.0,  0.3 ]

control:
  proximity_limit_cm: 50.0

camera:
  rotation:   90
  format:     "XRGB8888"
  resolution: [640, 480]
  framerate:  30
```

After changes, restart the service:

```bash
sudo systemctl restart start.service
```

---

## File Structure

```
3D/                        # 3D printable parts (Fusion 360 and STL files)
├── F3D/                   # Editable Fusion 360 files
├── STL/                   # Exported STL models for 3D printing

circuit/                  # Schematics and diagrams
├── fish.fzz              # Editable Fritzing project
├── fish.png              # Circuit image

code/
├── contour/              # HSV + contour-based tracking
│   ├── config.py         # YAML parser and utility functions
│   ├── config.yaml       # Configuration for contour mode
│   ├── control.py        # Avoidance and tracking logic
│   ├── direction.py      # Motor control logic
│   ├── draw.py           # Grid and overlay rendering
│   ├── main.py           # Entry point for contour version
│   ├── motor.py          # H-bridge interface
│   ├── pwm.py            # PWM helper class
│   ├── requirements.txt  # Python dependencies
│   ├── sensor.py         # Reads sensors from Arduino
│   ├── track.py          # Contour-based tracking logic
│   └── view_requirements.sh  # Shows installed packages
├── yolo/                 # YOLOv8-based tracking
│   ├── best.pt           # YOLOv8 weights
│   ├── config.py         # YAML parser and utility functions
│   ├── config.yaml       # Configuration for yolo mode
│   ├── control.py        # Avoidance and tracking logic
│   ├── direction.py      # Motor control logic
│   ├── draw.py           # Grid and overlay rendering
│   ├── main.py           # Entry point for yolo version
│   ├── motor.py          # H-bridge interface
│   ├── photo.py          # Dataset photo capture
│   ├── pwm.py            # PWM helper class
│   ├── requirements.txt  # Python dependencies
│   ├── sensor.py         # Reads sensors from Arduino
│   ├── track.py          # YOLOv8-based tracking logic
│   ├── light/            # Light condition photos (omitted)
│   ├── normal/           # Normal condition photos (omitted)
│   └── shake/            # Shaking condition photos (omitted)
├── mega/
│   └── mega.ino          # Arduino sketch for ultrasonic sensors

install.sh                # Unified installer script for contour/yolo
install.service           # Legacy service example (not required)
LICENSE                   # MIT License
README.md                 # This documentation
```

---

## Usage

### Interactive

```bash
source .venv/bin/activate
python main.py
```

Open windows **MAIN** (with overlays) and **BINARY** (mask).

### As a Service

```bash
sudo systemctl start start.service
sudo journalctl -f -u start.service
```

---

## Photo Dataset

```bash
python photo.py
```

1. Choose mode: `1` normal, `2` light, `3` shake
2. Enter count and interval
3. Images saved under `./normal/`, `./light/`, or `./shake/`.

---

## Contributing

1. Fork & clone
2. `git checkout -b feat/your-feature`
3. Commit & push
4. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).
