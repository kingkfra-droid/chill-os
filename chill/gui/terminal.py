#!/usr/bin/env python3

import os
import subprocess
import threading

from .tools import (
    categories,
    install_tool,
    remove_tool,
    search_tool,
    update_tools,
)


class ChillTerminal:

    def __init__(self):
        self.process = None
        self.lock = threading.Lock()

    def start(self):

        with self.lock:

            if self.process is not None:

                if self.process.poll() is None:
                    return True

            command = [
                "proot-distro",
                "login",
                "debian",
                "--",
                "/bin/bash",
                "--login"
            ]

            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            return True

    def running(self):

        return (
            self.process is not None
            and self.process.poll() is None
        )

    def chill_command(self, command):

        parts = command.strip().split()

        if not parts:
            return ""

        if parts[0] != "chill":
            return None

        if len(parts) == 1:

            return (
                "ChillOS package manager\n"
                "\n"
                "Commands:\n"
                "  chill list\n"
                "  chill search <query>\n"
                "  chill get <package>\n"
                "  chill remove <package>\n"
                "  chill update\n"
            )

        action = parts[1].lower()

        if action == "list":

            output = []

            for name, packages in categories().items():

                output.append(
                    name.upper() + ":"
                )

                output.extend(
                    "  " + package
                    for package in packages
                )

            return "\n".join(output)

        if action == "search":

            query = " ".join(parts[2:])

            if not query:
                return "Usage: chill search <query>"

            result = search_tool(query)

            return result.get(
                "output",
                ""
            )

        if action == "get":

            if len(parts) < 3:
                return "Usage: chill get <package>"

            package = parts[2]

            result = install_tool(package)

            return result.get(
                "output",
                ""
            )

        if action == "remove":

            if len(parts) < 3:
                return "Usage: chill remove <package>"

            package = parts[2]

            result = remove_tool(package)

            return result.get(
                "output",
                ""
            )

        if action == "update":

            result = update_tools()

            return result.get(
                "output",
                ""
            )

        return (
            "Unknown ChillOS command: "
            + action
            + "\n\n"
            "Use:\n"
            "  chill list\n"
            "  chill search <query>\n"
            "  chill get <package>\n"
            "  chill remove <package>\n"
            "  chill update"
        )

    def execute(self, command):

        command = command.strip()

        if not command:
            return ""

        chill_result = self.chill_command(command)

        if chill_result is not None:
            return chill_result

        self.start()

        with self.lock:

            try:

                marker = "__CHILLOS_CMD_DONE__"

                payload = (
                    command +
                    "\nprintf '\\n" +
                    marker +
                    "\\n'\n"
                )

                self.process.stdin.write(payload)
                self.process.stdin.flush()

                output = []

                while True:

                    line = self.process.stdout.readline()

                    if not line:
                        break

                    if marker in line:
                        break

                    output.append(line)

                return "".join(output)

            except Exception as exc:

                return (
                    "Terminal error: " +
                    str(exc)
                )

    def stop(self):

        with self.lock:

            if self.process is not None:

                if self.running():
                    self.process.terminate()

                self.process = None

        return True


terminal = ChillTerminal()
