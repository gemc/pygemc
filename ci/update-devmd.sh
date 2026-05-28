#!/usr/bin/env bash
set -euo pipefail

echo "[devmd] start"

FILE="releases/dev.md"
START="<!-- AUTO-DEVMD:START -->"
END="<!-- AUTO-DEVMD:END -->"
SINCE="${DEVMD_SINCE:-2026-05-23}"
UNTIL="${DEVMD_UNTIL:-}"

mkdir -p "$(dirname "$FILE")"

BRANCH="${GITHUB_REF_NAME:-$(git rev-parse --abbrev-ref HEAD || echo '')}"
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
  DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's#.*/##' || true)"
  BRANCH="${DEFAULT_BRANCH:-main}"
fi

FLAGS=()
[ -n "$SINCE" ] && FLAGS+=(--since="$SINCE")
[ -n "$UNTIL" ] && FLAGS+=(--until="$UNTIL")

echo "[devmd] branch=$BRANCH since=${SINCE:-<none>} until=${UNTIL:-<now>}"

if [ ! -f "$FILE" ]; then
  cat > "$FILE" <<EOF
# Dev Release Notes

$START
$END
EOF
fi

if ! grep -q "$START" "$FILE" || ! grep -q "$END" "$FILE"; then
  cat >> "$FILE" <<EOF

$START
$END
EOF
fi

git fetch --all --tags --prune --quiet || true

TMP_LOG="$(mktemp)"
if ! git log --date=short --no-show-signature \
    --pretty='- %ad **%h** - %s _(by %an)_' \
    "${FLAGS[@]}" \
    "$BRANCH" > "$TMP_LOG"; then
  echo "- (unable to read git log for $BRANCH)" > "$TMP_LOG"
fi

if ! [ -s "$TMP_LOG" ]; then
  echo "- (no commits in range)" > "$TMP_LOG"
fi

TMP_SECTION="$(mktemp)"
{
  printf "## Commits on %s" "$BRANCH"
  [ -n "$SINCE" ] && printf " since %s" "$SINCE"
  [ -n "$UNTIL" ] && printf " until %s" "$UNTIL"
  printf "\n\n"
  cat "$TMP_LOG"
  printf "\n"
} > "$TMP_SECTION"

TMP_NEW="$(mktemp)"
awk -v start="$START" -v end="$END" -v section="$TMP_SECTION" '
  BEGIN { in_auto = 0 }
  $0 == start {
    print
    while ((getline line < section) > 0) print line
    close(section)
    in_auto = 1
    next
  }
  $0 == end {
    in_auto = 0
    print
    next
  }
  !in_auto { print }
' "$FILE" > "$TMP_NEW"

mv "$TMP_NEW" "$FILE"
chmod 0644 "$FILE"

echo "[devmd] wrote $(wc -l < "$FILE") lines to $FILE"
echo "[devmd] done"
