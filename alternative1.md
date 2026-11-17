# Alternative 1 — Build the Citadel Before the Hardware Arrives

## The idea

A substantial part of Cyberdeck / The Citadel can be developed and tested before the Orange Pi 5 Plus and AR glasses arrive.

The goal is to make the first hardware session an integration exercise rather than the beginning of the software project. We can build the application, services, interfaces, simulation tools, and most of the operating environment on an ordinary Linux development machine.

There is one important distinction: **an ARM64 system can be simulated, but an Orange Pi 5 Plus is more than an ARM64 CPU.** Generic ARM64 emulation does not reproduce the RK3588's NPU, Mali GPU, GPIO electrical behaviour, power characteristics, or the exact USB-C DisplayPort behaviour of the glasses.

## What we can complete before buying or receiving hardware

### Priority 1 — Harden the agent

The agent must not be able to turn untrusted model output into unrestricted shell execution.

Work to do:

- Remove shell-based execution of LLM-generated commands, especially calls using `subprocess.run(..., shell=True)`.
- Replace free-form command execution with a small, explicit allowlist of structured actions.
- Validate arguments and reject unknown commands.
- Keep privileges as low as possible; use narrowly scoped permissions for any operation that genuinely needs elevation.
- Add tests for malicious input, malformed arguments, and rejected commands.

This is the most important security task because the agent is part of the system's control surface.

### Priority 2 — Make wall monitoring report errors honestly

The wall watcher should never silently turn a monitoring failure into an apparently calm system.

Work to do:

- Check how the service reads journal data and handles permissions, including its use of `sudo journalctl`.
- Capture and report command failures, missing permissions, timeouts, and malformed data.
- Distinguish a genuinely idle system from a monitor that cannot read its data.
- Add an explicit `UNKNOWN` or error state rather than defaulting to `IDLE`.
- Log useful diagnostic information without exposing secrets.

### Priority 3 — Detect stale status

The visual wall should know whether its status information is current.

Work to do:

- Add a timestamp or heartbeat to `wall_status.json`.
- Have the overlay check the age of the last update.
- Show a clear `STALE` or `UNKNOWN` state if the watcher stops updating or the status file is too old.
- Handle missing, empty, malformed, and unreadable status files safely.
- Test recovery when the watcher restarts.

This prevents an old “all clear” display from remaining on screen after the monitoring service has crashed.

### Priority 4 — Add tests, dependencies, and continuous integration

Make the project repeatable to install and safer to change.

Work to do:

- Add a dependency manifest, such as `requirements.txt` or `pyproject.toml`.
- Add a pytest test suite for the agent, wall watcher, status format, and failure cases.
- Add GitHub Actions to run tests and basic checks on each push and pull request.
- Keep hardware-dependent tests separate from tests that can run on any Linux machine.
- Document setup, configuration, service operation, and troubleshooting.

## Can we simulate the Orange Pi?

**Yes, to a useful extent.** We can use QEMU to run an ARM64 Linux environment and exercise much of the software stack there. We can also build mock hardware interfaces so that the rest of the application can be developed without physical components.

QEMU and mocks can help test:

- ARM64 Linux userspace compatibility.
- Python services and their startup behaviour.
- systemd units, service dependencies, restart policies, and recovery.
- Network events, firewall state changes, and WireGuard disconnect/reconnect handling.
- Simulated GPIO events, such as a kill-switch input.
- Simulated battery and device status.
- Display connected/disconnected events and display-profile changes.
- Installation and configuration scripts.
- The full application flow using simulated events.

However, QEMU does **not** make a generic ARM64 VM equivalent to the Orange Pi 5 Plus. It does not validate the RK3588 NPU, real NPU inference runtimes, Mali GPU performance, board-specific drivers, physical GPIO behaviour, thermal limits, or actual power consumption.

The right approach is to define hardware-independent interfaces and provide two implementations:

1. **Simulation implementation:** predictable fake devices and events for development and automated tests.
2. **Hardware implementation:** real board, GPIO, battery, display, and accelerator integrations, added and validated when the hardware is available.

A command such as `citadel --simulate` could start the system with simulated inputs and make it possible to demonstrate and test the whole experience on a normal PC.

## What about the AR glasses?

A lot of the software surrounding the glasses can also be developed on a normal Linux monitor.

Before the glasses arrive, we can work on:

- A 1920×1080 display profile and layout.
- Sway workspace and window-management behaviour.
- Waybar configuration and status indicators.
- Font sizes, scaling, and readable interface layouts.
- The transparent overlay and Burning Wall visualisation.
- Keyboard navigation and interaction flows.
- Simulated display hot-plug events and switching between display profiles.
- Recovery when a display disappears or changes resolution.

The physical integration still needs the real board and glasses. In particular, we must test USB-C DisplayPort compatibility, display detection, resolution and refresh behaviour, power delivery, cable/adapter requirements, and the actual comfort and readability of the image.

So the glasses are a genuine hardware validation hurdle, but they do not prevent us from building most of the interface beforehand.

## Proposed development milestones

### A. Harden the core

- Secure the agent command interface.
- Make watcher errors explicit.
- Add status heartbeats and stale-state handling.
- Add logging, dependency declarations, and automated tests.

### B. Build the operating environment

- Define the target Linux environment.
- Configure Sway and Waybar.
- Add systemd services, startup ordering, restart policies, and health checks.
- Create installation and configuration scripts.
- Test boot and service behaviour in a VM where practical.

### C. Complete the intelligence and connectivity layer

- Introduce a backend abstraction for local and home-hosted AI.
- Make it possible to switch between real and mock AI backends.
- Test offline behaviour and network loss.
- Improve WireGuard reconnect handling and define what should happen when the tunnel is unavailable.
- Keep secrets and credentials out of source control and logs.

### D. Finish the interface

- Refine the Burning Wall overlay and status transitions.
- Add keyboard-first interaction and workspace behaviour.
- Implement display profiles and simulated hot-plug handling.
- Ensure that monitoring failures are visually distinct from a quiet system.

### E. Build the virtual hardware test environment

- Run the software in an ARM64 Linux environment under QEMU.
- Provide mock GPIO, battery, network, display, and accelerator interfaces.
- Simulate attacks, VPN failures, AI requests, device events, and service crashes.
- Exercise installer, restart, and recovery paths.
- Run hardware-independent tests in GitHub Actions.

### F. Integrate with physical hardware

When the Orange Pi 5 Plus and glasses are available:

- Validate the board's Linux image, drivers, and peripherals.
- Bring up the real display connection and test the glasses.
- Validate RK3588 NPU software and inference performance.
- Measure GPU performance, thermals, and power consumption.
- Replace mock hardware interfaces with real implementations one at a time.
- Run end-to-end tests on the complete portable system.

## Recommended project structure

Keep the application logic independent of the physical board. A possible direction is:

```text
cyberdeck/
├── agent/
│   ├── command_dispatch.py
│   └── backends/
├── monitoring/
│   ├── wall_watcher.py
│   └── status.py
├── hardware/
│   ├── interfaces.py
│   ├── simulated/
│   └── orange_pi/
├── display/
│   ├── profiles/
│   └── overlay/
├── services/
├── tests/
├── scripts/
├── wall_overlay/
└── pyproject.toml
```

This is a proposed direction, not a requirement to reorganise everything at once. The important principle is to keep core behaviour testable without requiring the board.

## Definition of “hardware-ready”

Before the physical kit arrives, a useful target is:

- The agent uses safe, allowlisted actions rather than unrestricted shell commands.
- Monitoring distinguishes idle, active, stale, and error states.
- The overlay reacts correctly to status changes and missing data.
- Tests and CI run reliably.
- Services can start, fail, restart, and recover predictably.
- AI backends and hardware interfaces can be replaced by mocks.
- The application can run in a normal Linux environment and in an ARM64 VM.
- The interface can be exercised on a standard monitor with simulated display events.
- Setup and troubleshooting instructions are documented.

The remaining work should then be concentrated on board-specific drivers, NPU acceleration, physical display connectivity, power, thermals, and real-world usability.

## Development strategy

Work on a separate branch for this pre-hardware development so the existing working version remains intact. Implement and test the changes in small steps, then merge them when they are stable.

**Bottom line:** a great deal of The Citadel can be built before the hardware arrives. We can develop the core, security, monitoring, services, networking behaviour, interface, installation process, and much of the ARM64 software path now. The Orange Pi's specialised hardware and the real AR-glasses connection must still be validated physically, but they do not need to hold up the rest of the project.
