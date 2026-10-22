#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <telegram-ios-source-dir>" >&2
  exit 1
fi

SOURCE_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# This build connects to Telegram's official datacenters with the stock RSA
# keys and keeps the stock Telegram branding, so the template's branding +
# private-server patch is intentionally NOT applied. Only the unsigned
# sideload crash guards below are needed; each one asserts its target exists.

# App Group container fallback: a free Apple ID cannot grant
# com.apple.security.application-groups, and an unsigned IPA carries no
# entitlements at all, so AppDelegate must fall back to its own Documents.
python3 "$SCRIPT_DIR/apply_app_group_fallback.py" "$SOURCE_DIR"

# Unguarded NULL in an NSDictionary literal in BuildConfig.m (instant SIGABRT
# before the login screen).
python3 "$SCRIPT_DIR/apply_buildconfig_guard.py" "$SOURCE_DIR"

# ImageIO faults inside __PNGReadPlugin on the intro's loose PNG textures.
python3 "$SCRIPT_DIR/apply_intro_texture_guard.py" "$SOURCE_DIR"

# The intro's OpenGL machinery (EAGLContext, GLKView, animation timer).
python3 "$SCRIPT_DIR/apply_intro_disable.py" "$SOURCE_DIR"

# Keep the splash from dead-ending once the intro no longer draws.
python3 "$SCRIPT_DIR/apply_splash_auto_advance.py" "$SOURCE_DIR"

# The 1x1 UIGraphicsImageRenderer probe in Display/Source/GenerateImage.swift.
python3 "$SCRIPT_DIR/apply_graphics_probe_guard.py" "$SOURCE_DIR"

# CloudKit brk #1 in CKContainer.default() without the icloud entitlement.
python3 "$SCRIPT_DIR/apply_clouddata_guard.py" "$SOURCE_DIR"

# INPreferences.siriAuthorizationStatus() ObjC exception without the siri
# entitlement, raised right after a successful login.
python3 "$SCRIPT_DIR/apply_siri_guard.py" "$SOURCE_DIR"

echo "All unsigned-sideload crash guards applied."
