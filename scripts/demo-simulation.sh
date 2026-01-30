#!/bin/bash
# Simulated route-researcher output for README demo
# Recreates realistic Claude Code UI

set -e

# Colors
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
ORANGE='\033[38;5;208m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
RESET='\033[0m'

# Timing helpers
pause() { sleep "${1:-0.5}"; }
type_line() { echo -e "$1"; pause "${2:-0.2}"; }
type_char() {
    local text="$1"
    local delay="${2:-0.05}"
    for (( i=0; i<${#text}; i++ )); do
        printf '%s' "${text:$i:1}"
        sleep "$delay"
    done
}

# Clear and start
clear
pause 0.4

# Claude Code startup screen (exact UI format)
echo -e "╭─── ${BOLD}Claude Code${RESET} v2.1.25 ─────────────────────────────────────────────────────────────────────────────╮"
echo -e "│                                                    │ ${ORANGE}Tips for getting started${RESET}                       │"
echo -e "│                ${BOLD}Welcome back!${RESET}                       │ Run /init to create a CLAUDE.md file with ins… │"
echo -e "│                                                    │ ────────────────────────────────────────────── │"
echo -e "│                                                    │ ${ORANGE}Recent activity${RESET}                                │"
echo -e "│                       ${ORANGE}▐▛███▜▌${RESET}                      │ No recent activity                             │"
echo -e "│                      ${ORANGE}▝▜█████▛▘${RESET}                     │                                                │"
echo -e "│                        ${ORANGE}▘▘ ▝▝${RESET}                       │                                                │"
echo -e "│    ${ORANGE}Opus 4.5${RESET} · Claude Pro · user@example.com       │                                                │"
echo -e "│                                                    │                                                │"
echo -e "│              ~/projects/mountaineering             │                                                │"
echo -e "╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯"
pause 1.5

echo ""
echo ""

# Prompt with user typing
echo -ne "${MAGENTA}>${RESET} "
type_char "Research Mount Rainier" 0.06
pause 0.8
echo ""
echo ""
pause 0.6

# Claude "thinking" indicator then skill starts
type_line "${DIM}Analyzing request...${RESET}" 0.8
echo ""

# Phase 1: Peak Identification
type_line "${BOLD}${WHITE}🏔️  Route Researcher${RESET}" 0.4
type_line "" 0.15
type_line "${BOLD}Phase 1: Peak Identification${RESET}" 0.3
type_line "${DIM}  Searching PeakBagger database...${RESET}" 0.1
pause 1.5  # Realistic delay for API call
type_line "${GREEN}  ✓${RESET} Found: ${BOLD}Mount Rainier${RESET} (ID: 2296)" 0.6
type_line ""

# Phase 2: Peak Information
type_line "${BOLD}Phase 2: Peak Information${RESET}" 0.3
type_line "${DIM}  Fetching peak details...${RESET}" 0.1
pause 1.2  # API call delay
type_line "${GREEN}  ✓${RESET} Elevation: ${CYAN}14,411 ft${RESET} (4,392 m)" 0.25
type_line "${GREEN}  ✓${RESET} Location: ${CYAN}46.8523°N, 121.7603°W${RESET}" 0.25
type_line "${GREEN}  ✓${RESET} Prominence: ${CYAN}13,211 ft${RESET} - Most prominent peak in WA" 0.5
type_line ""

# Phase 3: Data Gathering - Stage 1 (parallel)
type_line "${BOLD}Phase 3: Data Gathering${RESET}" 0.3
type_line "${DIM}  Stage 1: Launching parallel tasks...${RESET}" 0.1

# Show tasks spawning
type_line "${YELLOW}  ├──${RESET} Route descriptions ${DIM}(SummitPost, WTA, AllTrails)${RESET}" 0.15
type_line "${YELLOW}  ├──${RESET} Ascent statistics ${DIM}(PeakBagger)${RESET}" 0.15
type_line "${YELLOW}  ├──${RESET} Trip report sources ${DIM}(CascadeClimbers, WTA)${RESET}" 0.15
type_line "${YELLOW}  ├──${RESET} Weather forecast ${DIM}(Open-Meteo, NOAA)${RESET}" 0.15
type_line "${YELLOW}  ├──${RESET} Avalanche conditions ${DIM}(NWAC)${RESET}" 0.15
type_line "${YELLOW}  ├──${RESET} Daylight calculations ${DIM}(Sunrise-Sunset API)${RESET}" 0.15
type_line "${YELLOW}  └──${RESET} Access & permits" 0.1

# Long pause - this is where parallel agents are working
pause 3.5

type_line ""
type_line "${GREEN}  ✓${RESET} Weather: 7-day forecast loaded" 0.2
type_line "${GREEN}  ✓${RESET} Avalanche: ${CYAN}Moderate${RESET} above 6,500 ft" 0.2
type_line "${GREEN}  ✓${RESET} Routes: ${CYAN}4 routes${RESET} found (DC, Emmons, Kautz, Liberty Ridge)" 0.2
type_line "${GREEN}  ✓${RESET} Trip report sources: ${CYAN}3 platforms${RESET} identified" 0.4
type_line ""

# Phase 3: Data Gathering - Stage 2 (sequential)
type_line "${DIM}  Stage 2: Fetching trip report content...${RESET}" 0.1
pause 2.5  # Fetching reports takes time
type_line "${GREEN}  ✓${RESET} Trip reports: ${CYAN}18 reports${RESET} fetched, analyzing content" 0.5
type_line ""

# Phase 4: Route Analysis
type_line "${BOLD}Phase 4: Route Analysis${RESET}" 0.3
type_line "${DIM}  Synthesizing data from all sources...${RESET}" 0.1
pause 2.0  # Analysis takes time
type_line "${GREEN}  ✓${RESET} Primary route: Disappointment Cleaver" 0.25
type_line "${GREEN}  ✓${RESET} Technical grade: Class 4 glacier climb" 0.25
type_line "${GREEN}  ✓${RESET} Key hazards: Crevasses, rockfall, altitude" 0.4
type_line ""

# Phase 5: Report Generation
type_line "${BOLD}Phase 5: Report Generation${RESET}" 0.3
type_line "${DIM}  Writing markdown report...${RESET}" 0.1
pause 1.8  # Writing takes time
type_line "${GREEN}  ✓${RESET} Generated 847 lines" 0.4
type_line ""

# Phase 6: Review
type_line "${BOLD}Phase 6: Report Review${RESET}" 0.3
type_line "${DIM}  Validating accuracy...${RESET}" 0.1
pause 1.5  # Review takes time
type_line "${GREEN}  ✓${RESET} No inconsistencies found" 0.4
type_line ""

# Phase 7: Complete
type_line "${BOLD}Phase 7: Completion${RESET}" 0.3
type_line ""
type_line "${GREEN}${BOLD}✅ Complete${RESET}" 0.4
type_line ""
type_line "📄 Saved: ${BOLD}${CYAN}2026-01-30-mount-rainier.md${RESET}" 0.5
type_line ""
type_line "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}" 0.25
type_line "${WHITE}Mount Rainier (14,411 ft) - Cascade Range, Washington${RESET}" 0.25
type_line "${DIM}Technical glacier climb requiring rope teams, crevasse rescue"
type_line "skills, and high-altitude mountaineering experience.${RESET}"
pause 3
