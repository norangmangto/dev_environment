#!/bin/bash
# Read JSON data that Claude Code sends to stdin
input=$(cat)

# --- Extract fields using jq ---

DIR=$(echo "$input" | jq -r '.workspace.current_dir')

MODEL=$(echo "$input" | jq -r '.model.display_name')
EFFORT=$(echo "$input" | jq -r '.effort.level')

WORKTREE=$(echo "$input" | jq -r '.workspace.git_worktree')

# --- Context window: session token counts + limit (real numbers, from stdin) ---
# The "// 0" provides a fallback if the field is null
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
IN_TOK=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
OUT_TOK=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
CTX_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
CTX_PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
SESSION_TOK=$((IN_TOK + OUT_TOK))

# --- Overall usage: 5h / weekly, percentage only (Claude Code doesn't expose raw counts here) ---
FIVE_HR=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

# --- End of extraction ---


# --- Prompt Settings Preparation ---
GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; CYAN='\033[36m'; RESET='\033[0m'

color_for() {
  local pct=$1
  if (( $(echo "$pct >= 80" | bc -l) )); then echo -e "$RED"
  elif (( $(echo "$pct >= 50" | bc -l) )); then echo -e "$YELLOW"
  else echo -e "$GREEN"; fi
}

fmt_tok() {
  # 12345 -> 12.3k, leaves small numbers as-is
  local n=$1
  if [ "$n" -ge 1000 ]; then
    awk -v n="$n" 'BEGIN{printf "%.1fk", n/1000}'
  else
    echo "$n"
  fi
}

# Git Branch
BRANCH=""
git rev-parse --git-dir > /dev/null 2>&1 && BRANCH=" | 🌿 $(git branch --show-current 2>/dev/null)"

# Pick bar color based on context usage
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))
printf -v FILL "%${FILLED}s"; printf -v PAD "%${EMPTY}s"
BAR="${FILL// /█}${PAD// /░}"

MINS=$((DURATION_MS / 60000)); SECS=$(((DURATION_MS % 60000) / 1000))

COST_FMT=$(printf '$%.2f' "$COST")

# --- End of Prompt Settings Preparation ---


# --- Prompt ---

PROMPT=""
PROMPT_1ST_LINE="[$MODEL${CYAN} · ${EFFORT}${RESET}] 📁 ${DIR##*/}$BRANCH"
PROMPT_2ND_LINE="${BAR_COLOR}${BAR}${RESET} ${PCT}% | 💰 ${YELLOW}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s"

# Session context window: tokens used / limit + percentage
if [ "$CTX_SIZE" -gt 0 ]; then
  PROMPT="$PROMPT | ctx: $(color_for "$CTX_PCT")$(fmt_tok "$SESSION_TOK")/$(fmt_tok "$CTX_SIZE") (${CTX_PCT}%)${RESET}"
fi

# Overall plan usage (percentage only - no raw numbers available from Claude Code)
[ -n "$FIVE_HR" ] && PROMPT="$PROMPT | 5h: $(color_for "$FIVE_HR")${FIVE_HR}%${RESET}"
[ -n "$WEEK" ] && PROMPT="$PROMPT | wk: $(color_for "$WEEK")${WEEK}%${RESET}"

PROMPT="$PROMPT | \$$(printf '%.2f' "$COST")"

echo -e "$PROMPT_1ST_LINE"
echo -e "$PROMPT_2ND_LINE"

# --- End of Prompt ---
