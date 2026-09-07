#!/usr/bin/env python3
"""Funciones compartidas del monitor serie ESP32."""

from __future__ import annotations

import sys
import time
from typing import Optional

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Falta pyserial. Instálalo con:")
    print("  pip install pyserial")
    print("  o: pip install -r requirements.txt")
    sys.exit(1)


BAUDIOS_POR_DEFECTO = 115200
BAUDIOS_COMUNES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600)


def obtener_puertos() -> list:
    return list(list_ports.comports())


def texto_puerto(p) -> str:
    return f"{p.device}  —  {p.description}"


def detectar_esp32() -> Optional[str]:
    """Busca chips típicos del ESP32; si solo hay un puerto, lo usa."""
    claves = ("cp210", "ch340", "ch910", "usb serial", "uart", "esp32", "silicon labs")
    for p in obtener_puertos():
        texto = f"{p.description} {p.manufacturer or ''} {p.hwid}".lower()
        if any(k in texto for k in claves):
            return p.device
    puertos = obtener_puertos()
    if len(puertos) == 1:
        return puertos[0].device
    return None


def abrir_serie(puerto: str, baudios: int) -> serial.Serial:
    ser = serial.Serial(puerto, baudios, timeout=0.2)
    time.sleep(0.4)  # el ESP32 suele reiniciarse al abrir el puerto
    ser.reset_input_buffer()
    return ser


def leer_linea(ser: serial.Serial) -> Optional[str]:
    raw = ser.readline()
    if not raw:
        return None
    return raw.decode("utf-8", errors="replace").rstrip("\r\n")
