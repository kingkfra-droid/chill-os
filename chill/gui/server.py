#!/usr/bin/env python3

import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from .system import system_info
from .hardware import hardware_info
from .capabilities import capabilities
from .profiles import profiles, get_profile, recommend_profile

from .tools import (
    search_tool,
    install_tool,
    update_tools,
    remove_tool,
    categories,
    category,
)


from .modules import modules, get_module, set_module
from .sniffer import snapshot, pcap_capability, traffic_snapshot, capture_pcap
from .setup import (
    setup_status,
    complete_setup,
    reset_setup
)

from .terminal_api import (
    terminal_status,
    terminal_start,
    terminal_command,
    terminal_stop,
)


HOST = "127.0.0.1"
PORT = 8765


def response(handler, data, status=200):

    body = json.dumps(
        data,
        indent=2
    ).encode()

    handler.send_response(status)

    handler.send_header(
        "Content-Type",
        "application/json"
    )

    handler.send_header(
        "Content-Length",
        str(len(body))
    )

    handler.end_headers()

    handler.wfile.write(body)


class ChillHandler(BaseHTTPRequestHandler):

    def serve_static(self, filename, content_type):

        base = Path("chill/gui/web")
        path = base / filename

        try:
            body = path.read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                content_type
            )

            self.send_header(
                "Content-Length",
                str(len(body))
            )

            self.end_headers()

            self.wfile.write(body)

        except Exception as exc:

            response(
                self,
                {"error": str(exc)},
                404
            )


    def serve_index(self):

        path = "chill/gui/web/index.html"

        try:
            with open(path, "rb") as f:
                body = f.read()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()

            self.wfile.write(body)

        except Exception as exc:
            response(
                self,
                {"error": str(exc)},
                500
            )


    def do_GET(self):

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Terminal
        if path == "/api/terminal/status":
            response(self, terminal_status())
            return

        if path == "/api/terminal/start":
            response(self, terminal_start())
            return

        if path == "/api/terminal/stop":
            response(self, terminal_stop())
            return


        if path == "/":
            self.serve_index()
            return

        if path == "/style.css":
            self.serve_static(
                "style.css",
                "text/css"
            )
            return

        if path == "/app.js":
            self.serve_static(
                "app.js",
                "application/javascript"
            )
            return

        # System
        # First-run setup
        if path == "/api/setup/status":
            response(self, setup_status())
            return

        if path == "/api/setup/complete":
            response(self, complete_setup())
            return

        if path == "/api/setup/reset":
            response(self, reset_setup())
            return

        if path == "/api/system":
            response(self, system_info())
            return

        # Hardware
        if path == "/api/hardware":
            response(self, hardware_info())
            return

        # Passive Sniffer telemetry
        if path == "/api/sniffer":
            response(self, snapshot())
            return

        # Capabilities
        if path == "/api/capabilities":
            response(self, capabilities())
            return

        # Profiles
        if path == "/api/profiles":
            response(self, profiles())
            return

        # Recommended profile
        if path == "/api/profile/recommended":
            response(self, recommend_profile())
            return

        # Individual profile
        if path.startswith("/api/profile/"):

            name = path.split(
                "/api/profile/",
                1
            )[1]

            profile = get_profile(name)

            if profile is None:
                response(
                    self,
                    {"error": "Profile not found"},
                    404
                )
                return

            response(self, profile)
            return

        # Modules
        if path == "/api/modules":
            response(self, modules())
            return

        # Enable/disable module
        if path == "/api/module/set":

            name = query.get(
                "name",
                [""]
            )[0]

            enabled = query.get(
                "enabled",
                ["true"]
            )[0].lower() == "true"

            response(
                self,
                set_module(name, enabled)
            )
            return

        # Individual module
        if path.startswith("/api/module/"):

            name = path.split(
                "/api/module/",
                1
            )[1]

            module = get_module(name)

            if module is None:
                response(
                    self,
                    {"error": "Module not found"},
                    404
                )
                return

            response(self, module)
            return

        # Tool categories
        if path == "/api/tools/categories":
            response(self, categories())
            return

        # Individual category
        if path.startswith("/api/tools/category/"):

            name = path.split(
                "/api/tools/category/",
                1
            )[1]

            response(
                self,
                {
                    "category": name,
                    "tools": category_details(name)
                }
            )
            return

        # Tool search
        if path == "/api/tools/search":

            query_text = query.get(
                "q",
                [""]
            )[0]

            response(
                self,
                search_tool(query_text)
            )
            return

        # Tool install
        if path == "/api/tools/install":

            package = query.get(
                "package",
                [""]
            )[0]

            response(
                self,
                install_tool(package)
            )
            return

        # Tool update
        if path == "/api/tools/update":

            response(
                self,
                update_tools()
            )
            return

        # Tool remove
        if path == "/api/tools/remove":

            package = query.get(
                "package",
                [""]
            )[0]

            response(
                self,
                remove_tool(package)
            )
            return

        # Sniffer traffic counters
        if path == "/api/sniffer/traffic":

            interface = query.get(
                "interface",
                [""]
            )[0]

            response(
                self,
                traffic_snapshot(interface)
            )
            return


        # Sniffer PCAP capability
        if path == "/api/sniffer/pcap":

            response(
                self,
                pcap_capability()
            )
            return


        response(
            self,
            {
                "error": "API endpoint not found",
                "path": path
            },
            404
        )

    def do_POST(self):

        parsed = urlparse(self.path)
        path = parsed.path

        if path != "/api/terminal/command":
            response(
                self,
                {
                    "error": "POST endpoint not found",
                    "path": path
                },
                404
            )
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            if length <= 0 or length > 16384:
                response(
                    self,
                    {"error": "Invalid request size"},
                    400
                )
                return

            raw = self.rfile.read(length)

            data = json.loads(
                raw.decode("utf-8")
            )

            command = data.get(
                "command",
                ""
            )

            if not isinstance(command, str):
                response(
                    self,
                    {"error": "command must be a string"},
                    400
                )
                return

            if len(command) > 4096:
                response(
                    self,
                    {"error": "Command too long"},
                    400
                )
                return

            result = terminal_command(command)

            response(
                self,
                result
            )

        except json.JSONDecodeError:
            response(
                self,
                {"error": "Invalid JSON"},
                400
            )

        except Exception as exc:
            response(
                self,
                {"error": str(exc)},
                500
            )


    def log_message(self, format, *args):
        return


def main():

    server = HTTPServer(
        (HOST, PORT),
        ChillHandler
    )

    print()
    print("CHILLOS API")
    print("=" * 40)
    print(f"Listening: http://{HOST}:{PORT}")
    print()
    print("API:")
    print("  /api/system")
    print("  /api/hardware")
    print("  /api/capabilities")
    print("  /api/profiles")
    print("  /api/modules")
    print("  /api/tools/categories")
    print("  /api/tools/search")
    print()

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("ChillOS API stopped.")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()
