from __future__ import annotations

from sqlalchemy import Engine, inspect, text


STUDY_COLUMNS = {
    "registry_stream": "VARCHAR(40) DEFAULT 'exposure'",
    "approval_status": "VARCHAR(40) DEFAULT 'approved'",
    "registry_version": "INTEGER DEFAULT 2",
    "added_in_version": "VARCHAR(20) DEFAULT '1.0'",
    "evidence_role": "VARCHAR(80) DEFAULT 'Exposure consequence'",
    "intervention_class": "VARCHAR(40) DEFAULT 'Not applicable'",
    "outcome_directness": "VARCHAR(80) DEFAULT 'Scope requires verification'",
    "decision_relevance": "VARCHAR(120) DEFAULT 'Research context'",
    "source_review": "VARCHAR(160) DEFAULT ''",
    "search_coverage_end": "VARCHAR(10) DEFAULT '2025-07-31'",
    "source_row": "INTEGER",
    "is_active": "BOOLEAN DEFAULT TRUE",
    "automation_status": "VARCHAR(40) DEFAULT 'manual'",
    "ingestion_candidate_id": "INTEGER",
}

# created_at for studies is dialect-specific — added in run_additive_migrations

SEARCH_RUN_COLUMNS = {
    "coverage_end_date": "DATE",
}

CANDIDATE_COLUMNS = {
    "source_url": "TEXT DEFAULT ''",
}

ELIGIBILITY_COLUMNS = {
    "source": "VARCHAR(80) DEFAULT ''",
}


def _add_missing_columns(
    connection,
    table_name: str,
    definitions: dict[str, str],
) -> None:
    inspector = inspect(connection)
    if table_name not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    for column_name, definition in definitions.items():
        if column_name in existing:
            continue
        connection.execute(
            text(
                f'ALTER TABLE "{table_name}" '
                f'ADD COLUMN "{column_name}" {definition}'
            )
        )


def run_additive_migrations(engine: Engine) -> None:
    """Apply additive schema changes that SQLAlchemy create_all cannot perform."""

    with engine.begin() as connection:
        _add_missing_columns(connection, "studies", STUDY_COLUMNS)
        # Add study timestamps with the correct dialect-specific syntax.
        inspector = inspect(connection)
        if "studies" in inspector.get_table_names():
            existing = {c["name"] for c in inspector.get_columns("studies")}
            dialect = connection.dialect.name
            if dialect == "postgresql":
                definition = "TIMESTAMPTZ DEFAULT NOW()"
            else:
                definition = "DATETIME"
            for timestamp_column in ("created_at", "updated_at"):
                if timestamp_column in existing:
                    continue
                connection.execute(
                    text(
                        f'ALTER TABLE "studies" '
                        f'ADD COLUMN "{timestamp_column}" {definition}'
                    )
                )
                if dialect == "sqlite":
                    connection.execute(
                        text(
                            f'UPDATE "studies" SET "{timestamp_column}" = '
                            "CURRENT_TIMESTAMP "
                            f'WHERE "{timestamp_column}" IS NULL'
                        )
                    )
        _add_missing_columns(connection, "search_runs", SEARCH_RUN_COLUMNS)
        _add_missing_columns(
            connection,
            "literature_candidates",
            CANDIDATE_COLUMNS,
        )
        _add_missing_columns(
            connection,
            "eligibility_results",
            ELIGIBILITY_COLUMNS,
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_studies_registry_stream "
                "ON studies (registry_stream)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_studies_approval_status "
                "ON studies (approval_status)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_studies_is_active "
                "ON studies (is_active)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_studies_automation_status "
                "ON studies (automation_status)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_studies_ingestion_candidate_id "
                "ON studies (ingestion_candidate_id)"
            )
        )
        # Widen intervention_type from VARCHAR(80) to TEXT — some values exceed 80 chars
        if connection.dialect.name == "postgresql":
            connection.execute(
                text(
                    'ALTER TABLE "studies" '
                    'ALTER COLUMN "intervention_type" TYPE TEXT'
                )
            )

        # Safety: resync the studies PK sequence after any explicit-id inserts
        if connection.dialect.name == "postgresql":
            try:
                connection.execute(
                    text(
                        "SELECT setval("
                        "'studies_id_seq', "
                        "GREATEST((SELECT COALESCE(MAX(id), 1) FROM studies), 1)"
                        ")"
                    )
                )
            except Exception:
                pass  # sequence may have a different name; explicit IDs in seed handle this
