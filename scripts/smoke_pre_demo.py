import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
results = []


def rec(name: str, ok: bool, note: str = "") -> None:
    """Registra y muestra el resultado de un smoke."""
    results.append((name, ok, note))
    status = "OK  " if ok else "FAIL"
    suffix = f" - {note}" if note else ""
    print(f"{status} {name}{suffix}")


def req(method: str, path: str, token=None, data=None, content_type=None):
    """Ejecuta una petición HTTP y devuelve (status, headers, payload)."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None and not isinstance(data, bytes | bytearray):
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    elif isinstance(data, bytes | bytearray):
        body = data
        if content_type:
            headers["Content-Type"] = content_type
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type", "")
            payload = json.loads(raw) if "json" in ct else raw
            return resp.status, resp.headers, payload
    except urllib.error.HTTPError as e:
        raw = e.read()
        ct = e.headers.get("Content-Type", "")
        try:
            payload = json.loads(raw) if "json" in ct else raw
        except Exception:
            payload = raw
        return e.code, e.headers, payload


s, _, p = req("GET", "/health")
rec("Health", s == 200 and isinstance(p, dict) and p.get("status") == "healthy", str(p))


def login(email: str, pw: str = "Demo1234!"):
    """Realiza login y retorna la respuesta HTTP."""
    return req(
        "POST",
        "/api/v1/auth/login",
        data={"correo_institucional": email, "contraseña": pw},
    )


sa, _, pa = login("aprendiz.demo@sena.edu.co")
si, _, pi = login("instructor.demo@sena.edu.co")
sc, _, pc = login("coordinador.demo@sena.edu.co")
ta = pa.get("access_token") if sa == 200 and isinstance(pa, dict) else None
ti = pi.get("access_token") if si == 200 and isinstance(pi, dict) else None
tc = pc.get("access_token") if sc == 200 and isinstance(pc, dict) else None
ra = pa.get("refresh_token") if sa == 200 and isinstance(pa, dict) else None
rec("Login aprendiz", sa == 200 and bool(ta), f"status={sa}")
rec("Login instructor", si == 200 and bool(ti), f"status={si}")
rec("Login coordinador", sc == 200 and bool(tc), f"status={sc}")

s, _, p = req("GET", "/api/v1/aprendiz/avance", token=ta)
avance_ok = s == 200 and isinstance(p, dict) and "porcentaje_avance" in p
rec("RF06 avance aprendiz", avance_ok, f"status={s}")

boundary = "----sgepbound"
pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
parts = []


def add_field(name: str, value: str) -> None:
    """Agrega un campo texto al cuerpo multipart."""
    head = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
    parts.append((head + f"{value}\r\n").encode())


def add_file(name: str, filename: str, ctype: str, content: bytes) -> None:
    """Agrega un archivo al cuerpo multipart."""
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
        f'filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'
    )
    parts.append(head.encode() + content + b"\r\n")


add_field("titulo", "Evidencia Smoke QA")
add_field("tipo_formato", "Bitacora")
add_file("file", "smoke.pdf", "application/pdf", pdf)
parts.append(f"--{boundary}--\r\n".encode())
body = b"".join(parts)
s, _, p = req(
    "POST",
    "/api/v1/evidencias/upload",
    token=ta,
    data=body,
    content_type=f"multipart/form-data; boundary={boundary}",
)
ev_id = p.get("id_evidencia") if s in (200, 201) and isinstance(p, dict) else None
rec("RF02 subir evidencia", s in (200, 201) and ev_id is not None, f"status={s} id={ev_id}")

s, _, p = req("GET", "/api/v1/evidencias/mis-evidencias", token=ta)
found = False
if s == 200 and ev_id and isinstance(p, list):
    found = any(e.get("id_evidencia") == ev_id for e in p)
rec("RF02 evidencia visible", s == 200 and found, f"status={s}")

if ev_id and ti:
    payload_eval = {
        "estado": "Aprobada",
        "observaciones": "Aprobada en smoke test automatizado",
    }
    s, _, _ = req("PUT", f"/api/v1/instructor/evaluar/{ev_id}", token=ti, data=payload_eval)
    rec("RF03/RF04 evaluar", s == 200, f"status={s}")
    s, _, p = req("GET", f"/api/v1/evidencias/{ev_id}/retroalimentacion", token=ta)
    retro_ok = s == 200 and isinstance(p, dict) and p.get("estado_evaluacion") == "Aprobada"
    rec("RF04 retro aprendiz", retro_ok, f"status={s}")
else:
    rec("RF03/RF04 evaluar", False, "sin id/token")
    rec("RF04 retro aprendiz", False, "sin id/token")

s, _, lista = req("GET", "/api/v1/asignaciones/", token=tc)
rec("RF05 listar asignaciones", s == 200, f"status={s}")

s, _, p = req("GET", "/api/v1/coordinador/estadisticas", token=tc)
dash_ok = s == 200 and isinstance(p, dict) and "total_evidencias" in p
rec("RF07 dashboard", dash_ok, f"status={s}")
s, _, csv = req("GET", "/api/v1/coordinador/exportar-avance", token=tc)
okcsv = s == 200 and isinstance(csv, bytes | bytearray) and len(csv) > 0
rec("RF07 exportar CSV", okcsv, f"status={s}")

s, _, _ = req("GET", "/api/v1/coordinador/estadisticas")
rec("RBAC 401 sin token", s == 401, str(s))
s, _, _ = req("GET", "/api/v1/coordinador/estadisticas", token=ta)
rec("RBAC 403 rol indebido", s == 403, str(s))

if ev_id:
    s, _, d = req("GET", f"/api/v1/evidencias/{ev_id}/descarga", token=ta)
    down_ok = s == 200 and isinstance(d, bytes | bytearray) and len(d) > 0
    rec("Descarga dueño", down_ok, f"status={s}")
    s, _, _ = req("GET", f"/api/v1/evidencias/{ev_id}/descarga")
    rec("Descarga sin token 401", s == 401, str(s))

if ra:
    s, _, p = req("POST", "/api/v1/auth/refresh", data={"refresh_token": ra})
    new_r = p.get("refresh_token") if s == 200 and isinstance(p, dict) else None
    rec("Refresh rotación", s == 200 and new_r and new_r != ra, f"status={s}")
    if new_r:
        s, _, _ = req("POST", "/api/v1/auth/logout", data={"refresh_token": new_r})
        rec("Logout revoca", s == 200, str(s))
        s, _, _ = req("POST", "/api/v1/auth/refresh", data={"refresh_token": new_r})
        rec("Refresh tras logout rechazado", s in (401, 400), str(s))
else:
    rec("Refresh rotación", False, "sin refresh")
    rec("Logout revoca", False, "skip")
    rec("Refresh tras logout rechazado", False, "skip")

hit429 = False
last = 0
retry = None
for _ in range(15):
    payload_login = {
        "correo_institucional": "nadie@sena.edu.co",
        "contraseña": "xinvalidx",
    }
    s, h, _ = req("POST", "/api/v1/auth/login", data=payload_login)
    last = s
    if s == 429:
        hit429 = True
        retry = h.get("Retry-After")
        break
rec("Rate limit 429", hit429, f"status={last} retry={retry}")

ok = sum(1 for _, o, _ in results if o)
print(f"\nTOTAL {ok}/{len(results)}")
