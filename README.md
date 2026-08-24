# 🧊 ChillOS

Linux environment for Android — built for the terminal.

ChillOS is a lightweight Linux environment for Android, built around a modular userspace, Debian-based root filesystem, PRoot, package management, diagnostics, system detection, developer tooling, and an evolving capability-based architecture.

## Project Status

Version: 0.1.0

ChillOS is actively under development.

## CLI

    chill doctor
    chill start
    chill status
    chill system
    chill version
    chill get <package>
    chill tool search <query>
    chill tool info <package>
    chill tool update
    chill tool remove <package>
    chill rootfs build
    chill rootfs status

## Diagnostics

`chill doctor` checks CPU architecture, Android ABI, Python, Termux, storage, network availability, and required tools including python, git, proot, proot-distro, curl, wget, tar, and xz.

Run:

    chill doctor

## Environment

ChillOS uses:

    ~/.chillos

The environment can contain:

    ~/.chillos/home
    ~/.chillos/etc
    ~/.chillos/var
    ~/.chillos/tmp
    ~/.chillos/packages
    ~/.chillos/workspace

ChillOS sessions expose:

    CHILLOS_HOME
    CHILLOS_ACTIVE

## System Information

Use:

    chill system

ChillOS detects CPU architecture, Android ABI, 64-bit ABI capability, userspace bitness, kernel information, Python information, and Termux.

Supported target architectures include:

    arm64
    amd64
    arm
    i386

## Root Filesystem

ChillOS currently uses a Debian 13 root filesystem with PRoot.

Build it with:

    chill rootfs build

Check it with:

    chill rootfs status

The rootfs system detects the appropriate architecture, checks required PRoot tooling, detects an existing Debian environment, and installs/configures it when necessary.

## Package Management

ChillOS uses Debian APT through the PRoot environment.

Install:

    chill get <package>

Search:

    chill tool search <query>

Package information:

    chill tool info <package>

Update package metadata:

    chill tool update

Remove:

    chill tool remove <package>

## Tool Catalogue

The ChillOS catalogue organizes tools into:

    Network
    Wireless
    Information Gathering
    Web
    OSINT
    Forensics
    Development
    System
    Security

Tool availability depends on Debian repositories, architecture, Android restrictions, permissions, and hardware support.

## GUI and Capability Architecture

The repository also contains an evolving GUI and capability subsystem covering:

    Capabilities
    Hardware
    Modules
    Profiles
    Server
    Terminal
    Tools
    System
    Network

These components are part of the development architecture. They are not currently exposed as a top-level `chill gui` command.

## Security

ChillOS does not automatically provide Android root access.

Actual capabilities depend on Android security, Termux permissions, kernel capabilities, filesystem permissions, hardware, architecture, and whether the device is rooted.

A PRoot Linux environment is not the same thing as Android root.

## Development

Clone the project:

    git clone https://github.com/kingkfra-droid/chill-os.git

Enter it:

    cd chill-os

Run ChillOS:

    python3 main.py

Run diagnostics:

    python3 main.py doctor

Check the system:

    python3 main.py system

Check the version:

    python3 main.py --version

## Contributing

Contributions are welcome from Linux developers, Android developers, Python developers, security researchers, network engineers, terminal enthusiasts, GUI developers, testers, and documentation contributors.

Useful contributions include code, bug fixes, testing, documentation, rootfs development, Android compatibility, package tooling, architecture detection, GUI development, capability modules, security improvements, and performance improvements.

## Troubleshooting

Start with:

    chill doctor

Check the system:

    chill system

Check the root filesystem:

    chill rootfs status

Update package metadata:

    chill tool update

If `chill` is unavailable, run:

    python3 main.py

## Vision

The goal of ChillOS is to build a practical, modular Linux environment that can live, grow, and evolve on Android.

Android → Environment Detection → Capability Detection → ChillOS Core → Debian RootFS → Packages → Tools → Terminal → GUI

## Repository

https://github.com/kingkfra-droid/chill-os

---

ChillOS 0.1.0

Linux on Android.
Stay chill. Build hard. 🧊
