# Pico 2 (RP2350) Hardware Reference

## Table of Contents

- [RP2350 Specifications](#rp2350-specifications)
- [Chip Variants](#chip-variants)
- [RP2040 vs RP2350 Comparison](#rp2040-vs-rp2350-comparison)
- [Pin Compatibility](#pin-compatibility)
- [Architecture Switching](#architecture-switching-arm-vs-risc-v)
- [Pico 2 W Wireless](#pico-2-w-wireless)
- [Security Features](#security-features-rp2350-only)
- [Board Layout](#board-layout)

## RP2350 Specifications

| Attribute | Value |
|-----------|-------|
| CPU (ARM) | Dual-core Arm Cortex-M33, up to 150 MHz |
| CPU (RISC-V) | Dual-core Hazard3 (open-hardware RISC-V), up to 150 MHz |
| SRAM | 520 kB in 10 independent banks |
| On-board flash (Pico 2) | 4 MB external QSPI |
| Max external flash | Up to 32 MB via QSPI XIP |
| PSRAM support | Yes, via QMI memory interface |
| GPIO (Pico 2 board) | 26 multi-function pins exposed (chip has 30; 4 used internally) |
| ADC | 4 analogue inputs + internal temperature sensor, 500 kS/s, 12-bit |
| PIO | 3 blocks x 4 state machines = 12 total |
| DMA | 16 channels |
| PWM | 16 channels (RP2350A) / 24 channels (RP2350B) |
| HSTX | High-speed serial transmit peripheral (DVI video output) |
| USB | USB 1.1 controller and PHY, host and device |
| UART | 2x |
| SPI | 2x |
| I2C | 2x |
| Timers | 2 timers with 4 alarms each + Always-On (AON) timer |
| FPU | Hardware single + double precision (ARM mode only) |
| Core voltage | On-chip buck converter (SMPS) + optional LDO for sleep |
| AHB crossbar | AHB5 (upgraded from AHB-Lite on RP2040) |

## Chip Variants

| Variant | GPIO | ADC Channels | Flash | PWM |
|---------|------|-------------|-------|-----|
| RP2350A | 30 | 4 | External QSPI only | 16 |
| RP2350B | 48 | 8 | External QSPI only | 24 |
| RP2354A | 30 | 4 | 2 MB stacked on-chip | 16 |
| RP2354B | 48 | 8 | 2 MB stacked on-chip | 24 |

The Pico 2 board uses the RP2350A variant.

## RP2040 vs RP2350 Comparison

| Feature | Pico 1 / RP2040 | Pico 2 / RP2350 |
|---------|-----------------|-----------------|
| CPU | Dual Cortex-M0+ | Dual Cortex-M33 or Dual Hazard3 RISC-V |
| Clock | Up to 133 MHz | Up to 150 MHz |
| SRAM | 264 kB (6 banks) | 520 kB (10 banks) |
| On-board flash | 2 MB | 4 MB |
| Max external flash | 16 MB | 32 MB |
| PSRAM | Not supported | Supported via QMI |
| PIO | 2 blocks, 8 state machines | 3 blocks, 12 state machines |
| DMA channels | 12 | 16 |
| HSTX | No | Yes |
| FPU | Software float | Hardware single+double (ARM only) |
| Integer divider | Dedicated hardware block | In-CPU native division |
| Security | None | TrustZone, signed boot, OTP, SHA-256, TRNG, glitch detectors |
| Timers | 1 timer, 4 alarms | 2 timers, 4 alarms each, + AON timer |
| AHB | AHB-Lite | AHB5 |
| Core voltage | On-chip LDO | On-chip SMPS + optional LDO |

Performance: M33 core is roughly 2x faster than M0+ at comparable tasks.

### Migration Notes

- Pico 2 is a drop-in hardware replacement for Pico 1 (same 40-pin form factor, same pin layout).
- Code targeting RP2040 needs recompilation with `-DPICO_BOARD=pico2` but most SDK code is portable.
- Code using the RP2040 dedicated hardware integer divider directly (not via SDK) needs adjustment; RP2350 uses in-CPU division.
- For DVI/video output, prefer the HSTX peripheral on RP2350 instead of pushing PIO to its limits.

## Pin Compatibility

Pico 2 maintains full pin compatibility with Pico 1:
- Same 40-pin form factor and castellated pads
- Same 26 user GPIO pins at the same positions
- Same pin numbering
- Same power pin positions: 3V3, VSYS, VBUS, 3V3_EN, ADC_VREF, AGND, RUN
- Same peripheral pin mapping (SPI, I2C, UART, ADC on the same GPIOs)
- LED on GP25 (non-wireless) or WL_GPIO0 (wireless models)

No breaking pin changes between generations.

## Architecture Switching (ARM vs RISC-V)

RP2350 contains both dual Cortex-M33 and dual Hazard3 RISC-V cores. One architecture is selected at build time; they cannot run simultaneously.

The boot ROM auto-detects ARM vs RISC-V from the binary and switches automatically.

### Build for ARM (default)

```bash
cmake -DPICO_BOARD=pico2 ..
```

### Build for RISC-V

```bash
export PICO_TOOLCHAIN_PATH=/opt/riscv/riscv-toolchain-14/
export PICO_PLATFORM=rp2350-riscv
cmake -DPICO_BOARD=pico2 ..
```

Prebuilt RISC-V toolchains: https://github.com/raspberrypi/pico-sdk-tools/releases

### RISC-V Limitations

- No double-precision FPU (software float only)
- Some security features unavailable (TrustZone is ARM-specific)
- Must delete build directory and re-run cmake when switching architectures

## Pico 2 W Wireless

| Feature | Detail |
|---------|--------|
| Wireless chip | Infineon CYW43439, SPI at up to 33 MHz |
| Antenna | On-board, licensed from ABRACON |
| Wi-Fi | 802.11n, 2.4 GHz, WPA3, soft AP (up to 4 clients) |
| Bluetooth | BT 5.2: BLE Central + Peripheral, Classic |
| LED | Via WL_GPIO0 (not GP25) |

### SDK Libraries for Wireless

- `pico_cyw43_driver` / `pico_cyw43_arch` - Wi-Fi driver
- `pico_lwip` - TCP/IP networking
- `pico_btstack` - Bluetooth (BlueKitchen BTStack)
- `pico_mbedtls` - TLS/crypto

### Wireless Pin Sharing

The SPI CLK to CYW43439 is shared with the VSYS voltage monitor. You can only read VSYS via ADC when no SPI transaction to the wireless chip is in progress. Similarly, CYW43439 DIN/OUT and IRQ share a pin.

### Antenna Placement

Keep the antenna area free of metal. Grounded metal along the sides can improve bandwidth, but metal near or under the antenna degrades gain.

## Security Features (RP2350 Only)

RP2040 has no security features. RP2350 adds:

| Feature | Detail |
|---------|--------|
| Arm TrustZone | Secure/non-secure world isolation (Cortex-M33 only) |
| Signed boot | Boot ROM verifies binary signatures |
| Encrypted boot | AES-256 encrypted code in flash |
| OTP memory | 8 kB antifuse one-time-programmable for key storage |
| SHA-256 | Hardware acceleration (pico_sha256 SDK library) |
| TRNG | Hardware true random number generator |
| Glitch detectors | Fault injection protection |

### Secure Boot with picotool

```bash
# Sign a binary
picotool seal --sign app.elf app.signed.elf private.pem otp.json

# Encrypt a binary (self-decrypting)
picotool encrypt --embed --sign app.elf app.enc.elf aes_key.bin iv_salt.bin private.pem otp.json

# Program OTP
picotool otp load otp.json
```

### OTP Warnings

- OTP bits go from 0 to 1 and cannot be reversed. Permanent.
- Setting SECURE_BOOT_ENABLE without a boot key and with PICOBOOT disabled permanently bricks the device.
- Errata RP2350-E15: OTP permissions require running a small binary on-device. If secure boot is active, that binary must be signed. picotool handles this automatically.

## Board Layout

### SWD Debug Connector Location

| Board | Location | Type |
|-------|----------|------|
| Pico 2 | Bottom edge | Three castellated through-hole pads |
| Pico 2 with headers | Bottom edge | Keyed 3-pin JST-SH connector |
| Pico 2 W | Central, below MCU | Three through-hole pads |
| Pico 2 W with headers | Central, below MCU | Keyed 3-pin JST-SH connector |

### Power Pins (40-pin edges)

- Pin 36: 3V3(OUT)
- Pin 37: 3V3_EN (pull to GND to turn off board)
- Pin 39: VSYS
- Pin 40: VBUS
- Pin 35: ADC_VREF
- Pin 33: AGND (analogue ground)
- Pin 30: RUN (active low reset)
