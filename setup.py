#!/usr/bin/env python3
"""
Setup script for MicroCFO MCP Server
"""

import subprocess
import sys
import os

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Virtual environment created!")
    else:
        print("Virtual environment already exists.")

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:  # Unix/Linux/Mac
        pip_path = os.path.join("venv", "bin", "pip")
    
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("Dependencies installed!")

def main():
    """Main setup function"""
    print("Setting up MicroCFO MCP Server...")
    create_virtual_environment()
    install_dependencies()
    print("\nSetup complete!")
    print("\nTo run the server:")
    if os.name == 'nt':  # Windows
        print("1. Activate virtual environment: venv\\Scripts\\activate")
    else:  # Unix/Linux/Mac
        print("1. Activate virtual environment: source venv/bin/activate")
    print("2. Run server: python server.py")
    print("3. For MCP Inspector: mcp dev server.py")

if __name__ == "__main__":
    main()