"""Funciones de utilidad compartidas entre cogs."""
import json
import os
import datetime

BASE = os.path.join(os.path.dirname(__file__), "datos")

ROLES_MANDO = ["Entrenadores", "Administradores", "Coronel", "Cabo Primero", "Cabo"]

def _ruta(archivo: str) -> str:
    return os.path.join(BASE, archivo)

def cargar(archivo: str) -> dict:
    try:
        with open(_ruta(archivo), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar(archivo: str, datos: dict):
    with open(_ruta(archivo), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def es_mando(interaction) -> bool:
    roles = [r.name for r in interaction.user.roles]
    return any(r in roles for r in ROLES_MANDO)

def ahora() -> str:
    return datetime.datetime.now().isoformat()

def ahora_fmt() -> str:
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

def perfil_base(member) -> dict:
    return {
        "nombre": member.display_name,
        "rango": next((r.name for r in reversed(member.roles) if r.name != "@everyone"), "Sin rango"),
        "fecha_ingreso": ahora(),
        "misiones": 0,
        "puntos": 0,
        "ausencias": 0,
        "sanciones": 0,
    }

def obtener_perfil(member) -> dict:
    perfiles = cargar("perfiles.json")
    uid = str(member.id)
    if uid not in perfiles:
        perfiles[uid] = perfil_base(member)
        guardar("perfiles.json", perfiles)
    return perfiles[uid]

def sumar_puntos(user_id: str, cantidad: int, motivo: str):
    puntos = cargar("puntos.json")
    if user_id not in puntos:
        puntos[user_id] = {"puntos": 0, "historial": []}
    puntos[user_id]["puntos"] += cantidad
    puntos[user_id]["historial"].append({
        "cantidad": cantidad,
        "motivo": motivo,
        "fecha": ahora_fmt(),
    })
    guardar("puntos.json", puntos)

    perfiles = cargar("perfiles.json")
    if user_id in perfiles:
        perfiles[user_id]["puntos"] = puntos[user_id]["puntos"]
        guardar("perfiles.json", perfiles)

COLOR_MILITAR = 0xB48C14
COLOR_ROJO    = 0xB42828
COLOR_VERDE   = 0x2EB86B
COLOR_AZUL    = 0x1E50A0
COLOR_OSCURO  = 0x282832
