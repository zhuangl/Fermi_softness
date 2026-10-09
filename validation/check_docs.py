"""Check local Markdown link targets in files intended for the source release."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def documents():
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
    )
    if result.returncode == 0:
        return sorted({ROOT / p for p in result.stdout.decode().split("\0") if p.endswith(".md")})
    roots = [ROOT / name for name in ("docs", "validation", "research/notes", "vasp-plugin")]
    return sorted(set(ROOT.glob("*.md")).union(*(set(p.rglob("*.md")) for p in roots)))


def main():
    failures = []
    checked = 0
    pages = documents()
    for page in pages:
        body = re.sub(r"```.*?```", "", page.read_text(encoding="utf-8"), flags=re.S)
        for match in re.finditer(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
            raw = match.group(1).strip()
            target = raw[1:raw.index(">")] if raw.startswith("<") else raw.split(' "', 1)[0]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            checked += 1
            path = (page.parent / unquote(parsed.path)).resolve()
            if not path.is_relative_to(ROOT) or not path.exists():
                failures.append(f"{page.relative_to(ROOT)}: {target}")
    if failures:
        raise SystemExit("Invalid local links:\n" + "\n".join(failures))
    print(f"Checked {checked} local link targets across {len(pages)} Markdown files.")


if __name__ == "__main__":
    main()
