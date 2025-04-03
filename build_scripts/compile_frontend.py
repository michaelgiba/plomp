#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
from functools import cache
from pathlib import Path


@cache
def _global_config():
    root_dir = Path(__file__).parent.parent.absolute()

    return {
        "ROOT_DIR": root_dir,
        "FRONTEND_DIR": root_dir / "frontend",
        "DIST_DIR": root_dir / "frontend" / "dist",
        "TARGET_DIR": root_dir / "plomp" / "resources" / "templates",
    }


def print_colored(message, color="green"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


def check_node_installed():
    try:
        subprocess.run(
            ["node", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_npm_installed():
    try:
        subprocess.run(
            ["npm", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def install_dependencies():
    print_colored("Installing npm dependencies...", "blue")
    os.chdir(_global_config()["FRONTEND_DIR"])
    try:
        subprocess.run(["npm", "install"], check=True)
        print_colored("Dependencies installed successfully!", "green")
        return True
    except subprocess.SubprocessError as e:
        print_colored(f"Error installing dependencies: {e}", "red")
        return False


def build_frontend():
    print_colored("Building frontend...", "blue")
    os.chdir(_global_config()["FRONTEND_DIR"])

    build_cmd = ["npm", "run", "build"]

    try:
        subprocess.run(build_cmd, check=True)
        print_colored("Frontend built successfully!", "green")
        return True
    except subprocess.SubprocessError as e:
        print_colored(f"Error building frontend: {e}", "red")
        return False


def copy_bundle():
    print_colored("Copying bundle to Python resources...", "blue")
    target_dir = _global_config()["TARGET_DIR"]
    dist_dir = _global_config()["DIST_DIR"]
    html_file = dist_dir / "index.html"

    target_dir.mkdir(parents=True, exist_ok=True)
    if not html_file.exists():
        print_colored(f"HTML file not found at {html_file}", "red")
        return False

    # Copy the self-contained HTML file
    target_html = target_dir / "index.html"
    shutil.copy2(html_file, target_html)
    print_colored(f"Self-contained HTML copied to {target_html}", "green")
    return True


def main():
    print_colored("Starting frontend compilation process...", "magenta")

    if not check_node_installed():
        print_colored(
            "Node.js is not installed. Please install it to build the frontend.", "red"
        )
        return 1

    if not check_npm_installed():
        print_colored(
            "npm is not installed. Please install it to build the frontend.", "red"
        )
        return 1

    if not install_dependencies():
        return 1

    if not build_frontend():
        return 1

    if not copy_bundle():
        return 1

    print_colored("Frontend compilation process completed successfully!", "magenta")
    return 0


if __name__ == "__main__":
    sys.exit(main())
