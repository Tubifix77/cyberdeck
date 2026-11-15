# Alternative 2 — Citadel Mobile
## A phone-powered cyberdeck with ESP32-S3 hardware extensions

## The idea

Instead of using an Orange Pi as the portable computer, use a smartphone as the central computing and communications hub. The phone connects to the home PC over 5G or Wi-Fi, while the ESP32-S3 connects to the phone and acts as an external hardware extension.

This creates a different kind of cyberdeck:

- **Phone:** Main portable computer, touchscreen, user interface, mobile internet, storage, sensors, and application platform.
- **ESP32-S3:** Dedicated hardware interface for physical controls, small displays, LEDs, buttons, sensors, and audio peripherals.
- **Home PC:** Heavy computing and intelligence, including Ollama, Gemma, firewall monitoring, the Citadel agent, and home services.

The Orange Pi is not part of this design. It is deliberately removed from the build.

## Proposed architecture

```text
                 HOME PC
      ┌─────────────────────────────┐
      │ Gemma / Ollama              │
      │ Citadel agent               │
      │ Firewall and monitoring     │
      │ Home services               │
      └──────────────┬──────────────┘
                     │
             WireGuard VPN
                     │
             Internet / 5G / Wi-Fi
                     │
      ┌──────────────▼──────────────┐
      │        SMARTPHONE           │
      │                             │
      │ Citadel Hub application     │
      │ Touchscreen and UI          │
      │ Mobile data / Wi-Fi         │
      │ Local processing and storage│
      │ GPS and phone capabilities  │
      └──────────────┬──────────────┘
                     │
              Bluetooth LE
                or USB-C
                     │
      ┌──────────────▼──────────────┐
      │          ESP32-S3           │
      │                             │
      │ Buttons and rotary controls │
      │ Small display / Burning Wall│
      │ Sensors and LEDs            │
      │ Microphone / speaker         │
      │ Other physical extensions   │
      └─────────────────────────────┘
```

## Why this architecture makes sense

A modern smartphone already provides many of the capabilities that the original portable Linux computer was intended to supply:

- A powerful processor and graphics hardware.
- A high-resolution touchscreen.
- 5G and Wi-Fi connectivity.
- GPS, cameras, microphones, speakers, and motion sensors.
- Battery, storage, and a mature operating system.
- An application platform for the Citadel interface.

The ESP32-S3 can focus on the things a phone does not provide as conveniently: custom physical controls, dedicated sensor inputs, small embedded displays, status lights, and purpose-built hardware.

The home PC continues to do the demanding work. The phone provides the mobile connection and user experience, while the ESP32-S3 makes the system tangible and extensible.

## Responsibilities of each component

### 1. Home PC — Citadel Core

The home PC remains the central server and intelligence provider.

It can run:

- Ollama and Gemma 3 12B.
- The Citadel AI agent.
- Firewall and intrusion monitoring.
- Network and service health monitoring.
- The home VPN endpoint.
- APIs for status, notifications, and authorised commands.

The phone should not need direct access to arbitrary server processes. It should communicate with a small, authenticated Citadel API that exposes only the operations the mobile application needs.

### 2. Smartphone — Citadel Hub

The phone becomes the main portable computer and user interface.

The Citadel Hub application can provide:

- The main Citadel dashboard.
- Burning Wall visualisation.
- Firewall and network alerts.
- Home AI chat and voice interaction.
- VPN and home-server status.
- Authorised command controls.
- Communication with one or more ESP32-S3 devices.
- Local caching of recent status when the home server is unreachable.

The phone can use mobile 5G to reach the home network through WireGuard, or use ordinary Wi-Fi when available.

The phone operating system may restrict background networking, Bluetooth activity, and long-running tasks. The application must therefore handle sleep, reconnection, permission changes, and periods when it is not running in the foreground.

### 3. ESP32-S3 — Hardware Extender

The ESP32-S3 runs dedicated firmware rather than a full desktop operating system.

Possible functions include:

- Physical buttons and rotary encoders.
- A small OLED or TFT status display.
- A miniature Burning Wall animation.
- LEDs and vibration or buzzer alerts.
- Temperature, motion, proximity, and other sensors.
- A microphone and speaker for push-to-talk audio.
- Dedicated physical controls for approved Citadel actions.

The ESP32-S3 should not run the large language model. It sends events and readings to the phone, and receives display updates or approved instructions in return.

## Communication links

Use two separate links with clearly defined responsibilities.

### Phone to home PC

Use WireGuard over 5G or Wi-Fi.

The phone establishes an encrypted tunnel to the home network and communicates with a Citadel API on the home PC. The API should authenticate requests, validate inputs, enforce permissions, and return structured responses.

The design should account for:

- Mobile IP address changes.
- Temporary loss of 5G or Wi-Fi.
- VPN reconnects and tunnel failures.
- Home internet or server outages.
- Expired credentials and revoked devices.
- API timeouts and retries.

### Phone to ESP32-S3

Start with Bluetooth Low Energy (BLE) for wireless control and status messages. USB-C can be considered when a wired connection, lower latency, or higher throughput is useful.

Define a small, versioned message protocol. For example, messages can represent:

- Device identity and capabilities.
- Button presses and encoder changes.
- Sensor readings.
- Display state and alert level.
- Battery and connection status.
- Requests for approved actions.

Pairing should be deliberate. Authenticate the device, protect sensitive messages, and avoid treating any nearby Bluetooth device as trusted.

## Example ESP32-S3 extensions

### Control panel

A small display, buttons, and rotary encoder can provide:

- IDLE, WATCHING, BLOCKED, and STORM status.
- Firewall alert summaries.
- VPN and home-server status.
- Menu navigation and alert acknowledgement.
- Physical confirmation for sensitive operations.

### Voice module

A microphone, speaker, and push-to-talk button can provide a simple voice interface. The phone can relay audio or recognised commands to the home AI, depending on the phone application and available libraries.

The home PC performs the large-model inference. The ESP32-S3 handles the physical audio interface and lightweight processing.

### Sensor module

An ESP32-S3 can collect readings from attached sensors and forward them to the phone. The phone can then send relevant events to the home PC for logging, notification, or analysis.

### Command module

Dedicated physical controls can trigger narrowly defined actions, such as acknowledging an alert or requesting a status report. High-impact operations should require explicit confirmation on the phone and server-side authorisation.

## Security model

The phone acts as the gateway, but it should not be an unrestricted command relay.

Recommended rules:

- Pair and authenticate each ESP32 device.
- Use WireGuard for the phone-to-home network connection.
- Expose a small authenticated API rather than unrestricted shell access.
- Validate every command on the home PC.
- Use an allowlist of structured actions.
- Require confirmation for sensitive or disruptive operations.
- Keep credentials out of firmware source, logs, and the repository.
- Support device revocation and credential rotation.
- Use secure boot, flash encryption, and signed/secure OTA updates where supported by the selected ESP32-S3 module and firmware configuration.
- Fail safely when the phone, VPN, or home server is unavailable.

The original Citadel security principle remains: model output and device messages must never become unrestricted shell commands.

## Development roadmap

### A. Citadel Hub

- Choose the phone platform and application technology.
- Build the basic mobile dashboard.
- Define the Citadel API on the home PC.
- Establish WireGuard connectivity.
- Display server, VPN, and firewall status.
- Handle network loss and reconnection.

### B. Citadel Link

- Connect the ESP32-S3 to the phone over BLE.
- Define a versioned message protocol.
- Implement pairing and device authentication.
- Exchange basic status and button events.
- Test disconnect, reconnect, and low-power behaviour.

### C. Citadel Display

- Identify the display already fitted to the ESP32-S3 board, if any.
- Render IDLE, WATCHING, BLOCKED, and STORM states.
- Create a small Burning Wall-inspired animation appropriate to the display and available memory.
- Keep display rendering independent from the home-server API.

### D. Citadel Controls

- Add buttons and a rotary encoder.
- Implement menu navigation and alert acknowledgement.
- Add confirmation for sensitive actions.
- Introduce sensors or audio peripherals only when the core link is reliable.

### E. Citadel Intelligence

- Connect the phone interface to the home AI.
- Add chat and, if practical, push-to-talk voice interaction.
- Send structured monitoring summaries to the phone.
- Cache recent status and explain clearly when information is stale or unavailable.

### F. Citadel Portable

- Design a practical enclosure and mounting arrangement.
- Plan battery power for the ESP32-S3 and any attached display or peripherals.
- Add sleep and wake behaviour.
- Test BLE range, reconnection, and phone background restrictions.
- Consider additional ESP32 modules as independent, authenticated extensions.

## What this design does not require

- No Orange Pi.
- No Linux desktop running on the ESP32-S3.
- No Ollama or Gemma running on the ESP32-S3.
- No requirement to replace the home PC.
- No need to buy every peripheral before the first prototype.

The exact phone platform and ESP32-S3 board determine some implementation details. In particular, the board's display, PSRAM, audio hardware, and USB capabilities should be checked before choosing libraries or designing the enclosure.

## First prototype

Keep the first version deliberately small:

1. Run a simple Citadel status API on the home PC.
2. Connect the phone to the home PC using WireGuard.
3. Display home-server and firewall status in a basic phone interface.
4. Connect the ESP32-S3 to the phone over BLE.
5. Send one button event from the ESP32-S3 to the phone.
6. Show a status change on the ESP32-S3 display, if the board has one.

Once this works reliably, add controls, alerts, voice, sensors, and enclosure design incrementally.

## Bottom line

**Citadel Mobile = Home PC + Smartphone + ESP32-S3.**

The home PC supplies intelligence and services. The smartphone supplies mobile computing, the screen, and 5G connectivity. The ESP32-S3 supplies custom physical controls, sensors, and embedded displays.

This is a standalone direction for The Citadel, not a temporary substitute for an Orange Pi. It preserves the project's security and visual identity while making use of hardware already available.
