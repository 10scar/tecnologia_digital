#!/usr/bin/env python3
"""Menú interactivo por consola para el monitor serie ESP32."""

from __future__ import annotations

from typing import Optional

import serial

from app.serie_core import (
    BAUDIOS_COMUNES,
    BAUDIOS_POR_DEFECTO,
    abrir_serie,
    detectar_esp32,
    leer_linea,
    obtener_puertos,
    texto_puerto,
)


def pausar():
    input("\nPulsa Enter para volver al menú...")


def menu_listar():
    puertos = obtener_puertos()
    print("\n--- Puertos serie ---")
    if not puertos:
        print("  (ninguno encontrado — ¿está conectado el ESP32?)")
    else:
        for i, p in enumerate(puertos, 1):
            print(f"  {i}. {texto_puerto(p)}")
    pausar()


def menu_elegir_puerto(actual: Optional[str]) -> Optional[str]:
    puertos = obtener_puertos()
    print("\n--- Elegir puerto ---")
    if not puertos:
        print("No hay puertos. Conecta el ESP32 y vuelve a intentar.")
        pausar()
        return actual

    for i, p in enumerate(puertos, 1):
        marca = "  ◀ actual" if p.device == actual else ""
        print(f"  {i}. {texto_puerto(p)}{marca}")
    print("  0. Cancelar")

    try:
        op = int(input("Número: ").strip())
    except ValueError:
        print("Opción no válida.")
        pausar()
        return actual

    if op == 0:
        return actual
    if 1 <= op <= len(puertos):
        elegido = puertos[op - 1].device
        print(f"Puerto seleccionado: {elegido}")
        pausar()
        return elegido

    print("Opción fuera de rango.")
    pausar()
    return actual


def menu_baudios(actual: int) -> int:
    print("\n--- Baudios ---")
    print(f"Actual: {actual}")
    for i, b in enumerate(BAUDIOS_COMUNES, 1):
        marca = "  ◀" if b == actual else ""
        print(f"  {i}. {b}{marca}")
    print("  0. Escribir otro valor")

    try:
        op = int(input("Número: ").strip())
    except ValueError:
        print("Opción no válida.")
        pausar()
        return actual

    if op == 0:
        try:
            nuevo = int(input("Baudios: ").strip())
            if nuevo > 0:
                return nuevo
        except ValueError:
            pass
        print("Valor no válido.")
        pausar()
        return actual

    if 1 <= op <= len(BAUDIOS_COMUNES):
        return BAUDIOS_COMUNES[op - 1]

    print("Opción fuera de rango.")
    pausar()
    return actual


def menu_autodetectar(actual: Optional[str]) -> Optional[str]:
    print("\n--- Autodetectar ESP32 ---")
    encontrado = detectar_esp32()
    if encontrado:
        print(f"Detectado: {encontrado}")
        pausar()
        return encontrado
    print("No se pudo detectar. Lista de puertos:")
    for p in obtener_puertos():
        print(f"  · {texto_puerto(p)}")
    print("Prueba la opción «Elegir puerto».")
    pausar()
    return actual


def monitor_consola(puerto: str, baudios: int):
    print(f"\n=== Monitor: {puerto} @ {baudios} ===")
    print("Ctrl+C para volver al menú.\n")
    try:
        with abrir_serie(puerto, baudios) as ser:
            while True:
                linea = leer_linea(ser)
                if linea is not None:
                    print(linea)
    except serial.SerialException as e:
        print(f"\nError de puerto: {e}")
        print("¿ESP32 conectado? ¿Permisos? (grupo dialout en Linux)")
        pausar()
    except KeyboardInterrupt:
        print("\n— Monitor cerrado —")
        pausar()


def menu_consola():
    from app.gui import lanzar_gui  # import local para evitar ciclos al cargar

    puerto: Optional[str] = detectar_esp32()
    baudios = BAUDIOS_POR_DEFECTO

    while True:
        print("\n" + "=" * 40)
        print("  MONITOR SERIE ESP32")
        print("=" * 40)
        print(f"  Puerto:  {puerto or '(ninguno)'}")
        print(f"  Baudios: {baudios}")
        print("-" * 40)
        print("  1. Listar puertos")
        print("  2. Autodetectar ESP32")
        print("  3. Elegir puerto")
        print("  4. Cambiar baudios")
        print("  5. Abrir monitor")
        print("  6. Abrir ventana gráfica")
        print("  0. Salir")
        print("-" * 40)

        op = input("Opción: ").strip()

        if op == "1":
            menu_listar()
        elif op == "2":
            puerto = menu_autodetectar(puerto)
        elif op == "3":
            puerto = menu_elegir_puerto(puerto)
        elif op == "4":
            baudios = menu_baudios(baudios)
        elif op == "5":
            if not puerto:
                print("\nPrimero elige o autodetecta un puerto.")
                pausar()
            else:
                monitor_consola(puerto, baudios)
        elif op == "6":
            try:
                lanzar_gui(puerto, baudios)
            except Exception as e:
                print(f"No se pudo abrir la GUI: {e}")
                pausar()
        elif op == "0":
            print("Hasta luego.")
            break
        else:
            print("Opción no válida.")
