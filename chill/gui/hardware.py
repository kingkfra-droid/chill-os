#!/usr/bin/env python3

import os
import platform


def exists(path):
    return os.path.exists(path)


def network_interfaces():
    path = "/sys/class/net"

    if not os.path.isdir(path):
        return []

    try:
        return sorted(os.listdir(path))
    except Exception:
        return []


def hardware_info():
    return {
        "machine": platform.machine(),
        "usb": exists("/dev/bus/usb"),
        "input": exists("/dev/input"),
        "network": exists("/sys/class/net"),
        "sysfs": exists("/sys"),
        "proc": exists("/proc"),
        "thermal": exists("/sys/class/thermal"),
        "interfaces": network_interfaces()
    }
