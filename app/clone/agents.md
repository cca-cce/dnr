## Local Python Environment

This repository uses the Python virtual environment:
~/lib/python/uv-osm

---

### Environment Activation

When running any Python-related command (python, pytest, quarto render with python, etc.),
ALWAYS prefix the command with:

source ~/lib/python/uv-osm/bin/activate && <command>

If multiple commands are needed, prefer a single bash -lc invocation that activates once and runs all steps.

---

### Package Management Policy (IMPORTANT)

This environment uses **uv** for dependency management.

DO NOT install, upgrade, or remove any Python packages without explicitly asking first.

If a dependency is required:

1. Explain why the package is needed.
2. Confirm with the user.
3. Install it using:

   source ~/lib/python/uv-osm/bin/activate && uv pip install <package>

Rules:

- Prefer `uv pip install` over `pip install`.
- Never use plain `pip install`.
- Never install packages globally.
- Never modify requirements files or pyproject.toml without confirmation.
- If a package is missing, check first before proposing installation.

---

### File System Safety Policy (IMPORTANT)

You may read and inspect files anywhere.

You may create, modify, or delete files ONLY inside:

    /tmp/
    ~/tmp/

This includes any subdirectory under /tmp/ or ~/tmp/ (e.g., /tmp/project/, /tmp/test/output.txt, ~/tmp/project/).

You must NEVER modify files outside /tmp/ or ~/tmp/ without explicit confirmation.

If changes to project files are required:
1. Write the proposed version to /tmp/ or ~/tmp/.
2. Show or explain the changes.
3. Ask for approval before modifying the original file.

Treat everything outside /tmp/ and ~/tmp/ as read-only unless explicitly approved.
