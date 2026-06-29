"""
gold.py
=======
Gold dataset — manually authored, never auto-generated.

Rules:
  - Every example is written by hand in GOLD_EXAMPLES below
  - Minimum 10 examples per operation type
  - Covers: basic use, optional params, FUZZY placeholder, edge cases
  - Never modified after initial creation (treat as append-only)
  - Never used for training — evaluation only

Public API
----------
  generate_gold()  → list[dict]
"""

from collections import defaultdict

from src.data_generation.dsl_builder import dsl, fuzzy, rename_dsl, rename_file_dsl, has_fuzzy, extract_intent


# ---------------------------------------------------------------------------
# ID helper
# ---------------------------------------------------------------------------

def _make_id(intent: str, n: int) -> str:
    return f"gold_{intent}_{n:04d}"


# ---------------------------------------------------------------------------
# Raw examples
# Each entry: {"intent": str, "input": str, "output": str}
# ---------------------------------------------------------------------------

_RAW: list[dict] = [

    # ── MOVE ──────────────────────────────────────────────────────────────
    {"intent": "MOVE", "input": "move all pdfs from downloads to notes",
     "output": dsl("MOVE", src="Downloads", dst="Notes", ext="pdf")},

    {"intent": "MOVE", "input": "transfer csv files from desktop to projects folder",
     "output": dsl("MOVE", src="Desktop", dst="./projects", ext="csv")},

    {"intent": "MOVE", "input": "move everything from downloads to documents",
     "output": dsl("MOVE", src="Downloads", dst="Documents", ext="*")},

    {"intent": "MOVE", "input": "shift all images from pictures to backup",
     "output": dsl("MOVE", src="Pictures", dst="~/backup", ext="jpg")},

    {"intent": "MOVE", "input": "move my resume to the desktop",
     "output": dsl("MOVE", src=fuzzy("resume"), dst="Desktop", ext="pdf")},

    {"intent": "MOVE", "input": "put all log files from projects into archive",
     "output": dsl("MOVE", src="./projects", dst="~/archive", ext="log")},

    {"intent": "MOVE", "input": "move photos from the sikkim trip to travel folder",
     "output": dsl("MOVE", src="Sikkim", dst="Travel", ext="jpg")},

    {"intent": "MOVE", "input": "transfer all documents from job folder to cv",
     "output": dsl("MOVE", src="Job", dst="CV", ext="pdf")},

    {"intent": "MOVE", "input": "move restaurant photos to food folder",
     "output": dsl("MOVE", src="Restaurant", dst="Food", ext="jpg")},

    {"intent": "MOVE", "input": "shift my tax documents to finance folder",
     "output": dsl("MOVE", src=fuzzy("tax documents"), dst="Finance", ext="pdf")},

    # ── COPY ──────────────────────────────────────────────────────────────
    {"intent": "COPY", "input": "copy my resume to the desktop",
     "output": dsl("COPY", src=fuzzy("resume"), dst="Desktop", ext="pdf")},

    {"intent": "COPY", "input": "duplicate all images from pictures to external drive",
     "output": dsl("COPY", src="Pictures", dst="~/external", ext="*")},

    {"intent": "COPY", "input": "copy all pdfs from documents to backup",
     "output": dsl("COPY", src="Documents", dst="~/backup", ext="pdf")},

    {"intent": "COPY", "input": "copy the config file to home directory",
     "output": dsl("COPY", src=fuzzy("config file"), dst="Home", ext="*")},

    {"intent": "COPY", "input": "copy all python files from src to backup",
     "output": dsl("COPY", src="./src", dst="./backup", ext="py")},

    {"intent": "COPY", "input": "back up my cv folder to documents",
     "output": dsl("COPY", src="CV", dst="Documents", ext="*")},

    {"intent": "COPY", "input": "copy sikkim trip photos to family folder",
     "output": dsl("COPY", src="Sikkim", dst="Family", ext="jpg")},

    {"intent": "COPY", "input": "make a copy of the offer letter in job folder",
     "output": dsl("COPY", src=fuzzy("offer letter"), dst="Job", ext="pdf")},

    {"intent": "COPY", "input": "copy all invoices from finance to backup",
     "output": dsl("COPY", src="Finance", dst="~/backup", ext="pdf")},

    {"intent": "COPY", "input": "duplicate goa photos to vacation folder",
     "output": dsl("COPY", src="Goa", dst="Vacation", ext="jpg")},

    # ── RENAME ────────────────────────────────────────────────────────────
    {"intent": "RENAME", "input": "rename all files with draft_ prefix to final_ in reports",
     "output": rename_dsl("./reports", "draft_", "final_", "docx")},

    {"intent": "RENAME", "input": "replace old_ with new_ in all filenames in documents",
     "output": rename_dsl("Documents", "old_", "new_", "*")},

    {"intent": "RENAME", "input": "rename all jpg files replacing img with photo in pictures",
     "output": rename_dsl("Pictures", "img", "photo", "jpg")},

    {"intent": "RENAME", "input": "rename test_ prefix to prod_ for all py files in src",
     "output": rename_dsl("./src", "test_", "prod_", "py")},

    {"intent": "RENAME", "input": "replace 2023 with 2024 in all filenames in reports",
     "output": rename_dsl("./reports", "2023", "2024", "*")},

    # ── DELETE ────────────────────────────────────────────────────────────
    {"intent": "DELETE", "input": "delete all temp files from downloads",
     "output": dsl("DELETE", path="Downloads", ext="tmp", confirm=True)},

    {"intent": "DELETE", "input": "remove all log files from the logs folder",
     "output": dsl("DELETE", path="./logs", ext="log", confirm=True)},

    {"intent": "DELETE", "input": "clean up all .pyc files in the project",
     "output": dsl("DELETE", path=".", pattern="*.pyc", confirm=True)},

    {"intent": "DELETE", "input": "delete all zip files from downloads",
     "output": dsl("DELETE", path="Downloads", ext="zip", confirm=True)},

    {"intent": "DELETE", "input": "remove all backup files from the workspace",
     "output": dsl("DELETE", path=".", pattern="*.bak", confirm=True)},

    # ── COMPRESS ──────────────────────────────────────────────────────────
    {"intent": "COMPRESS", "input": "zip up my projects folder",
     "output": dsl("COMPRESS", src="./projects", dst="~/backups/projects.zip", format="zip")},

    {"intent": "COMPRESS", "input": "compress the api directory into a tar file",
     "output": dsl("COMPRESS", src="./api", dst="./api.tar", format="tar")},

    {"intent": "COMPRESS", "input": "archive the data folder as a zip",
     "output": dsl("COMPRESS", src="./data", dst="./data.zip", format="zip")},

    {"intent": "COMPRESS", "input": "create a zip backup of documents",
     "output": dsl("COMPRESS", src="Documents", dst="~/backups/documents.zip", format="zip")},

    {"intent": "COMPRESS", "input": "compress the sikkim photos into a zip",
     "output": dsl("COMPRESS", src="Sikkim", dst="~/backups/sikkim.zip", format="zip")},

    # ── EXTRACT ───────────────────────────────────────────────────────────
    {"intent": "EXTRACT", "input": "extract the backup zip to restored folder",
     "output": dsl("EXTRACT", src=fuzzy("backup zip"), dst="./restored")},

    {"intent": "EXTRACT", "input": "unzip the archive to downloads",
     "output": dsl("EXTRACT", src=fuzzy("archive"), dst="Downloads")},

    {"intent": "EXTRACT", "input": "unpack the tar file into projects",
     "output": dsl("EXTRACT", src=fuzzy("tar file"), dst="./projects")},

    {"intent": "EXTRACT", "input": "extract data.zip to the data directory",
     "output": dsl("EXTRACT", src="./data.zip", dst="./data")},

    {"intent": "EXTRACT", "input": "unzip release.zip into the build folder",
     "output": dsl("EXTRACT", src="./release.zip", dst="./build")},

    # ── SEARCH ────────────────────────────────────────────────────────────
    {"intent": "SEARCH", "input": "find all python files in my projects",
     "output": dsl("SEARCH", path="./projects", pattern="*.py", type="file", recursive=True)},

    {"intent": "SEARCH", "input": "search for any csv files in documents",
     "output": dsl("SEARCH", path="Documents", pattern="*.csv", type="file", recursive=True)},

    {"intent": "SEARCH", "input": "list all folders in downloads",
     "output": dsl("SEARCH", path="Downloads", pattern="*", type="dir", recursive=False)},

    {"intent": "SEARCH", "input": "find all log files in the project directory",
     "output": dsl("SEARCH", path=".", pattern="*.log", type="file", recursive=True)},

    {"intent": "SEARCH", "input": "search for pdfs in job folder",
     "output": dsl("SEARCH", path="Job", pattern="*.pdf", type="file", recursive=True)},

    # ── GIT ───────────────────────────────────────────────────────────────
    {"intent": "GIT_INIT", "input": "init a git repo here",
     "output": dsl("GIT_INIT", path=".")},

    {"intent": "GIT_INIT", "input": "create a new git project in this folder",
     "output": dsl("GIT_INIT", path=".")},

    {"intent": "GIT_CLONE", "input": "clone https://github.com/user/repo.git",
     "output": dsl("GIT_CLONE", url="https://github.com/user/repo.git", dst=None)},

    {"intent": "GIT_CLONE", "input": "download the repo to my-project",
     "output": dsl("GIT_CLONE", url="https://github.com/user/project.git", dst="my-project")},

    {"intent": "GIT_COMMIT", "input": "commit all changes with message fix typo",
     "output": dsl("GIT_COMMIT", message="fix typo", add_all=True)},

    {"intent": "GIT_COMMIT", "input": "save my changes with commit message add login endpoint",
     "output": dsl("GIT_COMMIT", message="add login endpoint", add_all=True)},

    {"intent": "GIT_PUSH", "input": "push to main",
     "output": dsl("GIT_PUSH", remote="origin", branch="main")},

    {"intent": "GIT_PUSH", "input": "push my commits to the dev branch",
     "output": dsl("GIT_PUSH", remote="origin", branch="dev")},

    {"intent": "GIT_BRANCH", "input": "create a new branch called feature/auth",
     "output": dsl("GIT_BRANCH", name="feature/auth")},

    {"intent": "GIT_CHECKOUT", "input": "switch to the develop branch",
     "output": dsl("GIT_CHECKOUT", branch="develop")},

    # ── PYTHON ────────────────────────────────────────────────────────────
    {"intent": "PY_VENV", "input": "create a virtual environment here",
     "output": dsl("PY_VENV", path=".", name="venv", python=None)},

    {"intent": "PY_VENV", "input": "set up a venv with python 3.11 in this project",
     "output": dsl("PY_VENV", path=".", name="venv", python="python3.11")},

    {"intent": "PY_INSTALL", "input": "install numpy and pandas into the venv",
     "output": dsl("PY_INSTALL", packages=["numpy", "pandas"], venv="./venv", requirements=None)},

    {"intent": "PY_INSTALL", "input": "pip install requests flask",
     "output": dsl("PY_INSTALL", packages=["requests", "flask"], venv=None, requirements=None)},

    {"intent": "PY_INSTALL", "input": "install packages from requirements.txt",
     "output": dsl("PY_INSTALL", packages=[], venv=None, requirements="./requirements.txt")},

    {"intent": "PY_TEST", "input": "run the tests",
     "output": dsl("PY_TEST", path="./tests", framework="pytest", verbose=False)},

    {"intent": "PY_TEST", "input": "run pytest with verbose output",
     "output": dsl("PY_TEST", path=".", framework="pytest", verbose=True)},

    {"intent": "PY_NOTEBOOK", "input": "open jupyter notebook",
     "output": dsl("PY_NOTEBOOK", path=".", file=None)},

    {"intent": "PY_NOTEBOOK", "input": "launch the analysis notebook",
     "output": dsl("PY_NOTEBOOK", path="./notebooks", file=fuzzy("analysis notebook"))},

    # ── SYSTEM ────────────────────────────────────────────────────────────
    {"intent": "SYS_OPEN", "input": "open firefox",
     "output": dsl("SYS_OPEN", app="Firefox")},

    {"intent": "SYS_OPEN", "input": "launch vs code",
     "output": dsl("SYS_OPEN", app="Visual Studio Code")},

    {"intent": "SYS_KILL", "input": "kill the node process",
     "output": dsl("SYS_KILL", process="node", confirm=True)},

    {"intent": "SYS_KILL", "input": "stop the python server running on my machine",
     "output": dsl("SYS_KILL", process="python", confirm=True)},

    {"intent": "SYS_STORAGE", "input": "how much space is left on my disk",
     "output": dsl("SYS_STORAGE", path="/")},

    {"intent": "SYS_STORAGE", "input": "show disk usage for the projects folder",
     "output": dsl("SYS_STORAGE", path="./projects")},

    {"intent": "SYS_MEMORY", "input": "how much ram is being used",
     "output": dsl("SYS_MEMORY")},

    {"intent": "SYS_MEMORY", "input": "show current memory usage",
     "output": dsl("SYS_MEMORY")},

    # ── DEV UTILITIES ─────────────────────────────────────────────────────
    {"intent": "DEV_ORGANIZE", "input": "organize downloads by file type",
     "output": dsl("DEV_ORGANIZE", path="Downloads", strategy="by_ext")},

    {"intent": "DEV_ORGANIZE", "input": "sort my desktop files by date",
     "output": dsl("DEV_ORGANIZE", path="Desktop", strategy="by_date")},

    {"intent": "DEV_CLEAN", "input": "clean up pycache files in the api project",
     "output": dsl("DEV_CLEAN", path="./api", targets=["__pycache__", "*.pyc"], confirm=True)},

    {"intent": "DEV_CLEAN", "input": "remove build artifacts from the project",
     "output": dsl("DEV_CLEAN", path=".", targets=["__pycache__", "*.pyc", "*.tmp"], confirm=True)},

    {"intent": "DEV_ARCHIVE_LOGS", "input": "archive logs older than 30 days",
     "output": dsl("DEV_ARCHIVE_LOGS", path="./logs", older_than_days=30, dst="./archive", ext="log")},

    {"intent": "DEV_ARCHIVE_LOGS", "input": "move old log files to archive folder",
     "output": dsl("DEV_ARCHIVE_LOGS", path="./logs", older_than_days=7, dst="./archive", ext="log")},

    # ── MKDIR ─────────────────────────────────────────────────────────────
    {"intent": "MKDIR", "input": "create a folder called Resume",
     "output": dsl("MKDIR", path=".", name="Resume", exist_ok=True)},

    {"intent": "MKDIR", "input": "make a new folder named Projects on the desktop",
     "output": dsl("MKDIR", path="Desktop", name="Projects", exist_ok=True)},

    {"intent": "MKDIR", "input": "create a Work directory in documents",
     "output": dsl("MKDIR", path="Documents", name="Work", exist_ok=True)},

    {"intent": "MKDIR", "input": "make a folder for my trip photos",
     "output": dsl("MKDIR", path=".", name="trip photos", exist_ok=True)},

    {"intent": "MKDIR", "input": "add a new directory called archive here",
     "output": dsl("MKDIR", path=".", name="archive", exist_ok=True)},

    # ── LIST ──────────────────────────────────────────────────────────────
    {"intent": "LIST", "input": "show me what's in Downloads",
     "output": dsl("LIST", path="Downloads", type="all", pattern="*")},

    {"intent": "LIST", "input": "list all files in the current folder",
     "output": dsl("LIST", path=".", type="file", pattern="*")},

    {"intent": "LIST", "input": "show folders in my documents",
     "output": dsl("LIST", path="Documents", type="dir", pattern="*")},

    {"intent": "LIST", "input": "list all pdfs here",
     "output": dsl("LIST", path=".", type="file", pattern="*.pdf")},

    {"intent": "LIST", "input": "what is inside the project directory",
     "output": dsl("LIST", path="./project", type="all", pattern="*")},

    # ── RENAME_FILE ───────────────────────────────────────────────────────
    {"intent": "RENAME_FILE", "input": "rename my resume to chirag_cv_2024.pdf",
     "output": rename_file_dsl(fuzzy("resume"), "chirag_cv_2024.pdf")},

    {"intent": "RENAME_FILE", "input": "change the name of config.json to config.old.json",
     "output": rename_file_dsl("config.json", "config.old.json")},

    {"intent": "RENAME_FILE", "input": "rename the presentation to final_deck.pptx",
     "output": rename_file_dsl(fuzzy("presentation"), "final_deck.pptx")},

    {"intent": "RENAME_FILE", "input": "rename report.docx to report_v2.docx",
     "output": rename_file_dsl("report.docx", "report_v2.docx")},

    {"intent": "RENAME_FILE", "input": "rename this script to run.py",
     "output": rename_file_dsl(fuzzy("script"), "run.py")},

    # ── OPEN_FILE ─────────────────────────────────────────────────────────
    {"intent": "OPEN_FILE", "input": "open my resume",
     "output": dsl("OPEN_FILE", src=fuzzy("resume"), app=None)},

    {"intent": "OPEN_FILE", "input": "open this config file in vscode",
     "output": dsl("OPEN_FILE", src=fuzzy("config file"), app="Visual Studio Code")},

    {"intent": "OPEN_FILE", "input": "open the budget spreadsheet",
     "output": dsl("OPEN_FILE", src=fuzzy("budget spreadsheet"), app=None)},

    {"intent": "OPEN_FILE", "input": "open notes.txt",
     "output": dsl("OPEN_FILE", src="notes.txt", app=None)},

    {"intent": "OPEN_FILE", "input": "launch the presentation",
     "output": dsl("OPEN_FILE", src=fuzzy("presentation"), app=None)},
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_gold() -> list[dict]:
    """
    Build and return the gold dataset as a list of record dicts.

    Each record has:
      id, tier, intent, input, output, source, has_fuzzy
    """
    records: list[dict]        = []
    counters: dict[str, int]   = defaultdict(int)

    for raw in _RAW:
        intent = raw["intent"]
        counters[intent] += 1
        records.append({
            "id":        _make_id(intent, counters[intent]),
            "tier":      "gold",
            "intent":    intent,
            "input":     raw["input"],
            "output":    raw["output"],
            "source":    "manual",
            "has_fuzzy": has_fuzzy(raw["output"]),
        })

    return records