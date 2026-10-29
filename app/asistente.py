"""Asistente de IA de la biblioteca (Groq vía el SDK de OpenAI).

Flujo:
1. El navegador envía la pregunta y el historial a POST /asistentebiblioteca/preguntar
2. El servidor busca en la base de datos los libros relacionados con la pregunta
   (y, si el usuario tiene permiso, los préstamos y multas de un socio por su CI).
3. Esos datos reales se inyectan en el prompt de sistema; la IA solo responde con ellos.
"""
import re

from flask import current_app, jsonify, request
from flask_wtf.csrf import generate_csrf
from flask_appbuilder import BaseView, expose, has_access
from sqlalchemy import or_

from .extensions import appbuilder, db
from .models import Autor, Categoria, Libro, Multa, Prestamo, Socio

MAX_HISTORIAL = 10     # mensajes previos que se envían a la IA
MAX_LIBROS = 8         # libros que se incluyen como contexto
PALABRAS_VACIAS = {
    "tiene", "tienen", "quiero", "busco", "libro", "libros", "sobre", "hay", "para",
    "algun", "alguna", "como", "cual", "cuales", "que", "esta", "estan", "disponible",
    "disponibles", "recomienda", "recomiendame", "dime", "autor", "este", "esos",
}


def _normalizar(texto):
    return texto.lower()


def buscar_libros(texto):
    """Libros activos cuyo título, autor o categoría contienen alguna palabra clave."""
    palabras = {p for p in re.findall(r"\w+", _normalizar(texto))
                if len(p) >= 4 and p not in PALABRAS_VACIAS}
    consulta = (db.session.query(Libro).join(Autor).join(Categoria)
                .filter(Libro.activo.is_(True)))
    if palabras:
        condiciones = []
        for p in palabras:
            patron = f"%{p}%"
            condiciones += [Libro.titulo.ilike(patron), Autor.nombre.ilike(patron),
                            Categoria.nombre.ilike(patron)]
        consulta = consulta.filter(or_(*condiciones))
    else:
        return []
    return consulta.order_by(Libro.titulo).limit(MAX_LIBROS).all()


def resumen_general():
    total = db.session.query(Libro).filter(Libro.activo.is_(True)).count()
    cats = [c.nombre for c in db.session.query(Categoria).order_by(Categoria.nombre)]
    return f"Libros activos en el catálogo: {total}. Categorías: {', '.join(cats) or 'ninguna'}."


def datos_socio(texto):
    """Préstamos activos y multas pendientes del socio cuyo CI aparece en el texto."""
    m = re.search(r"\b\d{6,}\b", texto)
    if not m:
        return ""
    socio = db.session.query(Socio).filter_by(ci=m.group()).first()
    if not socio:
        return f"No existe ningún socio con CI {m.group()}."
    lineas = [f"Socio: {socio.nombre} (CI {socio.ci})."]
    activos = [p for p in socio.prestamos if p.estado == "Activo"]
    if activos:
        for p in activos:
            estado = "VENCIDO" if p.vencido else "vigente"
            lineas.append(f"- Préstamo activo: «{p.libro.titulo}», límite {p.fecha_limite} ({estado}).")
    else:
        lineas.append("No tiene préstamos activos.")
    pendientes = (db.session.query(Multa).join(Prestamo)
                  .filter(Prestamo.socio_id == socio.id, Multa.pagada.is_(False)).all())
    total = sum(m.monto for m in pendientes)
    lineas.append(f"Multas pendientes: {len(pendientes)} por un total de Bs {total}.")
    return "\n".join(lineas)


def construir_contexto(pregunta, puede_ver_socios):
    partes = [resumen_general()]
    libros = buscar_libros(pregunta)
    if libros:
        partes.append("Libros relacionados con la pregunta:")
        for l in libros:
            partes.append(f"- «{l.titulo}» de {l.autor.nombre} | categoría {l.categoria.nombre} | "
                          f"año {l.anio_publicacion or 's/d'} | disponibles {l.ejemplares_disponibles} "
                          f"de {l.ejemplares_total}")
    else:
        partes.append("No se encontraron libros que coincidan con la pregunta.")
    if puede_ver_socios:
        info = datos_socio(pregunta)
        if info:
            partes.append(info)
    return "\n".join(partes)


SISTEMA = (
    "Eres el asistente virtual de una biblioteca universitaria. Respondes en español, "
    "de forma breve y amable. Usa SOLO los datos del bloque DATOS para hablar de libros, "
    "disponibilidad, préstamos o multas. Si algo no está en los datos, di que no lo encuentras "
    "en el catálogo; no inventes títulos, autores ni cifras. Puedes recomendar entre los libros "
    "que aparecen en los datos.\n\nDATOS ACTUALES DE LA BASE DE DATOS:\n{contexto}"
)


def llamar_ia(mensajes):
    """Envía los mensajes al modelo y devuelve el texto de la respuesta."""
    from openai import OpenAI
    cfg = current_app.config
    if not cfg.get("AI_API_KEY"):
        raise RuntimeError("Falta AI_API_KEY en el archivo .env")
    cliente = OpenAI(api_key=cfg["AI_API_KEY"], base_url=cfg["AI_URL"], timeout=30)
    respuesta = cliente.chat.completions.create(model=cfg["AI_MODEL"], messages=mensajes,
                                                temperature=0.3)
    return (respuesta.choices[0].message.content or "").strip()


class AsistenteView(BaseView):
    route_base = "/asistentebiblioteca"
    default_view = "chat"

    @expose("/chat/")
    @has_access
    def chat(self):
        self.update_redirect()
        return self.render_template("asistente.html", csrf_token_valor=generate_csrf())

    @expose("/preguntar", methods=["POST"])
    @has_access
    def preguntar(self):
        datos = request.get_json(silent=True) or {}
        pregunta = (datos.get("mensaje") or "").strip()
        if not pregunta:
            return jsonify({"error": "Escribe una pregunta."}), 400
        if len(pregunta) > 500:
            return jsonify({"error": "La pregunta es demasiado larga (máx. 500 caracteres)."}), 400

        historico = [m for m in (datos.get("historico") or [])
                     if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
        historico = historico[-MAX_HISTORIAL:]

        sm = appbuilder.sm
        puede_ver_socios = sm.has_access("can_list", "SocioView")
        contexto = construir_contexto(pregunta, puede_ver_socios)
        mensajes = ([{"role": "system", "content": SISTEMA.format(contexto=contexto)}]
                    + historico + [{"role": "user", "content": pregunta}])
        try:
            texto = llamar_ia(mensajes)
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 503
        except Exception:  # red caída, clave inválida, límite de uso...
            current_app.logger.exception("Fallo al llamar a la IA")
            return jsonify({"error": "No pude contactar a la IA. Intenta de nuevo en un momento."}), 502
        return jsonify({"respuesta": texto or "No obtuve respuesta del modelo."})
