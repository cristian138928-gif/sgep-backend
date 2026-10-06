## Documentación Técnica SGEP

Informe de Entregables y Arquitectura Técnica (SGEP)Proyecto: Sistema de Gestión de Evidencias para Etapa Práctica (SGEP)Programa: Análisis y Desarrollo de Software (ADSO) - SENAAprendiz: Cristian Rene Muñoz FierroFicha: 3388939Instructor: David González Cárdenas1. Visión y Alcance del SistemaDescripción GeneralEl SGEP es una solución web orientada a la gestión documental y académica que automatiza, centraliza y audita la carga, revisión, aprobación y seguimiento de evidencias (bitácoras, formatos F023/F028 y certificados) presentadas por los aprendices en su etapa práctica.AlcanceAutenticación y Perfiles: Control de acceso con Roles (RBAC): Aprendiz, Instructor Seguidor y Coordinador/Administrador.Gestión Documental: Carga y almacenamiento estructurado de evidencias en formato PDF.Flujo Evaluativo: Módulo de revisión, asignación de estados (Aprobado/Requerido Ajuste) y retroalimentación con comentarios.Seguimiento y Notificaciones: Control de avance porcentual de la etapa práctica, control de fechas límite y alertas.Reportes: Dashboard consolidado para la gestión académica.2. Requerimientos del Sistema (SRS)Requerimientos Funcionales (RF)RF01 - Autenticación: Inicio de sesión con correo institucional y contraseña (retorna token JWT).RF02 - Carga de Evidencias: Permite al aprendiz adjuntar bitácoras/formatos PDF.RF03 - Evaluación: Permite al instructor calificar la evidencia ("Aprobada" o "Pendiente de Ajuste").RF04 - Retroalimentación: Registro de observaciones de texto por evidencia.RF05 - Asignación de Seguimiento: Vincular aprendices a un instructor seguidor.RF06 - Control de Avance: Cálculo automático del % de cumplimiento de la etapa práctica según bitácoras aprobadas.RF07 - Reportes: Consolidado de expedientes por la coordinación.Requerimientos No Funcionales (RNF)RNF01 - Seguridad en Archivos: Rutas protegidas contra acceso no autorizado.RNF02 - Integridad: Validaciones de tipo de archivo (PDF único, límite de tamaño) y transacciones ACID en PostgreSQL.RNF03 - Arquitectura Limpia: Separación estricta de capas mediante Python (FastAPI) y SQLAlchemy.RNF04 - Usabilidad y Rendimiento: Vistas con tiempos de respuesta < 2s y diseño responsivo.3. Stack Tecnológico SeleccionadoCategoríaTecnología / HerramientaRol en SGEPFrontendHTML5 / CSS3 / JavaScriptInterfaz de Usuario Web ResponsivaBackend BasePython 3.12+Lenguaje principal POOFramework APIFastAPIConstrucción de la API REST de alto rendimientoORM / DatosSQLAlchemyMapeo Objeto-Relacional para entidadesBase de DatosPostgreSQL / pgAdmin 4Persistencia relacional de expedientesSeguridadPasslib (bcrypt) + JWTCifrado de claves y control de tokens de accesoEntorno / CIDocker, VS Code, Git/GitHubEntorno de desarrollo contenerizado y control de versiones4. Arquitectura en Tres CapasCapa de Presentación (UI): Frontend web en HTML5/JS (Vistas para Aprendiz, Instructor y Admin). Comunicación mediante peticiones HTTP/JSON (REST).Capa de Lógica de Negocio (Backend): Servidor FastAPI (Python) con Middlewares JWT, Enrutadores, Controladores de Evidencias y Servicios de Reglas de Negocio.Capa de Persistencia (Datos): Mapeo ORM mediante SQLAlchemy conectado a PostgreSQL. Almacenamiento directo de archivos PDF en disco seguro.5. Diseño Orientado a Objetos (POO)El modelo de clases del sistema implementa los cuatro pilares POO:Diagrama UML de Clases +---------------------------------------------+
| UsuarioBase |
+---------------------------------------------+
| - id_usuario: int |
| - nombre_completo: string |
| - correo_inst: string |
| - clave_hash: string |
| - rol: string |
+---------------------------------------------+
| + autenticar(): bool |
+---------------------------------------------+
^
| (Herencia)
+----------------+----------------+
| |
+--------------------------+ +--------------------------+
| Aprendiz | | Instructor |
+--------------------------+ +--------------------------+
| - numero_ficha: string | | - centro_formacion: string|
| - programa: string | | - especialidad: string |
+--------------------------+ +--------------------------+
| + consultar_avance(): int| | + evaluar_evidencia():void|
+--------------------------+ +--------------------------+
| (1 a N) | (1 a N)
v (posee) v (revisa)
+---------------------------------------------+
| Evidencia |
+---------------------------------------------+
| - id_evidencia: int |
| - titulo: string |
| - tipo_formato: string |
| - ruta_archivo_pdf: string |
| - fecha_carga: datetime |
| - estado: string |
+---------------------------------------------+
| + registrar_carga(): bool |
| + cambiar_estado(nuevo_estado: string): void|
+---------------------------------------------+
| (1 a 1)
v (genera)
+---------------------------------------------+
| Retroalimentacion |
+---------------------------------------------+
| - id_retroalimentacion: int |
| - observaciones: string |
| - fecha_revision: datetime |
+---------------------------------------------+
| + guardar_comentario(): void |
+---------------------------------------------+ 6. Matriz de Trazabilidad (Endpoints y Pruebas)
| Requisito | Endpoint FastAPI | Caso de Prueba | Estado |
|-----------|------------------|----------------|--------|
| RF01 | POST /api/v1/auth/login | CP-01: Login correcto/incorrecto | **Aprobado** |
| RF02 | POST /api/v1/evidencias/upload | CP-02: Carga de PDF válido | **Aprobado** |
| RF03 | PUT /api/v1/instructor/evaluar/{id} | CP-03: Cambio de estado a Aprobado | **Aprobado** |
| RF04 | POST /api/v1/retroalimentacion/ | CP-04: Registro de comentarios | **Aprobado** |
| RF05 | POST /api/v1/asignaciones/ | CP-05: Asignación de instructor | **Aprobado** |
| RF06 | GET /api/v1/aprendiz/avance | CP-06: Cálculo de % de bitácoras | **Aprobado** |
| RF07 | GET /api/v1/coordinador/estadisticas | CP-07: Dashboard consolidado | **Aprobado** |
| RNF01 | GET /api/v1/evidencias/{id}/descarga | CP-08: Descarga con RBAC y sanitizacion de upload | **Aprobado** |
| RNF-Seguimiento | GET /api/v1/aprendiz/alertas?dias=7 | CP-09: Alertas Vencida / Por vencer | **Aprobado** |
| RNF-Seguimiento | GET /api/v1/instructor/alertas?dias=7 | CP-10: Vencimientos de aprendices asignados | **Aprobado** |
| RNF-Seguimiento | GET /api/v1/coordinador/alertas?dias=7 | CP-11: Vencimientos globales del sistema | **Aprobado** |

7. Plan de Trabajo (Gantt - 16 Semanas)Semanas 1-4 (Análisis): Levantamiento de requerimientos, historias de usuario y casos de uso.Semanas 4-8 (Diseño): Diagrama de clases UML, diseño de base de datos PostgreSQL y prototipos UI.Semanas 8-12 (Desarrollo): Configuración Docker, FastAPI, ORM SQLAlchemy y endpoints REST.Semanas 11-14 (Pruebas): Pruebas unitarias API, pruebas de integración BD y carga de PDFs.Semanas 15-16 (Despliegue y Cierre): Despliegue en servidor, capacitación de usuarios y entrega final.
