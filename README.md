# Pilot Fish

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An autonomous Raspberry Pi 4 rover that **follows** a colored object (“fish”) in an aquarium using computer vision with Python, and **avoids** obstacles via 8 ultrasonic sensors on an Arduino Mega.
Movement is commanded through an H-bridge and PWM.

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Prerequisites](#prerequisites)  
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

- **Hardware**  
  - Raspberry Pi 4 + Picamera2
  - 2 × H-bridge motor drivers (e.g. L298N)  
  - 4 × DC motors (min. 2 kg·cm torque; model used: JGA25-370 DC 12V 100 RPM)  
  - Arduino Mega + 8 HC-SR04 sensors  
- **Software**  
  - Raspberry Pi OS (Bullseye or newer)  
  - Python 3.7+  
  - GPIO access (`RPi.GPIO`)  
  - `libcamera`, `python3-opencv`  
  - Git  

---

## Installation


### Quick Start

```bash
git clone https://github.com/<your-user>/Pilot_Fish.git \
  && cd Pilot_Fish \
  && chmod +x install.sh \
  && sudo ./install.sh \
  && sudo systemctl start start.service
```
```bash
# 1) Clone the repository
git clone https://github.com/<your-user>/Pilot_Fish.git
cd Pilot_Fish

# 2) Make the installer executable
chmod +x install.sh

# 3) Run as root to set up system & Python environment
sudo ./install.sh
```

This will:

* Install system packages (`python3-venv`, `python3-opencv`, etc.)
* Create a `.venv/` and install Python dependencies from `requirements.txt`
* Copy & enable `start.service` as a systemd unit that runs at boot

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
Pilot_Fish/
├── install.sh          # System & Python installer
├── config.yaml         # All parameters & mappings
├── config.py           # Loads YAML → constants & helpers
├── main.py             # Orchestrates capture, track, control, draw, display
├── track.py            # Fish detection (HSV, contour, ROI, FPS)
├── draw.py             # Grid + rotated labels + overlay
├── control.py          # Avoidance + fish-follow logic
├── direction.py        # Motor commands + drive() for Braitenberg
├── sensor.py           # Serial reader for 8 HC-SR04 via Arduino
├── pwm.py              # PWM wrapper
├── motor.py            # H-bridge motor interface
├── photo.py            # Dataset photo capture script
├── start.service       # systemd unit (installed to /etc/systemd/system)
└── requirements.txt    # Python dependencies
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
