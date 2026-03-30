#!/bin/bash
# Claude Code Status Line - Enhanced with Context Categories
# Shows: Model, Directory, Git Branch, Context (with progress bar + category rotation), Work Time, Todos, Tasks, Agents

# Load common functions and constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/statusline-common.sh"

# Read JSON input from stdin
input=$(cat)

# Extract all useful properties
MODEL=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir // "~"')
DIR_NAME="${CURRENT_DIR##*/}"
TRANSCRIPT_PATH=$(echo "$input" | jq -r '.transcript_path // ""')
SESSION_ID=$(echo "$input" | jq -r '.session_id // ""')

# Work time tracking removed per user request

# Extract context size
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')

# Get CURRENT context usage (not cumulative from transcript)
# This ensures we see real-time changes when subagents start/finish
CURRENT_USAGE=$(echo "$input" | jq -r '.context_window.current_usage // null')

# Check if Claude is still loading
IS_LOADING=false
CURRENT_TOKENS=0

if [ "$CURRENT_USAGE" != "null" ] && [ -n "$CURRENT_USAGE" ]; then
    # Use current_usage: reflects actual current context (changes with subagents)
    INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
    CACHE_CREATE=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
    CACHE_READ=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
    CURRENT_TOKENS=$((INPUT_TOKENS + CACHE_CREATE + CACHE_READ))

    # If tokens are very low and transcript is empty/minimal, Claude is still loading
    if [ $CURRENT_TOKENS -lt 5000 ] && [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
        MESSAGE_COUNT=$(jq -Rs 'split("\n") | map(select(length > 0)) | length' "$TRANSCRIPT_PATH" 2>/dev/null || echo 0)
        [ "$MESSAGE_COUNT" -lt 3 ] && IS_LOADING=true
    fi
else
    # Fallback: sum from transcript (for sessions where current_usage is null)
    if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
        USAGE_SUM=$(jq -Rs '
            split("\n")
            | map(select(length > 0) | fromjson)
            | map(select(.message.role == "assistant" and has("usage")))
            | map(.usage | (.input_tokens // 0) + (.cache_creation_input_tokens // 0) + (.cache_read_input_tokens // 0))
            | add // 0
        ' "$TRANSCRIPT_PATH" 2>/dev/null)

        if [ -n "$USAGE_SUM" ] && [ "$USAGE_SUM" != "null" ] && [ "$USAGE_SUM" != "0" ]; then
            CURRENT_TOKENS=$USAGE_SUM
        else
            # No usage data yet, Claude is loading
            IS_LOADING=true
        fi
    else
        # No transcript yet, Claude is loading
        IS_LOADING=true
    fi
fi

# Calculate percentage
if [ "$CURRENT_TOKENS" -gt 0 ] && [ "$CONTEXT_SIZE" -gt 0 ]; then
    CONTEXT_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($CURRENT_TOKENS / $CONTEXT_SIZE) * 100}")
else
    CONTEXT_PERCENT=0
fi

CONTEXT_INT=$(printf "%.0f" "$CONTEXT_PERCENT")

# Use common format_tokens function
USAGE_DISPLAY=$(format_tokens $CURRENT_TOKENS)
TOTAL_DISPLAY=$(format_tokens $CONTEXT_SIZE)
FREE_TOKENS=$((CONTEXT_SIZE - CURRENT_TOKENS))
FREE_DISPLAY=$(format_tokens $FREE_TOKENS)

# ========== Progress Bar ==========
# Generate visual progress bar using common function
PROGRESS_BAR=$(generate_progress_bar $CONTEXT_INT)

# ========== Context Category Statistics ==========
# Extract category usage from transcript and estimate system overhead
CATEGORY_DISPLAY=""
CATEGORY_ITEMS=()

# Skip detailed analysis if still loading
if [ "$IS_LOADING" = false ] && [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    # ONE-TIME transcript parsing using common function (with statistics)
    TRANSCRIPT_DATA=$(parse_transcript "$TRANSCRIPT_PATH" true)

    # Extract individual statistics from the result
    AGENT_COUNT=$(echo "$TRANSCRIPT_DATA" | jq -r '.agent_count // 0' 2>/dev/null || echo 0)
    MEMORY_FILES=$(echo "$TRANSCRIPT_DATA" | jq -r '.memory_files // 0' 2>/dev/null || echo 0)
    SKILL_COUNT=$(echo "$TRANSCRIPT_DATA" | jq -r '.skill_count // 0' 2>/dev/null || echo 0)
    MESSAGE_COUNT=$(echo "$TRANSCRIPT_DATA" | jq -r '.message_count // 0' 2>/dev/null || echo 0)

    # Estimate system overhead using defined constant
    SYSTEM_TOKENS=$(awk "BEGIN {printf \"%.0f\", $CURRENT_TOKENS * $SYSTEM_OVERHEAD_PERCENT}")
    SYSTEM_DISPLAY=$(format_tokens $SYSTEM_TOKENS)

    # Estimate agent overhead using defined constant
    if [ $AGENT_COUNT -gt 0 ]; then
        AGENT_TOKENS=$(( AGENT_COUNT * AVG_AGENT_TOKENS ))
        AGENT_DISPLAY=$(format_tokens $AGENT_TOKENS)
        CATEGORY_ITEMS+=("Agents: ${AGENT_DISPLAY} (${AGENT_COUNT})")
    fi

    # Estimate memory files using defined constant
    if [ $MEMORY_FILES -gt 0 ]; then
        MEMORY_TOKENS=$(( MEMORY_FILES * AVG_MEMORY_FILE_TOKENS ))
        MEMORY_DISPLAY=$(format_tokens $MEMORY_TOKENS)
        CATEGORY_ITEMS+=("Memory: ${MEMORY_DISPLAY} (${MEMORY_FILES})")
    fi

    # Estimate skills using defined constant
    if [ $SKILL_COUNT -gt 0 ]; then
        SKILL_TOKENS=$(( SKILL_COUNT * AVG_SKILL_TOKENS ))
        SKILL_DISPLAY=$(format_tokens $SKILL_TOKENS)
        CATEGORY_ITEMS+=("Skills: ${SKILL_DISPLAY} (${SKILL_COUNT})")
    fi

    # Add system and free space
    CATEGORY_ITEMS+=("System: ${SYSTEM_DISPLAY}")
    CATEGORY_ITEMS+=("Free: ${FREE_DISPLAY}")
elif [ "$IS_LOADING" = true ]; then
    # Show loading indicator
    CATEGORY_ITEMS+=("Loading...")
fi

# Git branch (used internally for width calc, not displayed)
BRANCH=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
fi

# Rotation cycle (shared by categories, tasks, and agents)
CURRENT_TIME=$(date +%s)

# Rotate through categories
CATEGORY_COUNT=${#CATEGORY_ITEMS[@]}
if [ $CATEGORY_COUNT -gt 0 ]; then
    CATEGORY_INDEX=$(( (CURRENT_TIME / CYCLE_DURATION) % CATEGORY_COUNT ))
    CATEGORY_DISPLAY=" | ${CATEGORY_ITEMS[$CATEGORY_INDEX]}"

    # Add rotation indicator if multiple categories
    if [ $CATEGORY_COUNT -gt 1 ]; then
        CATEGORY_DISPLAY="${CATEGORY_DISPLAY} [$(($CATEGORY_INDEX + 1))/${CATEGORY_COUNT}]"
    fi
fi

# Get terminal width for adaptive truncation
TERM_WIDTH=$(tput cols 2>/dev/null || echo 120)
# Reserve space for fixed parts: [Model] 📁 Dir | 🌿 branch | XX% | ✓ X/X | [X/X] | 🤖 agent [X/X]
# Estimate: ~80 chars for fixed parts + dir name + branch name + agent name
FIXED_WIDTH=80

# Extract Todo List status, all Agents, and all Tasks from transcript using common functions
TODO_STATUS=""
AGENT_STATUS=""
TASK_STATUS=""

# Skip detailed Todo/Task/Agent analysis if still loading
if [ "$IS_LOADING" = false ] && [ -n "$TRANSCRIPT_DATA" ] && [ "$TRANSCRIPT_DATA" != "null" ]; then
    # Extract tasks and agents from the unified TRANSCRIPT_DATA
    TASK_DATA=$(echo "$TRANSCRIPT_DATA" | jq -r '.tasks' 2>/dev/null)
    RECENT_AGENTS=$(echo "$TRANSCRIPT_DATA" | jq -r '.recent_agents' 2>/dev/null)

    # Use common functions to generate status strings
    TODO_STATUS=$(get_task_status "$TASK_DATA")
    TASK_STATUS=$(get_task_display "$TASK_DATA" "$CURRENT_TIME" "$TERM_WIDTH" "$FIXED_WIDTH" "$DIR_NAME" "$BRANCH")
    AGENT_STATUS=$(get_agent_display "$RECENT_AGENTS" "$CURRENT_TIME")
fi

# Color coding based on context usage using common function
DISPLAY_INFO=$(get_context_display $CONTEXT_INT $IS_LOADING)
COLOR=$(echo "$DISPLAY_INFO" | cut -d'|' -f1)
ICON=$(echo "$DISPLAY_INFO" | cut -d'|' -f2)
RESET="\033[0m"

# Display format: [Model] 📁 Dir | 🌿 Branch | Context: PROGRESS_BAR XX% (Used/Total) | Category | ✓ Todos | Task | 🤖 Agent
if [ "$IS_LOADING" = true ]; then
    # Simplified display during loading
    echo -e "${COLOR}[$MODEL] ${ICON} Loading Claude...${RESET}"
else
    # Full display after loading complete
    echo -e "${COLOR}[$MODEL] Context: ${PROGRESS_BAR} ${CONTEXT_INT}% (${USAGE_DISPLAY}/${TOTAL_DISPLAY})${CATEGORY_DISPLAY}${TODO_STATUS}${TASK_STATUS}${AGENT_STATUS}${RESET}"
fi
