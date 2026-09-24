"""Hook de Claude Code (PreToolUse, Bash): bloquea fusionar PRs y escribir en main. Eso lo hace siempre Diego.
Lee el comando por stdin (JSON). Sale con 2 para bloquear: Claude ve el motivo y no ejecuta el comando."""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# Siempre prohibido, este donde este
PROHIBIDO = [
    (r"\bgh\s+pr\s+merge\b", "fusionar PRs"),
    (r"\bgh\s+api\b", "gh api (puede fusionar o escribir en main)"),
    (r"\bgit\b[^;&|]*\bmerge(?![-\w])", "git merge"),
    (r"\bgit\b[^;&|]*\bpush\b[^;&|]*(\bmain\b|--all\b|--mirror\b)", "push a main"),
]
# Prohibido si la rama actual es main (o el mismo comando se cambia a main antes)
ESCRIBE = r"\bgit\b[^;&|]*\b(commit|push|cherry-pick|revert|am|rebase)\b"
A_MAIN = r"\bgit\b[^;&|]*\b(checkout|switch)\s+(-\S+\s+)*main\b"


def rama():
    try:
        return subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def motivo(cmd):
    for patron, que in PROHIBIDO:
        if re.search(patron, cmd):
            return que
    m = re.search(ESCRIBE, cmd)
    if m:
        antes = cmd[:m.start()]
        if rama() == "main" or re.search(A_MAIN, antes):
            return f"git {m.group(1)} estando en main"
    return None


def main():
    try:
        cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except Exception:
        return 0
    que = motivo(cmd)
    if que:
        print(f"BLOQUEADO por .claude/hooks/proteger_main.py: {que}. Nunca fusiones un PR ni escribas en main; "
              "eso lo hace siempre Diego. Trabaja en una rama tarea/... y acaba en gh pr create.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
