# commit title
backend: document migration guard rules and add rollforward backup runbooks

# changed file scope
- src/backend/BACKEND.md
- src/backend/README.md
- src/backend/MIGRATION_ROLLFORWARD.md
- src/backend/DB_BACKUP_RESTORE.md

# reason
- Establish de facto migration operational rules without introducing script-enforced policy.
- Provide explicit rollforward-first incident handling steps for Alembic failures.
- Provide concrete backup/restore procedures for postgres and local sqlite.

# impact
- Team has a single documented policy for alembic revision naming and length.
- Migration incidents can be handled with a consistent rollforward playbook.
- Backup and restore operations are standardized and reusable across local/external DB environments.
