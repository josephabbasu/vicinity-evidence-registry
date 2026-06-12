from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db_models import RegistryUpdate, Study


SEED_PATH = Path(__file__).resolve().parent / "data" / "studies.json"


def seed_database(session: Session) -> None:
    count = session.scalar(select(func.count()).select_from(Study))
    if count:
        return

    records = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    session.add_all(Study(**record) for record in records)
    session.add(
        RegistryUpdate(
            title="Registry launched",
            description=(
                "VICINITY launched with 32 studies from the validated systematic-review "
                "extraction workbook."
            ),
        )
    )
    session.commit()
