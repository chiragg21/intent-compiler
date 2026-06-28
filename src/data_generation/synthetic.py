"""
synthetic.py
============
Template-based synthetic dataset generation.

Each template is a (nl_pattern, dsl_fn, vars_fn) triple:
  - nl_pattern : format string for the natural language input
  - dsl_fn     : lambda(vars) → DSL string
  - vars_fn    : lambda()     → dict of random variable values

Templates intentionally cover:
  1. Standard folder names  ("move pdfs from Downloads to Documents")
  2. Personal folder names  ("move photos to Sikkim")
  3. FUZZY placeholders     ("copy my resume to Desktop")
  4. Mixed                  ("move my cv folder to Job")

Public API
----------
  generate_synthetic(n_per_template)  → list[dict]
"""

import random
from collections import defaultdict

import configs.data_config as C
from src.data_generation.dsl_builder import dsl, fuzzy, rename_dsl, has_fuzzy, extract_intent

random.seed(C.RANDOM_SEED)


# ---------------------------------------------------------------------------
# Shorthand
# ---------------------------------------------------------------------------

def _r(lst: list):
    """Pick one item at random."""
    return random.choice(lst)


def _make_id(intent: str, n: int) -> str:
    return f"syn_{intent}_{n:04d}"


# ---------------------------------------------------------------------------
# Template registry
# Each entry: (nl_pattern, dsl_fn, vars_fn)
# ---------------------------------------------------------------------------

TEMPLATES: list[tuple] = [

    # ── MOVE — standard folders ────────────────────────────────────────────
    ("move all {ext} files from {src} to {dst}",
     lambda v: dsl("MOVE", src=v["src"], dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "src": _r(C.FOLDERS_SRC), "dst": _r(C.FOLDERS_DST)}),

    ("transfer {ext} files from {src} to {dst}",
     lambda v: dsl("MOVE", src=v["src"], dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "src": _r(C.FOLDERS_SRC), "dst": _r(C.FOLDERS_DST)}),

    ("put everything in {src} into {dst}",
     lambda v: dsl("MOVE", src=v["src"], dst=v["dst"], ext="*"),
     lambda: {"src": _r(C.FOLDERS_SRC), "dst": _r(C.FOLDERS_DST)}),

    ("shift all {ext} from {src} into {dst}",
     lambda v: dsl("MOVE", src=v["src"], dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "src": _r(C.FOLDERS_SRC), "dst": _r(C.FOLDERS_DST)}),

    # ── MOVE — personal folder as destination ─────────────────────────────
    ("move {ext} files to {dst}",
     lambda v: dsl("MOVE", src="Downloads", dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "dst": _r(C.FOLDERS_PERSONAL)}),

    ("move photos from {src} to {dst}",
     lambda v: dsl("MOVE", src=v["src"], dst=v["dst"], ext="jpg"),
     lambda: {"src": _r(C.FOLDERS_PERSONAL), "dst": _r(C.FOLDERS_PERSONAL)}),

    ("transfer all files from {src} to {dst}",
     lambda v: dsl("MOVE", src=v["src"], dst=v["dst"], ext="*"),
     lambda: {"src": _r(C.FOLDERS_PERSONAL), "dst": _r(C.FOLDERS_PERSONAL)}),

    # ── MOVE — FUZZY reference ─────────────────────────────────────────────
    ("move my {ref} to {dst}",
     lambda v: dsl("MOVE", src=fuzzy(v["ref"]), dst=v["dst"], ext="*"),
     lambda: {"ref": _r(C.FUZZY_REFS), "dst": _r(C.FOLDERS_DST)}),

    ("move the {ref} to {dst}",
     lambda v: dsl("MOVE", src=fuzzy(v["ref"]), dst=v["dst"], ext="*"),
     lambda: {"ref": _r(C.FUZZY_FILE_REFS), "dst": _r(C.FOLDERS_DST)}),

    ("put my {ref} in {dst}",
     lambda v: dsl("MOVE", src=fuzzy(v["ref"]), dst=v["dst"], ext="*"),
     lambda: {"ref": _r(C.FUZZY_REFS), "dst": _r(C.FOLDERS_PERSONAL)}),

    # ── COPY — standard ───────────────────────────────────────────────────
    ("copy all {ext} files from {src} to {dst}",
     lambda v: dsl("COPY", src=v["src"], dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "src": _r(C.FOLDERS_SRC), "dst": _r(C.FOLDERS_DST)}),

    ("duplicate all {ext} from {src} to {dst}",
     lambda v: dsl("COPY", src=v["src"], dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "src": _r(C.FOLDERS_SRC), "dst": _r(C.FOLDERS_DST)}),

    ("back up all {ext} files from {src} to {dst}",
     lambda v: dsl("COPY", src=v["src"], dst=v["dst"], ext=v["ext"]),
     lambda: {"ext": _r(C.EXTENSIONS), "src": _r(C.FOLDERS_PERSONAL), "dst": _r(C.FOLDERS_DST)}),

    # ── COPY — personal folder ─────────────────────────────────────────────
    ("copy everything in {src} to {dst}",
     lambda v: dsl("COPY", src=v["src"], dst=v["dst"], ext="*"),
     lambda: {"src": _r(C.FOLDERS_PERSONAL), "dst": _r(C.FOLDERS_DST)}),

    ("duplicate {src} folder to {dst}",
     lambda v: dsl("COPY", src=v["src"], dst=v["dst"], ext="*"),
     lambda: {"src": _r(C.FOLDERS_PERSONAL), "dst": _r(C.FOLDERS_PERSONAL)}),

    # ── COPY — FUZZY reference ─────────────────────────────────────────────
    ("copy my {ref} to {dst}",
     lambda v: dsl("COPY", src=fuzzy(v["ref"]), dst=v["dst"], ext="*"),
     lambda: {"ref": _r(C.FUZZY_REFS), "dst": _r(C.FOLDERS_DST)}),

    ("make a copy of my {ref} in {dst}",
     lambda v: dsl("COPY", src=fuzzy(v["ref"]), dst=v["dst"], ext="*"),
     lambda: {"ref": _r(C.FUZZY_REFS), "dst": _r(C.FOLDERS_DST)}),

    ("back up my {ref} to {dst}",
     lambda v: dsl("COPY", src=fuzzy(v["ref"]), dst=v["dst"], ext="*"),
     lambda: {"ref": _r(C.FUZZY_FILE_REFS), "dst": _r(C.FOLDERS_PERSONAL)}),

    # ── RENAME ────────────────────────────────────────────────────────────
    ("rename files replacing {frm} with {to} in {path}",
     lambda v: rename_dsl(v["path"], v["frm"], v["to"], "*"),
     lambda: {**_rename_vars(), "path": _r(C.FOLDERS_SRC)}),

    ("replace {frm} with {to} in all {ext} filenames in {path}",
     lambda v: rename_dsl(v["path"], v["frm"], v["to"], v["ext"]),
     lambda: {**_rename_vars(), "ext": _r(C.EXTENSIONS), "path": _r(C.FOLDERS_SRC)}),

    ("rename all {ext} files changing {frm} to {to} in {path}",
     lambda v: rename_dsl(v["path"], v["frm"], v["to"], v["ext"]),
     lambda: {**_rename_vars(), "ext": _r(C.EXTENSIONS), "path": _r(C.FOLDERS_PERSONAL)}),

    # ── DELETE ────────────────────────────────────────────────────────────
    ("delete all {ext} files from {path}",
     lambda v: dsl("DELETE", path=v["path"], ext=v["ext"], confirm=True),
     lambda: {"ext": _r(C.EXTENSIONS), "path": _r(C.FOLDERS_SRC)}),

    ("remove all {ext} files from {path}",
     lambda v: dsl("DELETE", path=v["path"], ext=v["ext"], confirm=True),
     lambda: {"ext": _r(C.EXTENSIONS), "path": _r(C.FOLDERS_SRC)}),

    ("clean up all {ext} files in {path}",
     lambda v: dsl("DELETE", path=v["path"], ext=v["ext"], confirm=True),
     lambda: {"ext": _r(C.EXTENSIONS), "path": _r(C.FOLDERS_SRC)}),

    # ── COMPRESS ──────────────────────────────────────────────────────────
    ("zip up {src}",
     lambda v: dsl("COMPRESS", src=v["src"], dst=f"~/backups/{v['src'].strip('./').strip('~/')}.zip", format="zip"),
     lambda: {"src": _r(C.FOLDERS_SRC)}),

    ("compress {src} as a {fmt} file",
     lambda v: dsl("COMPRESS", src=v["src"], dst=f"./archive.{v['fmt']}", format=v["fmt"]),
     lambda: {"src": _r(C.FOLDERS_PERSONAL), "fmt": _r(C.COMPRESS_FMTS)}),

    ("create a {fmt} archive of {src}",
     lambda v: dsl("COMPRESS", src=v["src"], dst=f"~/backups/archive.{v['fmt']}", format=v["fmt"]),
     lambda: {"src": _r(C.FOLDERS_SRC), "fmt": _r(C.COMPRESS_FMTS)}),

    # ── EXTRACT ───────────────────────────────────────────────────────────
    ("extract my {ref} to {dst}",
     lambda v: dsl("EXTRACT", src=fuzzy(v["ref"]), dst=v["dst"]),
     lambda: {"ref": _r(["backup zip", "archive", "tar file", "zip file"]), "dst": _r(C.FOLDERS_DST)}),

    ("unzip {ref} into {dst}",
     lambda v: dsl("EXTRACT", src=fuzzy(v["ref"]), dst=v["dst"]),
     lambda: {"ref": _r(["the archive", "the zip", "the backup"]), "dst": _r(C.FOLDERS_DST)}),

    ("unpack the archive into {dst}",
     lambda v: dsl("EXTRACT", src=fuzzy("archive"), dst=v["dst"]),
     lambda: {"dst": _r(C.FOLDERS_PERSONAL)}),

    # ── SEARCH ────────────────────────────────────────────────────────────
    ("find all {pattern} in {path}",
     lambda v: dsl("SEARCH", path=v["path"], pattern=v["pattern"], type="file", recursive=True),
     lambda: {"pattern": _r(C.SEARCH_PATTERNS), "path": _r(C.FOLDERS_SRC)}),

    ("search for {pattern} in {path}",
     lambda v: dsl("SEARCH", path=v["path"], pattern=v["pattern"], type="file", recursive=True),
     lambda: {"pattern": _r(C.SEARCH_PATTERNS), "path": _r(C.FOLDERS_PERSONAL)}),

    ("list all folders in {path}",
     lambda v: dsl("SEARCH", path=v["path"], pattern="*", type="dir", recursive=False),
     lambda: {"path": _r(C.FOLDERS_SRC)}),

    ("find {pattern} files in {path}",
     lambda v: dsl("SEARCH", path=v["path"], pattern=v["pattern"], type="file", recursive=True),
     lambda: {"pattern": _r(C.SEARCH_PATTERNS), "path": _r(C.FOLDERS_PERSONAL)}),

    # ── GIT ───────────────────────────────────────────────────────────────
    ("init a git repo here",
     lambda v: dsl("GIT_INIT", path="."),
     lambda: {}),

    ("create a git repository in this folder",
     lambda v: dsl("GIT_INIT", path="."),
     lambda: {}),

    ("start version control in the current directory",
     lambda v: dsl("GIT_INIT", path="."),
     lambda: {}),

    ("clone {url}",
     lambda v: dsl("GIT_CLONE", url=v["url"], dst=None),
     lambda: {"url": _r(C.GIT_URLS)}),

    ("download the repository from {url} to {dst}",
     lambda v: dsl("GIT_CLONE", url=v["url"], dst=v["dst"]),
     lambda: {"url": _r(C.GIT_URLS), "dst": _r(["my-project", "./app", "./service"])}),

    ("commit all changes with message {msg}",
     lambda v: dsl("GIT_COMMIT", message=v["msg"], add_all=True),
     lambda: {"msg": _r(C.COMMIT_MSGS)}),

    ("save my work with commit message {msg}",
     lambda v: dsl("GIT_COMMIT", message=v["msg"], add_all=True),
     lambda: {"msg": _r(C.COMMIT_MSGS)}),

    ("git commit {msg}",
     lambda v: dsl("GIT_COMMIT", message=v["msg"], add_all=True),
     lambda: {"msg": _r(C.COMMIT_MSGS)}),

    ("push to {branch}",
     lambda v: dsl("GIT_PUSH", remote="origin", branch=v["branch"]),
     lambda: {"branch": _r(["main", "develop", "staging"])}),

    ("push my commits to the {branch} branch",
     lambda v: dsl("GIT_PUSH", remote="origin", branch=v["branch"]),
     lambda: {"branch": _r(C.GIT_BRANCHES)}),

    ("create a new branch called {name}",
     lambda v: dsl("GIT_BRANCH", name=v["name"]),
     lambda: {"name": _r(C.GIT_BRANCHES)}),

    ("make a branch for {name}",
     lambda v: dsl("GIT_BRANCH", name=v["name"]),
     lambda: {"name": _r(C.GIT_BRANCHES)}),

    ("switch to the {branch} branch",
     lambda v: dsl("GIT_CHECKOUT", branch=v["branch"]),
     lambda: {"branch": _r(C.GIT_BRANCHES)}),

    ("checkout {branch}",
     lambda v: dsl("GIT_CHECKOUT", branch=v["branch"]),
     lambda: {"branch": _r(C.GIT_BRANCHES)}),

    # ── PYTHON ────────────────────────────────────────────────────────────
    ("create a virtual environment here",
     lambda v: dsl("PY_VENV", path=".", name="venv", python=None),
     lambda: {}),

    ("set up a venv with {python} in this project",
     lambda v: dsl("PY_VENV", path=".", name="venv", python=v["python"]),
     lambda: {"python": _r(["python3.9", "python3.10", "python3.11", "python3.12"])}),

    ("create a python environment called {name}",
     lambda v: dsl("PY_VENV", path=".", name=v["name"], python=None),
     lambda: {"name": _r(["venv", ".venv", "env", "myenv"])}),

    ("install {pkgs} into the venv",
     lambda v: dsl("PY_INSTALL", packages=v["pkgs"], venv="./venv", requirements=None),
     lambda: {"pkgs": _r(C.PY_PKGS_SETS)}),

    ("pip install {pkgs}",
     lambda v: dsl("PY_INSTALL", packages=v["pkgs"], venv=None, requirements=None),
     lambda: {"pkgs": _r(C.PY_PKGS_SETS)}),

    ("install packages from requirements.txt",
     lambda v: dsl("PY_INSTALL", packages=[], venv=None, requirements="./requirements.txt"),
     lambda: {}),

    ("install {pkgs} in the project venv",
     lambda v: dsl("PY_INSTALL", packages=v["pkgs"], venv="./venv", requirements=None),
     lambda: {"pkgs": _r(C.PY_PKGS_SETS)}),

    ("run the tests",
     lambda v: dsl("PY_TEST", path="./tests", framework="pytest", verbose=False),
     lambda: {}),

    ("run pytest in {path}",
     lambda v: dsl("PY_TEST", path=v["path"], framework="pytest", verbose=False),
     lambda: {"path": _r(["./tests", "./test", "."])}),

    ("run all unit tests with verbose output",
     lambda v: dsl("PY_TEST", path=".", framework="pytest", verbose=True),
     lambda: {}),

    ("open jupyter notebook",
     lambda v: dsl("PY_NOTEBOOK", path=".", file=None),
     lambda: {}),

    ("launch notebook in {path}",
     lambda v: dsl("PY_NOTEBOOK", path=v["path"], file=None),
     lambda: {"path": _r(["./notebooks", "./analysis", "./experiments"])}),

    ("open my {ref} notebook",
     lambda v: dsl("PY_NOTEBOOK", path=".", file=fuzzy(v["ref"] + " notebook")),
     lambda: {"ref": _r(["analysis", "training", "eda", "visualization", "reporting"])}),

    # ── SYSTEM ────────────────────────────────────────────────────────────
    ("open {app}",
     lambda v: dsl("SYS_OPEN", app=v["app"]),
     lambda: {"app": _r(C.APPS)}),

    ("launch {app}",
     lambda v: dsl("SYS_OPEN", app=v["app"]),
     lambda: {"app": _r(C.APPS)}),

    ("start {app}",
     lambda v: dsl("SYS_OPEN", app=v["app"]),
     lambda: {"app": _r(C.APPS)}),

    ("kill the {process} process",
     lambda v: dsl("SYS_KILL", process=v["process"], confirm=True),
     lambda: {"process": _r(C.PROCESSES)}),

    ("stop {process}",
     lambda v: dsl("SYS_KILL", process=v["process"], confirm=True),
     lambda: {"process": _r(C.PROCESSES)}),

    ("terminate the {process} service",
     lambda v: dsl("SYS_KILL", process=v["process"], confirm=True),
     lambda: {"process": _r(C.PROCESSES)}),

    ("how much space is left on my disk",
     lambda v: dsl("SYS_STORAGE", path="/"),
     lambda: {}),

    ("show disk usage for {path}",
     lambda v: dsl("SYS_STORAGE", path=v["path"]),
     lambda: {"path": _r(C.FOLDERS_SRC)}),

    ("check storage usage in {path}",
     lambda v: dsl("SYS_STORAGE", path=v["path"]),
     lambda: {"path": _r(C.FOLDERS_PERSONAL)}),

    ("how much ram is being used",
     lambda v: dsl("SYS_MEMORY"),
     lambda: {}),

    ("show memory usage",
     lambda v: dsl("SYS_MEMORY"),
     lambda: {}),

    ("check system memory",
     lambda v: dsl("SYS_MEMORY"),
     lambda: {}),

    # ── DEV UTILITIES ─────────────────────────────────────────────────────
    ("organize {path} by file type",
     lambda v: dsl("DEV_ORGANIZE", path=v["path"], strategy="by_ext"),
     lambda: {"path": _r(["Downloads", "Desktop", "Documents"] + C.FOLDERS_PERSONAL)}),

    ("sort files in {path} by date",
     lambda v: dsl("DEV_ORGANIZE", path=v["path"], strategy="by_date"),
     lambda: {"path": _r(["Downloads", "Desktop"] + C.FOLDERS_PERSONAL)}),

    ("tidy up {path}",
     lambda v: dsl("DEV_ORGANIZE", path=v["path"], strategy="by_ext"),
     lambda: {"path": _r(["Downloads", "Desktop"] + C.FOLDERS_PERSONAL)}),

    ("clean up pycache files in {path}",
     lambda v: dsl("DEV_CLEAN", path=v["path"], targets=["__pycache__", "*.pyc"], confirm=True),
     lambda: {"path": _r([".", "./src", "./api", "./app"])}),

    ("remove build artifacts from {path}",
     lambda v: dsl("DEV_CLEAN", path=v["path"], targets=["__pycache__", "*.pyc", "*.tmp"], confirm=True),
     lambda: {"path": _r([".", "./src", "./api"])}),

    ("delete {targets} from {path}",
     lambda v: dsl("DEV_CLEAN", path=v["path"], targets=v["targets"], confirm=True),
     lambda: {"targets": _r(C.CLEAN_TARGETS), "path": _r([".", "./src"])}),

    ("archive logs older than {days} days",
     lambda v: dsl("DEV_ARCHIVE_LOGS", path="./logs", older_than_days=v["days"], dst="./archive", ext="log"),
     lambda: {"days": _r(C.LOG_DAYS)}),

    ("move old log files to archive",
     lambda v: dsl("DEV_ARCHIVE_LOGS", path="./logs", older_than_days=7, dst="./archive", ext="log"),
     lambda: {}),

    ("archive {path} logs older than {days} days to {dst}",
     lambda v: dsl("DEV_ARCHIVE_LOGS", path=v["path"], older_than_days=v["days"], dst=v["dst"], ext="log"),
     lambda: {
         "path": _r(["./logs", "~/projects/api/logs", "./var/logs"]),
         "days": _r(C.LOG_DAYS),
         "dst":  _r(["./archive", "~/archive", "./old_logs"]),
     }),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rename_vars() -> dict:
    """Return a random (frm, to) pair from RENAME_PAIRS."""
    frm, to = _r(C.RENAME_PAIRS)
    return {"frm": frm, "to": to}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_synthetic(n_per_template: int = C.SYNTHETIC_PER_TEMPLATE) -> list[dict]:
    """
    Generate synthetic dataset records by instantiating each template
    n_per_template times with random variable values.

    Records are shuffled before returning.
    """
    records:  list[dict]      = []
    counters: dict[str, int]  = defaultdict(int)
    skipped   = 0

    for nl_pattern, dsl_fn, vars_fn in TEMPLATES:
        for _ in range(n_per_template):
            try:
                vars_  = vars_fn()
                nl     = nl_pattern.format(**vars_)
                output = dsl_fn(vars_)
            except Exception as exc:
                skipped += 1
                print(f"  [skip] template error: {exc!r} | pattern='{nl_pattern}'")
                continue

            intent = extract_intent(output)
            counters[intent] += 1

            records.append({
                "id":        _make_id(intent, counters[intent]),
                "tier":      "synthetic",
                "intent":    intent,
                "input":     nl,
                "output":    output,
                "source":    "template",
                "has_fuzzy": has_fuzzy(output),
            })

    if skipped:
        print(f"  [warn] {skipped} template(s) skipped due to errors")

    random.shuffle(records)
    return records