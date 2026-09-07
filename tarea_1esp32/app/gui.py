#!/usr/bin/env python3
"""Ventana gráfica (Tkinter) para el monitor serie ESP32."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional

import serial

from app.serie_core import (
    BAUDIOS_COMUNES,
    BAUDIOS_POR_DEFECTO,
    abrir_serie,
    detectar_esp32,
    leer_linea,
    obtener_puertos,
)


def lanzar_gui(
    puerto_inicial: Optional[str] = None,
    baudios_inicial: int = BAUDIOS_POR_DEFECTO,
):
    root = tk.Tk()
    root.title("Monitor serie ESP32")
    root.geometry("780x520")
    root.minsize(640, 400)

    ser_lock = threading.Lock()
    ser_ref: dict = {"ser": None, "stop": threading.Event()}

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")

    ttk.Label(top, text="Puerto:").pack(side="left")
    puerto_var = tk.StringVar()
    combo_puerto = ttk.Combobox(top, textvariable=puerto_var, width=28, state="readonly")
    combo_puerto.pack(side="left", padx=(4, 8))

    ttk.Label(top, text="Baudios:").pack(side="left")
    baudios_var = tk.StringVar(value=str(baudios_inicial))
    combo_baud = ttk.Combobox(
        top,
        textvariable=baudios_var,
        values=[str(b) for b in BAUDIOS_COMUNES],
        width=10,
    )
    combo_baud.pack(side="left", padx=(4, 8))

    estado_var = tk.StringVar(value="Desconectado")
    ttk.Label(top, textvariable=estado_var).pack(side="right")

    botones = ttk.Frame(root, padding=(8, 0, 8, 8))
    botones.pack(fill="x")

    txt = scrolledtext.ScrolledText(root, wrap="word", font=("Consolas", 11), state="disabled")
    txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def escribir(msg: str, final_nl: bool = True):
        txt.configure(state="normal")
        txt.insert("end", msg + ("\n" if final_nl else ""))
        txt.see("end")
        txt.configure(state="disabled")

    def refrescar_puertos():
        puertos = obtener_puertos()
        valores = [p.device for p in puertos]
        combo_puerto["values"] = valores
        if puerto_inicial and puerto_inicial in valores:
            puerto_var.set(puerto_inicial)
        elif valores and not puerto_var.get():
            auto = detectar_esp32()
            puerto_var.set(auto if auto in valores else valores[0])
        if not valores:
            puerto_var.set("")
            escribir("(No hay puertos. Conecta el ESP32 y pulsa «Listar / refrescar».)")

    def autodetectar():
        encontrado = detectar_esp32()
        if encontrado:
            puerto_var.set(encontrado)
            escribir(f"Autodetectado: {encontrado}")
        else:
            messagebox.showinfo(
                "Autodetectar",
                "No se encontró un ESP32 típico.\nElige el puerto a mano.",
            )
            refrescar_puertos()

    def hilo_lectura():
        while not ser_ref["stop"].is_set():
            with ser_lock:
                ser = ser_ref["ser"]
                if ser is None or not ser.is_open:
                    break
                try:
                    linea = leer_linea(ser)
                except serial.SerialException:
                    root.after(0, lambda: desconectar(error="Se perdió la conexión serie."))
                    break
            if linea is not None:
                root.after(0, lambda l=linea: escribir(l))
            else:
                time.sleep(0.02)

    def conectar():
        if ser_ref["ser"] is not None:
            return
        puerto = puerto_var.get().strip()
        if not puerto:
            messagebox.showwarning("Puerto", "Selecciona un puerto primero.")
            return
        try:
            baudios = int(baudios_var.get().strip())
        except ValueError:
            messagebox.showwarning("Baudios", "Valor de baudios no válido.")
            return
        try:
            ser = abrir_serie(puerto, baudios)
        except serial.SerialException as e:
            messagebox.showerror("Error", f"No se pudo abrir {puerto}:\n{e}")
            return

        ser_ref["ser"] = ser
        ser_ref["stop"].clear()
        estado_var.set(f"Conectado · {puerto} @ {baudios}")
        btn_conectar.configure(state="disabled")
        btn_desconectar.configure(state="normal")
        escribir(f"=== Conectado a {puerto} @ {baudios} ===")
        threading.Thread(target=hilo_lectura, daemon=True).start()

    def desconectar(error: Optional[str] = None):
        ser_ref["stop"].set()
        with ser_lock:
            ser = ser_ref["ser"]
            ser_ref["ser"] = None
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
        estado_var.set("Desconectado")
        btn_conectar.configure(state="normal")
        btn_desconectar.configure(state="disabled")
        if error:
            escribir(error)
        else:
            escribir("=== Desconectado ===")

    def limpiar():
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.configure(state="disabled")

    def al_cerrar():
        desconectar()
        root.destroy()

    ttk.Button(botones, text="Listar / refrescar", command=refrescar_puertos).pack(
        side="left", padx=2
    )
    ttk.Button(botones, text="Autodetectar", command=autodetectar).pack(side="left", padx=2)
    btn_conectar = ttk.Button(botones, text="Conectar / monitor", command=conectar)
    btn_conectar.pack(side="left", padx=2)
    btn_desconectar = ttk.Button(
        botones, text="Desconectar", command=desconectar, state="disabled"
    )
    btn_desconectar.pack(side="left", padx=2)
    ttk.Button(botones, text="Limpiar pantalla", command=limpiar).pack(side="left", padx=2)

    refrescar_puertos()
    root.protocol("WM_DELETE_WINDOW", al_cerrar)
    root.mainloop()
