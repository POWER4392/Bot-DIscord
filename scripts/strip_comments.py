import os
import tokenize
import io
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".venv", ".git", "__pycache__", "scratch", ".agents", "tests", "scripts"}
SKIP_FILES = {"strip_comments.py"}


def strip_comments_only(source: str) -> str:
    result = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return source

    prev_end = (1, 0)

    for tok in tokens:
        ttype, tstring, tstart, tend, tline = tok

        if ttype == tokenize.COMMENT:
            pass
        else:
            srow, scol = tstart
            erow_prev, ecol_prev = prev_end

            if srow == erow_prev:
                result.append(" " * max(0, scol - ecol_prev))
            else:
                result.append("\n" * (srow - erow_prev))
                result.append(" " * scol)

            result.append(tstring)
            prev_end = tend

    output = "".join(result)
    output = re.sub(r"[ \t]+\n", "\n", output)
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output.rstrip() + "\n"


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

                if stripped.strip() != original.strip():
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
