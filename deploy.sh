#!/bin/bash
# Auto-deploy script for buildyourownsplitwise
# Pulls from git every minute, rebuilds if changes detected
# On build failure, keeps old version running

PROJECT_DIR="$HOME/buildyourownsplitwise"
LOG="$PROJECT_DIR/deploy.log"
LOCK="$PROJECT_DIR/.deploy.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# Prevent concurrent runs
if [ -f "$LOCK" ]; then
    pid=$(cat "$LOCK")
    if kill -0 "$pid" 2>/dev/null; then
        log "SKIP: Previous deploy still running (PID $pid)"
        exit 0
    fi
    rm -f "$LOCK"
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

cd "$PROJECT_DIR" || { log "ERROR: Cannot cd to $PROJECT_DIR"; exit 1; }

# Pull latest changes
BEFORE=$(git rev-parse HEAD)
PULL_OUTPUT=$(git pull --ff-only 2>&1)
PULL_STATUS=$?

if [ $PULL_STATUS -ne 0 ]; then
    log "ERROR: git pull failed (exit $PULL_STATUS)"
    echo "$PULL_OUTPUT" >> "$LOG"
    exit 1
fi

AFTER=$(git rev-parse HEAD)

# No changes, nothing to do
if [ "$BEFORE" = "$AFTER" ]; then
    exit 0
fi

log "=========================================="
log "CHANGE DETECTED: $BEFORE -> $AFTER"
log "$(git log --oneline ${BEFORE}..${AFTER})"
log "=========================================="

# --- Stop conflicting containers on our ports ---
for PORT in 8000 5432 6379; do
    CONTAINER_ID=$(sudo docker ps --format '{{.ID}}' --filter "publish=$PORT" | head -1)
    if [ -n "$CONTAINER_ID" ]; then
        CONTAINER_NAME=$(sudo docker inspect --format '{{.Name}}' "$CONTAINER_ID" | sed 's/\///')
        # Only kill containers NOT managed by our compose project
        if ! echo "$CONTAINER_NAME" | grep -q "buildyourownsplitwise"; then
            log "CLEANUP: Stopping conflicting container $CONTAINER_NAME on port $PORT"
            sudo docker stop "$CONTAINER_ID" >> "$LOG" 2>&1
            sudo docker rm "$CONTAINER_ID" >> "$LOG" 2>&1
        fi
    fi
done

# --- Docker Compose rebuild ---
log "DEPLOY: Rebuilding and restarting containers..."

sudo docker-compose build >> "$LOG" 2>&1
BUILD_STATUS=$?

if [ $BUILD_STATUS -ne 0 ]; then
    log "DEPLOY FAILED: sudo docker-compose build failed (exit $BUILD_STATUS)"
    log "DEPLOY: Old containers still running, no changes applied"
    exit 1
fi

sudo docker-compose up -d >> "$LOG" 2>&1
UP_STATUS=$?

if [ $UP_STATUS -eq 0 ]; then
    log "DEPLOY SUCCESS: All containers updated and running"
else
    log "DEPLOY ERROR: sudo docker-compose up failed (exit $UP_STATUS)"
fi
