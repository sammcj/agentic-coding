# Pico SDK and Toolchain Reference

## Table of Contents

- [Current Versions](#current-versions)
- [SDK Setup](#sdk-setup)
- [CMake Configuration](#cmake-configuration)
- [Project Structure](#project-structure)
- [Toolchain Requirements](#toolchain-requirements)
- [picotool](#picotool)
- [SDK Libraries](#sdk-libraries)
- [stdio Configuration](#stdio-configuration)
- [MicroPython](#micropython)
- [CircuitPython](#circuitpython)
- [BOOTSEL and UF2 Flashing](#bootsel-and-uf2-flashing)
- [Key References](#key-references)

## Current Versions

| Tool | Version |
|------|---------|
| pico-sdk | 2.2.0 |
| picotool | 2.2.0 |
| Debug Probe firmware | 2.3.0 |
| CircuitPython (Pico 2) | 10.1.4 stable |

## SDK Setup

### Clone and Configure

```bash
git clone https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
export PICO_SDK_PATH=$(pwd)
```

Submodules pull: tinyusb, cyw43-driver, lwip, btstack, mbedtls. Missing submodules cause build failures for USB and wireless features.

### System Dependencies

**Debian/Ubuntu:**
```bash
sudo apt install cmake python3 build-essential gcc-arm-none-eabi \
  libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib
```

**macOS (Homebrew):**
```bash
brew install cmake python arm-none-eabi-gcc
```

### SDK Integration Methods

1. **Cloned locally (most common):** Copy `external/pico_sdk_import.cmake` into your project. Set `PICO_SDK_PATH` env var or pass `-DPICO_SDK_PATH=...` to cmake.
2. **Git submodule:** Include `pico-sdk/pico_sdk_init.cmake` directly.
3. **Auto-download:** Set `PICO_SDK_FETCH_FROM_GIT=on` before including `pico_sdk_import.cmake`.

## CMake Configuration

### Key Variables

| Variable | Purpose | Values |
|----------|---------|--------|
| `PICO_BOARD` | Board definition (sets pin defaults, enables libs) | `pico`, `pico_w`, `pico2`, `pico2_w` |
| `PICO_PLATFORM` | Chip platform and architecture | `rp2040`, `rp2350-arm-s`, `rp2350-riscv` |
| `PICO_SDK_PATH` | Path to cloned SDK | Absolute path |
| `PICO_TOOLCHAIN_PATH` | Override toolchain location | Path to compiler prefix |
| `CMAKE_BUILD_TYPE` | Build type | `Debug`, `Release`, `MinSizeRel`, `RelWithDebInfo` |

Setting `PICO_BOARD=pico2` automatically sets `PICO_PLATFORM=rp2350-arm-s`. Only set `PICO_PLATFORM` explicitly for RISC-V override.

Board definitions live in `pico-sdk/src/boards/include/boards/` as header files.

### Minimal CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.13...3.27)

include(pico_sdk_import.cmake)

project(my_project C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(my_app src/main.c)
target_link_libraries(my_app pico_stdlib)
pico_add_extra_outputs(my_app)  # generates .uf2, .bin, .hex, .map
```

### Build Commands

```bash
# Pico 2 (ARM, default)
mkdir build && cd build
cmake -DPICO_BOARD=pico2 ..
make -j$(nproc)

# Pico 2 (RISC-V)
export PICO_TOOLCHAIN_PATH=/opt/riscv/riscv-toolchain-14/
mkdir build-riscv && cd build-riscv
cmake -DPICO_BOARD=pico2 -DPICO_PLATFORM=rp2350-riscv ..
make -j$(nproc)

# Pico 2 W
cmake -DPICO_BOARD=pico2_w ..

# Pico 1 (default if PICO_BOARD not set)
cmake ..
# or explicitly:
cmake -DPICO_BOARD=pico ..

# Debug build (for GDB debugging)
cmake -DPICO_BOARD=pico2 -DCMAKE_BUILD_TYPE=Debug ..
```

## Project Structure

```
my_project/
  CMakeLists.txt
  pico_sdk_import.cmake      # copied from pico-sdk/external/
  src/
    main.c
  include/
    config.h
```

### Full Example CMakeLists.txt (Pico 2 with USB stdio)

```cmake
cmake_minimum_required(VERSION 3.13...3.27)

include(pico_sdk_import.cmake)

project(my_project C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(my_app
    src/main.c
)

target_include_directories(my_app PRIVATE include)

target_link_libraries(my_app
    pico_stdlib
    hardware_gpio
    hardware_i2c
    hardware_pio
    hardware_adc
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(my_app 1)
pico_enable_stdio_uart(my_app 0)

pico_add_extra_outputs(my_app)
```

## Toolchain Requirements

| Target | Compiler | Package (Debian) |
|--------|----------|------------------|
| RP2040 (Cortex-M0+) | `arm-none-eabi-gcc` | `gcc-arm-none-eabi`, `libnewlib-arm-none-eabi`, `libstdc++-arm-none-eabi-newlib` |
| RP2350 ARM (Cortex-M33) | `arm-none-eabi-gcc` | Same as above |
| RP2350 RISC-V (Hazard3) | RISC-V GCC | Prebuilt from `pico-sdk-tools` releases |

Also requires: CMake >= 3.13, Python 3, native C compiler (for SDK build tools).

### RISC-V Toolchain Setup

```bash
# Download (example for aarch64 Linux)
wget https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.0.0-5/riscv-toolchain-14-aarch64-lin.tar.gz
sudo mkdir -p /opt/riscv/riscv-toolchain-14
tar xvf riscv-toolchain-14-aarch64-lin.tar.gz -C /opt/riscv/riscv-toolchain-14
export PICO_TOOLCHAIN_PATH=/opt/riscv/riscv-toolchain-14/
```

## picotool

CLI tool for working with RP2040/RP2350 devices and binaries.

### Installation

**macOS:** `brew install picotool`

**Linux (from source):**
```bash
git clone https://github.com/raspberrypi/picotool.git
cd picotool && mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

**Prebuilt:** Download from https://github.com/raspberrypi/pico-sdk-tools/releases. Set `picotool_DIR` env var to the extracted path.

### Commands

| Command | Purpose |
|---------|---------|
| `picotool info` | Display connected device or binary info |
| `picotool info -a` | Show all available info |
| `picotool load <file>` | Flash binary to device |
| `picotool load -x <file>` | Flash and immediately execute |
| `picotool reboot` | Reboot into application mode |
| `picotool reboot -u` | Reboot into BOOTSEL mode |
| `picotool reboot -u -c riscv` | Reboot into BOOTSEL, pre-select RISC-V |
| `picotool config` | Read/write device configuration |
| `picotool partition info` | Display partition table |
| `picotool seal` | Sign a binary (RP2350 only) |
| `picotool encrypt` | Encrypt and sign (RP2350 only) |
| `picotool otp load` | Load data into OTP rows |
| `picotool otp dump` | Dump OTP contents |
| `picotool otp permissions` | Set OTP access permissions |

## SDK Libraries

| Library | Header | Purpose |
|---------|--------|---------|
| `pico_stdlib` | `pico/stdlib.h` | Aggregates GPIO, UART, time |
| `hardware_gpio` | `hardware/gpio.h` | GPIO control |
| `hardware_i2c` | `hardware/i2c.h` | I2C controller |
| `hardware_spi` | `hardware/spi.h` | SPI controller |
| `hardware_pio` | `hardware/pio.h` | Programmable I/O |
| `hardware_adc` | `hardware/adc.h` | ADC |
| `hardware_pwm` | `hardware/pwm.h` | PWM |
| `hardware_timer` | `hardware/timer.h` | Hardware timers |
| `pico_multicore` | `pico/multicore.h` | Dual-core programming |
| `pico_cyw43_arch` | `pico/cyw43_arch.h` | Wi-Fi/BT (Pico W / Pico 2 W) |
| `pico_sha256` | | SHA-256 hardware accel (RP2350 only) |
| `pico_stdio_rtt` | | RTT stdio driver |

## stdio Configuration

The SDK supports three stdio backends, selectable per-target in CMakeLists.txt:

```cmake
# USB CDC (appears as serial port on host)
pico_enable_stdio_usb(my_app 1)
pico_enable_stdio_uart(my_app 0)

# UART (default UART0 on GP0/GP1)
pico_enable_stdio_usb(my_app 0)
pico_enable_stdio_uart(my_app 1)

# Both simultaneously
pico_enable_stdio_usb(my_app 1)
pico_enable_stdio_uart(my_app 1)

# RTT (via SWD debug channel, needs pico_stdio_rtt linked)
```

UART stdio is useful with the Debug Probe's UART bridge. USB stdio is convenient for standalone development without a Debug Probe.

## MicroPython

### UF2 Downloads

- Pico 2: `https://micropython.org/download/RPI_PICO2/RPI_PICO2-latest.uf2`
- Pico 2 W: `https://micropython.org/download/RPI_PICO2_W/RPI_PICO2_W-latest.uf2`

### Differences from Pico 1

- Separate firmware builds (RPI_PICO2 vs rp2-pico)
- 520 kB SRAM available (vs 264 kB)
- Third PIO block (PIO2) accessible
- Cortex-M33 FPU for floating-point
- Wi-Fi/BT on Pico 2 W (CYW43439)

### Workflow

Hold BOOTSEL, plug USB, device mounts as "RP2350", drag UF2 onto it. Use Thonny IDE or `mpremote` for interactive development.

## CircuitPython

Fully supported on Pico 2. Current stable: 10.1.4.
Download: `https://circuitpython.org/board/raspberry_pi_pico2/`

Benefits from Pico 2's 4 MB flash (larger filesystem), extra SRAM, and third PIO block.

## BOOTSEL and UF2 Flashing

1. Hold BOOTSEL button while connecting Pico to USB
2. Device mounts as USB mass storage "RPI-RP2"
3. Drag and drop .uf2 file onto the drive
4. Pico reboots and runs new firmware

BOOTSEL is in read-only ROM and cannot be overwritten. It always works regardless of firmware state.

### Flash Erase

Copy `nuke.uf2` onto the device while in BOOTSEL to wipe external flash. Source: `pico-examples/flash/nuke/nuke.c`.

### Partition Tables (RP2350)

RP2350 supports A/B partition tables in flash. `picotool partition info` shows the layout. UF2 family IDs: `rp2350-arm-s` (ARM) and `rp2350-riscv` (RISC-V).

## Key References

| Resource | URL |
|----------|-----|
| pico-sdk | https://github.com/raspberrypi/pico-sdk |
| pico-examples | https://github.com/raspberrypi/pico-examples |
| pico-extras | https://github.com/raspberrypi/pico-extras |
| picotool | https://github.com/raspberrypi/picotool |
| C/C++ SDK docs | https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html |
| RP2350 datasheet | https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |
| Pico 2 datasheet | https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf |
| Getting Started PDF | https://rptl.io/pico-get-started |
| SDK API reference | https://rptl.io/pico-c-sdk |
| Doxygen API docs | https://rptl.io/pico-doxygen |
| MicroPython docs | https://www.raspberrypi.com/documentation/microcontrollers/micropython.html |
| CircuitPython Pico 2 | https://circuitpython.org/board/raspberry_pi_pico2/ |
| VS Code extension | `raspberry-pi.raspberry-pi-pico` |
| RISC-V toolchains | https://github.com/raspberrypi/pico-sdk-tools/releases |
| Board definitions | `pico-sdk/src/boards/include/boards/` |
| Pico W networking | https://rptl.io/picow-connect |
