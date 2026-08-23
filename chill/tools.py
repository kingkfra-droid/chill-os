#!/usr/bin/env python3

import shutil
import subprocess


DISTRO = "debian"


def require_proot():
    if shutil.which("proot-distro") is None:
        print("ERROR: proot-distro is not installed.")
        print("Install with: pkg install proot-distro")
        return False

    return True


def container_exists():
    try:
        result = subprocess.run(
            [
                "proot-distro",
                "login",
                DISTRO,
                "--",
                "true"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )

        return result.returncode == 0

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        OSError
    ):
        return False


def require_container():
    if not container_exists():
        print()
        print("ERROR: ChillOS Debian container is not installed.")
        print()
        print("Install with:")
        print("  proot-distro install debian")
        print()
        return False

    return True


def debian(command, capture=False):

    return subprocess.run(
        ["proot-distro", "login", DISTRO, "--"] + command,
        capture_output=capture,
        text=True
    )


def get(packages):

    if not packages:
        print("Usage: chill get <package> [package ...]")
        return 1

    if not require_proot() or not require_container():
        return 1

    print()
    print("CHILLOS GET")
    print("=" * 40)
    print("Backend : Debian APT")
    print("Target  : ChillOS Debian")
    print()
    print("Packages:")
    for package in packages:
        print(f"  • {package}")

    print()
    print("Updating package metadata...")

    result = debian([
        "apt-get",
        "update"
    ])

    if result.returncode != 0:
        print()
        print("ERROR: Package metadata update failed.")
        return result.returncode

    print()
    print("Installing...")

    result = debian([
        "apt-get",
        "install",
        "-y",
        "--no-install-recommends",
        *packages
    ])

    if result.returncode != 0:
        print()
        print("ERROR: Installation failed.")
        return result.returncode

    print()
    print("=" * 40)
    print("Installation complete.")
    print("=" * 40)

    return 0


def search(query):

    if not query:
        print("Usage: chill tool search <query>")
        return 1

    if not require_proot() or not require_container():
        return 1

    print()
    print("CHILLOS TOOL SEARCH")
    print("=" * 40)
    print()
    print(f"Query: {query}")
    print()
    print("Searching Debian package index...")
    print()

    result = debian([
        "apt-cache",
        "search",
        query
    ])

    return result.returncode


def info(package):

    if not package:
        print("Usage: chill tool info <package>")
        return 1

    if not require_proot() or not require_container():
        return 1

    return debian([
        "apt-cache",
        "show",
        package
    ]).returncode


def update():

    if not require_proot() or not require_container():
        return 1

    print("Updating ChillOS package metadata...")

    return debian([
        "apt-get",
        "update"
    ]).returncode


def remove(package):

    if not package:
        print("Usage: chill tool remove <package>")
        return 1

    if not require_proot() or not require_container():
        return 1

    return debian([
        "apt-get",
        "remove",
        "-y",
        package
    ]).returncode


def main(args=None):

    if args is None:
        args = []

    if not args:
        print("""
ChillOS Tool Manager

Usage:

  chill get <package> [package ...]
  chill tool search <query>
  chill tool info <package>
  chill tool update
  chill tool remove <package>
""")
        return 1

    command = args[0]

    if command == "get":
        packages = args[1:]
        return get(packages)

    if command == "search":
        return search(
            args[1] if len(args) > 1 else ""
        )

    if command == "info":
        return info(
            args[1] if len(args) > 1 else ""
        )

    if command == "update":
        return update()

    if command == "remove":
        return remove(
            args[1] if len(args) > 1 else ""
        )

    print(f"Unknown tool command: {command}")
    return 1


# =========================================
# CHILLOS TOOL CATALOG
# =========================================

TOOL_CATALOG = {
    "Network": [
        "nmap",
        "net-tools",
        "iproute2",
        "tcpdump",
        "curl",
        "wget",
    ],

    "Wireless": [
        "iw",
        "wireless-tools",
        "rfkill",
    ],

    "Information Gathering": [
        "nmap",
        "whois",
        "dnsutils",
        "traceroute",
    ],

    "Web": [
        "curl",
        "wget",
        "httpie",
        "nikto",
    ],

    "OSINT": [
        "whois",
        "dnsutils",
        "jq",
        "git",
    ],

    "Forensics": [
        "file",
        "binutils",
        "strings",
        "xxd",
    ],

    "Development": [
        "python3",
        "python3-pip",
        "git",
        "make",
        "gcc",
    ],

    "System": [
        "htop",
        "procps",
        "lsof",
        "psmisc",
        "tree",
    ],

    "Security": [
        "nmap",
        "tcpdump",
        "openssl",
        "netcat-openbsd",
    ],
}


def categories():
    """Return the ChillOS tool categories."""
    return list(TOOL_CATALOG.keys())


def category(name):
    """Return packages belonging to a ChillOS category."""
    if not name:
        return []

    wanted = name.strip().lower()

    for category_name, packages in TOOL_CATALOG.items():
        if category_name.lower() == wanted:
            return packages

    return []




# =========================================
# CHILLOS TOOL METADATA / INSTALL STATE
# =========================================

TOOL_DESCRIPTIONS = {
    "nmap": "Network discovery and security auditing utility.",
    "tcpdump": "Command-line packet capture and network diagnostics.",
    "curl": "Transfer data using HTTP, HTTPS and other protocols.",
    "wget": "Command-line network downloader.",
    "net-tools": "Classic networking utilities including ifconfig and netstat.",
    "iproute2": "Modern Linux networking utilities including ip and ss.",
    "iw": "Linux wireless device configuration utility.",
    "wireless-tools": "Legacy Linux wireless networking utilities.",
    "rfkill": "Enable and disable wireless devices.",
    "whois": "Query domain registration information.",
    "dnsutils": "DNS lookup utilities such as dig and nslookup.",
    "traceroute": "Trace the network path to a destination.",
    "httpie": "User-friendly command-line HTTP client.",
    "nikto": "Web server security assessment utility.",
    "jq": "Command-line JSON processor.",
    "git": "Distributed version control system.",
    "file": "Identify file types from their contents.",
    "binutils": "Binary and object-file manipulation utilities.",
    "strings": "Extract printable strings from binary files.",
    "xxd": "Create hexadecimal dumps of files.",
    "python3": "Python 3 programming language.",
    "python3-pip": "Python package installer.",
    "make": "Build automation utility.",
    "gcc": "GNU C compiler.",
    "htop": "Interactive process and resource monitor.",
    "procps": "Utilities for inspecting Linux processes.",
    "lsof": "List open files, sockets and processes.",
    "psmisc": "Additional Linux process utilities.",
    "tree": "Display directory structures as trees.",
    "openssl": "Cryptographic and TLS command-line utilities.",
    "netcat-openbsd": "TCP/UDP networking utility.",
}


def tool_description(package):
    return TOOL_DESCRIPTIONS.get(
        package,
        "Debian Linux package available through ChillOS."
    )


def installed(package):
    """Check whether a package is installed inside Debian."""
    if not package or not require_proot():
        return False

    result = subprocess.run(
        [
            "proot-distro",
            "login",
            DISTRO,
            "--",
            "dpkg-query",
            "-W",
            "-f=${Status}",
            package,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    return (
        result.returncode == 0
        and result.stdout.strip()
        == "install ok installed"
    )


def tool_info(package):
    """Return GUI-friendly information for one package."""

    return {
        "package": package,
        "description": tool_description(package),
        "installed": installed(package),
    }


def category_details(name):
    """Return complete tool cards for a category."""

    return [
        tool_info(package)
        for package in category(name)
    ]


def catalog_search(query):
    """Search the ChillOS catalog."""

    query = (query or "").strip().lower()

    if not query:
        return []

    results = []

    for category_name, packages in TOOL_CATALOG.items():

        for package in packages:

            description = tool_description(package)

            if (
                query in package.lower()
                or query in description.lower()
                or query in category_name.lower()
            ):
                item = tool_info(package)
                item["category"] = category_name

                if item not in results:
                    results.append(item)

    return results

