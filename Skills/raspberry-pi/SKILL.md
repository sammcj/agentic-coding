---
name: raspberry-pi-pico2
description: >
  Use when developing with Raspberry Pi Pico 2 or the Pi Debug Probe.
allowed-tools: Bash Read Write Edit Grep Glob Agent
---

# Raspberry Pi Pico 2 and Debug Probe

This skill covers development with Raspberry Pi Pico 2 (RP2350) boards and the Raspberry Pi Debug Probe. It includes hardware specs, SDK setup, build configuration, debugging workflows, and common pitfalls.

## Reference Files

Consult these for detailed technical content. Read only the file relevant to the current task:

- `references/pico2-hardware.md` - RP2350 specs, RP2040 vs RP2350 comparison, pin layout, wireless variant, security features, chip variants
- `references/debug-probe.md` - Debug Probe hardware, wiring diagrams, OpenOCD setup, GDB workflow, UART serial, RTT, VS Code integration, rescue mode, troubleshooting
- `references/sdk-toolchain.md` - pico-sdk setup, CMake configuration, ARM vs RISC-V builds, picotool commands, MicroPython/CircuitPython, project structure

## Quick Reference

### Board Selection (CMake)

| Board | CMake Flag | Platform |
|-------|-----------|----------|
| Pico 1 | `-DPICO_BOARD=pico` (default) | rp2040 |
| Pico 1 W | `-DPICO_BOARD=pico_w` | rp2040 |
| Pico 2 | `-DPICO_BOARD=pico2` | rp2350-arm-s |
| Pico 2 W | `-DPICO_BOARD=pico2_w` | rp2350-arm-s |
| Pico 2 RISC-V | `-DPICO_BOARD=pico2 -DPICO_PLATFORM=rp2350-riscv` | rp2350-riscv |

### Debug Probe Wiring (SWD)

| Debug Probe "D" Pin | Wire Colour | Pico 2 SWD Pad |
|---------------------|-------------|-----------------|
| SC | Orange | SWCLK |
| GND | Black | GND |
| SD | Yellow | SWDIO |

### Debug Probe Wiring (UART)

| Debug Probe "U" Pin | Wire Colour | Pico 2 Pin | GPIO |
|---------------------|-------------|------------|------|
| TX | Orange | Pin 2 | GP1 (RX) |
| RX | Yellow | Pin 1 | GP0 (TX) |
| GND | Black | Pin 3 | GND |

Note the crossover: probe TX to Pico RX, probe RX to Pico TX.

### OpenOCD Target Configs

| Target | Config File |
|--------|------------|
| Pico 1 (RP2040) | `target/rp2040.cfg` |
| Pico 2 (RP2350) | `target/rp2350.cfg` |
| Pico 2 RISC-V | `target/rp2350.cfg` with `-c "set USE_CORE { rv0 rv1 }"` |
| Rescue (RP2350) | `target/rp2350.cfg` with `-c "set RESCUE 1"` |

### Typical Debug Session

```bash
# Terminal 1: OpenOCD
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000"

# Terminal 2: GDB
arm-none-eabi-gdb my_app.elf
(gdb) target remote localhost:3333
(gdb) monitor reset init
(gdb) load
(gdb) break main
(gdb) continue
```

### Flash via SWD

```bash
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg \
  -c "adapter speed 5000" \
  -c "program my_app.elf verify reset exit"
```

Use the `.elf` file for SWD flashing, not `.uf2`.

## Gotchas

These are the most common mistakes and non-obvious behaviours. Pay close attention.

1. **SDK defaults to Pico 1.** You must explicitly pass `-DPICO_BOARD=pico2` to target RP2350. Forgetting this builds for RP2040 and the binary will not run on a Pico 2.

2. **Use the Raspberry Pi fork of OpenOCD.** Upstream OpenOCD (0.12.0) lacks full RP2350 support. Clone from `https://github.com/raspberrypi/openocd.git` branch `rpi-common`.

3. **Wrong target config = failed connection.** Using `rp2040.cfg` with a Pico 2 silently fails. Always match the target config to the chip.

4. **SWD uses .elf, BOOTSEL uses .uf2.** These are different formats for different flashing methods. Do not try to flash a .uf2 via OpenOCD/SWD.

5. **Debug builds required for meaningful debugging.** Always pass `-DCMAKE_BUILD_TYPE=Debug` to cmake. Release builds optimise away variable state and reorder code, making breakpoints unreliable.

6. **RISC-V mode has no FPU.** The hardware floating-point unit is only available on Cortex-M33. RISC-V mode uses software float, which is significantly slower for float-heavy code.

7. **RISC-V requires a clean build directory.** When switching between ARM and RISC-V, delete the build directory and re-run cmake. In-place switching does not work.

8. **RISC-V debugging requires pre-selection.** The RP2350 boots into Cortex-M33 by default. To debug RISC-V: `picotool reboot -u -c riscv`, then use OpenOCD with `set USE_CORE { rv0 rv1 }`.

9. **Debug Probe does not power the target.** The Pico 2 must be powered via its own USB or VSYS. The SWD connector carries no power.

10. **LED pin differs on wireless models.** Non-wireless Pico 2 uses GP25 for the onboard LED. Pico 2 W uses WL_GPIO0 through the CYW43439 wireless chip. Code must be conditional.

11. **Git submodules are required.** The pico-sdk needs `git submodule update --init` to pull tinyusb, cyw43-driver, lwip, btstack, and mbedtls. Missing submodules cause cryptic build failures.

12. **OTP is irreversible.** Writing OTP bits is permanent. Misconfiguring secure boot (setting `SECURE_BOOT_ENABLE` without a boot key and with PICOBOOT disabled) permanently bricks the device.

13. **Wireless SPI pin sharing.** On Pico 2 W, the VSYS ADC reading and CYW43439 IRQ checking are blocked during SPI transactions to the wireless chip.

14. **Connect GND first.** When the Pico 2 is powered from a separate source, connect GND between the target and Debug Probe before any signal lines. Voltage differences can damage the probe.

15. **macOS: OpenOCD needs hidapi and libusb.** Install via `brew install hidapi libusb`. If OpenOCD cannot find the probe, check no other process (VS Code, another OpenOCD instance) holds the USB device.

16. **Multiple debug probes.** If multiple CMSIS-DAP devices are connected, specify the serial number: `adapter serial <serial_number>` in your OpenOCD config.
