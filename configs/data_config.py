"""
config.py
=========
Single source of truth for all constants, paths, and vocabulary banks.

To add new folder names, fuzzy references, or extensions:
  → edit the vocab banks in this file only.
  → no other file needs to change.

To change output paths or split ratios:
  → edit the PATHS and SPLIT sections below.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR      = Path("data")
GOLD_DIR      = ROOT_DIR / "gold"
SYNTHETIC_DIR = ROOT_DIR / "synthetic"
OOD_DIR       = ROOT_DIR / "ood"
STATS_FILE    = ROOT_DIR / "stats.json"

# ---------------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------------

SPLIT_RATIOS = {"train": 0.80, "val": 0.10, "test": 0.10}

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

RANDOM_SEED = 42

# How many times each synthetic template is instantiated (before paraphrase)
SYNTHETIC_PER_TEMPLATE = 10

# ---------------------------------------------------------------------------
# Vocabulary banks
# ---------------------------------------------------------------------------
# Three distinct roles for folder names — do not mix them:
#
#   FOLDERS_STANDARD  : OS-level well-known folders (always resolve to real paths)
#   FOLDERS_PERSONAL  : User-created named folders  (literal path tokens)
#   FOLDERS_SRC       : Union used in src/path positions
#   FOLDERS_DST       : Union used in dst positions
#
# Two distinct roles for fuzzy references:
#
#   FUZZY_FILE_REFS   : Descriptions of files        ("my resume", "the config")
#   FUZZY_FOLDER_REFS : Descriptions of folders      ("my trip folder", "work stuff")
#   FUZZY_REFS        : Union of both
# ---------------------------------------------------------------------------

# Standard OS-level shortcuts the executor knows how to resolve
FOLDERS_STANDARD: list[str] = [
    "Downloads", "Desktop", "Documents",
    "Pictures",  "Videos",  "Music", "Home",
]

# User-created personal folders — model must learn these are valid literal paths,
# NOT fuzzy references. Covers: travel, food, career, finance, study, personal.
#
# ↓ ADD YOUR OWN FOLDER NAMES HERE ↓
FOLDERS_PERSONAL: list[str] = [
    # Travel & trips
    "Sikkim", "Manali", "Goa", "Europe",
    "Trip",   "Trips",  "Travel", "Vacation",

    # Food & places
    "Restaurant", "Restaurants", "Food", "Recipes",

    # Career & documents
    "Job",    "CV",     "Resume",  "Work",     "Office",
    "Applications", "Interviews", "Offer_Letters",

    # Finance
    "Finance", "Taxes", "Invoices", "Bills", "Bank_Statements",

    # Study & learning
    "College", "Study",    "Courses",       "Assignments",
    "Research","Notes",    "Lecture_Notes",

    # Personal & media
    "Family",  "Friends",  "Wedding",   "Events",
    "Screenshots", "Wallpapers", "Memes",

    # Projects & code
    "Projects", "Side_Projects", "Archive", "Backup",
    "my_app", "test_dir", "src_code", "build_output", "temp_files",

    # Health
    "Medical", "Reports", "Prescriptions",
]

# Source and destination pools — both standard and personal folders appear here
FOLDERS_SRC: list[str] = (
    FOLDERS_STANDARD
    + FOLDERS_PERSONAL
    + ["./data", "./logs", "./reports", "./src", "~/projects", "./backup"]
)

FOLDERS_DST: list[str] = (
    FOLDERS_STANDARD
    + FOLDERS_PERSONAL
    + ["~/archive", "~/backup", "./processed", "./output", "./build"]
)

# File extensions
EXTENSIONS: list[str] = [
    "pdf", "csv", "txt",  "py",   "log",
    "docx","xlsx","jpg",  "jpeg", "png",
    "mp4", "json","zip",  "tar",  "md",
]

# Fuzzy references — file level (user describes a file, not a folder)
FUZZY_FILE_REFS: list[str] = [
    "resume",            "cv",                 "cover letter",
    "offer letter",      "config file",        "settings file",
    "credentials file",  "old logs",           "error log",
    "data file",         "dataset",            "notebook",
    "analysis notebook", "report",             "monthly report",
    "quarterly report",  "invoice",            "tax document",
    "bank statement",    "project proposal",   "presentation",
    "backup file",       "profile photo",      "profile picture",
    "id card",           "passport scan",      "aadhar copy",
]

# Fuzzy references — folder level (user describes a folder ambiguously)
FUZZY_FOLDER_REFS: list[str] = [
    "trip folder",           "travel folder",       "vacation folder",
    "old project folder",    "work folder",         "job folder",
    "college folder",        "study material folder",
    "photo album",           "event photos folder",
    "finance folder",        "tax documents folder",
    "restaurant photos",     "food photos",
    "family photos folder",  "wedding photos",
    "old backup folder",     "archived files",
    "medical records folder","health documents",
]

# Specific file names for RENAME_FILE and OPEN_FILE
FILE_NAMES: list[str] = [
    "resume.pdf", "config.json", "settings.yaml", "presentation.pptx", 
    "report_q1.docx", "budget.xlsx", "vacation_pic.jpg", "notes.txt"
]

# Union — used in generic templates that don't distinguish file vs folder
FUZZY_REFS: list[str] = FUZZY_FILE_REFS + FUZZY_FOLDER_REFS

# Git
GIT_BRANCHES: list[str] = [
    "main", "develop", "feature/auth", "feature/payments",
    "hotfix/login", "release/v2", "staging", "feature/api",
]
GIT_URLS: list[str] = [
    "https://github.com/user/repo.git",
    "https://github.com/org/project.git",
    "git@github.com:user/app.git",
]
COMMIT_MSGS: list[str] = [
    "fix typo",             "add login endpoint",     "update readme",
    "refactor auth module", "fix null pointer",       "add unit tests",
    "update dependencies",  "fix pagination bug",     "add dark mode",
    "optimize db queries",  "fix memory leak",
]

# Python
PY_PKGS_SETS: list[list[str]] = [
    ["numpy", "pandas"],           ["requests", "flask"],
    ["scikit-learn", "matplotlib"],["fastapi", "uvicorn"],
    ["django", "gunicorn"],        ["pytest", "coverage"],
    ["torch", "torchvision"],      ["sqlalchemy", "alembic"],
    ["pydantic", "httpx"],         ["celery", "redis"],
]

# System
APPS: list[str] = [
    "Firefox", "Visual Studio Code", "Terminal",
    "Spotify", "Chrome", "Slack", "Postman", "VLC",
    "Obsidian", "Notion",
]
PROCESSES: list[str] = [
    "node", "python", "java", "nginx",
    "postgres", "redis", "chrome", "jupyter",
    "flask", "uvicorn",
]

# File ops misc
RENAME_PAIRS: list[tuple[str, str]] = [
    ("draft_", "final_"), ("old_",  "new_"),
    ("test_",  "prod_"),  ("2023",  "2024"),
    ("img",    "photo"),  ("tmp_",  ""),
    ("backup_",""),
]
LOG_DAYS: list[int]           = [3, 7, 14, 30, 60, 90]
CLEAN_TARGETS: list[list[str]] = [
    ["__pycache__", "*.pyc"],
    ["*.tmp", "*.bak"],
    ["__pycache__", "*.pyc", "*.tmp"],
    ["*.log", "*.tmp"],
    ["node_modules", "*.cache"],
]
COMPRESS_FMTS: list[str]    = ["zip", "tar"]
SEARCH_PATTERNS: list[str]  = [
    "*.py",    "*.csv",    "*.log",  "*.pdf",
    "*.txt",   "*.json",   "*.md",   "*.jpg",
    "report*", "backup*",  "*.config",
]
ORGANIZE_STRATS: list[str] = ["by_ext", "by_date"]