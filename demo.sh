#!/usr/bin/env bash
# Scripted walkthrough for recording a terminal demo of Sage.
#
# Usage:
#   1. Install asciinema:  pip install asciinema   (or: brew install asciinema)
#   2. Record:             asciinema rec demo.cast -c "./demo.sh"
#   3. Convert to a GIF for the README (two options):
#        - agg (fast, local, no network needed for rendering once installed):
#            cargo install --locked agg   # or download a release binary
#            agg demo.cast demo.gif
#        - or upload demo.cast to asciinema.org and embed the player link
#   4. Drop demo.gif at the top of README.md
#
# This script only touches files under a throwaway temp folder — safe to
# run repeatedly.

set -e

DEMO_DIR="$(mktemp -d)/biology_notes"
mkdir -p "$DEMO_DIR"

type_line() {
  # Fakes a human typing the command, for a more natural-looking recording.
  local text="$1"
  echo -n "$ "
  for ((i = 0; i < ${#text}; i++)); do
    echo -n "${text:$i:1}"
    sleep 0.02
  done
  echo
}

pause() { sleep "${1:-1.2}"; }

clear
type_line "# Sage — offline-first AI study assistant"
pause 1.5

cat > "$DEMO_DIR/photosynthesis.md" << 'EOF'
# Lecture 4: Photosynthesis
Photosynthesis converts light energy into chemical energy stored in
glucose. The Calvin cycle takes place in the stroma and uses ATP and
NADPH produced by the light-dependent reactions to fix carbon dioxide.
Chlorophyll absorbs red and blue light and reflects green light.
EOF

cat > "$DEMO_DIR/cell_respiration.txt" << 'EOF'
Cellular respiration breaks down glucose to release ATP in three
stages: glycolysis (cytoplasm), the Krebs cycle (mitochondrial
matrix), and the electron transport chain (inner mitochondrial
membrane), which produces the majority of the cell's ATP.
EOF

pause 0.5
type_line "sage sync $DEMO_DIR"
sage sync "$DEMO_DIR"
pause 2

type_line 'sage ask "where does the calvin cycle take place"'
sage ask --db "$DEMO_DIR/.sage_index.db" "where does the calvin cycle take place"
pause 2

type_line 'sage ask "what are the three stages of cellular respiration"'
sage ask --db "$DEMO_DIR/.sage_index.db" "what are the three stages of cellular respiration"
pause 2

type_line "# No internet connection was used for either answer."
pause 2

rm -rf "$DEMO_DIR"
