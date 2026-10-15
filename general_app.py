"""Entrada independiente para compartir únicamente la cartera general.

Los enlaces personalizan el saludo; no verifican identidad ni conceden acceso
a la aplicación principal. Publicar como una segunda app, nunca como página
de navegación de la app que contiene la cartera propia.
"""
from pathlib import Path
import runpy
import streamlit as st

PERFILES = {
    "nicolas": {"nombre": "Nicolás"},
    "fernando": {"nombre": "Fernando"},
    "carlos": {"nombre": "Carlos"},
    "gonzalo": {"nombre": "Gonzalo"},
}

perfil = PERFILES.get(str(st.query_params.get("usuario", "")).lower(), {})
runpy.run_path(
    str(Path(__file__).with_name("app.py")),
    init_globals={"SOLO_CARTERA_GENERAL": True, "NOMBRE_VISITANTE": perfil.get("nombre", "")},
    run_name="__main__",
)
