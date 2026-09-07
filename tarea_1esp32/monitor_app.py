#!/usr/bin/env python3
"""
Monitor serie para ESP32 — punto de entrada.

Uso:
  python3 monitor_app.py          # menú en consola
  python3 monitor_app.py --gui    # ventana gráfica
"""

from __future__ import annotations

import argparse

from app.consola import menu_consola, monitor_consola
from app.gui import lanzar_gui
from app.serie_core import BAUDIOS_POR_DEFECTO, detectar_esp32, obtener_puertos, texto_puerto


def main():
    parser = argparse.ArgumentParser(description="Monitor serie ESP32 (menú o GUI)")
    parser.add_argument("--gui", action="store_true", help="Abrir ventana gráfica")
    parser.add_argument("-p", "--puerto", help="Puerto serie (modo directo)")
    parser.add_argument("-b", "--baudios", type=int, default=BAUDIOS_POR_DEFECTO)
    parser.add_argument("-l", "--listar", action="store_true", help="Listar puertos y salir")
    args = parser.parse_args()

    if args.listar:
        puertos = obtener_puertos()
        if not puertos:
            print("No se encontró ningún puerto serie.")
        else:
            print("Puertos serie disponibles:")
            for p in puertos:
                print(f"  {texto_puerto(p)}")
        return

    if args.puerto:
        monitor_consola(args.puerto, args.baudios)
        return

    if args.gui:
        lanzar_gui(detectar_esp32(), args.baudios)
        return

    menu_consola()


if __name__ == "__main__":
    main()
