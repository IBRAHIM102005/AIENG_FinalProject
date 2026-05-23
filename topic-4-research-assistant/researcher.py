"""Module entrypoint required by the Topic 4 project brief.

This thin wrapper keeps the implementation in ``src.cli`` while supporting:
    python -m researcher ask "your question"
"""

from __future__ import annotations

from src.cli import main


if __name__ == "__main__":
    main()
