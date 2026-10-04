"""
VORTEX VPN — Linux Desktop GUI (PyQt6)
Matches the VORTEX dark-first cybersecurity visual system.
"""
import sys
import os

# Share GUI logic with desktop framework
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "windows-client")))
from app import VortexWindowsApp, main

if __name__ == "__main__":
    main()
