"""Cog: Sistema de Cursos — Formación táctica progresiva con roles y exámenes."""
import discord
from discord.ext import commands
import os, sys, asyncio, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, es_mando, sumar_puntos, COLOR_MILITAR, ahora_fmt

GUILD_ID                = int(os.getenv("GUILD_ID", "0"))
CANAL_ENTRENAMIENTOS_ID = int(os.getenv("CANAL_ENTRENAMIENTOS_ID", "0"))
CANAL_MANDO_ID          = int(os.getenv("CANAL_MANDO_ID", "0"))
UMBRAL_APROBADO         = 0.70   # 70 % para pasar
COOLDOWN_HORAS          = 24     # horas de espera entre intentos (cursos avanzados)
PUNTOS_DUDA_RESUELTA    = 10     # puntos al instructor por resolver una duda

# ─────────────────────────────────────────────────────────────────────────────
#  DEFINICIÓN DE CURSOS
# ─────────────────────────────────────────────────────────────────────────────
CURSOS = {
    "basico": {
        "nombre":        "Curso Básico — Operación Supervivencia",
        "codigo":        "OS-01",
        "emoji":         "🪖",
        "color":         0x2E8B57,
        "rol_nombre":    "Soldado Básico",
        "rol_color":     0x3CB371,
        "requisitos":    [],
        "duracion_dias": 3,
        "cooldown_h":    0,   # sin cooldown — puede reintentar siempre
        "descripcion": (
            "El punto de partida de todo operador. Sin este curso no puedes acceder "
            "a ningún otro. Cubre los sistemas esenciales para sobrevivir: "
            "**ACE3, TFAR, navegación MGRS y primeros auxilios.**"
        ),
        "practica": (
            "**Ejercicios requeridos antes del examen:**\n"
            "1. Realiza un radio check con tu TL (canal SR)\n"
            "2. Localiza y reporta tu posición MGRS desde el microDAGR\n"
            "3. Venda correctamente a un compañero simulando una herida de bala\n"
            "4. Completa el recorrido de orientación con el mapa y la brújula"
        ),
        "loadout": (
            "**✅ Loadout autorizado — Soldado Básico**\n\n"
            "**Armas primarias:** M4A1, M16A4, AK-74M, G36C\n"
            "**Secundaria:** M9 Beretta, Makarov PM\n"
            "**NVG:** AN/PVS-14 estándar\n"
            "**Radio:** SR — AN/PRC-152\n"
            "**Médico básico:** QuikClot ×3 · Elastic Bandage ×3 · Tourniquet ×2 · Morphine ×1 · Epinefrina ×1\n"
            "**Chalecos:** CIRAS, Carrier Lite, 6B23\n"
            "**Ópticas:** iron sight, red dot, ACOG básico"
        ),
        "puntos_recompensa": 30,
    },
    "medico": {
        "nombre":        "Curso Médico — Cruz de Campo",
        "codigo":        "CC-02",
        "emoji":         "⚕️",
        "color":         0xDC143C,
        "rol_nombre":    "Médico de Campo",
        "rol_color":     0xCC2222,
        "requisitos":    ["basico"],
        "duracion_dias": 3,
        "cooldown_h":    24,
        "descripcion": (
            "Formación completa en **KAT Advanced Medical**. El médico de pelotón es "
            "responsable de mantener a todos en combate. Cubre triaje, procedimientos avanzados "
            "y evacuación médica bajo fuego."
        ),
        "practica": (
            "**Ejercicios requeridos:**\n"
            "1. Triaje de 3 bajas simultáneas bajo fuego real\n"
            "2. Administrar IV Saline 1000 ml a un paciente en estado crítico\n"
            "3. Solicitar un CASEVAC completo (9-Line) por radio LR\n"
            "4. Preparar y marcar una LZ para helicóptero médico"
        ),
        "loadout": (
            "**✅ Equipo adicional — Médico de Campo**\n"
            "*(Se suma al loadout del Soldado Básico)*\n\n"
            "**Kit médico avanzado:** IV Saline 500/1000 ml ×4 · Sangre O- ×2 · Chest Seal ×2 "
            "· Adenosina ×2 · Naloxone ×1 · Atropine ×1\n"
            "**Mochila médica:** Bergen médica de pelotón 30 L\n"
            "**Extras:** BackpackOnChest con suministros · Defibrilador ACE\n"
            "**Uniforme:** Marcado con cruz roja (protección Convenio de Ginebra)"
        ),
        "puntos_recompensa": 50,
    },
    "drones": {
        "nombre":        "Curso Drones — Ojo del Cielo",
        "codigo":        "OC-03",
        "emoji":         "🚁",
        "color":         0x9932CC,
        "rol_nombre":    "Operador ISR",
        "rol_color":     0x8B008B,
        "requisitos":    ["basico"],
        "duracion_dias": 2,
        "cooldown_h":    24,
        "descripcion": (
            "Sistemas UAV: reconocimiento ISR con **Mavic 3**, ataques FPV con **Crocus** "
            "y sistemas autónomos **Brasko AI**. El operador de drones es los ojos del pelotón."
        ),
        "practica": (
            "**Ejercicios requeridos:**\n"
            "1. Volar Mavic 3 a >100 m y reportar 3 posiciones enemigas en MGRS\n"
            "2. Realizar un ataque FPV Crocus a un vehículo designado por el TL\n"
            "3. Cubrir la retirada del pelotón con ISR continuo\n"
            "4. Operar Brasko en modo semi-autónomo con autorización del TL"
        ),
        "loadout": (
            "**✅ Equipo adicional — Operador ISR**\n"
            "*(Se suma al loadout del Soldado Básico)*\n\n"
            "**Drones:** Mavic 3 Improved · FPV Crocus ×2 · Terminal de control\n"
            "**Arma compacta:** Opción de M4 CQBR o AK-74U para movilidad\n"
            "**Chaleco:** Preferencia Carrier Lite (menor peso)\n"
            "**Mochila:** Bergen pequeña para equipo UAV"
        ),
        "puntos_recompensa": 50,
    },
    "aviacion": {
        "nombre":        "Curso Aviación — Alas de Acero",
        "codigo":        "AA-04",
        "emoji":         "✈️",
        "color":         0x4169E1,
        "rol_nombre":    "Piloto Certificado",
        "rol_color":     0x1E50A0,
        "requisitos":    ["basico"],
        "duracion_dias": 4,
        "cooldown_h":    24,
        "descripcion": (
            "Certificación de piloto para **Hatchet H-60** y aeronaves **USAF**. "
            "Cubre inserción, CASEVAC, CAS 9-Line y protocolos de LZ. "
            "Solo pilotos certificados pueden operar aeronaves en misiones oficiales."
        ),
        "practica": (
            "**Ejercicios requeridos:**\n"
            "1. Inserción de pelotón completo con H-60 en LZ hostil\n"
            "2. Completar un 9-Line CAS para un A-10C sobre objetivo designado\n"
            "3. CASEVAC hot extraction bajo fuego activo\n"
            "4. Configurar cargas en Pylon Manager y completar misión de bombardeo"
        ),
        "loadout": (
            "**✅ Equipo adicional — Piloto Certificado**\n"
            "*(Se suma al loadout del Soldado Básico)*\n\n"
            "**Aeronaves:** Hatchet H-60 (UH/HH/MH) · aeronaves USAF completas\n"
            "**Radio LR:** AN/PRC-117F (obligatoria para pilotos)\n"
            "**Casco:** HGU-56P con visor NVG integrado\n"
            "**Chaleco:** Chaleco de vuelo con survival kit\n"
            "**Pylon Manager:** Configuración completa de cargas\n"
            "**Emergencia:** M9 + kit de supervivencia"
        ),
        "puntos_recompensa": 60,
    },
    "cqb": {
        "nombre":        "Curso CQB — Sombra Urbana",
        "codigo":        "SU-05",
        "emoji":         "🔫",
        "color":         0xFF4500,
        "rol_nombre":    "Operador CQB",
        "rol_color":     0xCC3300,
        "requisitos":    ["basico"],
        "duracion_dias": 3,
        "cooldown_h":    24,
        "descripcion": (
            "Combate en espacios cerrados — el entorno más letal. "
            "**Breach Rewrite, limpieza de cuartos, melee y equipamiento especial** "
            "para operaciones urbanas. Requiere disciplina absoluta."
        ),
        "practica": (
            "**Ejercicios requeridos:**\n"
            "1. Limpiar edificio de 3 pisos con equipo de 4 personas\n"
            "2. Realizar 3 breachings diferentes (explosivo, ariete, palanca)\n"
            "3. Eliminación silenciosa de centinela sin alertar al grupo\n"
            "4. Simulacro de rescate de rehén sin bajas amigas"
        ),
        "loadout": (
            "**✅ Equipo adicional — Operador CQB**\n"
            "*(Se suma al loadout del Soldado Básico)*\n\n"
            "**NVG avanzado:** TPNVG AN/PSQ-20 (panorámico 4 tubos)\n"
            "**Dual weapons:** KJW — segunda arma primaria compacta\n"
            "**Supresores:** Sound moderators RHS para M4/AK\n"
            "**Breaching:** Explosive charge ×2 · Battering ram · Bolt cutters\n"
            "**Armas CQB:** M4 CQBR · AKS-74U · MP5 (con supresor)\n"
            "**Melee:** Cuchillo + takedown silencioso ACE"
        ),
        "puntos_recompensa": 50,
    },
    "zeus": {
        "nombre":        "Curso Zeus — Dios de la Guerra",
        "codigo":        "DG-06",
        "emoji":         "⚡",
        "color":         0xFFD700,
        "rol_nombre":    "Game Master",
        "rol_color":     0xDAA520,
        "requisitos":    ["basico", "medico", "cqb"],
        "duracion_dias": 4,
        "cooldown_h":    24,
        "descripcion": (
            "Formación de **Game Master**. El Zeus dirige la narrativa, controla la IA "
            "con **LAMBS** y crea experiencias inmersivas. Requiere conocimiento profundo "
            "del servidor y responsabilidad extrema. Requiere Básico + Médico + CQB."
        ),
        "practica": (
            "**Ejercicios requeridos:**\n"
            "1. Dirigir misión de 30 min con mínimo 6 jugadores\n"
            "2. Usar LAMBS correctamente (Danger + Suppression mínimo)\n"
            "3. Crear evento de refuerzo enemigo dinámico desde Zeus\n"
            "4. Gestionar incidente técnico en vivo sin romper inmersión"
        ),
        "loadout": (
            "**✅ Acceso especial — Game Master**\n\n"
            "**Zeus Enhanced:** Acceso completo a Zeus Enhanced + Additions + Crows\n"
            "**Módulos LAMBS:** Danger · Suppression · RPG · Turrets\n"
            "**Crows:** Cámaras de espectador y seguimiento de misión\n"
            "**Frecuencia GM:** LR Zeus 88.000 MHz (canal exclusivo)\n"
            "**Nota:** El GM opera fuera del juego en las misiones que no dirige."
        ),
        "puntos_recompensa": 80,
    },
    "comando": {
        "nombre":        "Curso Comando — Fuerzas Especiales",
        "codigo":        "FE-07",
        "emoji":         "🦅",
        "color":         0x1A1A2E,
        "rol_nombre":    "Fuerzas Especiales",
        "rol_color":     0x2C2C54,
        "requisitos":    ["basico", "medico", "drones", "aviacion", "cqb", "zeus"],
        "duracion_dias": 7,
        "cooldown_h":    48,
        "descripcion": (
            "El curso más exigente del clan. Solo quien haya completado **TODOS** los cursos "
            "anteriores puede postularse. Las Fuerzas Especiales ejecutan misiones de alto valor, "
            "inserción profunda y operaciones negras. Solo los mejores llegan aquí."
        ),
        "practica": (
            "**Ejercicios requeridos (todos obligatorios):**\n"
            "1. Infiltración nocturna sin detección — TPNVG obligatorio\n"
            "2. Rescate de rehén con extracción SPIE en HH-60\n"
            "3. Destrucción de HVT con IED + exfil bajo fuego\n"
            "4. Coordinación multi-elemento: drones + tierra + aviación simultáneos\n"
            "5. Examen práctico ante evaluador del mando (1h sin errores críticos)"
        ),
        "loadout": (
            "**✅ Equipo Tier-1 — Fuerzas Especiales**\n"
            "*(Acceso total + todo lo anterior más:)*\n\n"
            "**Armas SF:** HK416 D14.5 · CQBR Block II · MK18 Mod 1 · M110 SASS\n"
            "**Supresores Tier-1:** AAC M4-2000 · Daniel Defense · SureFire SOCOM\n"
            "**Ópticas top:** LPVO Schmidt & Bender · ACOG RCO · GPNVG-18 quad-tube\n"
            "**Equipo especial:** SOFLAM AN/PEQ-1 · Strobe IR · SPIE Rig\n"
            "**Explosivos:** M183 Demolition Charge · C4 Block\n"
            "**Ghillie:** Suit completo para sniper/recon\n"
            "**Todo:** KJW dual SF · BackpackOnChest ×2 · Loadout médico completo"
        ),
        "puntos_recompensa": 150,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  PREGUNTAS DE EXAMEN (mínimo 10 por curso)
# ─────────────────────────────────────────────────────────────────────────────
EXAMENES = {
    "basico": [
        {"p": "¿Qué tecla abre el menú de interacción ACE sobre otro soldado?",
         "o": ["F", "Tecla Windows (Inicio)", "Ctrl+E", "Alt+F"], "c": 1},
        {"p": "¿Qué vendaje es más efectivo para una herida de bala en KAT Medical?",
         "o": ["Bandage básico", "Elastic Bandage", "QuikClot", "Splint"], "c": 2},
        {"p": "¿Con qué tecla hablas por la radio SR en TFAR?",
         "o": ["Alt+Caps Lock", "Caps Lock", "Ctrl+T", "V"], "c": 1},
        {"p": "¿Qué precisión da una cuadrícula MGRS de 6 dígitos (3+3)?",
         "o": ["1 000 metros", "100 metros", "10 metros", "1 metro"], "c": 1},
        {"p": "¿Cuál es el PRIMER paso al encontrar a un herido en combate?",
         "o": ["Aplicar morfina", "Llamar por radio", "Arrastrarlo a cubierto y detener hemorragias", "Aplicar IV"], "c": 2},
        {"p": "¿Qué significa 'Cambio' al finalizar un mensaje de radio?",
         "o": ["Cambiar de canal", "Fin del mensaje, espero tu respuesta", "Urgencia máxima", "Cambiar de operador"], "c": 1},
        {"p": "¿Cuál es el rango de la radio SR en terreno plano?",
         "o": ["500 metros", "2–3 kilómetros", "10 kilómetros", "Ilimitado"], "c": 1},
        {"p": "En MGRS, ¿qué eje lees PRIMERO al dar una cuadrícula?",
         "o": ["Norte (Northing)", "Este (Easting)", "Altitud", "Azimut"], "c": 1},
        {"p": "¿Qué color de humo indica que una LZ es SEGURA para aterrizar?",
         "o": ["Rojo", "Morado", "Verde", "Amarillo"], "c": 2},
        {"p": "¿Con qué tecla hablas por la radio LR en TFAR?",
         "o": ["Caps Lock", "Ctrl+Caps Lock", "Alt+Caps Lock", "Shift+V"], "c": 2},
        {"p": "¿Para qué sirve el tourniquet en KAT Medical?",
         "o": ["Reduce el dolor", "Repone sangre", "Detiene hemorragias severas en extremidades", "Revive inconscientes"], "c": 2},
        {"p": "¿Qué hace la auto-interacción ACE (Alt+Windows)?",
         "o": ["Interactúa con objetos del suelo", "Accede a tu propio menú de acciones", "Abre el mapa", "Llama al médico"], "c": 1},
    ],
    "medico": [
        {"p": "¿Qué procedimiento médico es exclusivo del médico de pelotón?",
         "o": ["Elastic Bandage", "Tourniquet", "IV Saline 1000 ml", "QuikClot"], "c": 2},
        {"p": "En triage NATO, ¿qué significa T1 (rojo)?",
         "o": ["Herida mínima", "Riesgo vital inmediato — atención URGENTE", "Sin posibilidad de sobrevivir", "Demorado"], "c": 1},
        {"p": "¿Cuál es la frecuencia cardíaca normal en KAT Medical?",
         "o": ["30–50 lpm", "60–100 lpm", "120–160 lpm", "40–60 lpm"], "c": 1},
        {"p": "¿Qué medicamento trata la fibrilación ventricular en KAT?",
         "o": ["Morphine", "Epinefrina", "Adenosina", "Naloxone"], "c": 2},
        {"p": "¿Cuánto volumen de sangre es normal en KAT?",
         "o": ["2 000–3 000 ml", "4 000–5 000 ml", "5 000–6 000 ml", "8 000–9 000 ml"], "c": 2},
        {"p": "¿Para qué sirve el Naloxone IV?",
         "o": ["Tratar fibrilación", "Revertir sobredosis de morfina", "Cerrar heridas de tórax", "Reponer sangre"], "c": 1},
        {"p": "¿Qué es un Chest Seal oclusivo?",
         "o": ["Venda para extremidades", "Cierre hermético para heridas de tórax con succión", "Tourniquet", "Soporte de fractura"], "c": 1},
        {"p": "¿Qué línea del 9-Line MEDEVAC describe la seguridad de la zona?",
         "o": ["Línea 1", "Línea 3", "Línea 6", "Línea 9"], "c": 2},
        {"p": "Paciente inconsciente con pulso débil. ¿Qué prioridad de triage?",
         "o": ["T3 Mínimo", "T4 Expectante", "T1 Urgente", "T2 Prioritario"], "c": 2},
        {"p": "¿Qué añade KAT Rewrite que no tiene ACE básico?",
         "o": ["Tourniquet", "Sistema de temperatura y shock hemorrágico", "Morphine", "Elastic Bandage"], "c": 1},
        {"p": "¿Qué hace la Epinefrina en KAT?",
         "o": ["Reduce el dolor", "Repone sangre", "Revive pacientes inconscientes con pulso débil", "Detiene hemorragias"], "c": 2},
        {"p": "¿Cuánto tiempo tenés idealmente para tratar un T1 antes de que sea crítico?",
         "o": ["30 minutos", "2 horas", "Menos de 1 hora (Golden Hour)", "10 minutos"], "c": 2},
    ],
    "drones": [
        {"p": "¿A qué altura mínima volar el Mavic 3 para evitar detección auditiva?",
         "o": ["20 m", "50 m", "100 m", "200 m"], "c": 2},
        {"p": "¿Cuál es la principal diferencia del FPV Crocus vs el Mavic 3?",
         "o": ["Mayor autonomía", "Cámara térmica avanzada", "Drone de ataque kamikaze de un solo uso", "Control autónomo total"], "c": 2},
        {"p": "¿Qué cámara usa el Mavic 3 Improved para operaciones nocturnas?",
         "o": ["RGB estándar", "Cámara EO/IR (térmica y visual)", "Infrarroja simple", "Sin capacidad nocturna"], "c": 1},
        {"p": "Antes de usar el Brasko AI en modo semi-autónomo, ¿qué debes hacer?",
         "o": ["Usarlo sin restricciones", "Obtener confirmación del TL", "Solo usarlo de noche", "Reportar al Zeus"], "c": 1},
        {"p": "¿Cuál es el alcance de control aproximado del FPV Crocus?",
         "o": ["200 m", "500 m", "1,5 km", "5 km"], "c": 2},
        {"p": "Contra un IFV blindado, ¿dónde impactas con el FPV para mayor efecto?",
         "o": ["Frontal", "Torreta", "Parte trasera del motor", "Laterales"], "c": 2},
        {"p": "¿Qué debes hacer PRIMERO al detectar posición enemiga con el Mavic 3?",
         "o": ["Atacar inmediatamente", "Reportar MGRS al TL", "Aterrizar el drone", "Grabar y guardar"], "c": 1},
        {"p": "¿Cuánto tiempo de vuelo tiene el Mavic 3 Improved?",
         "o": ["5 min", "10 min", "~20 min", "45 min"], "c": 2},
        {"p": "¿Qué hace el modo de patrulla del Brasko AI FPV?",
         "o": ["Ataca automáticamente todo lo que detecta", "Vuela por waypoints designados", "Solo toma fotos", "Se desactiva solo"], "c": 1},
        {"p": "¿Por qué el estruendo del Crocus puede comprometer la posición?",
         "o": ["No genera ruido", "El impacto alerta al enemigo sobre la ubicación aproximada del operador", "Solo afecta de noche", "El drone silencia el área"], "c": 1},
    ],
    "aviacion": [
        {"p": "¿Cuándo lanza el TL el humo para marcar la LZ?",
         "o": ["Al iniciar la aproximación del helo", "Cuando el piloto dice 'humo en tu posición'", "Al llegar a la LZ siempre", "El copiloto lo lanza"], "c": 1},
        {"p": "¿Qué significa una LZ marcada con humo ROJO?",
         "o": ["Aterriza inmediatamente", "LZ caliente — aborta el aterrizaje", "Zona neutral", "Zona de combustible"], "c": 1},
        {"p": "¿Qué es la línea 7 del 9-Line CAS?",
         "o": ["Posición de tropas amigas", "Descripción del objetivo", "Método de marcado del objetivo", "Elevación"], "c": 2},
        {"p": "¿Qué variante del H-60 es específica para MEDEVAC?",
         "o": ["UH-60M", "HH-60M", "MH-60M", "AH-60"], "c": 1},
        {"p": "¿Para qué sirve el Pylon Manager?",
         "o": ["Gestionar frecuencias", "Configurar cargas de armas antes del despegue", "Piloto automático", "Control de drones"], "c": 1},
        {"p": "¿Tiempo máximo recomendado de touch down en LZ hostil?",
         "o": ["5 segundos", "30 segundos", "2 minutos", "Sin límite"], "c": 1},
        {"p": "¿Cuál es el armamento del AC-130H Spectre?",
         "o": ["Misiles Hellfire", "105mm obús + 40mm Bofors + 25mm GAU-12", "GAU-8 Avenger", "Bombas GBU-12"], "c": 1},
        {"p": "¿Qué radio deben llevar obligatoriamente los pilotos?",
         "o": ["AN/PRC-152 (SR)", "AN/PRC-117F (LR)", "RF-7800S-TR", "Solo Teamspeak"], "c": 1},
        {"p": "¿Cuántos pasajeros transporta el UH-60M en configuración de personal?",
         "o": ["6 PAX", "8 PAX", "11 PAX", "14 PAX"], "c": 2},
        {"p": "En la línea 1 del 9-Line CAS, ¿qué se reporta?",
         "o": ["Número de enemigos", "IP — Punto de inicio del ataque", "Posición de tropas amigas", "Tipo de munición"], "c": 1},
    ],
    "cqb": [
        {"p": "¿Por qué NUNCA debes detenerte en el umbral de una puerta?",
         "o": ["Es la zona de muerte desde el interior", "Porque la puerta puede cerrarse", "Por protocolo estético", "Para cubrirte mejor"], "c": 0},
        {"p": "En un breach explosivo, ¿dónde se posiciona el Breacher?",
         "o": ["Centro del arco", "A un lado de la puerta, fuera del arco", "Frente a la puerta a 2 m", "Detrás del stack"], "c": 1},
        {"p": "¿Cuál es el método de breach más silencioso?",
         "o": ["Carga explosiva", "Ariete (battering ram)", "Palanca (pry bar)", "Patada directa"], "c": 2},
        {"p": "¿Cuántos soldados son el mínimo para limpiar un cuarto correctamente?",
         "o": ["1", "2", "4", "6"], "c": 1},
        {"p": "¿Qué tecla activa el golpe de culata en Improved Melee?",
         "o": ["G", "V", "B", "Ctrl+M"], "c": 1},
        {"p": "¿Qué ventaja tienen las TPNVG sobre las NVG estándar?",
         "o": ["Son idénticas", "Campo visual de ~120° vs ~40° estándar", "Solo funcionan de día", "Son más baratas"], "c": 1},
        {"p": "¿Qué señal manual significa 'Alto — no te muevas'?",
         "o": ["Mano plana hacia adelante", "Puño cerrado", "Dos dedos apuntando a los ojos", "Pulgar arriba"], "c": 1},
        {"p": "¿Cuál es la vocalización de confirmación tras limpiar un cuarto?",
         "o": ["'Rompiendo'", "'Entrada'", "'¡Limpio!'", "'Check'"], "c": 2},
        {"p": "¿Qué tipo de breach usarías para una puerta blindada sin tiempo?",
         "o": ["Palanca", "Carga explosiva", "Ariete", "Ninguno"], "c": 1},
        {"p": "Al entrar a un cuarto, ¿hacia dónde se mueve el primer hombre?",
         "o": ["Se detiene en el umbral", "Cruza al ángulo opuesto a la puerta", "Va al centro", "Se agacha"], "c": 1},
    ],
    "zeus": [
        {"p": "¿Cuál es la responsabilidad PRINCIPAL del Zeus/GM?",
         "o": ["Ganar contra los jugadores", "Crear narrativa para que todos se diviertan", "Usar todos los módulos", "Reportar al Discord"], "c": 1},
        {"p": "¿Cuándo se aplican módulos LAMBS a grupos enemigos?",
         "o": ["En cualquier momento del combate", "Al inicio, antes de que estén en combate", "Solo si los jugadores pierden", "LAMBS es automático"], "c": 1},
        {"p": "¿Cuál es la frecuencia LR reservada para el canal GM?",
         "o": ["50.000 MHz", "30.000 MHz", "88.000 MHz", "100.000 MHz"], "c": 2},
        {"p": "Si el pelotón avanza muy fácilmente, ¿cómo responde el Zeus?",
         "o": ["Spawna enemigos invencibles", "Añade complicaciones narrativas", "Termina la misión", "Reduce la IA"], "c": 1},
        {"p": "¿Qué añade Zeus Enhanced al Zeus vanilla de Arma 3?",
         "o": ["Solo mejora gráfica", "Cientos de módulos extra (spawn, weather, IED, etc.)", "Solo LAMBS", "Solo vehículos"], "c": 1},
        {"p": "¿Qué hace LAMBS Suppression específicamente?",
         "o": ["La IA no dispara", "La IA suprime posiciones donde detecta fuego enemigo", "La IA se retira siempre", "Solo afecta torretas"], "c": 1},
        {"p": "¿Pueden los jugadores contactar al Zeus directamente durante la misión?",
         "o": ["Sí, en cualquier momento", "No, solo el CO puede contactar al Zeus", "Solo en emergencias", "Solo por chat"], "c": 1},
        {"p": "¿Qué debe preparar el Zeus ANTES de la operación?",
         "o": ["Nada, todo improvisado", "Grupos, waypoints de contingencia y briefing assets", "Solo los enemigos del sector 1", "Solo el clima"], "c": 1},
        {"p": "¿Qué hace Crows Zeus Additions?",
         "o": ["Añade armas", "Mejora cámaras de espectador durante la operación", "Crea patrullas", "Controla el clima"], "c": 1},
        {"p": "El pelotón es masacrado sin chance de reacción. ¿Qué hace el Zeus?",
         "o": ["Continúa igual para mantener dificultad", "Reduce la presión para dar oportunidad de reacción", "Termina la misión", "Ignora la situación"], "c": 1},
        {"p": "¿Qué hace LAMBS Danger con la IA enemiga?",
         "o": ["La deshabilita", "La hace cubrir, flanquear y retirarse cuando es superada", "La hace más lenta", "Solo afecta a jefes"], "c": 1},
        {"p": "¿Cuál es el canal del Curso Zeus como prerrequisito para el Curso Comando?",
         "o": ["Es el único prerequisito", "Se requiere además Básico y Médico (mínimo)", "Básico + Médico + CQB (todos requeridos)", "No requiere nada extra"], "c": 2},
    ],
    "comando": [
        {"p": "Como SF, protocolo al contactar centinela sin ser detectado:",
         "o": ["Disparar", "Menú ACE desde atrás → Takedown silencioso", "Granada", "Esperar refuerzos"], "c": 1},
        {"p": "¿Qué NVG usa el operador SF en infiltración nocturna?",
         "o": ["AN/PVS-14 estándar", "TPNVG AN/PSQ-20 panorámico", "Térmica simple", "Sin NVG para sigilo"], "c": 1},
        {"p": "¿Cuántos cursos previos requiere el Curso Comando?",
         "o": ["2 cursos", "3 cursos", "Todos los 6 anteriores", "Solo el Básico"], "c": 2},
        {"p": "En extracción SPIE bajo fuego, ¿rol del médico SF?",
         "o": ["Pilotear", "Continuar tratamiento durante la extracción", "Solo documentar bajas", "No participa en SPIE"], "c": 1},
        {"p": "¿Qué es el SOFLAM AN/PEQ-1?",
         "o": ["Radio especial", "Designador láser para guiar munición inteligente y CAS", "Drone de ataque", "Sistema médico"], "c": 1},
        {"p": "En coordinación multi-elemento, ¿quién coordina todos los activos?",
         "o": ["El Zeus", "El piloto de mayor rango", "El CO o líder con radio LR", "El operador de drones"], "c": 2},
        {"p": "Si la op SF se compromete (detectados), ¿protocolo inmediato?",
         "o": ["Continuar sin cambios", "Contactar CO por LR, evaluar abort/continue, exfil de emergencia", "Rendirse", "Esperar a que pase"], "c": 1},
        {"p": "Al encontrar un IED en la ruta de exfil, primera acción:",
         "o": ["Desactivar solo", "Marcar MGRS, reportar al CO, perímetro y llamar EOD", "Ignorar", "Detonar con fuego"], "c": 1},
        {"p": "¿Qué es el M183 Demolition Charge?",
         "o": ["Granada de humo", "Carga explosiva de demolición para estructuras/HVT", "IED improvisado", "Munición de artillería"], "c": 1},
        {"p": "Un HVT escapa durante la misión. ¿Qué hace el elemento SF?",
         "o": ["Perseguir sin coordinar", "Reportar dirección de fuga en MGRS al CO y esperar órdenes", "Abortar la misión", "Usar drones sin autorización"], "c": 1},
        {"p": "¿Diferencia entre CASEVAC y MEDEVAC en contexto SF?",
         "o": ["Son iguales", "CASEVAC es evacuación táctica en campo, MEDEVAC es evacuación médica formal con aeronave", "MEDEVAC es para civiles", "CASEVAC requiere helo obligatoriamente"], "c": 1},
        {"p": "¿Qué requiere completar para acceder al examen del Curso Comando?",
         "o": ["Solo el Curso Básico", "Básico + Médico", "Los 6 cursos anteriores completos", "Cualquier 3 cursos"], "c": 2},
        {"p": "¿Cuál es el rol del ghillie suit en operaciones SF de reconocimiento?",
         "o": ["Solo decorativo", "Permite infiltración sin detección en terreno natural", "Solo para francotiradores fijos", "Todo el equipo lo usa siempre"], "c": 1},
        {"p": "Al coordinar CAS como líder SF, ¿cuándo marcas el objetivo con el SOFLAM?",
         "o": ["Antes de confirmar con el piloto", "Solo cuando el piloto confirma que está en la pasada", "Al inicio del engagement", "El Zeus lo marca por ti"], "c": 1},
        {"p": "¿Cuántos puntos de honor se ganan al completar el Curso Comando?",
         "o": ["30 puntos", "80 puntos", "100 puntos", "150 puntos"], "c": 3},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _pregunta_embed(tipo: str, idx: int) -> discord.Embed:
    preguntas = EXAMENES[tipo]
    preg = preguntas[idx]
    curso = CURSOS[tipo]
    total = len(preguntas)
    e = discord.Embed(
        title=f"{curso['emoji']} Examen — {curso['nombre']}",
        description=f"**Pregunta {idx+1} de {total}**\n\n{preg['p']}",
        color=curso["color"],
    )
    for i, op in enumerate(preg["o"]):
        e.add_field(name=f"{'ABCD'[i]})", value=op, inline=False)
    e.set_footer(text=f"Necesitas {int(UMBRAL_APROBADO*100)}% para aprobar · {total - idx - 1} preguntas restantes")
    return e


def _resultado_embed(tipo: str, correctas: int, total: int) -> discord.Embed:
    pct = correctas / total
    aprobado = pct >= UMBRAL_APROBADO
    curso = CURSOS[tipo]
    titulo = f"{'✅ APROBADO' if aprobado else '❌ REPROBADO'} — {curso['nombre']}"
    e = discord.Embed(title=titulo, color=0x2E8B57 if aprobado else 0xDC143C)
    e.description = f"**Resultado:** {correctas}/{total} correctas — **{pct*100:.0f}%**\n\n"
    if aprobado:
        e.description += (
            f"¡Felicitaciones, soldado! Has demostrado dominar el **{curso['nombre']}**.\n"
            f"Se te ha asignado el rango **{curso['rol_nombre']}** {curso['emoji']} "
            f"y **+{curso['puntos_recompensa']} puntos** de honor.\n\n"
            f"{curso['loadout']}"
        )
    else:
        e.description += (
            f"Necesitas al menos **{int(UMBRAL_APROBADO*100)}%** para aprobar.\n"
            f"Estudia el material en **#protocolos** y vuelve cuando estés listo.\n\n"
        )
        if CURSOS[tipo]["cooldown_h"] > 0:
            e.description += f"*Podrás intentarlo nuevamente en {CURSOS[tipo]['cooldown_h']} horas.*"
        else:
            e.description += "*Puedes intentarlo cuando quieras.*"
    return e


async def _obtener_o_crear_rol(guild: discord.Guild, nombre: str, color: int) -> discord.Role:
    rol = discord.utils.get(guild.roles, name=nombre)
    if not rol:
        rol = await guild.create_role(name=nombre, color=discord.Color(color), reason="Rol de curso creado automáticamente")
    return rol


def _completados_usuario(uid: str) -> list:
    return cargar("cursos.json").get("usuarios", {}).get(uid, {}).get("completados", [])


async def _bloquear_si_sin_basico(interaction: discord.Interaction, tipo: str) -> bool:
    """Devuelve True si el acceso está BLOQUEADO (sin requisitos). Envía el mensaje de error."""
    if tipo == "basico":
        return False  # básico siempre accesible
    uid = str(interaction.user.id)
    completados = _completados_usuario(uid)
    if "basico" not in completados:
        e = discord.Embed(title="🔒 Contenido bloqueado", color=0x8B0000)
        e.description = (
            "Para acceder al contenido de cursos avanzados primero debes aprobar el "
            "**Curso Básico — Operación Supervivencia**.\n\n"
            "**¿Cómo desbloquearlo?**\n"
            "1. Ve a **#protocolos** y estudia los Bloques 1–4\n"
            "2. Pulsa **🎯 Rendir Examen Básico** al final del canal\n"
            "3. Obtén el rol **Soldado Básico** y vuelve aquí\n\n"
            "> El conocimiento no se regala — se gana. Demuestra que mereces estar aquí."
        )
        e.set_footer(text="Curso Básico — Operación Supervivencia · #protocolos")
        await interaction.response.send_message(embed=e, ephemeral=True)
        return True
    # También verifica prerrequisitos propios del curso para info/práctica
    for req in CURSOS[tipo]["requisitos"]:
        if req != "basico" and req not in completados:
            req_nombre = CURSOS[req]["nombre"]
            e = discord.Embed(title="🔒 Prerrequisito faltante", color=0xFF8C00)
            e.description = (
                f"Para estudiar este curso también necesitas completar:\n"
                f"**{req_nombre}**\n\n"
                "Sigue la ruta de formación en orden y vuelve cuando tengas los requisitos."
            )
            await interaction.response.send_message(embed=e, ephemeral=True)
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: GUÍA DE APRENDIZAJE CIENTÍFICO (ephemeral, no persistente)
# ─────────────────────────────────────────────────────────────────────────────
class GuiaAprendizajeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🧠 La Curva del Olvido", style=discord.ButtonStyle.secondary, row=0)
    async def curva_olvido(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🧠 La Curva del Olvido — Hermann Ebbinghaus (1885)", color=0x5865F2)
        e.description = (
            "**El descubrimiento más importante de la memoria humana:**\n"
            "Sin repasar, olvidamos el **50% en 24 horas**, el **70% en una semana** "
            "y el **90% en un mes**. Esto es biológico — no es falta de inteligencia.\n\n"
            "**La buena noticia:** cada vez que repasas, la curva se aplana.\n"
            "Después de 4–5 repasos, la información pasa a **memoria a largo plazo**.\n\n"
            "**Cómo aplicarlo en el clan:**\n"
            "• Día 1: estudia el bloque en #protocolos\n"
            "• Día 2: relee solo los títulos y trata de recordar el detalle\n"
            "• Día 4: practica en el servidor de juego lo que estudiaste\n"
            "• Día 7: usa los botones del examen como práctica (no solo al final)\n"
            "• Día 14: si hay operación, ya está consolidado\n\n"
            "**Por qué fracasan los que memorizan la noche anterior:**\n"
            "> Estudiar 3 horas el día antes del examen da una retención de ~30% al día siguiente "
            "y ~5% a la semana. Estudiar 20 minutos al día durante 5 días da 80% a la semana. "
            "La ciencia es clara: el tiempo **entre sesiones** importa más que la duración de cada una."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔄 Repetición Espaciada", style=discord.ButtonStyle.secondary, row=0)
    async def repeticion_espaciada(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🔄 Repetición Espaciada — El Sistema Más Poderoso", color=0x5865F2)
        e.description = (
            "**Qué es:** distribuir el estudio en intervalos que crecen progresivamente.\n"
            "Es el método respaldado por más evidencia científica para memorización a largo plazo "
            "*(Cepeda et al., 2006 — revisión de 317 estudios con 14.000 participantes)*.\n\n"
            "**Cronograma óptimo para este clan:**\n"
            "```\nDía 1    → Primera lectura del bloque (protocolos)\nDía 2    → Repaso mental: ¿qué recuerdas sin leer?\nDía 4    → Prueba el examen aunque no estés listo\nDía 7    → Practica en juego el procedimiento\nDía 14   → Revisa una vez más antes de cualquier operación\n```\n\n"
            "**Aplicado a procedimientos médicos:**\n"
            "El KAT Medical tiene ~20 procedimientos distintos. "
            "Si estudias 3 por día con repaso al siguiente, en **10 días** los tienes todos. "
            "Si tratas de aprenderlos todos en una sesión, los olvidarás en 48 horas.\n\n"
            "**Truco práctico:** Usa las frases clave de #protocolos como *flashcards mentales*. "
            "Pregúntate: *'¿Cuándo uso Adenosina y cuándo Atropine?'* antes de mirar la respuesta. "
            "Ese esfuerzo de recuperación es lo que construye el recuerdo."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="📝 Recuperación Activa", style=discord.ButtonStyle.secondary, row=0)
    async def active_recall(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="📝 Recuperación Activa — El Efecto Test", color=0x5865F2)
        e.description = (
            "**Descubrimiento clave** *(Roediger & Karpicke, 2006)*:\n"
            "Intentar recordar información **fortalece más el recuerdo** que volver a leerla.\n"
            "Estudiantes que hacían tests después de estudiar recordaron un **50% más** "
            "al cabo de una semana que los que solo releyeron.\n\n"
            "**Cómo aplicarlo:**\n"
            "1. Lee el bloque de protocolos **una vez**\n"
            "2. Cierra el bloque\n"
            "3. Escribe o di en voz alta todo lo que recuerdas\n"
            "4. Compara con lo que dice el bloque\n"
            "5. Solo repasa lo que **no** pudiste recordar\n\n"
            "**En este clan:**\n"
            "• Usa los botones de examen como herramienta de estudio, no solo de evaluación\n"
            "• Explícale un procedimiento a un compañero sin mirar el texto — si no puedes "
            "explicarlo, no lo has aprendido *(Richard Feynman)*\n"
            "• En el servidor de juego: haz el procedimiento de memoria, sin consultar guía\n\n"
            "**El principio de Feynman:**\n"
            "> *'Si no puedes explicarlo de forma simple, no lo entiendes suficientemente bien.'* "
            "Aplica esto a cada protocolo: triage, 9-Line, breach — explícaselo a alguien sin leerlo."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🎯 Práctica Deliberada", style=discord.ButtonStyle.secondary, row=1)
    async def practica_deliberada(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🎯 Práctica Deliberada — Calidad sobre Cantidad", color=0x5865F2)
        e.description = (
            "**Anders Ericsson** — el psicólogo detrás del mito de las '10.000 horas' — "
            "demostró que no son las horas lo que importa, sino **cómo** se practican.\n\n"
            "**Práctica normal vs. deliberada:**\n"
            "• Normal: volar el drone como siempre, sin desafío → no mejoras\n"
            "• Deliberada: practicar el punto débil específico con retroalimentación inmediata → mejoras\n\n"
            "**Cómo practicar deliberadamente en Arma 3:**\n"
            "1. **Identifica el punto débil** — ¿Qué parte del procedimiento falla?\n"
            "2. **Diseña el ejercicio mínimo** — un escenario que aísle esa habilidad\n"
            "3. **Ejecuta con atención máxima** — sin distracciones, concentración total\n"
            "4. **Obtén feedback inmediato** — un instructor, compañero, o el propio resultado\n"
            "5. **Repite hasta automatizar** — el objetivo es que no tengas que pensar\n\n"
            "**En combate no tienes tiempo de pensar — solo reaccionar.**\n"
            "El tourniquet en una hemorragia masiva debe aplicarse en <10 segundos "
            "o el paciente puede perder el conocimiento. "
            "Eso solo se logra con práctica deliberada hasta que es automático.\n\n"
            "> *'Bajo presión no subes a tu nivel de expectativas, caes a tu nivel de entrenamiento.'* — Archilochus"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="💪 Disciplina Militar", style=discord.ButtonStyle.danger, row=1)
    async def disciplina(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="💪 Disciplina Militar — Por qué lo Exigimos", color=0x8B0000)
        e.description = (
            "**La disciplina no es castigo — es la base de la supervivencia.**\n\n"
            "**¿Por qué el clan exige pasar los cursos en orden?**\n"
            "En el campo de batalla real (y en Arma 3), un operador sin formación "
            "no solo se muere él — compromete a todo el equipo. Un médico sin curso "
            "que aplica morfina a un paciente con SpO2 baja lo mata. "
            "Un piloto sin certificación que aterriza en zona caliente pierde el helo y 11 soldados.\n\n"
            "**El estándar mínimo:**\n"
            "• Llegar puntual a operaciones y entrenamientos\n"
            "• Estudiar los protocolos ANTES de la operación, no durante\n"
            "• Reportar al TL si no dominas un procedimiento — el silencio mata\n"
            "• Respetar la jerarquía: el TL manda en el campo, el Zeus manda la narrativa\n"
            "• Si fallas un examen: vuelves a estudiar, no protestar\n\n"
            "**La Regla de los 5 Segundos** *(Mel Robbins)*:\n"
            "Cuando no tienes ganas de estudiar, cuenta 5-4-3-2-1 y haz lo que tienes que hacer. "
            "La motivación es emoción — viene y va. La disciplina es una decisión.\n\n"
            "**Consecuencias de no respetar el sistema:**\n"
            "> Las infracciones en canales restringidos restan puntos. Los puntos negativos "
            "generan sanciones automáticas. Los que no completan el Curso Básico no participan "
            "en operaciones en roles avanzados. Las Fuerzas Especiales no son un título — "
            "son el resultado de trabajo real."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="😴 Sueño y Memoria", style=discord.ButtonStyle.secondary, row=1)
    async def sueno(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="😴 Sueño y Consolidación de Memoria — Neurociencia", color=0x5865F2)
        e.description = (
            "**Lo que la neurociencia dice sobre el sueño y el aprendizaje:**\n\n"
            "Durante el sueño, especialmente en fase **REM**, el cerebro:\n"
            "• Consolida lo que aprendiste durante el día\n"
            "• Transfiere información de memoria a corto plazo → largo plazo\n"
            "• Elimina conexiones neuronales irrelevantes y fortalece las útiles\n"
            "• Procesa información motora y procedimental (como ejecutar procedimientos)\n\n"
            "**Dato clave** *(Walker, 2017 — Why We Sleep)*:\n"
            "Dormir menos de 6 horas reduce la capacidad de aprendizaje en **40%**. "
            "Después de 17 horas sin dormir, tu rendimiento cognitivo equivale a "
            "un nivel de alcohol en sangre de 0.05%.\n\n"
            "**Para maximizar la retención:**\n"
            "1. Estudia el material **1–2 horas antes de dormir**\n"
            "2. Duerme al menos **7–8 horas** después\n"
            "3. No estudies mientras juegas al mismo tiempo\n"
            "4. Una siesta de **20 minutos** después de estudiar mejora la retención un 30%\n\n"
            "**Aplicado a las operaciones nocturnas:**\n"
            "> Si juegas de noche hasta las 3am con privación de sueño crónica, "
            "tu tiempo de reacción, toma de decisiones y memoria de procedimientos están "
            "seriamente comprometidos. El descanso es parte del entrenamiento."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  MODAL + VIEW: SISTEMA DE DUDAS
# ─────────────────────────────────────────────────────────────────────────────
class DudaModal(discord.ui.Modal, title="🤔 Plantear Duda al Instructor"):
    texto = discord.ui.TextInput(
        label="¿Cuál es tu duda?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe tu duda con el mayor detalle posible...",
        min_length=10,
        max_length=500,
    )

    def __init__(self, tipo: str):
        super().__init__()
        self.tipo = tipo

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        curso = CURSOS[self.tipo]

        # Buscar instructor del curso activo
        cursos_data = cargar("cursos.json")
        activo = cursos_data.get("curso_activo", {})
        instructor_id = activo.get("autor_id") if activo.get("tipo") == self.tipo else None

        # Categoría donde se crea el canal temporal (misma que #entrenamientos)
        canal_ref = guild.get_channel(CANAL_ENTRENAMIENTOS_ID)
        categoria = canal_ref.category if canal_ref else None

        nombre_seguro = "".join(c for c in interaction.user.display_name.lower()
                                if c.isalnum() or c == "-")[:20]
        nombre_canal = f"duda-{nombre_seguro}-{self.tipo}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                   manage_channels=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if instructor_id:
            m = guild.get_member(int(instructor_id))
            if m:
                overwrites[m] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        for rname in ["Entrenadores", "Administradores", "Coronel", "Cabo Primero"]:
            r = discord.utils.get(guild.roles, name=rname)
            if r:
                overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            canal_duda = await guild.create_text_channel(
                nombre_canal, category=categoria, overwrites=overwrites,
                reason=f"Duda {curso['nombre']} — {interaction.user.display_name}",
            )
        except Exception as exc:
            return await interaction.followup.send(f"❌ No se pudo crear el canal: {exc}",
                                                   ephemeral=True)

        canal_id_str = str(canal_duda.id)
        cursos_data.setdefault("dudas", {})[canal_id_str] = {
            "tipo":          self.tipo,
            "estudiante_id": str(interaction.user.id),
            "instructor_id": instructor_id,
            "puntos":        PUNTOS_DUDA_RESUELTA,
        }
        guardar("cursos.json", cursos_data)

        e = discord.Embed(
            title=f"🤔 Duda — {curso['emoji']} {curso['nombre']}",
            color=curso["color"],
            timestamp=datetime.datetime.now(),
        )
        e.description = (
            f"**Estudiante:** {interaction.user.mention}\n"
            f"**Curso:** {curso['nombre']}\n\n"
            f"**Pregunta:**\n> {self.texto.value}"
        )
        e.set_footer(text="Instructor: responde aquí y presiona el botón verde cuando esté resuelto.")

        if instructor_id:
            mencion = f"<@{instructor_id}>"
        else:
            partes = []
            for rname in ["Entrenadores", "Administradores"]:
                r = discord.utils.get(guild.roles, name=rname)
                if r:
                    partes.append(r.mention)
            mencion = " ".join(partes) if partes else "@Mando"

        await canal_duda.send(
            content=f"{mencion} — nueva duda de {interaction.user.mention}",
            embed=e,
            view=DudaResueltaView(),
        )
        await interaction.followup.send(
            f"✅ Duda enviada. Canal creado: {canal_duda.mention}",
            ephemeral=True,
        )


class DudaResueltaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Duda Resuelta — Cerrar Canal", style=discord.ButtonStyle.success,
                       custom_id="gl_duda_resuelta")
    async def resolver(self, interaction: discord.Interaction, _: discord.ui.Button):
        cursos_data = cargar("cursos.json")
        duda_info = cursos_data.get("dudas", {}).get(str(interaction.channel.id), {})

        es_instructor = str(interaction.user.id) == duda_info.get("instructor_id")
        if not es_instructor and not es_mando(interaction):
            return await interaction.response.send_message(
                "❌ Solo el instructor o el mando puede cerrar esta duda.", ephemeral=True
            )

        await interaction.response.defer()

        instructor_id  = duda_info.get("instructor_id")
        tipo           = duda_info.get("tipo", "")
        estudiante_id  = duda_info.get("estudiante_id")
        puntos         = duda_info.get("puntos", PUNTOS_DUDA_RESUELTA)

        if instructor_id:
            curso_nombre = CURSOS.get(tipo, {}).get("nombre", tipo)
            sumar_puntos(instructor_id, puntos, f"Resolvió duda — {curso_nombre}")

            canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
            if canal_mando:
                e_m = discord.Embed(title="✅ Duda Resuelta", color=0x2E8B57,
                                    timestamp=datetime.datetime.now())
                e_m.description = (
                    f"**Instructor:** <@{instructor_id}>\n"
                    f"**Estudiante:** <@{estudiante_id}>\n"
                    f"**Curso:** {curso_nombre}\n"
                    f"**Recompensa:** +{puntos} pts al instructor\n"
                    f"*Cerrado por {interaction.user.mention}*"
                )
                await canal_mando.send(embed=e_m)

        cursos_data.get("dudas", {}).pop(str(interaction.channel.id), None)
        guardar("cursos.json", cursos_data)

        e_cierre = discord.Embed(title="✅ Duda Resuelta", color=0x2E8B57)
        e_cierre.description = (
            f"Duda cerrada por {interaction.user.mention}.\n"
            + (f"El instructor recibió **+{puntos} puntos** de honor.\n" if instructor_id else "")
            + "\n**Este canal se eliminará en 10 segundos.**"
        )
        await interaction.followup.send(embed=e_cierre)
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete(reason="Duda resuelta")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: EXAMEN (dinámica, ephemeral)
# ─────────────────────────────────────────────────────────────────────────────
class ExamenView(discord.ui.View):
    def __init__(self, cog, tipo: str, idx: int, respuestas: list):
        super().__init__(timeout=300)
        self.cog = cog
        self.tipo = tipo
        self.idx = idx
        self.respuestas = respuestas
        preg = EXAMENES[tipo][idx]
        for i, op in enumerate(preg["o"]):
            btn = discord.ui.Button(
                label=f"{'ABCD'[i]}) {op[:72]}",
                style=discord.ButtonStyle.secondary,
                row=i // 2,
            )
            btn.callback = self._make_cb(i)
            self.add_item(btn)

    def _make_cb(self, opcion_idx: int):
        async def cb(interaction: discord.Interaction):
            nuevas = self.respuestas + [opcion_idx]
            siguiente = self.idx + 1
            if siguiente >= len(EXAMENES[self.tipo]):
                await self.cog._finalizar_examen(interaction, self.tipo, nuevas)
            else:
                view = ExamenView(self.cog, self.tipo, siguiente, nuevas)
                embed = _pregunta_embed(self.tipo, siguiente)
                await interaction.response.edit_message(embed=embed, view=view)
        return cb


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: CURSO BÁSICO — siempre visible en #protocolos
# ─────────────────────────────────────────────────────────────────────────────
class CursoBasicoPublicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎓 ¿Qué es el Curso Básico?", style=discord.ButtonStyle.success, custom_id="gl_cb_info", row=0)
    async def info(self, interaction: discord.Interaction, _: discord.ui.Button):
        curso = CURSOS["basico"]
        e = discord.Embed(title=f"{curso['emoji']} {curso['nombre']}", color=curso["color"])
        e.description = (
            f"{curso['descripcion']}\n\n"
            f"**Código:** `{curso['codigo']}`\n"
            f"**Rol al aprobar:** {curso['rol_nombre']}\n"
            f"**Recompensa:** +{curso['puntos_recompensa']} puntos de honor\n\n"
            f"**¿Qué cubre?**\n"
            "• Bloque 1 — ACE3 Fundamentos\n"
            "• Bloque 2 — TFAR Comunicaciones\n"
            "• Bloque 3 — Navegación MGRS\n"
            "• Bloque 4 — KAT Primeros Auxilios\n\n"
            f"**Mínimo para aprobar:** {int(UMBRAL_APROBADO*100)}% del examen\n\n"
            f"{curso['practica']}"
        )
        e.set_footer(text="Estudia los Bloques 1–4 en #protocolos antes del examen.")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="📦 Loadout si apruebo", style=discord.ButtonStyle.secondary, custom_id="gl_cb_loadout", row=0)
    async def loadout(self, interaction: discord.Interaction, _: discord.ui.Button):
        curso = CURSOS["basico"]
        e = discord.Embed(title=f"📦 Loadout — {curso['rol_nombre']}", color=curso["color"])
        e.description = curso["loadout"]
        e.set_footer(text="Este equipo quedará autorizado para ti permanentemente al aprobar.")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="📋 Cursos disponibles", style=discord.ButtonStyle.secondary, custom_id="gl_cb_lista", row=0)
    async def lista(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🎓 Cursos del Clan — Ruta de Formación", color=COLOR_MILITAR)
        lineas = []
        for tipo, c in CURSOS.items():
            reqs = " · ".join(CURSOS[r]["rol_nombre"] for r in c["requisitos"]) if c["requisitos"] else "Ninguno"
            lineas.append(f"**{c['emoji']} {c['nombre']}** `{c['codigo']}`\nRequisito: {reqs}\nRol: {c['rol_nombre']} (+{c['puntos_recompensa']} pts)\n")
        e.description = "\n".join(lineas)
        e.set_footer(text="El Curso Comando requiere TODOS los cursos anteriores.")
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="📚 Guía de Aprendizaje", style=discord.ButtonStyle.primary, custom_id="gl_cb_guia", row=1)
    async def guia(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="📚 Guía de Aprendizaje Científico", color=0x5865F2)
        e.description = (
            "Aprende a estudiar con la eficacia de los mejores operadores del mundo.\n"
            "Esta guía aplica **neurociencia y psicología cognitiva** al entrenamiento táctico.\n\n"
            "🧠 **La Curva del Olvido** — por qué olvidamos y cómo evitarlo\n"
            "🔄 **Repetición Espaciada** — el sistema con mayor evidencia científica\n"
            "📝 **Recuperación Activa** — estudiar haciendo tests, no releyendo\n"
            "🎯 **Práctica Deliberada** — calidad sobre cantidad de entrenamiento\n"
            "💪 **Disciplina Militar** — por qué exigimos el orden de los cursos\n"
            "😴 **Sueño y Memoria** — la neurociencia detrás del descanso"
        )
        e.set_footer(text="Selecciona un tema para ver la guía completa.")
        await interaction.response.send_message(embed=e, view=GuiaAprendizajeView(), ephemeral=True)

    @discord.ui.button(label="🎯 Rendir Examen Básico", style=discord.ButtonStyle.danger, custom_id="gl_cb_examen", row=1)
    async def examen(self, interaction: discord.Interaction, _: discord.ui.Button):
        await _iniciar_examen_check(interaction, "basico")

    @discord.ui.button(label="🤔 Tengo una Duda", style=discord.ButtonStyle.secondary, custom_id="gl_cb_duda", row=2)
    async def duda(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(DudaModal("basico"))


# ─────────────────────────────────────────────────────────────────────────────
#  CONTENIDO PROFUNDO — CURSO MÉDICO (sub-view ephemeral)
# ─────────────────────────────────────────────────────────────────────────────
class MedicoContentView(discord.ui.View):
    """Sub-panel de estudio del Curso Médico — no persistente, uso ephemeral."""

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🏷️ Triage de Campo", style=discord.ButtonStyle.secondary, row=0)
    async def triage(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚕️ Triage de Campo — Decisiones bajo Fuego", color=0xDC143C)
        e.description = (
            "El triage no es salvar a todos — es salvar a los que SÍ se pueden salvar.\n\n"
            "**Categorías y criterio en KAT**\n"
            "**🔴 T1 Urgente** · INMEDIATA → Inconsciente + pulso · Hemorragia masiva activa · SpO2 <90%\n"
            "**🟡 T2 Prioritario** · DEMORADO → Consciente pero sangrando · Fractura con circulación comprometida\n"
            "**🟢 T3 Rutina** · MÍNIMO → Herida leve · Consciente · Sin hemorragia activa · Puede esperar\n"
            "**⚫ T4 Expectante** · SIN RECURSOS → Sin pulso · Sin respiración · Sin tiempo/equipo para salvar\n\n"
            "**Escenario A — Dos bajas simultáneas**\n"
            "```\nBaja 1: Inconsciente, pulso débil, hemorragia pierna\nBaja 2: Consciente, grita de dolor, herida de bala en hombro\n\nDecisión correcta:\n→ Baja 1 = T1: Tourniquet inmediato + Epinefrina\n→ Baja 2 = T2: QuikClot hombro, espera mientras atiendes T1\n```\n\n"
            "**Escenario B — Sin pulso**\n"
            "```\nBaja: Sin pulso, sin respiración, 3 minutos sin atención\n\nDecisión correcta:\n→ T4: No gastes equipo ni tiempo si hay otras bajas T1 vivas\n→ Solo intenta CPR si NO hay otros pacientes críticos\n```\n\n"
            "**Error más común:** Atender al que más grita primero. El que grita tiene energía — el silencioso inconsciente se muere."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="💊 Farmacología de Combate", style=discord.ButtonStyle.secondary, row=0)
    async def farma(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚕️ Farmacología — Medicamentos en KAT Medical", color=0xDC143C)
        e.description = (
            "**Guía completa de medicamentos del médico de campo**\n\n"
            "**Morphine (Analgésico)**\n"
            "• Uso: dolor severo (heridas de bala, fracturas múltiples)\n"
            "• Efecto: reduce el dolor y el estado de agitación\n"
            "• Riesgo: **sobredosis** → FC baja + SpO2 cae → ANTÍDOTO: Naloxone IV\n"
            "• Máximo: 1–2 unidades seguidas. Espera antes de repetir.\n\n"
            "**Epinefrina (Adrenalina)**\n"
            "• Uso: paciente inconsciente con pulso débil o paro\n"
            "• Efecto: estimula el corazón, sube FC\n"
            "• Riesgo: si el corazón ya va rápido puede causar fibrilación\n"
            "• Monitorea FC después de aplicar\n\n"
            "**Adenosina IV**\n"
            "• Uso: fibrilación ventricular (FC >150 irregular)\n"
            "• Efecto: reinicia el ritmo cardíaco\n"
            "• Solo médico. No usar si FC es normal.\n\n"
            "**Atropine IV**\n"
            "• Uso: bradicardia severa (FC <40 lpm)\n"
            "• Efecto: sube la FC\n"
            "• No confundir con Adenosina — una sube, la otra baja la FC\n\n"
            "**Naloxone IV**\n"
            "• Uso: sobredosis de morfina\n"
            "• Señales: SpO2 cayendo + paciente sedado + FC bajando\n"
            "• Antídoto inmediato — administrar antes de que SpO2 baje de 85%\n\n"
            "**IV Saline (500 / 1000 ml)**\n"
            "• Uso: volumen de sangre bajo (<4000 ml)\n"
            "• Efecto: repone volumen pero NO repone glóbulos rojos\n"
            "• 1000 ml si el paciente está crítico (<3000 ml sangre)\n\n"
            "**Blood O- (Sangre universal)**\n"
            "• Uso: pérdida masiva de sangre (<2500 ml)\n"
            "• Efecto: repone sangre real — mejor que Saline en trauma severo\n"
            "• Recurso escaso — úsalo solo en T1 crítico"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🩺 Procedimientos Avanzados", style=discord.ButtonStyle.secondary, row=0)
    async def procedimientos(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚕️ Procedimientos Avanzados — Solo Médico", color=0xDC143C)
        e.description = (
            "**Chest Seal Oclusivo (herida de tórax)**\n"
            "• Cuándo: herida en pecho con sonido de succión al respirar\n"
            "• Cómo: Menú ACE → *Aplicar Chest Seal* sobre el torso\n"
            "• Si no se aplica: neumotórax → SpO2 cae a pesar de todo lo demás\n"
            "• El Chest Seal NO requiere bandage previo en esa zona\n\n"
            "**Intubación (vía aérea)**\n"
            "• Cuándo: paciente inconsciente con SpO2 en caída libre (<85%)\n"
            "• Efecto: abre la vía aérea mecánicamente\n"
            "• Requiere: Surgical Kit en el inventario\n"
            "• Menú ACE → *Intubar paciente*\n\n"
            "**CPR (Reanimación cardiopulmonar)**\n"
            "• Cuándo: sin pulso + sin otras bajas T1 que atender\n"
            "• Cómo: Menú ACE → *RCP / Compresiones*\n"
            "• Efectividad: ~30% de éxito en KAT — combínalo con Epinefrina IV\n"
            "• Continúa hasta recuperar pulso o 3 ciclos fallidos\n\n"
            "**Splint (fractura)**\n"
            "• Cuándo: extremidad con fractura confirmada (el juego lo indica)\n"
            "• Aplica DESPUÉS de detener la hemorragia con vendaje\n"
            "• Sin splint: el paciente cojea y no puede correr — carga táctica\n\n"
            "**Secuencia de atención T1 completa:**\n"
            "```\n1. Arrastrar a cubierto (ACE → Arrastrar)\n2. Tourniquet si hemorragia en extremidad\n3. QuikClot / Elastic Bandage en heridas\n4. Chest Seal si herida de tórax\n5. IV Saline/Blood si sangre baja\n6. Epinefrina si inconsciente\n7. Morphine si dolor severo (monitorea SpO2)\n8. Monitorear constantes hasta estabilizar\n```"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="📊 Monitoreo de Constantes", style=discord.ButtonStyle.secondary, row=1)
    async def constantes(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚕️ Monitoreo de Constantes Vitales — KAT", color=0xDC143C)
        e.description = (
            "**Abrir monitor:** Menú ACE sobre el paciente → *Monitorear*\n\n"
            "**Frecuencia Cardíaca (FC)**\n"
            "**>150 irregular** · Fibrilación → Adenosina IV\n"
            "**120–150** · Taquicardia → Revisar hemorragias activas\n"
            "**60–100** · ✅ Normal → Mantener\n"
            "**40–60** · Bradicardia leve → Vigilar\n"
            "**<40** · Bradicardia severa → Atropine IV\n"
            "**0** · Paro cardíaco → CPR + Epinefrina\n\n"
            "**SpO2 (Saturación de oxígeno)**\n"
            "**>95%** · ✅ Normal → —\n"
            "**90–95%** · Hipoxia leve → Revisar vía aérea\n"
            "**85–90%** · Hipoxia moderada → Intubar\n"
            "**<85%** · Hipoxia severa → Intubar URGENTE + O2\n\n"
            "**Volumen de Sangre**\n"
            "**5 000–6 000 ml** · ✅ Normal → —\n"
            "**3 500–5 000 ml** · Pérdida leve → IV Saline 500\n"
            "**2 500–3 500 ml** · Pérdida severa → IV Saline 1000\n"
            "**<2 500 ml** · Crítico → Sangre O- prioritaria\n\n"
            "**Regla de 3 simultáneos:**\n"
            "> Si FC baja + SpO2 baja + sangre baja al mismo tiempo → shock hemorrágico. "
            "Tourniquet primero, Blood O- segundo, Epinefrina si inconsciente."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🚁 CASEVAC bajo Fuego", style=discord.ButtonStyle.secondary, row=1)
    async def casevac(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚕️ CASEVAC bajo Fuego — Protocolo Completo", color=0xDC143C)
        e.description = (
            "**CASEVAC** = Casualty Evacuation. Tu trabajo no termina con el vendaje.\n\n"
            "**Paso 1 — Estabilizar en el campo**\n"
            "• Hemorragias controladas antes de mover\n"
            "• Paciente T1 mínimo en T2 antes de solicitar extracción\n"
            "• Si hay fuego activo: arrastra a cubierto PRIMERO\n\n"
            "**Paso 2 — Solicitar CASEVAC por radio LR**\n"
            "```\n\"[Callsign helo], aquí [TL], solicito CASEVAC:\nCuadrícula: [MGRS 6 dígitos]\nBajas: [N] T1, [N] T2\nZona: [HOT/COLD]\nHumo: [color — aún no lo lances]\nCambio.\"\n```\n\n"
            "**Paso 3 — Preparar LZ**\n"
            "• Área limpia mínimo 30×30 m\n"
            "• Dos soldados en seguridad 360°\n"
            "• Pacientes en camilla o cargados al borde de la LZ\n\n"
            "**Paso 4 — Marcado con humo**\n"
            "• Espera que el piloto diga: *'Identifica tu humo'*\n"
            "• Solo ENTONCES lanzas el humo\n"
            "• Piloto confirma color: *'Identifico verde — aterrizando'*\n\n"
            "**Paso 5 — Embarque**\n"
            "• Pacientes primero, armas y equipo después\n"
            "• Médico sube con el paciente — continúa tratamiento en vuelo\n"
            "• Tiempo máximo en tierra: 30 segundos en LZ caliente\n\n"
            "**Hot LZ — extracción de emergencia:**\n"
            "> Si el piloto no puede aterrizar: SPIE Rig o Fast Rope. "
            "El médico queda en tierra hasta que la zona sea segura. Coordina con CO."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="❌ Errores Críticos del Médico", style=discord.ButtonStyle.danger, row=1)
    async def errores(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚕️ Errores Críticos — Lo que NUNCA debes hacer", color=0x8B0000)
        e.description = (
            "Estos errores matan pacientes. Memorízalos.\n\n"
            "**❌ Atender al que más grita primero**\n"
            "El que grita tiene energía. El que está silencioso e inconsciente es el T1.\n\n"
            "**❌ Dar morfina sin revisar SpO2 y FC primero**\n"
            "Si el paciente ya tiene SpO2 baja, la morfina puede pararle la respiración.\n\n"
            "**❌ Aplicar Adenosina cuando la FC es baja**\n"
            "Adenosina = para la fibrilación (FC alta irregular). Si FC es baja y das Adenosina: paro.\n\n"
            "**❌ Olvidar el Chest Seal en heridas de tórax**\n"
            "El paciente puede estar vendado, con sangre estable y SpO2 bajando igual. La causa: herida de tórax sin sellar.\n\n"
            "**❌ Mover al paciente antes de controlar la hemorragia**\n"
            "Un paciente con hemorragia masiva que corres 50 metros = muerto antes de llegar al médico.\n\n"
            "**❌ No monitorear después de estabilizar**\n"
            "El paciente estaba bien y de repente colapsa. Revisa FC y sangre cada 30 segundos en pacientes críticos.\n\n"
            "**❌ Usar toda la sangre O- en el primer T1**\n"
            "Si hay 3 bajas críticas, gestiona el recurso. Saline primero, sangre para el peor caso.\n\n"
            "**❌ Exponerte para tratar**\n"
            "Un médico muerto no trata a nadie. Arrastra a cubierto SIEMPRE antes de iniciar tratamiento."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: CURSO AVANZADO — publicado en #entrenamientos cuando hay curso activo
# ─────────────────────────────────────────────────────────────────────────────
class CursoActivoView(discord.ui.View):
    def __init__(self, tipo: str):
        super().__init__(timeout=None)
        self.tipo = tipo
        curso = CURSOS[tipo]

        btn_info = discord.ui.Button(label="📖 Contenido del Curso", style=discord.ButtonStyle.primary,
                                     custom_id=f"gl_ca_{tipo}_info", row=0)
        btn_info.callback = self._info_cb
        self.add_item(btn_info)

        btn_prac = discord.ui.Button(label="🏋️ Ejercicio Práctico", style=discord.ButtonStyle.secondary,
                                     custom_id=f"gl_ca_{tipo}_prac", row=0)
        btn_prac.callback = self._prac_cb
        self.add_item(btn_prac)

        btn_load = discord.ui.Button(label="📦 Loadout al Aprobar", style=discord.ButtonStyle.secondary,
                                     custom_id=f"gl_ca_{tipo}_load", row=0)
        btn_load.callback = self._load_cb
        self.add_item(btn_load)

        btn_exam = discord.ui.Button(label=f"🎯 Rendir Examen", style=discord.ButtonStyle.danger,
                                     custom_id=f"gl_ca_{tipo}_exam", row=1)
        btn_exam.callback = self._exam_cb
        self.add_item(btn_exam)

        btn_mis = discord.ui.Button(label="🪖 Mis Cursos Completados", style=discord.ButtonStyle.secondary,
                                    custom_id=f"gl_ca_{tipo}_mis", row=1)
        btn_mis.callback = self._mis_cb
        self.add_item(btn_mis)

        btn_duda = discord.ui.Button(label="🤔 Tengo una Duda", style=discord.ButtonStyle.secondary,
                                     custom_id=f"gl_ca_{tipo}_duda", row=2)
        btn_duda.callback = self._duda_cb
        self.add_item(btn_duda)

        btn_guia = discord.ui.Button(label="📚 Guía de Aprendizaje", style=discord.ButtonStyle.primary,
                                     custom_id=f"gl_ca_{tipo}_guia", row=2)
        btn_guia.callback = self._guia_cb
        self.add_item(btn_guia)

    async def _info_cb(self, interaction: discord.Interaction):
        if await _bloquear_si_sin_basico(interaction, self.tipo):
            return
        tipo = self.tipo
        curso = CURSOS[tipo]

        # Curso médico: sub-panel interactivo con contenido profundo
        if tipo == "medico":
            e = discord.Embed(title="⚕️ Curso Médico — Material de Estudio", color=curso["color"])
            e.description = (
                "Selecciona el tema que quieres estudiar. "
                "Cada sección contiene guías detalladas, tablas de referencia y escenarios reales.\n\n"
                "🏷️ **Triage de Campo** — categorías y escenarios de decisión\n"
                "💊 **Farmacología** — todos los medicamentos, cuándo y cómo usarlos\n"
                "🩺 **Procedimientos Avanzados** — chest seal, intubación, CPR, secuencia completa\n"
                "📊 **Monitoreo de Constantes** — tablas de FC, SpO2 y volumen de sangre\n"
                "🚁 **CASEVAC bajo Fuego** — protocolo completo de evacuación médica\n"
                "❌ **Errores Críticos** — lo que NUNCA debes hacer como médico"
            )
            e.set_footer(text="Después de estudiar cada sección, rinde el examen con el botón rojo del panel principal.")
            return await interaction.response.send_message(embed=e, view=MedicoContentView(), ephemeral=True)

        # Resto de cursos — resumen de temas
        e = discord.Embed(title=f"{curso['emoji']} {curso['nombre']}", color=curso["color"])
        e.description = (
            f"{curso['descripcion']}\n\n"
            f"**Código:** `{curso['codigo']}`\n"
            f"**Duración típica:** {curso['duracion_dias']} días\n"
            f"**Rol al aprobar:** {curso['rol_nombre']}\n"
            f"**Recompensa:** +{curso['puntos_recompensa']} puntos de honor\n\n"
        )
        contenidos = {
            "drones": (
                "**Temas del examen:**\n"
                "• Altitud mínima para sigilo auditivo del Mavic 3\n"
                "• Diferencias tácticas entre Mavic 3, Crocus y Brasko\n"
                "• Técnica de ataque FPV sobre blindados (punto débil)\n"
                "• Protocolo de autorización para modo autónomo\n"
                "• Integración del drone con el pelotón en tiempo real\n\n"
                "**Estudia:** Bloque 7 de #protocolos + práctica de vuelo"
            ),
            "aviacion": (
                "**Temas del examen:**\n"
                "• Protocolo de marcado de LZ (secuencia de humos)\n"
                "• Variantes del H-60 y sus roles (UH/HH/MH)\n"
                "• 9-Line CAS — las 9 líneas, qué va en cada una\n"
                "• Pylon Manager — configuración de cargas antes del despegue\n"
                "• Radio LR obligatoria para pilotos y por qué\n\n"
                "**Estudia:** Bloque 6 de #protocolos + práctica de vuelo"
            ),
            "cqb": (
                "**Temas del examen:**\n"
                "• Por qué el umbral de la puerta es zona de muerte\n"
                "• Tipos de breach y cuándo usar cada uno\n"
                "• Secuencia exacta de limpieza de habitación\n"
                "• Señales manuales del equipo CQB\n"
                "• Ventajas del TPNVG vs NVG estándar\n\n"
                "**Estudia:** Bloque 8 de #protocolos + práctica de breach"
            ),
            "zeus": (
                "**Temas del examen:**\n"
                "• Responsabilidades del GM — qué SÍ y qué NO hacer\n"
                "• LAMBS — cuándo aplicar Danger, Suppression, RPG, Turrets\n"
                "• Módulos clave de Zeus Enhanced\n"
                "• Protocolo de comunicación GM ↔ CO (frecuencia 88.000 MHz)\n"
                "• Gestión de dificultad cuando el pelotón avanza fácil o es destruido\n\n"
                "**Estudia:** Bloque 9 de #protocolos + práctica de GM"
            ),
            "comando": (
                "**Temas del examen (combinados de todos los cursos):**\n"
                "• Tácticas SF: infiltración nocturna, HVT, extracción SPIE\n"
                "• Coordinación multi-elemento: tierra + aire + drones\n"
                "• Protocolo EOD al encontrar IED en ruta de exfil\n"
                "• SOFLAM y designación láser para guiar CAS\n"
                "• Decisiones de liderazgo bajo presión extrema\n\n"
                "**Requisito:** Los 6 cursos anteriores completados."
            ),
        }
        e.description += contenidos.get(tipo, "")
        await interaction.response.send_message(embed=e, ephemeral=True)

    async def _prac_cb(self, interaction: discord.Interaction):
        if await _bloquear_si_sin_basico(interaction, self.tipo):
            return
        curso = CURSOS[self.tipo]
        e = discord.Embed(title=f"🏋️ Ejercicio Práctico — {curso['nombre']}", color=curso["color"])
        e.description = (
            f"{curso['practica']}\n\n"
            "**Importante:** El ejercicio práctico se realiza en el servidor de juego. "
            "Un instructor o miembro del mando debe validar que lo completaste antes de que "
            "puedas rendir el examen teórico.\n\n"
            "> Reporta la finalización del práctico en el canal de mando."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    async def _load_cb(self, interaction: discord.Interaction):
        curso = CURSOS[self.tipo]
        e = discord.Embed(title=f"📦 Loadout — {curso['rol_nombre']}", color=curso["color"])
        e.description = curso["loadout"]
        e.set_footer(text="Equipo autorizado permanentemente al aprobar el curso.")
        await interaction.response.send_message(embed=e, ephemeral=True)

    async def _exam_cb(self, interaction: discord.Interaction):
        await _iniciar_examen_check(interaction, self.tipo)

    async def _mis_cb(self, interaction: discord.Interaction):
        await _mostrar_mis_cursos(interaction)

    async def _duda_cb(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DudaModal(self.tipo))

    async def _guia_cb(self, interaction: discord.Interaction):
        curso = CURSOS[self.tipo]
        e = discord.Embed(title="📚 Guía de Aprendizaje Científico", color=0x5865F2)
        e.description = (
            f"Aplica la **neurociencia y psicología cognitiva** al {curso['nombre']}.\n\n"
            "🧠 **La Curva del Olvido** — por qué olvidamos y cómo evitarlo\n"
            "🔄 **Repetición Espaciada** — el sistema con mayor evidencia científica\n"
            "📝 **Recuperación Activa** — estudiar haciendo tests, no releyendo\n"
            "🎯 **Práctica Deliberada** — calidad sobre cantidad de entrenamiento\n"
            "💪 **Disciplina Militar** — por qué exigimos el orden de los cursos\n"
            "😴 **Sueño y Memoria** — la neurociencia detrás del descanso"
        )
        e.set_footer(text="Selecciona un tema para ver la guía completa.")
        await interaction.response.send_message(embed=e, view=GuiaAprendizajeView(), ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS DE EXAMEN (usados por ambas views)
# ─────────────────────────────────────────────────────────────────────────────
async def _iniciar_examen_check(interaction: discord.Interaction, tipo: str):
    uid = str(interaction.user.id)
    cursos_data = cargar("cursos.json")
    usuario = cursos_data.get("usuarios", {}).get(uid, {})
    completados = usuario.get("completados", [])
    curso = CURSOS[tipo]

    # Verificar requisitos
    for req in curso["requisitos"]:
        if req not in completados:
            req_nombre = CURSOS[req]["nombre"]
            e = discord.Embed(title="❌ Requisito faltante", color=0xDC143C)
            e.description = f"Para acceder a este examen necesitas completar primero:\n**{req_nombre}**"
            return await interaction.response.send_message(embed=e, ephemeral=True)

    # Verificar cooldown (solo cursos avanzados)
    cooldown_h = curso.get("cooldown_h", 0)
    if cooldown_h > 0:
        ultimo = usuario.get("ultimo_intento", {}).get(tipo)
        if ultimo:
            dt_ultimo = datetime.datetime.strptime(ultimo, "%d/%m/%Y %H:%M")
            delta = datetime.datetime.now() - dt_ultimo
            restante = datetime.timedelta(hours=cooldown_h) - delta
            if restante.total_seconds() > 0:
                horas = int(restante.total_seconds() // 3600)
                minutos = int((restante.total_seconds() % 3600) // 60)
                e = discord.Embed(title="⏳ Cooldown activo", color=0xFFD700)
                e.description = f"Debes esperar **{horas}h {minutos}m** antes de rendir este examen nuevamente."
                return await interaction.response.send_message(embed=e, ephemeral=True)

    # Verificar si ya completó este curso
    if tipo in completados:
        rol_nombre = CURSOS[tipo]["rol_nombre"]
        e = discord.Embed(title="✅ Curso ya completado", color=0x2E8B57)
        e.description = f"Ya tienes el rango **{rol_nombre}** por haber aprobado este curso anteriormente."
        return await interaction.response.send_message(embed=e, ephemeral=True)

    # Registrar intento
    if "usuarios" not in cursos_data:
        cursos_data["usuarios"] = {}
    if uid not in cursos_data["usuarios"]:
        cursos_data["usuarios"][uid] = {"completados": [], "intentos": {}, "ultimo_intento": {}}
    cursos_data["usuarios"][uid].setdefault("intentos", {})[tipo] = \
        cursos_data["usuarios"][uid].get("intentos", {}).get(tipo, 0) + 1
    cursos_data["usuarios"][uid].setdefault("ultimo_intento", {})[tipo] = ahora_fmt()
    guardar("cursos.json", cursos_data)

    # Iniciar examen — primera pregunta
    cog = interaction.client.cogs.get("Cursos")
    view = ExamenView(cog, tipo, 0, [])
    embed = _pregunta_embed(tipo, 0)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def _mostrar_mis_cursos(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    cursos_data = cargar("cursos.json")
    usuario = cursos_data.get("usuarios", {}).get(uid, {})
    completados = usuario.get("completados", [])
    intentos = usuario.get("intentos", {})

    e = discord.Embed(title=f"🎖️ Cursos — {interaction.user.display_name}", color=COLOR_MILITAR)
    lineas = []
    for tipo, curso in CURSOS.items():
        estado = "✅" if tipo in completados else "❌"
        intento_str = f"({intentos.get(tipo, 0)} intentos)" if intentos.get(tipo, 0) > 0 else ""
        lineas.append(f"{estado} {curso['emoji']} **{curso['nombre']}** {intento_str}")
    e.description = "\n".join(lineas) if lineas else "Sin datos de cursos aún."
    total = len(completados)
    e.set_footer(text=f"{total}/{len(CURSOS)} cursos completados")
    await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: ADMIN — selector de tipo de curso
# ─────────────────────────────────────────────────────────────────────────────
class CursoTipoSelect(discord.ui.Select):
    def __init__(self):
        opciones = [
            discord.SelectOption(
                label=c["nombre"][:100],
                value=tipo,
                emoji=c["emoji"],
                description=f"Requisitos: {', '.join(c['requisitos']) or 'ninguno'} · {c['duracion_dias']}d",
            )
            for tipo, c in CURSOS.items()
        ]
        super().__init__(placeholder="Selecciona el tipo de curso...", options=opciones, custom_id="gl_adm_tipo_select")

    async def callback(self, interaction: discord.Interaction):
        tipo = self.values[0]
        view = DuracionSelectView(tipo)
        curso = CURSOS[tipo]
        e = discord.Embed(title=f"⏱️ Duración — {curso['nombre']}", color=curso["color"])
        e.description = (
            f"**Duración recomendada:** {curso['duracion_dias']} días\n\n"
            "Selecciona cuántos días durará el curso activo.\n"
            "Durante ese período **#entrenamientos quedará bloqueado** para mensajes normales."
        )
        await interaction.response.edit_message(embed=e, view=view)


class CursoTipoSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(CursoTipoSelect())


class DuracionSelect(discord.ui.Select):
    def __init__(self, tipo: str):
        self.tipo = tipo
        defecto = CURSOS[tipo]["duracion_dias"]
        opciones = [
            discord.SelectOption(label="1 día", value="1", description="Curso corto intensivo"),
            discord.SelectOption(label="2 días", value="2"),
            discord.SelectOption(label=f"3 días {'(recomendado)' if defecto==3 else ''}", value="3", default=defecto==3),
            discord.SelectOption(label=f"5 días {'(recomendado)' if defecto==5 else ''}", value="5", default=defecto==5),
            discord.SelectOption(label=f"7 días {'(recomendado)' if defecto==7 else ''}", value="7", default=defecto==7),
        ]
        super().__init__(placeholder="Selecciona la duración...", options=opciones, custom_id="gl_adm_duracion_select")

    async def callback(self, interaction: discord.Interaction):
        dias = int(self.values[0])
        tipo = self.tipo
        curso = CURSOS[tipo]
        view = ConfirmarCursoView(tipo, dias)
        e = discord.Embed(title=f"✅ Confirmar creación de curso", color=curso["color"])
        fin = datetime.datetime.now() + datetime.timedelta(days=dias)
        e.description = (
            f"**Curso:** {curso['emoji']} {curso['nombre']}\n"
            f"**Duración:** {dias} días\n"
            f"**Finalización:** {fin.strftime('%d/%m/%Y %H:%M')}\n\n"
            f"**Al confirmar:**\n"
            f"• Se publicará el curso en #entrenamientos\n"
            f"• El canal quedará bloqueado para mensajes normales\n"
            f"• Se desbloqueará automáticamente al finalizar\n\n"
            f"¿Proceder?"
        )
        await interaction.response.edit_message(embed=e, view=view)


class DuracionSelectView(discord.ui.View):
    def __init__(self, tipo: str):
        super().__init__(timeout=120)
        self.add_item(DuracionSelect(tipo))


class ConfirmarCursoView(discord.ui.View):
    def __init__(self, tipo: str, dias: int):
        super().__init__(timeout=120)
        self.tipo = tipo
        self.dias = dias

    @discord.ui.button(label="✅ Crear Curso", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.cogs.get("Cursos")
        if not cog:
            return await interaction.followup.send("❌ Error interno: cog no encontrado.", ephemeral=True)
        try:
            await cog._iniciar_curso(interaction.guild, self.tipo, self.dias, interaction.user.id)
            e = discord.Embed(title="✅ Curso creado exitosamente", color=0x2E8B57)
            e.description = (
                f"**{CURSOS[self.tipo]['emoji']} {CURSOS[self.tipo]['nombre']}** ha sido iniciado.\n"
                f"Duración: {self.dias} días · Publicado en #entrenamientos."
            )
            await interaction.followup.send(embed=e, ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"❌ Error al crear: {exc}", ephemeral=True)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Creación cancelada.", embed=None, view=None)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: ADMIN — gestión de cursos (enviada desde el panel de mando)
# ─────────────────────────────────────────────────────────────────────────────
class CursoAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ Crear Nuevo Curso", style=discord.ButtonStyle.success, custom_id="gl_adm_crear", row=0)
    async def crear(self, interaction: discord.Interaction, _: discord.ui.Button):
        cursos_data = cargar("cursos.json")
        activo = cursos_data.get("curso_activo")
        if activo:
            nombre = CURSOS.get(activo.get("tipo", ""), {}).get("nombre", "desconocido")
            e = discord.Embed(title="⚠️ Ya hay un curso activo", color=0xFFD700)
            e.description = (
                f"**Curso activo:** {nombre}\n"
                f"**Finaliza:** {activo.get('fin', '?')}\n\n"
                "Cancela el curso actual antes de crear uno nuevo."
            )
            return await interaction.response.send_message(embed=e, ephemeral=True)
        e = discord.Embed(title="🎓 Seleccionar Tipo de Curso", color=COLOR_MILITAR)
        e.description = (
            "Selecciona qué tipo de curso quieres activar.\n"
            "El curso se publicará en **#entrenamientos** y ese canal "
            "quedará bloqueado para mensajes durante su duración."
        )
        await interaction.response.send_message(embed=e, view=CursoTipoSelectView(), ephemeral=True)

    @discord.ui.button(label="📊 Curso Activo", style=discord.ButtonStyle.primary, custom_id="gl_adm_ver_activo", row=0)
    async def ver_activo(self, interaction: discord.Interaction, _: discord.ui.Button):
        cursos_data = cargar("cursos.json")
        activo = cursos_data.get("curso_activo")
        if not activo:
            e = discord.Embed(title="📭 Sin curso activo", color=0x808080)
            e.description = "Actualmente no hay ningún curso en progreso."
            return await interaction.response.send_message(embed=e, ephemeral=True)
        tipo = activo.get("tipo", "")
        curso = CURSOS.get(tipo, {})
        e = discord.Embed(title=f"📊 Curso Activo — {curso.get('nombre', 'Desconocido')}", color=curso.get("color", COLOR_MILITAR))
        e.description = (
            f"**Inicio:** {activo.get('inicio', '?')}\n"
            f"**Finalización:** {activo.get('fin', '?')}\n"
            f"**Creado por:** <@{activo.get('autor_id', '?')}>\n\n"
        )
        cursos_data_u = cursos_data.get("usuarios", {})
        completados_count = sum(1 for u in cursos_data_u.values() if tipo in u.get("completados", []))
        e.add_field(name="✅ Han completado este curso", value=str(completados_count), inline=True)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🗑️ Cancelar Curso Activo", style=discord.ButtonStyle.danger, custom_id="gl_adm_cancelar", row=0)
    async def cancelar_activo(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cursos_data = cargar("cursos.json")
        activo = cursos_data.get("curso_activo")
        if not activo:
            return await interaction.followup.send("❌ No hay curso activo.", ephemeral=True)
        cog = interaction.client.cogs.get("Cursos")
        if not cog:
            return await interaction.followup.send("❌ Error interno: cog no encontrado.", ephemeral=True)
        try:
            await cog._finalizar_curso(interaction.guild)
            await interaction.followup.send("✅ Curso cancelado y #entrenamientos desbloqueado.", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"❌ Error al cancelar: {exc}", ephemeral=True)

    @discord.ui.button(label="📋 Ver Progreso Global", style=discord.ButtonStyle.secondary, custom_id="gl_adm_progreso", row=1)
    async def ver_progreso(self, interaction: discord.Interaction, _: discord.ui.Button):
        cursos_data = cargar("cursos.json")
        usuarios = cursos_data.get("usuarios", {})
        e = discord.Embed(title="📋 Progreso Global de Cursos", color=COLOR_MILITAR)
        for tipo, curso in CURSOS.items():
            completados = [uid for uid, u in usuarios.items() if tipo in u.get("completados", [])]
            e.add_field(
                name=f"{curso['emoji']} {curso['rol_nombre']}",
                value=f"{len(completados)} operadores",
                inline=True,
            )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  COG PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class Cursos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        cursos_data = cargar("cursos.json")
        activo = cursos_data.get("curso_activo")
        if activo:
            fin_str = activo.get("fin")
            if fin_str:
                try:
                    fin_dt = datetime.datetime.strptime(fin_str, "%d/%m/%Y %H:%M")
                    if datetime.datetime.now() >= fin_dt:
                        await self._finalizar_curso(guild)
                    else:
                        delay = (fin_dt - datetime.datetime.now()).total_seconds()
                        asyncio.ensure_future(self._auto_finalizar(guild, delay))
                except Exception:
                    pass
        print("[Cursos] Sistema de cursos listo.")

    async def _finalizar_examen(self, interaction: discord.Interaction, tipo: str, respuestas: list):
        preguntas = EXAMENES[tipo]
        correctas = sum(1 for i, r in enumerate(respuestas) if r == preguntas[i]["c"])
        total = len(preguntas)
        aprobado = correctas / total >= UMBRAL_APROBADO

        embed = _resultado_embed(tipo, correctas, total)
        await interaction.response.edit_message(embed=embed, view=None)

        if aprobado:
            uid = str(interaction.user.id)
            cursos_data = cargar("cursos.json")
            if "usuarios" not in cursos_data:
                cursos_data["usuarios"] = {}
            if uid not in cursos_data["usuarios"]:
                cursos_data["usuarios"][uid] = {"completados": [], "intentos": {}, "ultimo_intento": {}}
            if tipo not in cursos_data["usuarios"][uid].get("completados", []):
                cursos_data["usuarios"][uid].setdefault("completados", []).append(tipo)
            guardar("cursos.json", cursos_data)

            curso = CURSOS[tipo]
            sumar_puntos(uid, curso["puntos_recompensa"], f"Aprobó {curso['nombre']}")

            guild = interaction.guild
            rol = await _obtener_o_crear_rol(guild, curso["rol_nombre"], curso["rol_color"])
            if rol and interaction.user not in [None]:
                try:
                    member = guild.get_member(interaction.user.id)
                    if member and rol not in member.roles:
                        await member.add_roles(rol, reason=f"Aprobó {curso['nombre']}")
                except Exception:
                    pass

            canal_mando = guild.get_channel(CANAL_MANDO_ID)
            if canal_mando:
                e_mando = discord.Embed(
                    title=f"🎉 Nuevo {curso['rol_nombre']}",
                    color=curso["color"],
                    timestamp=datetime.datetime.now(),
                )
                e_mando.description = (
                    f"{interaction.user.mention} ha completado el **{curso['nombre']}** "
                    f"con **{correctas}/{total}** correctas ({correctas/total*100:.0f}%).\n"
                    f"Se le ha asignado el rol **{curso['rol_nombre']}** {curso['emoji']}"
                )
                await canal_mando.send(embed=e_mando)

    async def _iniciar_curso(self, guild: discord.Guild, tipo: str, dias: int, autor_id: int):
        curso = CURSOS[tipo]
        inicio = datetime.datetime.now()
        fin = inicio + datetime.timedelta(days=dias)
        inicio_str = inicio.strftime("%d/%m/%Y %H:%M")
        fin_str = fin.strftime("%d/%m/%Y %H:%M")

        cursos_data = cargar("cursos.json")
        cursos_data["curso_activo"] = {
            "tipo":     tipo,
            "inicio":   inicio_str,
            "fin":      fin_str,
            "autor_id": str(autor_id),
            "msg_id":   None,
        }
        guardar("cursos.json", cursos_data)

        canal = guild.get_channel(CANAL_ENTRENAMIENTOS_ID)
        if canal:
            await canal.set_permissions(guild.default_role, send_messages=False,
                                        reason=f"Curso {tipo} en progreso")
            await canal.set_permissions(guild.me, send_messages=True)

            e = discord.Embed(
                title=f"📚 {curso['emoji']} {curso['nombre']}",
                description=(
                    f"{curso['descripcion']}\n\n"
                    f"**Código:** `{curso['codigo']}`\n"
                    f"**Inicio:** {inicio_str}\n"
                    f"**Finalización:** {fin_str}\n"
                    f"**Rol al aprobar:** {curso['rol_nombre']} (+{curso['puntos_recompensa']} puntos)\n\n"
                    "**Usa los botones para estudiar el contenido, ver el ejercicio práctico y rendir el examen.**\n"
                    f"Requisitos previos: {', '.join(CURSOS[r]['rol_nombre'] for r in curso['requisitos']) or 'ninguno'}"
                ),
                color=curso["color"],
                timestamp=datetime.datetime.now(),
            )
            e.set_footer(text=f"Mínimo para aprobar: {int(UMBRAL_APROBADO*100)}% · Canal bloqueado durante el curso")
            view = CursoActivoView(tipo)
            msg = await canal.send(embed=e, view=view)

            cursos_data = cargar("cursos.json")
            cursos_data["curso_activo"]["msg_id"] = str(msg.id)
            guardar("cursos.json", cursos_data)

        delay = (fin - datetime.datetime.now()).total_seconds()
        asyncio.ensure_future(self._auto_finalizar(guild, delay))

    async def _auto_finalizar(self, guild: discord.Guild, delay: float):
        await asyncio.sleep(delay)
        await self._finalizar_curso(guild)

    async def _finalizar_curso(self, guild: discord.Guild):
        cursos_data = cargar("cursos.json")
        activo = cursos_data.get("curso_activo")
        if not activo:
            return

        canal = guild.get_channel(CANAL_ENTRENAMIENTOS_ID)
        if canal:
            await canal.set_permissions(guild.default_role, send_messages=None,
                                        reason="Curso finalizado — canal desbloqueado")
            tipo = activo.get("tipo", "")
            curso = CURSOS.get(tipo, {})
            e = discord.Embed(
                title=f"📕 Curso Finalizado — {curso.get('emoji','')} {curso.get('nombre', tipo)}",
                color=0x808080,
                timestamp=datetime.datetime.now(),
            )
            e.description = (
                "El período de este curso ha concluido.\n"
                "Quienes no completaron el examen pueden hacerlo cuando se reactive el curso.\n\n"
                "**Canal de entrenamientos desbloqueado.**"
            )
            await canal.send(embed=e)

        cursos_data.pop("curso_activo", None)
        guardar("cursos.json", cursos_data)
        print(f"[Cursos] Curso finalizado automáticamente.")


async def setup(bot):
    await bot.add_cog(Cursos(bot))
