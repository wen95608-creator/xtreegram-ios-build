#!/usr/bin/env python3
"""Built-in proxy injection DISABLED by user request.

The app now connects to Telegram's datacenters directly with stock settings;
users reach them through their own VPN/proxy setup. Nothing is hardcoded.
"""
import sys

print("builtin proxy injection disabled - keeping stock direct connections")
sys.exit(0)
