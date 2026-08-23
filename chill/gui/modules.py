#!/usr/bin/env python3

import json
from pathlib import Path


STATE_FILE = Path.home() / ".chillos_modules.json"


MODULES = {
    "core": {
        "name": "ChillOS Core",
        "description": "Core ChillOS environment.",
        "status": "built-in",
        "enabled": True
    },

    "hardware": {
        "name": "Hardware Discovery",
        "description": "Detect hardware visible to Linux.",
        "status": "available",
        "enabled": True
    },

    "capabilities": {
        "name": "Capability Engine",
        "description": "Detect available system capabilities.",
        "status": "available",
        "enabled": True
    },

    "profiles": {
        "name": "Profile Manager",
        "description": "Manage adaptive profiles.",
        "status": "available",
        "enabled": True
    },

    "tools": {
        "name": "Tool Manager",
        "description": "Manage Linux packages and tools.",
        "status": "available",
        "enabled": True
    },

    "terminal": {
        "name": "Linux Terminal",
        "description": "Access the Debian userspace.",
        "status": "available",
        "enabled": True
    }
}


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(
            STATE_FILE.read_text()
        )
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2
        )
    )


def modules():
    state = load_state()
    result = {}

    for name, module in MODULES.items():
        item = dict(module)

        if name in state:
            item["enabled"] = state[name]

        result[name] = item

    return result


def get_module(name):
    return modules().get(name)


def module_names():
    return list(MODULES.keys())


def module_enabled(name):
    module = get_module(name)

    if module is None:
        return False

    return module["enabled"]


def set_module(name, enabled):

    if name not in MODULES:
        return {
            "ok": False,
            "error": "Module not found"
        }

    if MODULES[name]["status"] == "built-in":
        return {
            "ok": False,
            "error": "Built-in module cannot be disabled"
        }

    state = load_state()
    state[name] = bool(enabled)
    save_state(state)

    return {
        "ok": True,
        "module": name,
        "enabled": bool(enabled)
    }
