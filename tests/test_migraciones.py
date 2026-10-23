# tests/test_migraciones.py
"""
Regresiones de esquema multi-dialecto: registry de modelos y cadena Alembic en SQLite.

EXPLICACIÓN: la app debe arrancar con DB fresca en SQLite (dev/demo) igual que
en Postgres (prod); estas pruebas atrapan migraciones con DDL no soportado.
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from app.models import Base

RAIZ = Path(__file__).resolve().parents[1]


def test_registry_modelos_registra_todas_las_tablas() -> None:
    """Test: importar app.models registra refresh_tokens y el resto en Base.metadata."""
    tablas = set(Base.metadata.tables)
    assert "refresh_tokens" in tablas
    assert "aprendices" in tablas
    assert "evidencias" in tablas
    assert "usuarios" in tablas


def _alembic(args: list[str], database_url: str) -> subprocess.CompletedProcess[str]:
    """Ejecuta alembic en subproceso con DATABASE_URL apuntando a una BD SQLite temporal."""
    env = {**os.environ, "DATABASE_URL": database_url}
    return subprocess.run(  # noqa: S603 - comando fijo del proyecto, sin shell
        [sys.executable, "-m", "alembic", *args],
        cwd=RAIZ,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )


def test_alembic_upgrade_y_downgrade_en_sqlite(tmp_path: Path) -> None:
    """Test: upgrade a head y la última revisión en sentido inverso funcionan en SQLite."""
    url = f"sqlite+aiosqlite:///{tmp_path / 'mig.db'}"

    upgrade = _alembic(["upgrade", "head"], url)
    assert upgrade.returncode == 0, upgrade.stderr

    # EXPLICACIÓN: -1 ejercita el downgrade de 53e651e7df64 (batch recreate en SQLite)
    downgrade = _alembic(["downgrade", "-1"], url)
    assert downgrade.returncode == 0, downgrade.stderr

    otra_vez = _alembic(["upgrade", "head"], url)
    assert otra_vez.returncode == 0, otra_vez.stderr


def test_numero_ficha_no_unica_en_sqlite(tmp_path: Path) -> None:
    """Test: tras upgrade, la tabla aprendices NO tiene constraint UNIQUE en numero_ficha."""
    db = tmp_path / "ficha.db"
    url = f"sqlite+aiosqlite:///{db}"

    upgrade = _alembic(["upgrade", "head"], url)
    assert upgrade.returncode == 0, upgrade.stderr

    with sqlite3.connect(db) as conn:
        indices = conn.execute("PRAGMA index_list('aprendices')").fetchall()
        uniques = []
        for fila in indices:
            nombre_idx, unico = fila[1], fila[2]
            if unico:
                columnas = [c[2] for c in conn.execute(f"PRAGMA index_info('{nombre_idx}')")]
                uniques.append(columnas)
    assert ["numero_ficha"] not in uniques
