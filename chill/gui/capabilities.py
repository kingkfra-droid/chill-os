#!/usr/bin/env python3

import os
import shutil

from .hardware import hardware_info


def state(available, reason=""):
    if available:
        return {
            "state": "available",
            "reason": reason
        }

    return {
        "state": "unavailable",
        "reason": reason
    }


def capabilities():
    hw = hardware_info()

    proot = shutil.which("proot-distro") is not None
    python = shutil.which("python") is not None
    git = shutil.which("git") is not None

    usb = hw["usb"]
    input_devices = hw["input"]
    network = hw["network"]

    return {
        "linux_userspace": state(
            True,
            "ChillOS Linux userspace is active"
        ),

        "proot": state(
            proot,
            "proot-distro detected"
            if proot else
            "proot-distro not installed"
        ),

        "python": state(
            python,
            "Python runtime detected"
            if python else
            "Python not detected"
        ),

        "git": state(
            git,
            "Git detected"
            if git else
            "Git not detected"
        ),

        "network": state(
            network,
            "Network subsystem visible"
            if network else
            "Network subsystem not visible"
        ),

        "usb": state(
            usb,
            "USB device tree visible"
            if usb else
            "Android/Termux does not expose USB devices"
        ),

        "input": state(
            input_devices,
            "Input devices visible"
            if input_devices else
            "Android/Termux does not expose /dev/input"
        ),

        "sysfs": state(
            hw["sysfs"],
            "/sys is available"
            if hw["sysfs"] else
            "/sys is unavailable"
        ),

        "proc": state(
            hw["proc"],
            "/proc is available"
            if hw["proc"] else
            "/proc is unavailable"
        ),

        "thermal": state(
            hw["thermal"],
            "Thermal subsystem visible"
            if hw["thermal"] else
            "Thermal subsystem unavailable"
        ),

        "root": state(
            os.geteuid() == 0,
            "Running as root"
            if os.geteuid() == 0 else
            "Running without root privileges"
        )
    }


def available():
    result = capabilities()

    return [
        name
        for name, data in result.items()
        if data["state"] == "available"
    ]


def unavailable():
    result = capabilities()

    return [
        name
        for name, data in result.items()
        if data["state"] == "unavailable"
    ]
