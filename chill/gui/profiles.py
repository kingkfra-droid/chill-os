#!/usr/bin/env python3

from .capabilities import capabilities


PROFILES = {
    "mobile": {
        "name": "Mobile",
        "description": "Lightweight Linux environment for Android.",
        "packages": [
            "git",
            "python3",
            "curl",
            "wget"
        ]
    },

    "network": {
        "name": "Network",
        "description": "Network diagnostics and administration.",
        "packages": [
            "iproute2",
            "iputils-ping",
            "dnsutils",
            "net-tools"
        ]
    },

    "developer": {
        "name": "Developer",
        "description": "Linux development environment.",
        "packages": [
            "git",
            "python3",
            "python3-pip",
            "build-essential"
        ]
    },

    "security": {
        "name": "Security",
        "description": "Defensive security and system-analysis environment.",
        "packages": [
            "nmap",
            "tcpdump",
            "netcat-openbsd"
        ]
    }
}


def profiles():
    return PROFILES


def get_profile(name):
    return PROFILES.get(name)


def profile_names():
    return list(PROFILES.keys())


def recommend_profile():
    caps = capabilities()

    available = {
        name
        for name, data in caps.items()
        if data["state"] == "available"
    }

    if "network" in available:
        return {
            "profile": "network",
            "reason": "Network subsystem is available."
        }

    if "python" in available and "git" in available:
        return {
            "profile": "developer",
            "reason": "Python and Git are available."
        }

    return {
        "profile": "mobile",
        "reason": "Using the lightweight mobile profile."
    }
