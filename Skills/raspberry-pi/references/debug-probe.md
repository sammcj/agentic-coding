# Raspberry Pi Debug Probe Reference

## Table of Contents

- [Hardware Overview](#hardware-overview)
- [Wiring to Pico 2](#wiring-to-pico-2)
- [Software Installation](#software-installation)
- [OpenOCD Configuration](#openocd-configuration)
- [GDB Debugging Workflow](#gdb-debugging-workflow)
- [Flashing via SWD](#flashing-via-swd)
- [UART Serial Console](#uart-serial-console)
- [RTT (Real-Time Transfer)](#rtt-real-time-transfer)
- [VS Code Integration](#vs-code-integration)
- [Debug Probe Firmware](#debug-probe-firmware)
- [Using a Pico as Debug Probe](#using-a-pico-as-debug-probe)
- [Rescue Mode](#rescue-mode)
- [Troubleshooting](#troubleshooting)

## Hardware Overview

The Debug Probe is a USB device (built on RP2040) providing:
- USB to SWD (CMSIS-DAP compatible)
- USB to UART bridge (CDC serial)

Operates at 3.3V nominal I/O voltage.

### Connectors

| Connector | Label | Type | Purpose |
|-----------|-------|------|---------|
| USB Micro-B | (top) | USB | Power and data to host |
| SWD port | "D" | 3-pin JST-SH (1.0mm) | Serial Wire Debug |
| UART port | "U" | 3-pin JST-SH (1.0mm) | Serial UART bridge |

### Cable Colour Coding

| Colour | Signal |
|--------|--------|
| Orange | TX/SC (output from probe) |
| Black | GND |
| Yellow | RX/SD (input to probe or I/O) |

### Included Cables

1. JST-SH to JST-SH (for boards with JST connector)
2. JST-SH to 0.1-inch female header (for soldered pin headers)
3. JST-SH to 0.1-inch male header (for breadboard use)

## Wiring to Pico 2

### SWD Connection (Port "D")

The Pico 2 must be powered separately (USB or VSYS). The SWD connector carries no power.

**Boards with JST connector (Pico 2 with headers):**
Connect Debug Probe "D" port directly to Pico 2 SWD JST-SH with the JST-to-JST cable.

**Boards with castellated pads (standard Pico 2):**
Solder headers to the three SWD pads, then use the JST-SH to 0.1-inch female cable:

| Debug Probe "D" | Wire | Pico 2 SWD Pad |
|------------------|------|----------------|
| SC | Orange | SWCLK |
| GND | Black | GND |
| SD | Yellow | SWDIO |

### UART Connection (Port "U")

| Debug Probe "U" | Wire | Pico 2 Pin | GPIO |
|------------------|------|------------|------|
| TX | Orange | Pin 2 | GP1 (UART0 RX) |
| RX | Yellow | Pin 1 | GP0 (UART0 TX) |
| GND | Black | Pin 3 | GND |

Crossover: probe TX to Pico RX, probe RX to Pico TX.

### Safety

When the Pico 2 is powered from a separate source, connect GND between target and probe first before any signal lines. Voltage differences can damage the probe.

## Software Installation

### Option A: VS Code Extension (Recommended)

Install `raspberry-pi.raspberry-pi-pico` from the VS Code marketplace. It bundles OpenOCD, ARM toolchain, GDB, and Cortex-Debug integration.

### Option B: Manual Installation

#### OpenOCD (Raspberry Pi Fork)

The RPi fork is required for full RP2350 support. Upstream OpenOCD 0.12.0 is insufficient.

**macOS:**
```bash
brew install libusb hidapi libftdi capstone pkgconf
git clone https://github.com/raspberrypi/openocd.git --branch rpi-common --depth=1
cd openocd
./bootstrap
./configure --enable-cmsis-dap
make -j$(sysctl -n hw.logicalcpu)
sudo make install
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install automake autoconf build-essential texinfo libtool \
  libftdi-dev libusb-1.0-0-dev libhidapi-dev pkg-config
git clone https://github.com/raspberrypi/openocd.git --branch rpi-common --depth=1
cd openocd
./bootstrap
./configure --enable-cmsis-dap
make -j$(nproc)
sudo make install
```

#### GDB

- ARM builds: `arm-none-eabi-gdb` (from Arm GNU Toolchain)
- RISC-V builds: `riscv32-unknown-elf-gdb` or `gdb-multiarch`
- Linux alternative: `sudo apt install gdb-multiarch`

#### picotool

**macOS:** `brew install picotool`
**Linux:** Build from source at https://github.com/raspberrypi/picotool

## OpenOCD Configuration

### Target Config Files

| File | Purpose |
|------|---------|
| `target/rp2040.cfg` | RP2040 (Pico 1) dual Cortex-M0+ |
| `target/rp2350.cfg` | RP2350 (Pico 2) dual Cortex-M33 and/or Hazard3 RISC-V |
| `target/rp2350-riscv.cfg` | RP2350 RISC-V only |
| `target/rp2350-rescue.cfg` | RP2350 rescue mode |

### RP2040 vs RP2350 in OpenOCD

| Aspect | RP2040 | RP2350 |
|--------|--------|--------|
| Target config | `target/rp2040.cfg` | `target/rp2350.cfg` |
| DAP protocol | ADIv5 with multidrop SWD | ADIv6 with SWD |
| Flash driver | `rp2040` | `rp2xxx` |
| CPUTAPID | `0x01002927` | `0x00004927` |

### USE_CORE Options (RP2350)

Controls which cores OpenOCD connects to:

| Value | Effect |
|-------|--------|
| `{ cm0 cm1 }` | Both Cortex-M33 cores (default) |
| `cm0` | Cortex-M33 core 0 only |
| `rv0` | RISC-V Hazard3 core 0 only |
| `{ rv0 rv1 }` | Both RISC-V cores |
| `{ cm0 cm1 rv0 rv1 }` | All four core slots |

For RISC-V debugging, pre-select RISC-V mode first:
```bash
picotool reboot -u -c riscv
```

### OpenOCD Ports

| Port | Purpose |
|------|---------|
| 3333 | GDB connections |
| 4444 | Telnet (OpenOCD commands) |
| 6666 | TCL scripting |

## GDB Debugging Workflow

### Step 1: Build with Debug Symbols

```bash
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Debug -DPICO_BOARD=pico2 ..
make -j$(nproc)
```

`-DCMAKE_BUILD_TYPE=Debug` is critical. Without it, optimisations make breakpoints unreliable.

### Step 2: Start OpenOCD

```bash
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000"
```

### Step 3: Connect GDB

```bash
arm-none-eabi-gdb my_app.elf
```

```gdb
(gdb) target remote localhost:3333
(gdb) monitor reset init
(gdb) load
(gdb) break main
(gdb) continue
```

### Common GDB Commands

| Command | Effect |
|---------|--------|
| `target remote localhost:3333` | Connect to OpenOCD |
| `monitor reset init` | Reset and halt at entry |
| `load` | Flash ELF to target |
| `break main` | Breakpoint at main() |
| `continue` / `c` | Resume |
| `step` / `s` | Step into |
| `next` / `n` | Step over |
| `print var` | Print variable |
| `info registers` | Register state |
| `monitor reset halt` | Reset and halt |
| `backtrace` / `bt` | Call stack |

## Flashing via SWD

### Using OpenOCD

```bash
# Pico 2
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg \
  -c "adapter speed 5000" \
  -c "program my_app.elf verify reset exit"

# Pico 1
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg \
  -c "adapter speed 5000" \
  -c "program my_app.elf verify reset exit"
```

Use the .elf file for SWD. The .uf2 format is only for BOOTSEL drag-and-drop.

### Using picotool

```bash
picotool load my_app.elf
picotool reboot
```

## UART Serial Console

The Debug Probe "U" port exposes a CDC serial device on the host.

### Device Paths

| OS | Path |
|----|------|
| Linux | `/dev/ttyACM0` or `/dev/ttyACM1` |
| macOS | `/dev/cu.usbmodemXXXX` |
| Windows | `COMx` |

### Connecting

```bash
# Linux
minicom -b 115200 -o -D /dev/ttyACM0

# macOS
ls /dev/cu.usbmodem*
screen /dev/cu.usbmodemXXXX 115200
# or
minicom -b 115200 -o -D /dev/cu.usbmodemXXXX
```

Default baud rate for SDK examples: 115200.
Debug Probe firmware v2.3.0 supports opt-in autobaud.

Exit minicom: CTRL-A then X.
Exit screen: CTRL-A then K, then Y.

## RTT (Real-Time Transfer)

RTT uses the SWD debug channel for printf-style output. Faster than UART, no extra wiring needed.

### VS Code (Cortex-Debug)

Add to `launch.json`:
```json
"rttConfig": {
    "enabled": true,
    "address": "auto",
    "decoders": [
        {
            "label": "",
            "port": 0,
            "type": "console"
        }
    ]
}
```

Output appears in the TERMINAL tab under `RTT Ch:0 console`.

### Standalone GDB

```gdb
(gdb) target remote localhost:3333
(gdb) monitor reset init
(gdb) monitor rtt setup 0x20000000 2048 "SEGGER RTT"
(gdb) monitor rtt start
(gdb) monitor rtt server start 60000 0
(gdb) continue
```

Then in another terminal: `nc localhost 60000`

### SDK Setup

Enable `pico_stdio_rtt` as the stdio driver in CMakeLists.txt instead of (or alongside) UART/USB.

## VS Code Integration

### Raspberry Pi Pico Extension

Extension ID: `raspberry-pi.raspberry-pi-pico`

Provides: project scaffolding, CMake build integration, bundled OpenOCD/GCC/GDB, one-click debug, register viewer, RTT support.

### Cortex-Debug Extension

Extension ID: `marus25.cortex-debug`

For manual configuration, a `launch.json` entry uses:
- `"servertype": "openocd"`
- `"configFiles": ["interface/cmsis-dap.cfg", "target/rp2350.cfg"]`
- `"device": "RP2350"` (or `"RP2040"`)
- The ELF file as `"executable"`

## Debug Probe Firmware

Current version: 2.3.0 (released 2025-02-11).
Source: https://github.com/raspberrypi/debugprobe

### Check Version (Linux)

```bash
lsusb -v -d 2e8a:000c | grep bcdDevice
# Reports bcdDevice 2.30 for v2.3.0
```

The `Info : CMSIS-DAP: FW Version = 2.0.0` from OpenOCD is the CMSIS-DAP protocol version, not the firmware version.

### Update Procedure

1. Download `debugprobe.uf2` from https://github.com/raspberrypi/debugprobe/releases/latest
2. Remove the Debug Probe enclosure top (pinch to open)
3. Hold BOOTSEL while plugging into USB. "RPI-RP2" volume mounts.
4. Copy `debugprobe.uf2` onto the volume.
5. Probe reboots with new firmware.

## Using a Pico as Debug Probe

The debugprobe firmware can run on a regular Pico or Pico 2.

**Pico 1:** Download `debugprobe_on_pico.uf2` from releases, or build with `cmake -DDEBUG_ON_PICO=ON ..`

**Pico 2:**
```bash
git clone https://github.com/raspberrypi/debugprobe
cd debugprobe
git submodule update --init --recursive
mkdir build-pico2 && cd build-pico2
export PICO_SDK_PATH=/path/to/pico-sdk  # SDK v2.0.0+
cmake -DDEBUG_ON_PICO=1 -DPICO_BOARD=pico2 ../
make
```

Download `debugprobe_on_pico2.uf2` from releases page.

## Rescue Mode

Recover bricked Pico 2 devices (bad firmware causes crash loop):

```bash
# RP2350 rescue
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "set RESCUE 1"

# RP2040 rescue
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg -c "set RESCUE 1"
```

RP2350 uses the RP_AP CTRL register RESCUE_RESTART bit. Both cores stop in the bootrom after rescue. Restart OpenOCD without the RESCUE flag and load fresh code.

## Troubleshooting

### Linux Permissions (udev rules)

```bash
# Debug Probe (VID:PID 2e8a:000c)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", ATTR{idProduct}=="000c", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/99-debug-probe.rules

# Pico in BOOTSEL mode
# RP2040: 2e8a:0003, RP2350: 2e8a:000f
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", ATTR{idProduct}=="0003", MODE="0666"' | \
  sudo tee -a /etc/udev/rules.d/99-debug-probe.rules
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2e8a", ATTR{idProduct}=="000f", MODE="0666"' | \
  sudo tee -a /etc/udev/rules.d/99-debug-probe.rules

sudo udevadm control --reload-rules
sudo udevadm trigger
```

### USB VID:PID Reference

| Device | VID:PID |
|--------|---------|
| Debug Probe | `2e8a:000c` |
| RP2040 BOOTSEL | `2e8a:0003` |
| RP2350 BOOTSEL | `2e8a:000f` |

### macOS

- Install `hidapi` and `libusb` via Homebrew
- No special driver needed for CMSIS-DAP
- If probe not found: check no other process holds the USB device

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| OpenOCD cannot find probe | Another process using it | Close VS Code debug / other OpenOCD |
| Connection timeout | Wrong target config | Match rp2040.cfg or rp2350.cfg to your chip |
| Unreliable breakpoints | Release build | Rebuild with `-DCMAKE_BUILD_TYPE=Debug` |
| SWD not working | No power to target | Power Pico 2 via USB or VSYS |
| Garbled UART output | Wrong baud rate | Check code matches 115200 (or configure) |
| Multiple probes, wrong one selected | Ambiguous device | Use `adapter serial <serial>` |
| Slow/unstable SWD | Cable too long / speed too high | Reduce to `adapter speed 1000` |
