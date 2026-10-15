import os
import json
import pandas as pd
import numpy as np

REPORT_PATH = os.path.join(os.path.dirname(__file__), "downloads", "Reporte.xlsx")
PARQUET_PATH = os.path.join(os.path.dirname(__file__), "downloads", "Reporte.parquet")
CARTERA_PATH = os.path.join(os.path.dirname(__file__), "cartera.json")

COMERCIOS_EXACTOS_CARTERA = set()

# Diccionario de Localidades predefinidas (modificable por el usuario)
MAPA_LOCALIDADES = {
    "HONDA ARNALDI BARADERO": "Baradero",
    "GENOUD MOTOS BARADERO": "Baradero",
    "HOT MOTOS DEL VISO": "Del Viso (Pilar)",
    "HOT MOTOS PILAR": "Pilar",
    "MOTOSUR NEUQUÉN": "Neuquén",
    "MOTOSUR NEUQUEN": "Neuquén",
    "MOTOSUR SURIANI NEUQUÉN": "Neuquén",
    "MOTOSUR SURIANI NEUQUEN": "Neuquén",
    "MOTOLANDIA": "Buenos Aires",
    "RUTA 3 MOTOS SAN JUSTO": "San Justo (La Matanza)",
    "RUTA 3 MOTOS CASTELAR": "Castelar (Morón)",
    "MOTOS R": "Buenos Aires",
    "BIKECENTER PILAR": "Pilar",
    "CENTRO MOTOS SANTA TERESITA": "Santa Teresita",
    "BUSIN MOTOS GRAL. ROCA": "General Roca (Río Negro)",
    "GRUPO BUSIN NEUQUÉN": "Neuquén",
    "FOR EXPORT HURLINGHAM": "Hurlingham",
    "3 DE FEBRERO MOTOS SAN PEDRO": "San Pedro",
    "MOTOBEL GARÍN": "Garín (Escobar)",
    "HONDA MOTOPIER PILAR": "Pilar",
    "CENTRO MOTOS ZARATE": "Zárate",
    "ARROUZET HONDA - AZUL": "Azul",
    "G PRO TECH": "Buenos Aires",
    "M CABARCOS MOTOS ARRECIFES": "Arrecifes",
    "ALBANESECABARCOS MOTORSHOP": "Arrecifes",
    "MAXI MOTOS BARADERO": "Baradero",
    "OVERWHEELS JUNIN": "Junín",
    "SAN FRANCISCO MOTOS": "San Francisco",
    "MP MOTOS PILAR URUGUAY": "Pilar",
    "MOTOWOLF MONTE": "Monte",
    "ANTARES MOTOS ESCOBAR": "Escobar",
    "HONDA SOLO MOTOS SAN NICOLAS": "San Nicolás",
    "TBH MOTORCYCLES CAMPANA": "Campana",
    "FURLAN MOTOS SAN NICOLÁS": "San Nicolás",
    "PERGAMINO MOTOS": "Pergamino",
    "KELLER OFICIAL ING MASCHWITZ": "Escobar",
    "KELLER OFICIAL LUJAN": "Luján",
    "KELLER OFICIAL PUEBLO NUEVO": "Luján",
    "BAMBOO MOTOS Y BIKES CASTELAR": "Castelar (Morón)",
    "LAUREANO MOTOS SAN NICOLAS": "San Nicolás",
    # Champion Motos (2 locales — localidades a confirmar por Roberto)
    "CHAMPION MOTOS-CF MOTO OFICIAL": "San Nicolás",
    "CHAMPION MOTOS SAVIO 265": "San Nicolás",
    # Zkove San Nicolás
    "ZKOVE SAN NICOLAS": "San Nicolás",
    "ZKOVE SAN NICOLÁS": "San Nicolás",
}


def inferir_localidad(comercio_str: str) -> str:
    c_up = str(comercio_str).strip().upper()
    # Ubicaciones confirmadas por Roberto; prevalecen sobre inferencias.
    if "SUNRA" in c_up:
        return "Escobar"
    if "KELLER" in c_up:
        if any(zona in c_up for zona in ("MASCHWITZ", "MASHWITZ", "MASCHWIT", "ESCOBAR")):
            return "Escobar"
        if any(zona in c_up for zona in ("LUJAN", "LUJÁN", "PUEBLO NUEVO", "POLO NUEVO")):
            return "Luján"
    if c_up in MAPA_LOCALIDADES:
        return MAPA_LOCALIDADES[c_up]
        
    for k, loc in MAPA_LOCALIDADES.items():
        if loc != "Buenos Aires" and k in c_up:
            return loc
            
    # Inferencia por palabras clave
    if "PILAR" in c_up or "DEL VISO" in c_up:
        return "Pilar"
    if "NEUQUEN" in c_up or "NEUQUÉN" in c_up:
        return "Neuquén"
    if "SAN JUSTO" in c_up:
        return "San Justo (La Matanza)"
    if "CASTELAR" in c_up:
        return "Castelar (Morón)"
    if "SAN NICOLAS" in c_up or "SAN NICOLÁS" in c_up:
        return "San Nicolás"
    if "LUJAN" in c_up or "LUJÁN" in c_up:
        return "Luján"
    if "ESCOBAR" in c_up or "MASCHWITZ" in c_up or "GARIN" in c_up or "GARÍN" in c_up:
        return "Escobar / Garín"
    if "ZARATE" in c_up or "ZÁRATE" in c_up:
        return "Zárate"
    if "SAN PEDRO DE JUJUY" in c_up:
        return "San Pedro de Jujuy"
    if "SAN PEDRO" in c_up:
        return "San Pedro"
    if "BARADERO" in c_up:
        return "Baradero"
    if "ARRECIFES" in c_up:
        return "Arrecifes"
    if "PERGAMINO" in c_up:
        return "Pergamino"
    if "CAMPANA" in c_up:
        return "Campana"
    if "STA. TERESITA" in c_up or "SANTA TERESITA" in c_up:
        return "Santa Teresita"
    if "JUNIN" in c_up or "JUNÍN" in c_up:
        return "Junín"
    if "MONTE GRANDE" in c_up:
        return "Monte Grande"
    if "MONTEROS" in c_up:
        return "Monteros"
    if "MOTOWOLF MONTE" in c_up:
        return "Monte"
    if "HURLINGHAM" in c_up:
        return "Hurlingham"
    if "BUSIN" in c_up and "ROCA" in c_up:
        return "General Roca (Río Negro)"
    if "AZUL" in c_up:
        return "Azul"

    return "Otras Localidades"


def obtener_comercios_propios() -> list:
    return sorted(list(COMERCIOS_EXACTOS_CARTERA))


def limpiar_monto(val) -> float:
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip().replace("$", "").replace(" ", "")
    if s == "-" or s == "" or s.lower() == "nan":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def es_comercio_propio(comercio_str, cadena_str):
    return False


def procesar_excel_a_df(path: str = REPORT_PATH) -> pd.DataFrame:
    cols_requeridas = [
        "Solicitud", "Nombre", "Cadena", "Comercio", "Vendedor",
        "FechaAlta", "Linea", "MontoMaximo", "Capital",
        "FechaAprobacion", "FechaLiquidacion", "Estado"
    ]

    df = pd.read_excel(path, usecols=cols_requeridas)
    df["FechaAlta"] = pd.to_datetime(df["FechaAlta"], format="%d/%m/%Y", errors="coerce")
    df["Capital_Num"] = df["Capital"].apply(limpiar_monto)
    df["MontoMaximo_Num"] = df["MontoMaximo"].apply(limpiar_monto)

    def _asignar_monto(row):
        cap = row["Capital_Num"]
        max_m = row["MontoMaximo_Num"]
        st = str(row["Estado"]).strip().upper()
        if "LIQUID" in st or "APROB" in st or "ANALIS" in st:
            return cap if cap > 0 else max_m
        if "INCOMPL" in st:
            return max_m
        return 0.0

    df["Monto"] = df.apply(_asignar_monto, axis=1)
    df["Comercio"] = df["Comercio"].astype(str).str.strip()
    df["Cadena"] = df["Cadena"].astype(str).str.strip()
    df["Estado"] = df["Estado"].astype(str).str.strip()

    df["Es_Mi_Cartera"] = df.apply(lambda r: es_comercio_propio(r["Comercio"], r["Cadena"]), axis=1)
    df["Localidad"] = df["Comercio"].apply(inferir_localidad)

    try:
        df.to_parquet(PARQUET_PATH)
    except Exception:
        pass

    return df


def cargar_datos_reporte() -> pd.DataFrame:
    if (os.path.exists(PARQUET_PATH) and os.path.exists(REPORT_PATH)
            and os.path.getmtime(PARQUET_PATH) >= os.path.getmtime(REPORT_PATH)):
        try:
            df = pd.read_parquet(PARQUET_PATH)
            if "Localidad" not in df.columns:
                df["Localidad"] = df["Comercio"].apply(inferir_localidad)
                df.to_parquet(PARQUET_PATH)
            return df
        except Exception:
            pass
            
    if os.path.exists(REPORT_PATH):
        return procesar_excel_a_df(REPORT_PATH)
        
    return pd.DataFrame()
