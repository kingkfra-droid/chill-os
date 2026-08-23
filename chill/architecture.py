#!/usr/bin/env python3

import os
import platform
import subprocess


def getprop(name):
    try:
        result = subprocess.run(
            ["getprop", name],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def cpu_info():
    try:
        with open("/proc/cpuinfo", "r", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def detect():
    machine = platform.machine().lower()
    cpu = cpu_info()

    abi = getprop("ro.product.cpu.abi")
    abi64 = getprop("ro.product.cpu.abilist64")
    abilist = getprop("ro.product.cpu.abilist")

    # Determine physical CPU capability.
    is_armv8 = (
        "aarch64" in cpu.lower()
        or "armv8" in cpu.lower()
        or "architecture: 8" in cpu.lower()
    )

    cpu_capability = "64-bit" if is_armv8 else "32-bit"

    # Determine the ABI Android actually exposes.
    if abi64:
        userspace = "64-bit"
    elif abi in ("armeabi-v7a", "armeabi"):
        userspace = "32-bit"
    elif "64" in machine:
        userspace = "64-bit"
    else:
        userspace = "32-bit"

    # Determine ChillOS target.
    if userspace == "64-bit":
        if "aarch64" in machine or "arm64" in abi64 or "arm64" in abi:
            target = "arm64"
        elif "x86_64" in machine or "x86_64" in abi64:
            target = "amd64"
        else:
            target = "unknown"
    else:
        if (
            "arm" in machine
            or abi.startswith("armeabi")
            or "ARMv8" in cpu
        ):
            target = "arm"
        elif "x86" in machine:
            target = "i386"
        else:
            target = "unknown"

    return {
        "machine": machine,
        "cpu_capability": cpu_capability,
        "android_abi": abi or "unknown",
        "android_abi64": abi64 or "unavailable",
        "android_abilist": abilist or "unknown",
        "userspace": userspace,
        "target": target,
    }


def print_info():
    info = detect()

    print()
    print("CHILLOS ARCHITECTURE")
    print("=" * 40)
    print(f"CPU architecture : {info['machine']}")
    print(f"CPU capability   : {info['cpu_capability']}")
    print(f"Android ABI      : {info['android_abi']}")
    print(f"64-bit ABI       : {info['android_abi64']}")
    print(f"Userspace        : {info['userspace']}")
    print(f"ChillOS target   : {info['target']}")
    print()


if __name__ == "__main__":
    print_info()
