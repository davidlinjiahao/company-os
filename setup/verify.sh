#!/bin/bash
# Standalone verify shortcut — runs only health checks
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/steps/09-verify.sh" "$@"
