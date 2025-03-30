#!/usr/bin/env python3
"""
Compile the frontend TypeScript code into JavaScript and copy it to the Python package.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Define paths
ROOT_DIR = Path(__file__).parent.parent.absolute()
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
TARGET_DIR = ROOT_DIR / "plomp" / "resources" / "templates"
BUNDLE_FILE = DIST_DIR / "bundle.js"
TARGET_FILE = TARGET_DIR / "bundle.js"


def print_colored(message, color="green"):
    """Print a colored message to the console."""
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
    """Check if Node.js is installed."""
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
    """Check if npm is installed."""
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
    """Install the npm dependencies."""
    print_colored("Installing npm dependencies...", "blue")
    os.chdir(FRONTEND_DIR)
    try:
        subprocess.run(["npm", "install"], check=True)
        print_colored("Dependencies installed successfully!", "green")
        return True
    except subprocess.SubprocessError as e:
        print_colored(f"Error installing dependencies: {e}", "red")
        return False


def build_frontend(production=True):
    """Build the frontend using webpack."""
    print_colored("Building frontend...", "blue")
    os.chdir(FRONTEND_DIR)

    # Determine the build command
    build_cmd = ["npm", "run", "build"]
    if production:
        # Add production mode if needed
        build_cmd = [
            "npx",
            "webpack",
            "--config",
            "webpack.config.js",
            "--mode=production",
        ]

    try:
        subprocess.run(build_cmd, check=True)
        print_colored("Frontend built successfully!", "green")
        return True
    except subprocess.SubprocessError as e:
        print_colored(f"Error building frontend: {e}", "red")
        return False


def copy_bundle():
    """Copy the bundle file to the Python package."""
    print_colored("Copying bundle to Python resources...", "blue")

    # Create target directory if it doesn't exist
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if not BUNDLE_FILE.exists():
            print_colored(f"Bundle file not found at {BUNDLE_FILE}", "red")
            return False

        shutil.copy2(BUNDLE_FILE, TARGET_FILE)
        print_colored(f"Bundle copied to {TARGET_FILE}", "green")
        return True
    except Exception as e:
        print_colored(f"Error copying bundle: {e}", "red")
        return False


def main():
    """Main function to compile and copy the frontend code."""
    print_colored("Starting frontend compilation process...", "magenta")

    # Check if Node.js and npm are installed
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

    # Process arguments
    production_mode = True
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        production_mode = False
        print_colored("Using development mode", "yellow")

    # Run the build process
    if not install_dependencies():
        return 1

    if not build_frontend(production=production_mode):
        return 1

    if not copy_bundle():
        return 1

    print_colored("Frontend compilation process completed successfully!", "magenta")
    return 0


if __name__ == "__main__":
    sys.exit(main())
