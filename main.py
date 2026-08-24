#!/usr/bin/env python3

import argparse
import sys

from chill import architecture
from chill import doctor
from chill import environment
from chill import rootfs
from chill import start
from chill import tools


VERSION = "0.1.0"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="chill",
        description="ChillOS — Linux environment for Android.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"ChillOS {VERSION}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    # start
    start_parser = subparsers.add_parser(
        "start",
        help="Start a ChillOS session.",
    )

    start_parser.add_argument(
        "--check",
        action="store_true",
        help="Check the environment without starting it.",
    )

    # doctor
    subparsers.add_parser(
        "doctor",
        help="Run ChillOS diagnostics.",
    )

    # status
    subparsers.add_parser(
        "status",
        help="Show ChillOS environment status.",
    )

    # system
    subparsers.add_parser(
        "system",
        help="Show system and architecture information.",
    )

    # version
    subparsers.add_parser(
        "version",
        help="Show the ChillOS version.",
    )

    # get
    get_parser = subparsers.add_parser(
        "get",
        help="Install a package.",
    )

    get_parser.add_argument(
        "package",
        help="Package name.",
    )

    # tool
    tool_parser = subparsers.add_parser(
        "tool",
        help="Manage ChillOS tools.",
    )

    tool_subparsers = tool_parser.add_subparsers(
        dest="tool_command",
        metavar="COMMAND",
    )

    tool_search = tool_subparsers.add_parser(
        "search",
        help="Search the tool catalogue.",
    )

    tool_search.add_argument(
        "query",
        help="Search query.",
    )

    tool_info = tool_subparsers.add_parser(
        "info",
        help="Show package/tool information.",
    )

    tool_info.add_argument(
        "package",
        help="Package name.",
    )

    tool_subparsers.add_parser(
        "update",
        help="Update tool/package metadata.",
    )

    tool_remove = tool_subparsers.add_parser(
        "remove",
        help="Remove a package.",
    )

    tool_remove.add_argument(
        "package",
        help="Package name.",
    )

    # rootfs
    rootfs_parser = subparsers.add_parser(
        "rootfs",
        help="Manage the ChillOS Debian RootFS.",
    )

    rootfs_subparsers = rootfs_parser.add_subparsers(
        dest="rootfs_command",
        metavar="COMMAND",
    )

    rootfs_subparsers.add_parser(
        "build",
        help="Install/build the Debian RootFS.",
    )

    rootfs_subparsers.add_parser(
        "status",
        help="Show RootFS status.",
    )

    rootfs_subparsers.add_parser(
        "update",
        help="Update Debian package metadata.",
    )

    rootfs_subparsers.add_parser(
        "login",
        help="Enter the Debian RootFS.",
    )

    rootfs_subparsers.add_parser(
        "remove",
        help="Show safe RootFS removal information.",
    )

    return parser


def command_get(package):
    """Install a package through the ChillOS tool/package layer."""

    if hasattr(tools, "install"):
        return tools.install(package)

    if hasattr(tools, "get"):
        return tools.get(package)

    print(
        "Package installation is not available "
        "in the current tools module."
    )

    return 1


def command_tool(args):
    """Dispatch tool commands."""

    command = args.tool_command

    if command == "search":
        if hasattr(tools, "search"):
            return tools.search(args.query)

        print("Tool search is not available.")
        return 1

    if command == "info":
        if hasattr(tools, "info"):
            return tools.info(args.package)

        print("Tool information is not available.")
        return 1

    if command == "update":
        if hasattr(tools, "update"):
            return tools.update()

        print("Tool update is not available.")
        return 1

    if command == "remove":
        if hasattr(tools, "remove"):
            return tools.remove(args.package)

        print("Tool removal is not available.")
        return 1

    print("Usage: chill tool {search,info,update,remove}")
    return 1


def command_rootfs(args):
    """Dispatch RootFS commands through rootfs.main()."""

    command = args.rootfs_command

    if command is None:
        return rootfs.main(["status"])

    return rootfs.main([command])


def main(argv=None):
    parser = build_parser()

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        print(f"ChillOS {VERSION}")
        return 0

    if args.command == "status":
        environment.status()
        return 0

    if args.command == "doctor":
        return doctor.main()

    if args.command == "system":
        return architecture.report()

    if args.command == "start":
        if args.check:
            return start.check_only()

        return start.start()

    if args.command == "rootfs":
        return command_rootfs(args)

    if args.command == "get":
        return command_get(args.package)

    if args.command == "tool":
        return command_tool(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
