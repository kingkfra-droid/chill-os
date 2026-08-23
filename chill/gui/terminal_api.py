#!/usr/bin/env python3

from .terminal import terminal


def terminal_status():

    return {
        "running": terminal.running(),
        "environment": "debian",
        "backend": "proot-distro"
    }


def terminal_start():

    terminal.start()

    return terminal_status()


def terminal_command(command):

    output = terminal.execute(command)

    return {
        "ok": True,
        "output": output
    }


def terminal_stop():

    terminal.stop()

    return {
        "ok": True,
        "running": False
    }
