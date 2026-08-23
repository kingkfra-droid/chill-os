#!/usr/bin/env python3

import shutil
import subprocess


CATEGORIES = {
    "network": [
        "nmap",
        "iproute2",
        "iputils-ping",
        "dnsutils",
        "net-tools",
        "tcpdump"
    ],

    "development": [
        "git",
        "python3",
        "python3-pip",
        "build-essential"
    ],

    "diagnostics": [
        "htop",
        "lsof",
        "procps",
        "strace"
    ],

    "web": [
        "curl",
        "wget"
    ],

    "system": [
        "coreutils",
        "util-linux",
        "psmisc"
    ]
}


def proot_available():
    return shutil.which("proot-distro") is not None


def run_debian(command, timeout=120):

    if not proot_available():
        return {
            "code": 1,
            "output": "proot-distro is not installed."
        }

    try:
        result = subprocess.run(
            [
                "proot-distro",
                "login",
                "debian",
                "--"
            ] + command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "code": result.returncode,
            "output": result.stdout + result.stderr
        }

    except Exception as exc:
        return {
            "code": 1,
            "output": str(exc)
        }


def search_tool(query):

    if not query:
        return {
            "code": 1,
            "output": "No search query."
        }

    return run_debian([
        "apt-cache",
        "search",
        query
    ])


def install_tool(package):

    if not package:
        return {
            "code": 1,
            "output": "No package specified."
        }

    return run_debian(
        [
            "apt-get",
            "install",
            "-y",
            package
        ],
        timeout=300
    )


def update_tools():

    return run_debian(
        [
            "apt-get",
            "update"
        ],
        timeout=300
    )


def remove_tool(package):

    if not package:
        return {
            "code": 1,
            "output": "No package specified."
        }

    return run_debian([
        "apt-get",
        "remove",
        "-y",
        package
    ])


def categories():
    return CATEGORIES


def category(name):

    return CATEGORIES.get(
        name,
        []
    )
