#!/bin/bash
# Color codes and output helpers for setup scripts

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

ok()     { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()   { echo -e "  ${YELLOW}!${RESET} $1"; }
fail()   { echo -e "  ${RED}✗${RESET} $1"; }
info()   { echo -e "  ${DIM}→${RESET} $1"; }
header() { echo -e "\n${BOLD}${CYAN}[$1]${RESET} $2"; }
