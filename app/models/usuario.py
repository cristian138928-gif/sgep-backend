# ================================
# app/models/usuario.py
# ================================
"""
MODELOS DE USUARIO - Implementación POO del SGEP

Conceptos implementados:
1. HERENCIA: UsuarioBase es padre de Aprendiz, Instructor, Coordinador
2. ENCAPSULAMIENTO: clave_hash es privada (protegida con bcrypt)
3. POLIMORFISMO: métodos que varían según el tipo de usuario
4. ABSTRACCIÓN: mostramos interfaz simple, ocultamos complejidad
"""

import os
from datetime import UTC, datetime

import bcrypt
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

# Base de datos declarativa - todas nuestras clases heredarán de Base
Base = declarative_base()


# ======================================
# CLASE 1: UsuarioBase (CLASE PADRE)
# ======================================
class UsuarioBase(Base):
    """
    CONCEPTO: CLASE BASE CON HERENCIA

    Esta es la clase PADRE. Define lo común a TODOS los usuarios:
    - Todos tienen: id, nombre, correo, contraseña hasheada
    - Todos pueden: verificar_contrasena(), establecer_contrasena()

    Las clases hijas (Aprendiz, Instructor, Coordinador) HEREDAN todo esto
    y añaden sus propios atributos.
    """

    __tablename__ = "usuarios"  # Tabla en PostgreSQL

    # =====================
    # ATRIBUTOS COMUNES
    # =====================
    id_usuario = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID único del usuario en el sistema"
    )

    nombre_completo = Column(
        String(150),
        nullable=False,
        comment="Nombre y apellido completo"
    )

    correo_institucional = Column(
        String(120),
        unique=True,
        nullable=False,
        comment="Email único del SENA (validado en registro)"
    )

    clave_hash = Column(
        String(255),
        nullable=False,
        comment="Contraseña HASHEADA con bcrypt (NUNCA texto plano)"
    )

    tipo_documento = Column(
        String(20),
        nullable=False,
        comment="CC (Cédula), TI (Tarjeta Identidad), CE (Cédula Extranjería), etc."
    )

    numero_documento = Column(
        String(20),
        unique=True,
        nullable=False,
        comment="El número de documento (ej: 1023456789)"
    )

    rol = Column(
        String(50),
        nullable=False,
        comment="Tipo: 'aprendiz', 'instructor', 'coordinador'"
    )

    fecha_creacion = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Cuándo se creó la cuenta"
    )

    activo = Column(
        Integer,
        default=1,
        comment="1=activo, 0=inactivo"
    )

    # Para SQLAlchemy: identifica cuál es la clase hija (herencia)
    __mapper_args__ = {
        'polymorphic_on': rol,
        'polymorphic_identity': 'usuario_base'
    }

    # =====================
    # MÉTODOS: ENCAPSULAMIENTO
    # =====================

    def establecer_contrasena(self, contraseña_texto: str) -> None:
        """
        ENCAPSULAMIENTO EN ACCIÓN:

        Este es el ÚNICO método que puede setear la contraseña.
        Automáticamente la HASHEA con bcrypt (seguro).

        ¿Por qué? Porque NUNCA guardamos contraseña en texto plano.
        Si alguien accede a la BD, ve un hash ilegible, no tu contraseña.

        Ejemplo:
        >>> usuario = Aprendiz()
        >>> usuario.establecer_contrasena("MiContra123!")
        >>> # Internamente, se convierte a: $2b$12$R9h6cIPz...

        Args:
            contraseña_texto: Contraseña en TEXTO PLANO (ej: "MiContra123!")

        Returns:
            None (modifica self.clave_hash directamente)
        """
        # bcrypt.gensalt() crea un "salt" aleatorio (dificulta ataques)
        # .hashpw() hashea la contraseña
        # .decode('utf-8') convierte bytes a string
        # EXPLICACIÓN: Coste configurable (12=prod, 4=tests) porque bcrypt domina el tiempo de suite
        coste = int(os.getenv("BCRYPT_ROUNDS", "12"))
        self.clave_hash = bcrypt.hashpw(
            contraseña_texto.encode('utf-8'),
            bcrypt.gensalt(rounds=coste)
        ).decode('utf-8')

    def verificar_contrasena(self, contraseña_texto: str) -> bool:
        """
        ENCAPSULAMIENTO EN ACCIÓN:

        Verifica si la contraseña que el usuario escribe es correcta.
        Usa bcrypt para comparar de forma SEGURA.

        Flujo de autenticación:
        1. Usuario tipea: "MiContra123!"
        2. Nosotros hasheamos: "MiContra123!" → "$2b$12$R9h6..."
        3. Comparamos ese hash con el que está en la BD
        4. Si coinciden → True (contraseña correcta)
        5. Si NO coinciden → False (contraseña incorrecta)

        Ejemplo:
        >>> usuario.verificar_contrasena("MiContra123!")
        True  # ✅ Correcta

        >>> usuario.verificar_contrasena("OtraContra")
        False  # ❌ Incorrecta

        Args:
            contraseña_texto: Contraseña en TEXTO PLANO a verificar

        Returns:
            bool: True si es correcta, False si no
        """
        try:
            return bcrypt.checkpw(
                contraseña_texto.encode('utf-8'),
                self.clave_hash.encode('utf-8')
            )
        except Exception:
            # Si algo falla (error de encoding, etc.), retorna False
            return False

    def __repr__(self):
        """
        Método para debugging: ver el usuario como texto.
        Ej: <APRENDIZ Juan Pérez (juan@sena.edu.co)>
        """
        return f"<{self.rol.upper()} {self.nombre_completo} ({self.correo_institucional})>"

    def __str__(self):
        """Versión simple del usuario"""
        return self.nombre_completo


# ======================================
# CLASE 2: Aprendiz (HEREDA DE UsuarioBase)
# ======================================
class Aprendiz(UsuarioBase):
    """
    CONCEPTO: HERENCIA + POLIMORFISMO

    Un Aprendiz ES UN UsuarioBase, pero con atributos específicos:
    - Hereda: id_usuario, nombre, correo, clave_hash, métodos
    - Añade: numero_ficha, programa
    - Polimorfismo: tiene su propio consultar_avance()

    Ejemplo de tabla en BD:
    usuarios (id, nombre, correo, clave_hash, rol, ...)
    aprendices (id_usuario, numero_ficha, programa)

    La tabla "aprendices" referencia a "usuarios" (relación 1:1)
    """

    __tablename__ = "aprendices"

    # Herencia: referencia a la tabla padre "usuarios"
    # La llave foránea hace que sea única la relación 1:1
    id_usuario = Column(
        Integer,
        ForeignKey('usuarios.id_usuario'),  # Referencia a usuarios.id_usuario
        primary_key=True
    )

    # =====================
    # ATRIBUTOS ESPECÍFICOS DEL APRENDIZ
    # =====================

    # EXPLICACIÓN: SIN unique — una ficha agrupa a ~30 aprendices del mismo grupo SENA
    numero_ficha = Column(
        String(20),
        nullable=False,
        comment="Número de ficha de SENA (ej: 3388939; compartida por el grupo)"
    )

    programa = Column(
        String(100),
        nullable=False,
        comment="Programa de formación (ej: ADSO - Análisis y Desarrollo de Software)"
    )

    fecha_inicio_etapa = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Cuándo inicia la etapa práctica"
    )

    fecha_fin_etapa = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Cuándo termina la etapa práctica"
    )

    # Relación con Evidencia (un aprendiz tiene muchas evidencias)
    # Esto será útil cuando creemos la tabla Evidencia
    evidencias = relationship("Evidencia", back_populates="aprendiz", cascade="all, delete-orphan")

    # Identifier para SQLAlchemy (herencia)
    __mapper_args__ = {'polymorphic_identity': 'aprendiz'}

    # =====================
    # MÉTODOS: POLIMORFISMO
    # =====================

    def consultar_avance(self) -> float:
        """
        POLIMORFISMO EN ACCIÓN:

        Este método SOLO existe en Aprendiz.
        Instructor NO tiene este método (él tiene evaluar_evidencia).

        Calcula el porcentaje de avance de la etapa práctica.

        Algoritmo:
        1. Contar evidencias TOTALES del aprendiz
        2. Contar evidencias APROBADAS
        3. Porcentaje = (aprobadas / total) * 100

        Ejemplo:
        - Aprendiz subió 10 bitácoras
        - 7 fueron aprobadas
        - Avance = (7/10)*100 = 70%

        Returns:
            float: Porcentaje 0-100

        Raises:
            Retorna 0.0 si no hay evidencias
        """
        # Si el aprendiz no tiene evidencias aún, avance es 0
        if not self.evidencias:
            return 0.0

        # Contar cuántas están aprobadas
        aprobadas = sum(1 for ev in self.evidencias if ev.estado == "Aprobada")
        total = len(self.evidencias)

        # Calcular porcentaje, redondeado a 2 decimales
        return round((aprobadas / total) * 100, 2) if total > 0 else 0.0

    def __repr__(self):
        return f"<APRENDIZ {self.nombre_completo} - Ficha:{self.numero_ficha}>"


# ======================================
# CLASE 3: Instructor (HEREDA DE UsuarioBase)
# ======================================
class Instructor(UsuarioBase):
    """
    CONCEPTO: HERENCIA + POLIMORFISMO

    Un Instructor ES UN UsuarioBase, pero especializado:
    - Hereda: id_usuario, nombre, correo, clave_hash, métodos
    - Añade: centro_formacion, especialidad
    - Polimorfismo: tiene su propio evaluar_evidencia() (Aprendiz NO lo tiene)
    """

    __tablename__ = "instructores"

    # Herencia
    id_usuario = Column(
        Integer,
        ForeignKey('usuarios.id_usuario'),
        primary_key=True
    )

    # =====================
    # ATRIBUTOS ESPECÍFICOS DEL INSTRUCTOR
    # =====================

    centro_formacion = Column(
        String(150),
        nullable=False,
        comment="Centro donde trabaja (ej: Centro de Servicios de Salud)"
    )

    especialidad = Column(
        String(100),
        nullable=False,
        comment="Especialidad (ej: Desarrollo de Software, Enfermería)"
    )

    # Relación: Un instructor hace muchas evaluaciones
    evaluaciones = relationship("Retroalimentacion", back_populates="instructor_revisor")

    __mapper_args__ = {'polymorphic_identity': 'instructor'}

    # =====================
    # MÉTODOS: POLIMORFISMO
    # =====================

    def evaluar_evidencia(self, evidencia_obj, estado: str, observaciones: str) -> bool:
        """
        POLIMORFISMO EN ACCIÓN:

        Evalúa una evidencia y crea retroalimentación.
        La lógica real está en InstructorService.
        """
        if estado not in ["Aprobada", "Ajuste Requerido"]:
            raise ValueError(f"Estado inválido: {estado}. Debe ser 'Aprobada' o 'Ajuste Requerido'")
        return True

    def __repr__(self):
        return f"<INSTRUCTOR {self.nombre_completo} - {self.centro_formacion}>"


# ======================================
# CLASE 4: Coordinador (HEREDA DE UsuarioBase)
# ======================================
class Coordinador(UsuarioBase):
    """
    CONCEPTO: HERENCIA

    Un Coordinador ES UN UsuarioBase (coordinador académico).
    Hereda todo pero es más simple que Aprendiz e Instructor.
    """

    __tablename__ = "coordinadores"

    id_usuario = Column(
        Integer,
        ForeignKey('usuarios.id_usuario'),
        primary_key=True
    )

    departamento = Column(
        String(100),
        nullable=False,
        comment="Departamento (ej: Coordinación Académica)"
    )

    __mapper_args__ = {'polymorphic_identity': 'coordinador'}

    def __repr__(self):
        return f"<COORDINADOR {self.nombre_completo} - {self.departamento}>"


# ======================================
# CLASE 5: Evidencia
# ======================================
class Evidencia(Base):
    """
    Una Evidencia es un archivo que sube el aprendiz.

    RELACIONES:
    - 1 Aprendiz → muchas Evidencias (1:N)
    - 1 Evidencia → puede tener 1 Retroalimentacion (1:1)
    """

    __tablename__ = "evidencias"

    id_evidencia = Column(Integer, primary_key=True, autoincrement=True)

    # Relación con Aprendiz
    id_aprendiz = Column(
        Integer,
        ForeignKey('aprendices.id_usuario'),
        nullable=False,
        comment="ID del aprendiz que subió esta evidencia"
    )

    titulo = Column(
        String(200),
        nullable=False,
        comment="Nombre de la evidencia (ej: Bitácora Semana 3)"
    )

    tipo_formato = Column(
        String(50),
        nullable=False,
        comment="Tipo: Bitácora, F023, F028, etc."
    )

    ruta_archivo_pdf = Column(
        String(500),
        nullable=False,
        comment="Ruta en servidor donde se guarda el PDF"
    )

    estado = Column(
        String(50),
        default="Pendiente",
        comment="Estado: Pendiente, Aprobada, Ajuste Requerido"
    )

    fecha_carga = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Cuándo se subió"
    )

    fecha_deadline = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fecha límite de entrega"
    )

    # Relación inversa con Aprendiz
    aprendiz = relationship("Aprendiz", back_populates="evidencias")

    # Relación con Retroalimentacion
    retroalimentacion = relationship(
        "Retroalimentacion",
        back_populates="evidencia",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<EVIDENCIA {self.titulo} - {self.estado}>"


# ======================================
# CLASE 6: Retroalimentacion
# ======================================
class Retroalimentacion(Base):
    """
    Cuando un Instructor evalúa una Evidencia,
    crea un registro de Retroalimentacion (evaluación + comentarios).
    """

    __tablename__ = "retroalimentaciones"

    id_retroalimentacion = Column(Integer, primary_key=True, autoincrement=True)

    id_evidencia = Column(
        Integer,
        ForeignKey('evidencias.id_evidencia'),
        unique=True,
        nullable=False,
        comment="La evidencia que fue evaluada"
    )

    id_instructor = Column(
        Integer,
        ForeignKey('instructores.id_usuario'),
        nullable=False,
        comment="Quién evaluó"
    )

    observaciones = Column(
        String(1000),
        nullable=False,
        comment="Retroalimentación que el instructor escribió"
    )

    estado_evaluacion = Column(
        String(50),
        nullable=False,
        comment="Aprobada, Ajuste Requerido"
    )

    fecha_revision = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Cuándo el instructor evaluó"
    )

    # Relaciones
    evidencia = relationship("Evidencia", back_populates="retroalimentacion")
    instructor_revisor = relationship("Instructor", back_populates="evaluaciones")

    def __repr__(self):
        return f"<RETROALIMENTACION Evidencia#{self.id_evidencia} - {self.estado_evaluacion}>"


# ======================================
# CLASE 7: AsignacionSeguimiento
# ======================================
class AsignacionSeguimiento(Base):
    """Tabla pivote: vincula aprendices a un instructor seguidor (N:N)."""

    __tablename__ = "asignaciones_seguimiento"

    id_asignacion = Column(Integer, primary_key=True, autoincrement=True)

    id_aprendiz = Column(
        Integer,
        ForeignKey('aprendices.id_usuario'),
        nullable=False,
        comment="Aprendiz asignado"
    )

    id_instructor = Column(
        Integer,
        ForeignKey('instructores.id_usuario'),
        nullable=False,
        comment="Instructor seguidor asignado"
    )

    fecha_asignacion = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Cuándo se hizo la asignación"
    )

    activa = Column(
        Integer,
        default=1,
        comment="1=asignación activa, 0=desasignada"
    )

    # Relaciones inversas
    aprendiz = relationship("Aprendiz", foreign_keys=[id_aprendiz])
    instructor = relationship("Instructor", foreign_keys=[id_instructor])

    def __repr__(self):
        return f"<ASIGNACION Aprendiz#{self.id_aprendiz} -> Instructor#{self.id_instructor}>"


# ======================================
# CLASE 8: Notificacion
# ======================================
class Notificacion(Base):
    """
    Notificación IN-APP dirigida a un usuario.

    EXPLICACIÓN: Es persistente (no efímera como el email) porque el usuario
    debe poder verla al volver a entrar; `leida=0/1` da el badge de no leídas.
    """

    __tablename__ = "notificaciones"

    id_notificacion = Column(Integer, primary_key=True, autoincrement=True)

    id_usuario = Column(
        Integer,
        ForeignKey('usuarios.id_usuario'),
        nullable=False,
        index=True,
        comment="Quién recibe la notificación"
    )

    id_evidencia = Column(
        Integer,
        ForeignKey('evidencias.id_evidencia'),
        nullable=True,
        comment="Evidencia relacionada (permite deduplicar alertas de vencimiento)"
    )

    mensaje = Column(
        String(300),
        nullable=False,
        comment="Texto visible para el usuario"
    )

    tipo = Column(
        String(30),
        nullable=False,
        comment="evaluacion | vencimiento | sistema"
    )

    leida = Column(
        Integer,
        default=0,
        comment="0=no leída, 1=leída"
    )

    fecha_creacion = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Cuándo se creó"
    )

    # Relaciones
    usuario = relationship("UsuarioBase")

    def __repr__(self):
        return f"<NOTIFICACION {self.tipo} -> Usuario#{self.id_usuario}>"


print(" Modelos POO cargados correctamente")
