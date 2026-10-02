#!/bin/bash
# Link personal Claude Code config from the host into the container.

HOST_DIR="/home/vscode/.claude-host"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

if [ ! -d "$HOST_DIR" ] || [ -z "$(ls -A "$HOST_DIR")" ]; then
    echo "No host Claude config found in $HOST_DIR, skipping"
    exit 0
fi

# Link $1 to $2 unless $2 is a real file or directory owned by the container.
link() {
    if [ -e "$2" ] && [ ! -L "$2" ]; then
        echo "Not linking $2: it exists in the container"
        return
    fi
    ln -sfn "$1" "$2"
}

mkdir -p "$CLAUDE_DIR"
# NB: you must add the statusLine config yourself (only once)
# in ~/.claude/settings.json
# Look in your hosts settings.json to see how
for file in CLAUDE.md statusline-command.sh; do
    [ -f "$HOST_DIR/$file" ] && link "$HOST_DIR/$file" "$CLAUDE_DIR/$file"
done

for dir in skills agents commands rules; do
    [ -d "$HOST_DIR/$dir" ] || continue
    mkdir -p "$CLAUDE_DIR/$dir"
    for entry in "$HOST_DIR/$dir"/*; do
        name=$(basename "$entry")
        if [ ! -e "$entry" ]; then
            [ -L "$entry" ] && echo "Not linking $dir/$name: it points outside the host's ~/.claude"
            continue
        fi
        [ "$dir/$name" = "skills/synced" ] && continue
        link "$entry" "$CLAUDE_DIR/$dir/$name"
    done
    # Remove links to entries that were deleted on the host
    find "$CLAUDE_DIR/$dir" -maxdepth 1 -xtype l -lname "$HOST_DIR/*" -delete
done
