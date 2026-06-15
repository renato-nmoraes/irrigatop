# PlatformIO CLI Guide

Working with the IrrigaTOP firmware from the command line. Cursor has no working
PlatformIO extension (it's on the VSCode Marketplace, not Open VSX), so the CLI
is the reliable path. Use VSCode if you want the GUI debugger.

## Project specifics

From `platformio.ini`:

| Setting        | Value                              |
|----------------|------------------------------------|
| Environment    | `esp32doit-devkit-v1`              |
| Board          | ESP32 DOIT DevKit v1               |
| Framework      | Arduino                            |
| Serial speed   | `115200`                           |
| Web assets     | served from **SPIFFS** (`data/`)   |

The `data/` folder (`index.html`, `style.css`) is the on-device fallback web
page and lives in a **separate flash partition** — it is NOT included in a normal
firmware upload. See [Web assets / SPIFFS](#web-assets--spiffs).

## Install

Pick one (CLI only, no editor extension needed):

```bash
# pipx (recommended — isolated)
pipx install platformio

# pip
pip install --user platformio

# Homebrew
brew install platformio

# official installer script
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core-installer/master/get-platformio.py)"
```

Verify: `pio --version`. If `pio` isn't on PATH after pip, it's usually in
`~/.local/bin` (pip) or `~/.platformio/penv/bin` (script installer).

No install? See [Run via Docker](#run-via-docker-no-local-install).

## Everyday commands

Run from the repo root. The single env means you rarely need `-e`.

| Command | What it does |
|---------|--------------|
| `pio run` | Compile firmware |
| `pio run -t upload` | Compile + flash firmware over USB |
| `pio run -t uploadfs` | Build + flash the `data/` SPIFFS image (web assets) |
| `pio device monitor` | Open serial monitor (115200) |
| `pio run -t upload && pio device monitor` | Flash then watch serial |
| `pio run -t clean` | Remove build artifacts (`.pio/`) |
| `pio run -t erase` | Full chip erase (wipes flash incl. SPIFFS + WiFi NVS) |
| `pio device list` | List connected serial ports |
| `pio pkg list` | Show installed library dependencies |
| `pio pkg update` | Update libraries / platform |
| `pio pkg outdated` | Show what's out of date |

### Picking the serial port

PlatformIO usually auto-detects. To be explicit:

```bash
pio run -t upload --upload-port /dev/ttyUSB0
pio device monitor --port /dev/ttyUSB0 --baud 115200
```

Find the port with `pio device list` (Linux: typically `/dev/ttyUSB0`).
If upload fails to connect, hold the **BOOT** button while it starts uploading.

## Serial monitor

- Exit the monitor with **Ctrl+C**.
- Decode crash/reboot backtraces into file:line (very useful for the watchdog
  work) by adding this to `platformio.ini` under the env:

  ```ini
  monitor_filters = esp32_exception_decoder, time
  ```

  `time` prefixes each line with a timestamp; `esp32_exception_decoder` turns a
  panic/`Guru Meditation`/watchdog backtrace into readable source locations.

## Web assets / SPIFFS

The web UI fallback in `data/` is flashed **separately** from the firmware:

```bash
pio run -t uploadfs     # after editing anything in data/
```

`pio run -t upload` does NOT touch SPIFFS. If you change `data/index.html` or
`data/style.css`, you must run `uploadfs` or the device keeps serving the old
page. (Note: the primary UI is the Flask `web/` app; `data/` is only the
on-device page.)

## Debugging (breakpoints)

`pio debug` exists, but the **DevKit v1 has no built-in USB-JTAG**, so step
debugging requires an external **JTAG probe** (e.g. ESP-Prog / FT2232) wired to
the JTAG pins, plus `debug_tool = esp-prog` in `platformio.ini`. Without a probe,
use serial logging + the exception decoder above.

## Run via Docker (no local install)

Build without installing anything locally (this is how CI / a clean machine can
verify the firmware compiles). `git` is needed because `lib_deps` are git URLs;
the cache volume makes repeat runs fast:

```bash
docker run --rm \
  -v "$PWD":/workspace -w /workspace \
  -v /tmp/pio-cache:/root/.platformio \
  python:3.11-slim bash -c \
  "apt-get update -qq && apt-get install -y -qq git && pip install -q platformio && pio run"
```

Flashing/monitoring over USB from a container needs device passthrough
(`--device=/dev/ttyUSB0`) and is usually more trouble than a local install — use
Docker for **compile checks**, local `pio` for **flashing**.

## Typical loop

```bash
pio run                       # does it build?
pio run -t upload             # flash it
pio device monitor            # watch it boot (Ctrl+C to quit)
# edited data/ ? also:
pio run -t uploadfs
```
