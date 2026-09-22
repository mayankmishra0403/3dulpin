"""CLI entry: synthesize the demo locality dataset.

Usage (from backend/):
    .venv/bin/python -m app.scripts.generate_demo [data_dir] [--seed N]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.datagen.generator import main  # noqa: E402

if __name__ == "__main__":
    main()