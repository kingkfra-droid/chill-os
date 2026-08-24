#!/usr/bin/env python3

import os
import platform
import struct
import subprocess
from dataclasses import dataclass


@dataclass
class ArchitectureInfo:
    machine: str
    cpu_capability: str
    android_abi: str
    android_abi64: bool
    userspace: str
    userspace_bits: int
    target: str
    rootfs_target: str


def getprop(name):
    """Read an Android system property when getprop is available."""

    try:
        result = subprocess.run(
            ["getprop", name],
            capture_output=True,
            text=True,
            timeout=3,
        )

        if result.returncode == 0:
            return result.stdout.strip()

    except Exception:
        pass

    return ""


def normalize_machine(machine):
    machine = machine.lower().strip()

    mapping = {
        "aarch64": "arm64",
        "arm64": "arm64",
        "armv8": "arm64",
        "armv8l": "arm64",
        "x86_64": "amd64",
        "amd64": "amd64",
        "i386": "i386",
        "i486": "i386",
        "i586": "i386",
        "i686": "i386",
        "armv7l": "arm",
        "armv7": "arm",
        "arm": "arm",
    }

    return mapping.get(machine, machine or "unknown")


def detect_android_abi():
    abi = getprop("ro.product.cpu.abi")

    if abi:
        return abi

    abi = os.environ.get("ANDROID_ABI")

    if abi:
        return abi

    return "unknown"


def detect_android_abi64():
    """Determine whether Android exposes a 64-bit ABI."""

    supported = getprop("ro.product.cpu.abilist64")

    if supported:
        return True

    abi = detect_android_abi().lower()

    return abi in (
        "arm64-v8a",
        "x86_64",
        "mips64",
    )


def detect_cpu_capability(machine):
    """
    Determine the highest CPU capability visible to the system.

    This deliberately separates physical CPU capability from the
    currently running userspace.
    """

    machine = normalize_machine(machine)

    if machine == "arm64":
        return "64-bit"

    if machine == "amd64":
        return "64-bit"

    if machine in ("arm", "i386"):
        # Android may expose a 32-bit machine name even when the
        # underlying CPU supports 64-bit. Check Android ABI data.
        if detect_android_abi64():
            return "64-bit"

        return "32-bit"

    return "unknown"


def detect_userspace_bits():
    """Return the bitness of the currently running Python process."""

    try:
        return struct.calcsize("P") * 8
    except Exception:
        return 64 if platform.architecture()[0] == "64bit" else 32


def detect_userspace():
    bits = detect_userspace_bits()

    if bits == 64:
        return "64-bit"

    if bits == 32:
        return "32-bit"

    return "unknown"


def select_target(machine, abi, userspace_bits, cpu_capability):
    """
    Select the safest ChillOS target for the current userspace.

    ChillOS cannot directly use a 64-bit userspace when Android/Termux
    is itself restricted to 32-bit execution.
    """

    abi = abi.lower()

    if abi in ("arm64-v8a", "aarch64"):
        return "arm64"

    if abi in ("x86_64", "amd64"):
        return "amd64"

    if abi in ("armeabi-v7a", "armeabi", "arm"):
        return "arm"

    if abi in ("x86", "i386", "i686"):
        return "i386"

    if userspace_bits == 64:
        normalized = normalize_machine(machine)

        if normalized in ("arm64", "amd64"):
            return normalized

    if cpu_capability == "64-bit":
        normalized = normalize_machine(machine)

        if normalized in ("arm64", "amd64"):
            return normalized

    return normalize_machine(machine)


def select_rootfs_target(target, cpu_capability, android_abi64):
    """
    Select the RootFS architecture.

    Normally RootFS follows the executable userspace target. A 64-bit
    RootFS is only selected when the environment can actually execute it.
    """

    if target == "arm64":
        return "arm64"

    if target == "amd64":
        return "amd64"

    if target == "arm":
        return "arm"

    if target == "i386":
        return "i386"

    if android_abi64 and cpu_capability == "64-bit":
        machine = normalize_machine(platform.machine())

        if machine in ("arm64", "amd64"):
            return machine

    return target


def detect():
    """Return complete layered ChillOS architecture information."""

    machine = platform.machine()
    normalized_machine = normalize_machine(machine)

    abi = detect_android_abi()
    abi64 = detect_android_abi64()

    userspace_bits = detect_userspace_bits()
    userspace = detect_userspace()

    cpu_capability = detect_cpu_capability(machine)

    target = select_target(
        machine,
        abi,
        userspace_bits,
        cpu_capability,
    )

    rootfs_target = select_rootfs_target(
        target,
        cpu_capability,
        abi64,
    )

    return {
        "machine": machine,
        "normalized_machine": normalized_machine,
        "cpu_capability": cpu_capability,
        "android_abi": abi,
        "android_abi64": abi64,
        "userspace": userspace,
        "userspace_bits": userspace_bits,
        "target": target,
        "rootfs_target": rootfs_target,
    }


def report():
    """Display architecture information."""

    info = detect()

    print()
    print("╔════════════════════════════════════════╗")
    print("║        CHILLOS ARCHITECTURE            ║")
    print("╚════════════════════════════════════════╝")
    print()

    print(f"Physical machine : {info['machine']}")
    print(f"Normalized CPU   : {info['normalized_machine']}")
    print(f"CPU capability   : {info['cpu_capability']}")
    print(f"Android ABI      : {info['android_abi']}")
    print(
        "Android 64-bit   : "
        f"{'YES' if info['android_abi64'] else 'NO'}"
    )
    print(f"Userspace        : {info['userspace']}")
    print(f"Userspace bits   : {info['userspace_bits']}-bit")
    print(f"ChillOS target   : {info['target']}")
    print(f"RootFS target    : {info['rootfs_target']}")
    print()


if __name__ == "__main__":
    report()
