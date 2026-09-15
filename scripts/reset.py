"""Drop all tables and recreate them empty.

Run: python scripts/reset.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, engine
from app import models  # IMPORTANT: registers all models with Base.metadata


if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    print("Tables dropped and recreated. Run: python scripts/seed.py")