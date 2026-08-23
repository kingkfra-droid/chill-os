#!/usr/bin/env python3
import shutil
import time

import json
import re
import socket
import subprocess
from pathlib import Path


def run_command(command, timeout=3):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }

    except Exception as exc:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(exc),
            "returncode": -1
        }


def interfaces():

    result = []

    root = Path("/sys/class/net")

    try:
        entries = sorted(root.iterdir())
    except (PermissionError, FileNotFoundError, OSError):
        return result

    for item in entries:

        name = item.name

        state = "unknown"

        try:
            state = (
                item / "operstate"
            ).read_text().strip()
        except (PermissionError, FileNotFoundError, OSError):
            pass

        mac = None

        try:
            mac = (
                item / "address"
            ).read_text().strip()
        except (PermissionError, FileNotFoundError, OSError):
            pass

        result.append({
            "name": name,
            "state": state,
            "mac": mac
        })

    return result


def interface_stats():

    result = {}

    root = Path("/sys/class/net")

    try:
        entries = list(root.iterdir())
    except (PermissionError, FileNotFoundError, OSError):
        return result

    fields = [
        "rx_bytes",
        "rx_packets",
        "rx_errors",
        "rx_dropped",
        "tx_bytes",
        "tx_packets",
        "tx_errors",
        "tx_dropped"
    ]

    for item in entries:

        name = item.name
        statistics = item / "statistics"

        data = {}

        for field in fields:

            try:
                data[field] = int(
                    (statistics / field)
                    .read_text()
                    .strip()
                )
            except (
                PermissionError,
                FileNotFoundError,
                OSError,
                ValueError
            ):
                data[field] = None

        result[name] = data

    return result


def addresses():

    result = []

    command = run_command(
        ["ip", "-j", "addr"]
    )

    if not command["ok"]:
        return result

    try:
        data = json.loads(
            command["stdout"]
        )
    except Exception:
        return result

    for interface in data:

        name = interface.get("ifname")

        for address in interface.get(
            "addr_info",
            []
        ):

            result.append({
                "interface": name,
                "family":
                    address.get("family"),
                "address":
                    address.get("local"),
                "prefix":
                    address.get("prefixlen")
            })

    return result


def routes():

    result = []

    command = run_command(
        ["ip", "-j", "route"]
    )

    if not command["ok"]:
        return result

    try:
        data = json.loads(
            command["stdout"]
        )
    except Exception:
        return result

    for route in data:

        result.append({
            "destination":
                route.get(
                    "dst",
                    "default"
                ),
            "gateway":
                route.get("gateway"),
            "interface":
                route.get("dev"),
            "metric":
                route.get("metric")
        })

    return result


def dns_servers():

    servers = []

    try:
        text = Path(
            "/etc/resolv.conf"
        ).read_text()
    except (
        PermissionError,
        FileNotFoundError,
        OSError
    ):
        return servers

    for line in text.splitlines():

        parts = line.strip().split()

        if (
            len(parts) >= 2
            and parts[0] == "nameserver"
        ):
            servers.append(parts[1])

    return servers


def socket_visibility():

    result = {
        "available": False,
        "tcp": [],
        "udp": []
    }

    command = run_command(
        ["ss", "-tunap"]
    )

    if not command["ok"]:
        return result

    result["available"] = True

    lines = command["stdout"].splitlines()

    for line in lines[1:]:

        parts = line.split()

        if len(parts) < 5:
            continue

        protocol = parts[0].lower()

        item = {
            "state":
                parts[1] if len(parts) > 1 else "",
            "local":
                parts[4] if len(parts) > 4 else "",
            "remote":
                parts[5] if len(parts) > 5 else ""
        }

        if protocol == "tcp":
            result["tcp"].append(item)

        elif protocol == "udp":
            result["udp"].append(item)

    return result


def capability_test():

    result = {
        "raw_socket": False,
        "packet_capture": False,
        "monitor_mode": "unknown",
        "promiscuous_mode": "unknown",
        "usb_adapters": False
    }

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_RAW,
            socket.IPPROTO_ICMP
        )

        sock.close()

        result["raw_socket"] = True

    except (
        PermissionError,
        OSError
    ):
        pass

    for tool in (
        "tcpdump",
        "tshark"
    ):

        command = run_command(
            ["sh", "-c", f"command -v {tool}"],
            timeout=2
        )

        if command["ok"]:
            result["packet_capture"] = True
            break

    return result


def connectivity():

    result = {
        "dns": False,
        "https": False,
        "latency_ms": None
    }

    try:

        socket.gethostbyname(
            "example.com"
        )

        result["dns"] = True

    except Exception:
        pass

    https = run_command(
        [
            "curl",
            "-I",
            "-L",
            "--max-time",
            "5",
            "https://example.com"
        ],
        timeout=7
    )

    result["https"] = https["ok"]

    ping = run_command(
        [
            "ping",
            "-c",
            "1",
            "-W",
            "2",
            "1.1.1.1"
        ],
        timeout=4
    )

    if ping["ok"]:

        match = re.search(
            r"time[=<]([0-9.]+)\s*ms",
            ping["stdout"]
        )

        if match:

            try:
                result["latency_ms"] = float(
                    match.group(1)
                )
            except ValueError:
                pass

    return result


def snapshot():

    return {
        "status": "ok",

        "interfaces": interfaces(),

        "addresses": addresses(),

        "routes": routes(),

        "dns": dns_servers(),

        "statistics":
            interface_stats(),

        "sockets":
            socket_visibility(),

        "capabilities":
            capability_test(),

        "connectivity":
            connectivity()
    }


# ============================================================
# CHILLOS PASSIVE TRAFFIC / PCAP
# ============================================================

def pcap_capability():

    tcpdump = shutil.which("tcpdump")

    return {
        "available": bool(tcpdump),
        "engine": "tcpdump" if tcpdump else None,
        "passive": True,
        "injection": False,
        "reason": (
            "tcpdump available"
            if tcpdump
            else "tcpdump not installed"
        ),
    }


def traffic_snapshot(interface):

    if not interface:
        return {
            "interface": "",
            "rx_bytes": 0,
            "tx_bytes": 0,
            "source": "none",
            "error": "No interface selected",
        }

    interface = str(interface).strip()

    if (
        not interface or
        "/" in interface or
        " " in interface
    ):
        return {
            "interface": interface,
            "rx_bytes": 0,
            "tx_bytes": 0,
            "source": "none",
            "error": "Invalid interface",
        }

    # --------------------------------------------------------
    # Preferred source: Linux sysfs
    # --------------------------------------------------------

    root = Path("/sys/class/net") / interface

    try:

        rx = int(
            (
                root /
                "statistics/rx_bytes"
            ).read_text().strip()
        )

        tx = int(
            (
                root /
                "statistics/tx_bytes"
            ).read_text().strip()
        )

        return {
            "interface": interface,
            "rx_bytes": rx,
            "tx_bytes": tx,
            "source": "sysfs",
        }

    except (OSError, ValueError):
        pass

    # --------------------------------------------------------
    # Android / Termux fallback
    #
    # /sys/class/net may be inaccessible while `ip`
    # still exposes counters through netlink.
    # --------------------------------------------------------

    try:

        result = subprocess.run(
            [
                "ip",
                "-s",
                "link",
                "show",
                "dev",
                interface,
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )

        if result.returncode != 0:

            return {
                "interface": interface,
                "rx_bytes": 0,
                "tx_bytes": 0,
                "source": "ip",
                "error":
                    result.stderr.strip()
                    or "ip failed",
            }

        lines = result.stdout.splitlines()

        rx_bytes = 0
        tx_bytes = 0

        for index, line in enumerate(lines):

            stripped = line.strip()

            if stripped.startswith("RX:"):

                if index + 1 < len(lines):

                    fields = (
                        lines[index + 1]
                        .split()
                    )

                    if fields:
                        rx_bytes = int(
                            fields[0]
                        )

            if stripped.startswith("TX:"):

                if index + 1 < len(lines):

                    fields = (
                        lines[index + 1]
                        .split()
                    )

                    if fields:
                        tx_bytes = int(
                            fields[0]
                        )

        return {
            "interface": interface,
            "rx_bytes": rx_bytes,
            "tx_bytes": tx_bytes,
            "source": "ip",
        }

    except (
        OSError,
        ValueError,
        subprocess.SubprocessError
    ) as exc:

        return {
            "interface": interface,
            "rx_bytes": 0,
            "tx_bytes": 0,
            "source": "none",
            "error": str(exc),
        }


def capture_pcap(interface, duration=30):

    if not shutil.which("tcpdump"):
        return {
            "ok": False,
            "error": "tcpdump is not installed",
        }

    if not interface:
        return {
            "ok": False,
            "error": "No interface selected",
        }

    interface = str(interface)

    if (
        "/" in interface or
        " " in interface or
        interface in (".", "..")
    ):
        return {
            "ok": False,
            "error": "Invalid interface",
        }

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 30

    duration = max(
        1,
        min(duration, 300)
    )

    capture_dir = (
        Path.home() /
        ".chillos" /
        "captures"
    )

    capture_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        capture_dir /
        (
            "capture_" +
            str(int(time.time())) +
            ".pcap"
        )
    )

    try:

        result = subprocess.run(
            [
                "timeout",
                str(duration),
                "tcpdump",
                "-i",
                interface,
                "-w",
                str(filename),
            ],
            capture_output=True,
            text=True,
        )

        return {
            "ok": result.returncode in (0, 124),
            "file": str(filename),
            "interface": interface,
            "duration": duration,
            "output": result.stderr[-2000:],
        }

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
        }
