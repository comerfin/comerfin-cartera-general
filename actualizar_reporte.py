"""
Script autónomo para descargar el reporte actualizado de Prendo / MG Group.
Se puede ejecutar manualmente o programar 1, 2 o 3 veces al día vía cron / launchd.
"""

import os
import sys
import shutil
import time
import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

PORTAL_URL = os.getenv("PORTAL_URL", "https://app.mg-group.com.ar")
PORTAL_USER = os.getenv("PORTAL_USER")
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD")

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
SESSION_FILE = os.path.join(os.path.dirname(__file__), "session_state.json")


def login_and_download():
    print(f"[{datetime.datetime.now()}] Iniciando actualización de reporte...")
    
    with sync_playwright() as p:
        executable = shutil.which("chromium") or shutil.which("chromium-browser")
        browser = p.chromium.launch(
            executable_path=executable,
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        # Intentar cargar sesión existente
        storage = None  # Renovar la autenticación al iniciar cada actualización.
        context = browser.new_context(
            storage_state=storage,
            viewport={"width": 1440, "height": 900},
            accept_downloads=True
        )
        page = context.new_page()
        page.set_default_timeout(15000)

        try:
            page.goto("https://app.mg-group.com.ar/reportes", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # Si nos pide login nuevamente
            if "signin" in page.url or "auth0" in page.url or page.locator("text='Usuario y clave'").count() > 0:
                print("[*] Sesión expirada o no iniciada. Autenticando...")
                if not PORTAL_USER or not PORTAL_PASSWORD:
                    raise RuntimeError("Faltan las credenciales de Prendo en la configuración privada.")
                btn_usr = page.locator("text='Usuario y clave'").first
                if btn_usr.count() > 0:
                    btn_usr.click()
                    page.wait_for_timeout(4000)

                u_field = page.locator("input#username, input[name='username'], input[type='email']").first
                if u_field.count() > 0:
                    u_field.fill(PORTAL_USER)
                
                p_field = page.locator("input#password, input[name='password'], input[type='password']").first
                if p_field.count() > 0:
                    p_field.fill(PORTAL_PASSWORD)
                else:
                    btn_cont = page.locator("button[type='submit'], button:has-text('Continuar')").first
                    if btn_cont.count() > 0:
                        btn_cont.click()
                        page.wait_for_timeout(3000)
                        p_field = page.locator("input#password, input[name='password']").first
                        if p_field.count() > 0:
                            p_field.fill(PORTAL_PASSWORD)

                btn_sub = page.locator("button[type='submit'], button:has-text('Continuar'), button:has-text('Ingresar'), button:has-text('Iniciar sesión')").first
                if btn_sub.count() > 0:
                    btn_sub.click()
                else:
                    page.keyboard.press("Enter")

                page.wait_for_timeout(7000)
                page.wait_for_url("**/app.mg-group.com.ar/**", timeout=30000)
                if "signin" in page.url:
                    raise RuntimeError("No se pudo iniciar sesión en Prendo.")
                context.storage_state(path=SESSION_FILE)
                print("[+] Login exitoso y sesión renovada.")

                page.goto("https://app.mg-group.com.ar/reportes", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

            # Rellenar fechas
            page.locator(".MuiPickersInputBase-sectionsContainer").first.wait_for(state="visible", timeout=30000)
            containers = page.locator(".MuiPickersInputBase-sectionsContainer").all()
            if len(containers) >= 2:
                from zoneinfo import ZoneInfo
                hoy = datetime.datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
                inicio_mes = hoy.replace(day=1)
                
                desde_str = inicio_mes.strftime("%d%m%Y")
                hasta_str = hoy.strftime("%d%m%Y")
                
                containers[0].click()
                time.sleep(0.5)
                page.keyboard.type(desde_str)
                time.sleep(1)

                containers[1].click()
                time.sleep(0.5)
                page.keyboard.type(hasta_str)
                time.sleep(1)

                page.locator("text='Reporte de solicitudes'").click()
                time.sleep(1.5)

                btn_desc = page.locator("button:has-text('Descargar')").first
                if not btn_desc.is_disabled():
                    print("[*] Descargando archivo Reporte.xlsx...")
                    with page.expect_download(timeout=90000) as download_info:
                        btn_desc.click()
                    dl = download_info.value
                    dest = os.path.join(DOWNLOADS_DIR, "Reporte.xlsx")
                    temporal = dest + ".tmp.xlsx"
                    try:
                        dl.save_as(temporal)
                        import pandas as pd
                        required = {"Solicitud", "Cadena", "Comercio", "Vendedor", "FechaAlta", "Linea", "MontoMaximo", "Capital", "FechaAprobacion", "FechaLiquidacion", "Estado"}
                        columns = set(pd.read_excel(temporal, nrows=0).columns)
                        if not required.issubset(columns):
                            raise RuntimeError("El archivo descargado no tiene las columnas esperadas.")
                        os.replace(temporal, dest)
                    finally:
                        if os.path.exists(temporal):
                            os.remove(temporal)
                    print(f"[{datetime.datetime.now()}] [OK] Archivo actualizado exitosamente: {dest} ({os.path.getsize(dest)} bytes)")
                    # Historial anual: solo liquidados, filtrados por fecha de liquidación.
                    page.get_by_role("button", name="Todos", exact=True).click()
                    page.get_by_role("button", name="Liquidadas", exact=True).click()
                    page.get_by_role("button", name="Fecha de Alta", exact=True).click()
                    page.get_by_role("button", name="Fecha de Liquidación", exact=True).click()
                    page.get_by_role("spinbutton", name="Day", exact=True).nth(0).click()
                    page.keyboard.type(hoy.replace(month=1, day=1).strftime("%d%m%Y"))
                    page.keyboard.press("Tab")
                    with page.expect_download(timeout=90000) as historico_info:
                        page.get_by_role("button", name="Descargar", exact=True).click()
                    historico = historico_info.value
                    destino_historial = os.path.join(DOWNLOADS_DIR, "HistorialLiquidaciones.xlsx")
                    temporal_historial = destino_historial + ".tmp.xlsx"
                    try:
                        historico.save_as(temporal_historial)
                        columnas_historial = set(pd.read_excel(temporal_historial, nrows=0).columns)
                        if not required.issubset(columnas_historial):
                            raise RuntimeError("El historial descargado no tiene las columnas esperadas.")
                        os.replace(temporal_historial, destino_historial)
                    finally:
                        if os.path.exists(temporal_historial):
                            os.remove(temporal_historial)
                    print("[OK] Historial anual de liquidaciones actualizado.")

                else:
                    raise RuntimeError("El portal mantiene deshabilitado el botón Descargar. Revisá las fechas.")
            else:
                raise RuntimeError("No se encontraron los campos de fecha. Puede haber vencido la sesión.")

        except Exception as e:
            mensaje = "Faltan las credenciales de Prendo en la configuración privada." if not PORTAL_USER or not PORTAL_PASSWORD else "No se pudo completar el acceso o la descarga del portal."
            print(f"[!] {type(e).__name__}: {mensaje}")
            raise SystemExit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    login_and_download()
