# tests/test_models_poo.py
"""
Tests de la capa POO de models/usuario.py.
Cubre: __repr__/__str__, consultar_avance, evaluar_evidencia y hash corrupto.
"""

import pytest

from app.models.usuario import (
    Aprendiz,
    AsignacionSeguimiento,
    Coordinador,
    Evidencia,
    Instructor,
    Notificacion,
    Retroalimentacion,
    UsuarioBase,
)


def _aprendiz() -> Aprendiz:
    """EXPLICACIÓN: instancia en memoria (sin BD) para probar lógica pura de POO."""
    return Aprendiz(
        nombre_completo="Ana Torres",
        correo_institucional="ana@test.com",
        numero_documento="1001",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="2456789",
        programa="ADSO",
    )


def _evidencia(estado: str) -> Evidencia:
    """EXPLICACIÓN: fila en memoria; la relación no exige flush para consultarse."""
    return Evidencia(
        id_aprendiz=1,
        titulo="Bitacora Semana 1",
        tipo_formato="Bitacora",
        ruta_archivo_pdf="uploads/1/bitacora.pdf",
        estado=estado,
    )


# ====================================
# ENCAPSULAMIENTO
# ====================================

def test_verificar_contrasena_hash_corrupto_false():
    """Test: clave_hash no-bcrypt no revienta (except -> False)."""
    usuario = _aprendiz()
    usuario.clave_hash = "no-es-un-hash"

    assert usuario.verificar_contrasena("cualquiera") is False


def test_repr_usuario_base():
    """Test: __repr__ muestra rol en mayúsculas + correo."""
    base = UsuarioBase(
        nombre_completo="Generico",
        correo_institucional="gen@test.com",
        numero_documento="4004",
        tipo_documento="CC",
        rol="usuario_base",
    )
    assert repr(base) == "<USUARIO_BASE Generico (gen@test.com)>"


def test_str_usuario_base():
    """Test: __str__ devuelve solo el nombre (no delega en __repr__)."""
    assert str(_aprendiz()) == "Ana Torres"


# ====================================
# POLIMORFISMO: Aprendiz.consultar_avance
# ====================================

def test_consultar_avance_sin_evidencias():
    """Test: 0 evidencias => 0.0 (evita división por cero)."""
    assert _aprendiz().consultar_avance() == 0.0


def test_consultar_avance_parcial():
    """Test: 2 de 4 aprobadas => 50.0%."""
    aprendiz = _aprendiz()
    aprendiz.evidencias = [
        _evidencia("Aprobada"),
        _evidencia("Aprobada"),
        _evidencia("Pendiente"),
        _evidencia("Ajuste Requerido"),
    ]

    assert aprendiz.consultar_avance() == 50.0


def test_consultar_avance_total():
    """Test: 3 de 3 aprobadas => 100.0% redondeado a 2 decimales."""
    aprendiz = _aprendiz()
    aprendiz.evidencias = [
        _evidencia("Aprobada"),
        _evidencia("Aprobada"),
        _evidencia("Aprobada"),
    ]

    assert aprendiz.consultar_avance() == 100.0


# ====================================
# POLIMORFISMO: Instructor.evaluar_evidencia
# ====================================

def test_instructor_evaluar_estado_valido():
    """Test: Instructor.evaluar_evidencia acepta estados del dominio."""
    instructor = Instructor(
        nombre_completo="Luis Gomez",
        correo_institucional="luis@test.com",
        numero_documento="2002",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software",
    )

    assert instructor.evaluar_evidencia(_evidencia("Pendiente"), "Aprobada", "ok") is True


def test_instructor_evaluar_estado_invalido():
    """Test: estado fuera del dominio -> ValueError (polimorfismo protege el flujo)."""
    instructor = Instructor(
        nombre_completo="Luis Gomez",
        correo_institucional="luis@test.com",
        numero_documento="2002",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software",
    )

    with pytest.raises(ValueError, match="Estado invalido|Estado inválido"):
        instructor.evaluar_evidencia(_evidencia("Pendiente"), "Rechazada", "no")


# ====================================
# __repr__ DE TODAS LAS CLASES (trazabilidad UML)
# ====================================

def test_repr_aprendiz():
    """Test: Aprendiz sobrescribe __repr__ con su ficha (polimorfismo)."""
    assert repr(_aprendiz()) == "<APRENDIZ Ana Torres - Ficha:2456789>"


def test_repr_coordinador():
    coord = Coordinador(
        nombre_completo="Maria Ruiz",
        correo_institucional="maria@test.com",
        numero_documento="3003",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion",
    )
    assert repr(coord) == "<COORDINADOR Maria Ruiz - Coordinacion>"


def test_repr_instructor():
    instructor = Instructor(
        nombre_completo="Luis Gomez",
        correo_institucional="luis@test.com",
        numero_documento="2002",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software",
    )
    assert repr(instructor) == "<INSTRUCTOR Luis Gomez - Centro Salud>"


def test_repr_evidencia():
    assert repr(_evidencia("Aprobada")) == "<EVIDENCIA Bitacora Semana 1 - Aprobada>"


def test_repr_retroalimentacion():
    retro = Retroalimentacion(
        id_evidencia=7,
        id_instructor=3,
        observaciones="Todo bien",
        estado_evaluacion="Aprobada",
    )
    assert repr(retro) == "<RETROALIMENTACION Evidencia#7 - Aprobada>"


def test_repr_asignacion():
    asignacion = AsignacionSeguimiento(id_aprendiz=5, id_instructor=3)
    assert repr(asignacion) == "<ASIGNACION Aprendiz#5 -> Instructor#3>"


def test_repr_notificacion():
    notificacion = Notificacion(id_usuario=9, mensaje="Aviso", tipo="sistema")
    assert repr(notificacion) == "<NOTIFICACION sistema -> Usuario#9>"
