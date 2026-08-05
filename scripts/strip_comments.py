import os
import tokenize
import io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".venv", ".git", "__pycache__", "scratch", ".agents", "tests", "scripts"}
SKIP_FILES = {"strip_comments.py"}


def strip_comments_only(source: str) -> str:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return source

    lines = source.splitlines(keepends=True)

    comment_lines = set()
    inline_comment_cols = {}

    for tok in tokens:
        ttype, tstring, tstart, tend, tline = tok
        if ttype == tokenize.COMMENT:
            row, col = tstart
            if tline[:col].strip() == "":
                comment_lines.add(row)
            else:
                inline_comment_cols[row] = col

    result = []
    prev_blank = False
    for i, line in enumerate(lines, start=1):
        if i in comment_lines:
            continue

        if i in inline_comment_cols:
            col = inline_comment_cols[i]
            line = line[:col].rstrip() + "\n"

        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        prev_blank = is_blank
        result.append(line)

    out = "".join(result)
    if out and not out.endswith("\n"):
        out += "\n"
    return out


def process_project(root: str):
    changed = 0
    skipped = 0
    errors = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            if not fname.endswith(".py") or fname in SKIP_FILES:
                continue

            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root)

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    original = f.read()

                stripped = strip_comments_only(original)

                if stripped != original:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(stripped)
                    print(f"  [OK] {rel}")
                    changed += 1
                else:
                    skipped += 1

            except Exception as e:
                print(f"  [LOI] {rel}: {e}")
                errors += 1

    print(f"\nHoan thanh: {changed} file da xoa comment, {skipped} khong doi, {errors} loi.")


if __name__ == "__main__":
    print(f"[STRIP COMMENTS] Xu ly: {ROOT}\n")
    process_project(ROOT)
    print("[DONE]")
