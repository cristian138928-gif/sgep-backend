# seed_demo.py
"""
SIEMBRA DE DEMO: usuarios + evidencias de todos los estados, reproducible.

Uso (demo Docker, PDFs caen en el volumen montada):
    docker compose exec api python seed_demo.py

Uso (desarrollo local):
    uv run python seed_demo.py

EXPLICACIÓN: idempotente — si los correos demo ya existen, no reescribe nada
(asesinar datos en vivo justo antes de presentar es la peor sorpresa posible).
"""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database.connection import AsyncSessionLocal
from app.models.usuario import (
    Aprendiz,
    AsignacionSeguimiento,
    Coordinador,
    Evidencia,
    Instructor,
    Retroalimentacion,
    UsuarioBase,
)

PASS_DEMO = "Demo1234!"
UPLOAD_DIR = Path("uploads")

PDF_MINIMO = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


def _usuarios_demo() -> dict:
    """Contratos de los 4 usuarios demo (correos fijos y documentados)."""
    return {
        "coordinador": {
            "cls": Coordinador,
            "email": "coordinador.demo@sena.edu.co",
            "extra": {"departamento": "Tecnologia"},
        },
        "instructor": {
            "cls": Instructor,
            "email": "instructor.demo@sena.edu.co",
            "extra": {
                "centro_formacion": "Centro de Formacion de Software",
                "especialidad": "Desarrollo de Software",
            },
        },
        "aprendiz1": {
            "cls": Aprendiz,
            "email": "aprendiz.demo@sena.edu.co",
            "extra": {"numero_ficha": "3388939", "programa": "ADSO"},
        },
        "aprendiz2": {
            "cls": Aprendiz,
            "email": "aprendiz2.demo@sena.edu.co",
            "extra": {"numero_ficha": "3388939", "programa": "ADSO"},
        },
    }


async def _crear_usuario(db, clave: str, spec: dict, nombre: str, documento: str):
    """Crea un usuario demo si su correo no existe. Devuelve la instancia."""
    existente = (
        await db.execute(
            select(UsuarioBase).where(
                UsuarioBase.correo_institucional == spec["email"]
            )
        )
    ).scalars().first()
    if existente is not None:
        print(f"    {clave}: ya existe ({spec['email']}) -> skip")
        return existente, False

    usuario = spec["cls"](
        nombre_completo=nombre,
        correo_institucional=spec["email"],
        numero_documento=documento,
        tipo_documento="CC",
        rol={
            "coordinador": "coordinador",
            "instructor": "instructor",
            "aprendiz1": "aprendiz",
            "aprendiz2": "aprendiz",
        }[clave],
        **spec["extra"],
    )
    usuario.establecer_contrasena(PASS_DEMO)
    db.add(usuario)
    await db.flush()
    print(f"    {clave}: creado ({spec['email']})")
    return usuario, True


async def _crear_evidencia(db, id_aprendiz: int, titulo: str, tipo: str,
                           estado: str, observaciones: str | None,
                           id_instructor: int) -> None:
    """Crea evidencia + PDF en disco + retroalimentación si aplica."""
    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo=titulo,
        tipo_formato=tipo,
        ruta_archivo_pdf="",
        estado=estado,
        fecha_deadline=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(evidencia)
    await db.flush()

    user_dir = UPLOAD_DIR / str(id_aprendiz)
    user_dir.mkdir(parents=True, exist_ok=True)
    archivo = user_dir / f"{tipo.lower()}_{evidencia.id_evidencia}.pdf"
    archivo.write_bytes(PDF_MINIMO)
    evidencia.ruta_archivo_pdf = str(archivo)

    if observaciones is not None:
        db.add(
            Retroalimentacion(
                id_evidencia=evidencia.id_evidencia,
                id_instructor=id_instructor,
                observaciones=observaciones,
                estado_evaluacion=estado,
            )
        )


async def main() -> None:
    print(f"Seed contra: {settings.database_url.split('@')[-1]}")
    async with AsyncSessionLocal() as db:
        print("[1] Usuarios demo")
        creados = {}
        claves_docs = [
            ("coordinador", "Coordinador Demo SENA", "1000000001"),
            ("instructor", "Instructor Demo SENA", "1000000002"),
            ("aprendiz1", "Aprendiz Demo Uno", "1000000003"),
            ("aprendiz2", "Aprendiz Demo Dos", "1000000004"),
        ]
        specs = _usuarios_demo()
        for clave, nombre, doc in claves_docs:
            usuario, creado = await _crear_usuario(db, clave, specs[clave], nombre, doc)
            creados[clave] = (usuario, creado)

        # EXPLICACIÓN: flush/refresh para tener ids frescos en ambos caminos
        await db.flush()

        ya_sembrado = (
            await db.execute(
                select(Evidencia).where(
                    Evidencia.titulo == "Bitacora Semana 1 (demo)"
                )
            )
        ).scalars().first()
        if ya_sembrado is not None:
            print("[2] Evidencias demo: ya existen -> skip")
            await db.commit()
            return

        print("[2] Asignaciones (RF05)")
        ids = {k: v[0].id_usuario for k, v in creados.items()}
        for aprendiz in ("aprendiz1", "aprendiz2"):
            db.add(
                AsignacionSeguimiento(
                    id_aprendiz=ids[aprendiz], id_instructor=ids["instructor"]
                )
            )

        print("[3] Evidencias de todos los estados (RF02-RF04)")
        # Aprendiz 1: aprobada + ajuste + pendiente => avance 33.33%
        await _crear_evidencia(
            db, ids["aprendiz1"], "Bitacora Semana 1 (demo)", "Bitacora",
            "Aprobada", "Bitacora completa y a tiempo. Aprobada.", ids["instructor"],
        )
        await _crear_evidencia(
            db, ids["aprendiz1"], "Formato F023 (demo)", "F023",
            "Ajuste Requerido", "Falta firma del instructor seguidor en pagina 2.",
            ids["instructor"],
        )
        await _crear_evidencia(
            db, ids["aprendiz1"], "Formato F028 (demo)", "F028",
            "Pendiente", None, ids["instructor"],
        )
        # Aprendiz 2: todo aprobado => avance 100% (la estrella de la demo)
        await _crear_evidencia(
            db, ids["aprendiz2"], "Certificado etapa practica (demo)", "Certificado",
            "Aprobada", "Cumple todos los requisitos del RNF02.", ids["instructor"],
        )

        await db.commit()

    print(f"\nSeed listo. Login demo (password '{PASS_DEMO}'):")
    print("  coordinador.demo@sena.edu.co | instructor.demo@sena.edu.co")
    print("  aprendiz.demo@sena.edu.co (33%) | aprendiz2.demo@sena.edu.co (100%)")


if __name__ == "__main__":
    asyncio.run(main())
