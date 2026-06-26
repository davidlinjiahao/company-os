#!/bin/bash
# Company OS — One-Command Onboarding
# Thin wrapper: delegates to the modular setup/init.sh
#
# Usage:
#   ./setup.sh           Full setup
#   ./setup.sh --verify  Health checks only
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setup/init.sh" "$@"
