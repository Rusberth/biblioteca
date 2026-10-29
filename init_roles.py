"""Crea los roles Bibliotecario y Consulta con sus permisos.

Uso:  python init_roles.py      (se puede ejecutar varias veces)
Admin ya existe en FAB y tiene todos los permisos.
"""
from app import app

VISTAS_CATALOGO = ["LibroView", "AutorView", "CategoriaView"]
VISTAS_CIRCULACION = ["SocioView", "PrestamoView", "MultaView"]
TODOS = ["can_list", "can_show", "can_add", "can_edit", "can_delete"]
SOLO_LECTURA = ["can_list", "can_show"]


def dar(sm, rol, vista, permisos):
    for nombre in permisos + ["menu_access"]:
        pv = sm.find_permission_view_menu(nombre, vista)
        if pv:
            sm.add_permission_role(rol, pv)
    # permiso para ejecutar la acción "devolver"
    if vista == "PrestamoView" and "can_add" in permisos:
        pv = sm.find_permission_view_menu("devolver", vista)
        if pv:
            sm.add_permission_role(rol, pv)


with app.app_context():
    sm = app.appbuilder.sm

    biblio = sm.find_role("Bibliotecario") or sm.add_role("Bibliotecario")
    for v in VISTAS_CATALOGO + VISTAS_CIRCULACION:
        dar(sm, biblio, v, TODOS)
    for menu in ["Catálogo", "Circulación"]:
        pv = sm.find_permission_view_menu("menu_access", menu)
        if pv:
            sm.add_permission_role(biblio, pv)

    consulta = sm.find_role("Consulta") or sm.add_role("Consulta")
    for v in VISTAS_CATALOGO:
        dar(sm, consulta, v, SOLO_LECTURA)
    pv = sm.find_permission_view_menu("menu_access", "Catálogo")
    if pv:
        sm.add_permission_role(consulta, pv)

    # Asistente de IA: lo pueden usar Bibliotecario y Consulta
    for rol in (biblio, consulta):
        for nombre, vista in [("can_chat", "AsistenteView"), ("can_preguntar", "AsistenteView"),
                              ("menu_access", "Asistente IA"), ("menu_access", "Asistente")]:
            pv = sm.find_permission_view_menu(nombre, vista)
            if pv:
                sm.add_permission_role(rol, pv)

    # Reportes: solo Bibliotecario (y Admin). Se dan todos los permisos de ReportesView.
    for pv in sm.session.query(sm.permissionview_model).all():
        if pv.view_menu and pv.view_menu.name in ("ReportesView", "Reportes", "Libros más prestados",
                                                  "Préstamos vencidos", "Multas por socio"):
            sm.add_permission_role(biblio, pv)

    # Mostrador, carnet, acciones extra (pagar multa, ver carnet): Bibliotecario
    VISTAS_BIBLIO = {"MostradorView", "Mostrador", "CarnetView", "SocioView", "MultaView", "PrestamoView"}
    for pv in sm.session.query(sm.permissionview_model).all():
        if pv.view_menu and pv.view_menu.name in VISTAS_BIBLIO and pv.permission.name != "can_download":
            sm.add_permission_role(biblio, pv)

    print("Roles listos:", ", ".join(r.name for r in sm.get_all_roles()))
