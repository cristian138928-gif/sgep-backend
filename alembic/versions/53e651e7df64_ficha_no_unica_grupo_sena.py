"""ficha no unica - grupo SENA

Revision ID: 53e651e7df64
Revises: 6c3d62779376
Create Date: 2026-10-20 11:03:04.284357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53e651e7df64'
down_revision: Union[str, Sequence[str], None] = '6c3d62779376'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _recrear_aprendices(con_unique: bool) -> None:
    """EXPLICACIÓN: recreate controlado de 'aprendices' en SQLite (sin DROP CONSTRAINT).
    legacy_alter_table evita que el RENAME reescriba las FKs de las tablas hijas
    (evidencias, asignaciones) que referencian a 'aprendices'."""
    columnas = [
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('numero_ficha', sa.String(length=20), nullable=False),
        sa.Column('programa', sa.String(length=100), nullable=False),
        sa.Column('fecha_inicio_etapa', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_fin_etapa', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id_usuario']),
        sa.PrimaryKeyConstraint('id_usuario'),
    ]
    if con_unique:
        columnas.append(sa.UniqueConstraint('numero_ficha'))

    op.execute(sa.text('PRAGMA legacy_alter_table = ON'))
    op.execute(sa.text('ALTER TABLE aprendices RENAME TO aprendices_tmp'))
    op.create_table('aprendices', *columnas)
    op.execute(sa.text(
        'INSERT INTO aprendices (id_usuario, numero_ficha, programa, '
        'fecha_inicio_etapa, fecha_fin_etapa) '
        'SELECT id_usuario, numero_ficha, programa, '
        'fecha_inicio_etapa, fecha_fin_etapa FROM aprendices_tmp'
    ))
    op.execute(sa.text('DROP TABLE aprendices_tmp'))
    op.execute(sa.text('PRAGMA legacy_alter_table = OFF'))


def upgrade() -> None:
    """Upgrade schema."""
    # EXPLICACIÓN: SQLite no compila ColumnComment ni DROP CONSTRAINT => recreate.
    # El comment es solo metadata documental (no afecta datos); la unique SÍ debe caer
    # para que una ficha agrupe a todo el grupo SENA.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.alter_column('aprendices', 'numero_ficha',
                   existing_type=sa.VARCHAR(length=20),
                   comment='Número de ficha de SENA (ej: 3388939; compartida por el grupo)',
                   existing_comment='Número de ficha de SENA (ej: 3388939)',
                   existing_nullable=False)
        op.drop_constraint(op.f('aprendices_numero_ficha_key'), 'aprendices', type_='unique')
        return
    _recrear_aprendices(con_unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_unique_constraint(op.f('aprendices_numero_ficha_key'), 'aprendices',
                                    ['numero_ficha'], postgresql_nulls_not_distinct=False)
        op.alter_column('aprendices', 'numero_ficha',
                   existing_type=sa.VARCHAR(length=20),
                   comment='Número de ficha de SENA (ej: 3388939)',
                   existing_comment='Número de ficha de SENA (ej: 3388939; compartida por el grupo)',
                   existing_nullable=False)
        return
    _recrear_aprendices(con_unique=True)
