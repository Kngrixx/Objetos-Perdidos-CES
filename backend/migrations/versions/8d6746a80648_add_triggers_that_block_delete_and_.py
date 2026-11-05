"""add triggers that block delete and update of history

Revision ID: 8d6746a80648
Revises: f357c059a7eb
Create Date: 2026-11-03 20:38:01.882686

Revisión escrita a mano: autogenerate no detecta triggers ni funciones.
Regla del enunciado: "El backend impide eliminar físicamente filas, fotos e historial".
La aplicación no tiene rutas DELETE; estos triggers son la garantía en la base de datos:
  - ninguna tabla de negocio acepta DELETE ni TRUNCATE,
  - audit_logs y return_records son históricos: tampoco aceptan UPDATE.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d6746a80648'
down_revision = 'f357c059a7eb'
branch_labels = None
depends_on = None

BUSINESS_TABLES = [
    "roles", "users", "password_reset_tokens", "token_revocations",
    "campuses", "blocks", "departments", "object_categories", "object_types",
    "persons", "object_lost", "object_photos", "claims", "return_records", "audit_logs",
]
READ_ONLY_TABLES = ["return_records", "audit_logs"]


def upgrade():
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_delete() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'No se permite eliminar registros de la tabla %', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_update() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'La tabla % es un histórico de solo lectura', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in BUSINESS_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_no_delete BEFORE DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION prevent_delete();"
        )
        op.execute(
            f"CREATE TRIGGER trg_{table}_no_truncate BEFORE TRUNCATE ON {table} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION prevent_delete();"
        )
    for table in READ_ONLY_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_no_update BEFORE UPDATE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION prevent_update();"
        )


def downgrade():
    for table in READ_ONLY_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_no_update ON {table};")
    for table in BUSINESS_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_no_truncate ON {table};")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_no_delete ON {table};")
    op.execute("DROP FUNCTION IF EXISTS prevent_update();")
    op.execute("DROP FUNCTION IF EXISTS prevent_delete();")
