"""Cog: Protocolos — Guías de referencia táctica interactivas."""
import discord
from discord.ext import commands
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, COLOR_MILITAR

GUILD_ID           = int(os.getenv("GUILD_ID", "0"))
CANAL_PROTO_ID     = 1489821849788354721
CATEGORIA_PROTO_ID = 1489806586544394357

STEAM_BASE = "https://steamcommunity.com/sharedfiles/filedetails/?id={}"

MODS_CATEGORIAS = {
    "nucleo": {
        "emoji": "🔧", "nombre": "Núcleo", "color": 0x78909C,
        "mods": [
            ("CBA_A3",                            450814997),
            ("ACE3",                              463939057),
            ("KAT - Advanced Medical",            2020940806),
            ("Task Force Arrowhead Radio (BETA)", 894678801),
            ("Zeus Enhanced",                     1779063631),
            ("BackpackOnChest - Redux",           2372036642),
            ("TPNVG - Legacy Version",            2976607403),
        ],
    },
    "aviacion": {
        "emoji": "✈️", "nombre": "Aviación / Vehículos", "color": 0x1565C0,
        "mods": [
            ("Hatchet Interaction Framework",     2941986336),
            ("Hatchet H-60 pack",                1745501605),
            ("Hatchet H-60 - No Over Torque",   2801005195),
            ("USAF Mod - Main",                  2397360831),
            ("USAF Mod - Fighters",              2397371875),
            ("USAF Mod - Utility",               2397376046),
            ("USAF AC-130 BETA",                 2226368165),
            ("Pylon Manager",                    1867660876),
            ("Better CAS Environment (BCE)",     2853828143),
            ("Ride Where You Look",              2153127400),
        ],
    },
    "arsenal": {
        "emoji": "🔫", "nombre": "Armas / Arsenal", "color": 0x388E3C,
        "mods": [
            ("RHSAFRF",                           843425103),
            ("RHSUSAF",                           843577117),
            ("RHSGREF",                           843593391),
            ("JCA - Infantry Arsenal",            3333302397),
            ("Project OPFOR",                     735566597),
            ("ACE3 Arsenal Extended - Core",      2522638637),
            ("ACE3 Arsenal Extended - RHS",       2944314446),
            ("ACE3 Arsenal Extended - Vanilla",   2939048233),
            ("ACEAX ACE Equipment Compat",        2927505555),
            ("KJW's Two Secondary Weapons",       3018159841),
            ("KJW's Two Primary Weapons",         2893363164),
            ("Thumb Over Bore for RHS",           1905865989),
        ],
    },
    "mecanicas": {
        "emoji": "🎯", "nombre": "Mecánicas", "color": 0xF57C00,
        "mods": [
            ("Breach - Rewrite",                  3283645995),
            ("Improved Melee System",             2291129343),
            ("Speshal Core",                      3283642267),
            ("Animate - Rewrite",                 3283612524),
            ("Alternative Running",               2198339170),
            ("Hide Among The Grass (HATG)",       3346427969),
            ("IEDD Notebook",                     3048818056),
            ("Advanced ACE Repair - Inferno",    3688159183),
            ("dzn eXtended Pointer Interactions", 3540049844),
            ("Animated Recoil Changer",           2623341670),
        ],
    },
    "drones": {
        "emoji": "🚁", "nombre": "Drones / UAV", "color": 0x7B1FA2,
        "mods": [
            ("Mavic 3 - Improved",                3401580668),
            ("FPV Drone Crocus",                  3045129955),
            ("Brasko's AI FPV Drones",            3666776978),
        ],
    },
    "iazeus": {
        "emoji": "🤖", "nombre": "IA y Zeus", "color": 0x546E7A,
        "mods": [
            ("LAMBS Danger.fsm",                  1858075458),
            ("LAMBS RPG",                         1858070328),
            ("LAMBS Suppression",                 1808238502),
            ("LAMBS Turrets",                     1862208264),
            ("ASR AI3",                           642457233),
            ("Fast Reaction AI (FRAI)",           3673419571),
            ("Smart Aircraft AI",                 3682445063),
            ("Crows Zeus Additions",              2447965207),
            ("Zeus Additions",                    2387297579),
            ("Modules Enhanced",                  3043987264),
            ("3den Enhanced",                     623475643),
            ("O&T Expansion Eden",                1923321700),
        ],
    },
    "mapas": {
        "emoji": "🗺️", "nombre": "Mapas / Terrenos", "color": 0x5D4037,
        "mods": [
            ("Dagger Island Training Complex",    2983546566),
            ("CUP Terrains - Core",               583496184),
            ("CUP Terrains - Maps",               583544987),
            ("Tembelan Island",                   1252091296),
            ("Lybor",                             3013515917),
            ("Kujari",                            1726494027),
            ("Green Sea Terrain",                 2645015212),
            ("Bornholm [R]",                      2914536900),
            ("Virolahti - Valtatie 7",            1926513010),
            ("Šumava",                            2947655994),
            ("G.O.S Gunkizli",                   693153082),
            ("G.O.S Al Rayak",                   648172507),
            ("G.O.S Leskovets",                  855464203),
            ("Reshmaan Province",                843362862),
        ],
    },
    "efectos": {
        "emoji": "💥", "nombre": "Efectos / Audio", "color": 0xC62828,
        "mods": [
            ("JSRS SOUNDMOD 2025",                3407948300),
            ("Project SFX: Footsteps",            2806487814),
            ("Project SFX: Remastered",           2129532219),
            ("WBK Simple Blood",                  3132949782),
            ("Death and Hit Reactions",           2993442344),
            ("Realistic Ragdoll Physics",         3639557777),
            ("Some Effects Rework: Grenades",     3686863566),
            ("Real Engine Enhanced",              3715450352),
            ("Weather Plus",                      2735613231),
            ("YouTube Player Music",              3683168022),
            ("Acoustic Guitar Mod",               1378775292),
            ("Rome Music",                        1840706660),
        ],
    },
    "privados": {
        "emoji": "🔒", "nombre": "Mods Privados RTF", "color": 0x263238,
        "mods": [
            ("@ModsPrivados",                     3516492549),
            ("@mecanicas RTF",                    3718798290),
            ("@modulos RTF",                      3718802481),
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: GRANADAS DE HUMO
# ─────────────────────────────────────────────────────────────────────────────
class ProtocoloHumoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚪ Blanco", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_humo_blanco", row=0)
    async def blanco(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚪ Humo BLANCO — Cortina Táctica", color=0xAAAAAA)
        e.description = (
            "**Uso principal:** Cortina de humo para cubrir movimiento o marcar posición.\n\n"
            "**Cuándo usarlo:**\n"
            "• Cubrir avance o retirada sin revelar información al enemigo\n"
            "• Marcar posición cuando no hay otro color disponible\n"
            "• Reducir visibilidad en un área sin implicar contacto\n\n"
            "**⚠️ Importante:** El blanco es neutral — no indica zona segura ni contacto. "
            "Siempre comunica por radio qué estás haciendo antes de tirarlo."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🟢 Verde", style=discord.ButtonStyle.success,
                       custom_id="gl_prot_humo_verde", row=0)
    async def verde(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🟢 Humo VERDE — Zona Segura / MEDEVAC", color=0x2E8B57)
        e.description = (
            "**Uso principal:** Marcar LZ segura o zona de evacuación médica.\n\n"
            "**Cuándo usarlo:**\n"
            "• Marcar LZ para helo de CASEVAC/MEDEVAC\n"
            "• Señalizar zona de reagrupamiento segura\n"
            "• Confirmar zona de aterrizaje cuando el piloto pide identificación\n\n"
            "**Protocolo LZ:**\n"
            "1. Espera que el piloto diga: *'¿Tienen humo?'*\n"
            "2. Tiras el verde\n"
            "3. Piloto confirma: *'Identifico verde — aterrizando'*\n"
            "4. Solo entonces el helo inicia aproximación\n\n"
            "**🔴 NUNCA** tires verde si la zona no es segura — engañas al piloto."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔴 Roja", style=discord.ButtonStyle.danger,
                       custom_id="gl_prot_humo_roja", row=0)
    async def roja(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🔴 Humo ROJO — Contacto Enemigo / CAS", color=0xDC143C)
        e.description = (
            "**Uso principal:** Señalizar posición enemiga o solicitar fuego de apoyo.\n\n"
            "**Cuándo usarlo:**\n"
            "• Marcar objetivo enemigo para CAS (Close Air Support)\n"
            "• Identificar posición enemiga para el Zeus o artillería\n"
            "• Señalizar punto de contacto activo\n\n"
            "**⚠️ Crítico:** Nunca tires rojo cerca de tu propia posición sin coordinar.\n"
            "Un piloto que ve rojo interpreta que AHÍ está el enemigo.\n\n"
            "**Antes de tirar:** *'Tiro humo rojo en [MGRS], marca enemiga, cambio.'*"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔵 Azul", style=discord.ButtonStyle.primary,
                       custom_id="gl_prot_humo_azul", row=1)
    async def azul(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🔵 Humo AZUL — Fuerzas Aliadas", color=0x4169E1)
        e.description = (
            "**Uso principal:** Identificar posición propia para evitar fuego fratricida.\n\n"
            "**Cuándo usarlo:**\n"
            "• Cuando una aeronave necesita confirmar tu posición\n"
            "• Para evitar fuego amigo en zonas de combate confusas\n\n"
            "**Protocolo:**\n"
            "Piloto: *'¿Tienen humo en cuadrícula X?'*\n"
            "TL: *'Tirando azul — somos nosotros.'*\n"
            "Piloto: *'Confirmo azul — friendlies ubicados.'*\n\n"
            "**Nunca** tires azul sin que alguien lo pida — un azul inesperado confunde."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🟡 Amarillo", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_humo_amarillo", row=1)
    async def amarillo(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🟡 Humo AMARILLO — Precaución", color=0xFFD700)
        e.description = (
            "**Uso principal:** Señalizar área de peligro no-combate o alerta táctica.\n\n"
            "**Cuándo usarlo:**\n"
            "• Marcar zona con IED confirmado o sospechado\n"
            "• Señalizar campo minado o área de riesgo ambiental\n"
            "• Zona inestable sin confirmación de enemigos pero con peligro activo\n\n"
            "**Diferencia con Naranja:**\n"
            "🟡 Amarillo → peligro ambiental o incertidumbre táctica\n"
            "🟠 Naranja → presencia civil CON enemigos activos"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🟠 Naranja", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_humo_naranja", row=1)
    async def naranja(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🟠 Humo NARANJA — Zona Civil + Enemiga", color=0xFF8C00)
        e.description = (
            "**Uso principal:** Zona con presencia civil Y enemiga simultáneamente.\n\n"
            "**Cuándo usarlo:**\n"
            "• Pueblo o zona urbana con civiles confirmados y enemigos activos\n"
            "• Antes de solicitar CAS en área con civiles — aviso a la aeronave\n"
            "• Para coordinar restricción de ROE antes de comprometer la zona\n\n"
            "**ROE automática al ver naranja:**\n"
            "→ Identificación positiva antes de disparar\n"
            "→ Sin armamento de área sin autorización del CO\n"
            "→ Reportar al CO y esperar ROE actualizada\n\n"
            "> **Naranja = coordinar antes de actuar. Siempre.**"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: CALLSIGNS
# ─────────────────────────────────────────────────────────────────────────────
class ProtocoloCallsignsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✈️ Plataformas Aéreas", style=discord.ButtonStyle.primary,
                       custom_id="gl_prot_cs_aereos", row=0)
    async def aereos(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="✈️ Callsigns — Plataformas Aéreas", color=0x1E50A0)
        e.description = (
            "**FALCON** — Aviones de combate\n"
            "> F/A-18, A-10C, Su-25, jets armados.\n\n"
            "**HERCULES** — Aviones de transporte\n"
            "> C-130, AC-130, ala fija de transporte o logística.\n\n"
            "**VIPER** — Helicópteros de combate\n"
            "> AH-64, Mi-24, gunships armados.\n\n"
            "**PELICAN** — Helicópteros de transporte\n"
            "> UH-60, CH-47, Mi-8. Inserción, extracción, CASEVAC.\n\n"
            "**Formato de llamada:**\n"
            "*'Pelican-1, aquí Alfa, solicito extracción en [MGRS], cambio.'*"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🚗 Vehículos Terrestres", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_cs_terrestres", row=0)
    async def terrestres(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🚗 Callsigns — Vehículos Terrestres", color=0x556B2F)
        e.description = (
            "**VICTOR** — Vehículos ligeros de transporte\n"
            "> MRAP, HUMVEE, BRDM, Quad. Movilidad y transporte de personal.\n\n"
            "**HEAVY** — Tanques de batalla principal\n"
            "> M1A2, T-72, Leopard. Blindaje pesado y cañón principal.\n\n"
            "**STEEL** — Vehículos blindados de infantería\n"
            "> IFV, BMP, APC, Bradley. Transporte blindado con armamento.\n\n"
            "**BURRITO / MULE** — Vehículos de logística\n"
            "> Camiones, UTVs, transporte de suministros.\n\n"
            "*Otros vehículos reciben callsign en el briefing de misión.*"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="⚙️ Activos Especiales", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_cs_especiales", row=0)
    async def especiales(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="⚙️ Callsigns — Activos Especiales", color=0x2C2C54)
        e.description = (
            "**NÁUTICO** — Embarcaciones\n"
            "> Lanchas, botes de asalto, patrulla o inserción acuática.\n\n"
            "**CUERVO** — Drones / UAV\n"
            "> Mavic 3, FPV Crocus, Brasko. Cualquier plataforma no tripulada.\n"
            "> Con múltiples drones activos: *Cuervo-1, Cuervo-2…*\n\n"
            "**⚡ Zeus / Game Master:**\n"
            "> Sin callsign de combate.\n"
            "> Frecuencia LR exclusiva: **88.000 MHz**.\n"
            "> Solo el CO puede contactar al Zeus durante la operación."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: ZONAS DE FUEGO
# ─────────────────────────────────────────────────────────────────────────────
class ProtocoloZonasView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Zona Verde", style=discord.ButtonStyle.success,
                       custom_id="gl_prot_zona_verde", row=0)
    async def zona_verde(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🟢 ZONA VERDE — Fuego Libre", color=0x2E8B57)
        e.description = (
            "**Condiciones:**\n"
            "• Sin presencia civil confirmada\n"
            "• Actividad enemiga confirmada en el área\n"
            "• CO ha declarado la zona como Verde\n\n"
            "**Reglas de Enfrentamiento:**\n"
            "✅ Engage a discreción del TL\n"
            "✅ Armamento de área autorizado (granadas, HE, explosivos)\n"
            "✅ Sin identificación individual del objetivo requerida\n"
            "✅ Supresión libre sobre posiciones enemigas\n\n"
            "**⚠️** El CO puede cambiar la zona en cualquier momento. Monitorea la radio."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🟠 Zona Naranja", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_zona_naranja", row=0)
    async def zona_naranja(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🟠 ZONA NARANJA — Precaución", color=0xFF8C00)
        e.description = (
            "**Condiciones:**\n"
            "• Se sospecha o hay presencia de civiles\n"
            "• Posibilidad de fuego amigo en la zona\n"
            "• Zona urbana o de alto valor con restricciones\n\n"
            "**Reglas de Enfrentamiento:**\n"
            "⚠️ Fuego solo en defensa propia o amenaza directa confirmada\n"
            "⚠️ Identificación positiva del objetivo antes de disparar\n"
            "❌ Sin armamento de área sin autorización del CO\n"
            "❌ Sin supresión ciega sobre edificios\n\n"
            "**Si hay duda:** No disparas → reportas al TL → TL decide o consulta al CO."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔴 Zona Roja", style=discord.ButtonStyle.danger,
                       custom_id="gl_prot_zona_roja", row=0)
    async def zona_roja(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🔴 ZONA ROJA — Fuego Prohibido", color=0xDC143C)
        e.description = (
            "**Condiciones:**\n"
            "• Civiles claramente identificados en el área\n"
            "• Área neutral, patrullada o de rendición\n"
            "• Puede haber aliados o personal no combatiente\n\n"
            "**Reglas de Enfrentamiento:**\n"
            "🚫 Fuego prohibido sin orden directa del CO\n"
            "🚫 Sin excepciones — ni en defensa sin reportar primero\n"
            "✅ Fuerza no letal permitida (arresto ACE, inmovilización)\n"
            "✅ Si recibes fuego: reporta al CO PRIMERO, luego responde\n\n"
            "> **Fuego no autorizado en Zona Roja = sanción automática.**\n"
            "> El Zeus puede anular el engagement. El CO puede reasignarte."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: ORIENTACIÓN Y NAVEGACIÓN
# ─────────────────────────────────────────────────────────────────────────────
class ProtocoloNavView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🧭 Brújula y Azimuts", style=discord.ButtonStyle.primary,
                       custom_id="gl_prot_nav_brujula", row=0)
    async def brujula(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🧭 Brújula — Lectura de Azimut", color=0x4169E1)
        e.description = (
            "**Abrir brújula:** Tecla **K**\n\n"
            "**Las 4 cardinales:**\n"
            "**N** → November — 0° / 360°\n"
            "**E** → Eco — 90°\n"
            "**S** → Sierra — 180°\n"
            "**W** → Whiskey — 270°\n\n"
            "**Puntos intermedios:**\n"
            "**NE** → November Eco — 0° a 90°\n"
            "**SE** → Sierra Eco — 90° a 180°\n"
            "**SW** → Sierra Whiskey — 180° a 270°\n"
            "**NW** → November Whiskey — 270° a 360°\n\n"
            "**Reportar un azimut por radio — dígitos sueltos:**\n"
            "`086°` → *cero-ocho-seis*\n"
            "`270°` → *dos-siete-cero*\n"
            "`045°` → *cero-cuatro-cinco*"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="📍 MGRS — Cuadrículas", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_nav_mgrs", row=0)
    async def mgrs(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="📍 MGRS — Sistema de Cuadrícula Militar", color=0x4169E1)
        e.description = (
            "**Abrir microDAGR:** Menú ACE → GPS/DAGR\n\n"
            "**Precisión según número de dígitos:**\n"
            "**4 dígitos** (2+2) → 1.000 metros\n"
            "**6 dígitos** (3+3) → 100 metros ← **Estándar del clan**\n"
            "**8 dígitos** (4+4) → 10 metros\n"
            "**10 dígitos** (5+5) → 1 metro\n\n"
            "**Orden de lectura — ESTE primero, luego NORTE:**\n"
            "> *'Lees la calle (Este) antes de subir el edificio (Norte)'*\n\n"
            "**Ejemplo en radio:**\n"
            "Cuadrícula `037 142` → Este: 037 · Norte: 142\n"
            "Se dice: *'cero-tres-siete · uno-cuatro-dos'*"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🗺️ Orientación Sin GPS", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_nav_sinGps", row=0)
    async def sin_gps(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🗺️ Orientación Sin GPS", color=0x4169E1)
        e.description = (
            "**Método de triangulación básica:**\n"
            "1. Abre el mapa (tecla **M**) y estima tu posición aproximada\n"
            "2. Identifica 2 landmarks visibles (montaña, río, camino, pueblo)\n"
            "3. Ubica esos landmarks en el mapa\n"
            "4. Con la brújula, toma el azimut hacia cada landmark\n"
            "5. Tu posición es donde se cruzan las dos líneas\n\n"
            "**Truco rápido:**\n"
            "Si estás en un camino y ves una curva, encuéntrala en el mapa — "
            "estás antes o después de ella según lo que ves adelante y atrás.\n\n"
            "**Perdido sin mapa:**\n"
            "> *'[TL], me he separado. Última posición conocida [descripción]. "
            "Escucho en SR, cambio.'*\n\n"
            "**Nunca te muevas solo sin avisar.**"
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: SERVIDOR Y CONEXIÓN
# ─────────────────────────────────────────────────────────────────────────────
class ProtocoloServidorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="🌐 Descargar TeamSpeak 3",
            style=discord.ButtonStyle.link,
            url="https://teamspeak.com/en/teamspeak3/",
            row=1,
        ))

    @discord.ui.button(label="🎮 Cómo Conectar — Arma 3", style=discord.ButtonStyle.primary,
                       custom_id="gl_prot_sv_arma", row=0)
    async def arma_info(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🎮 Conexión — Arma 3", color=0x2E7D32)
        e.description = (
            "**Dirección del servidor:**\n"
            "```\nserver.reapertaskforce.com\n```"
            "**Puerto:**\n"
            "```\n2317\n```"
            "**Contraseña:**\n"
            "```\nReaper0925\n```\n"
            "**Pasos para conectar:**\n"
            "1. Abre Arma 3 → **Multijugador**\n"
            "2. Selecciona **Buscar por IP** / **Direct Connect**\n"
            "3. Ingresa la IP y el puerto `2317`\n"
            "4. Escribe la contraseña cuando se solicite\n\n"
            "> Asegúrate de tener todos los mods del preset activos antes de conectar."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🎤 Cómo Conectar — TeamSpeak 3", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_sv_ts3", row=0)
    async def ts3_info(self, interaction: discord.Interaction, _: discord.ui.Button):
        e = discord.Embed(title="🎤 Conexión — TeamSpeak 3", color=0x1565C0)
        e.description = (
            "**Dirección del servidor:**\n"
            "```\nalectotrans.myts3server.ovh\n```\n"
            "**Pasos para conectar:**\n"
            "1. Descarga **TeamSpeak 3** con el botón de abajo ↓\n"
            "2. Instala y abre TeamSpeak 3\n"
            "3. Ve a **Connections → Connect**\n"
            "4. Ingresa la dirección del servidor y pulsa **Connect**\n\n"
            "> Usa el mismo nickname que en Discord para que el Staff te reconozca.\n"
            "> El TeamSpeak es **obligatorio** durante las operaciones activas."
        )
        await interaction.response.send_message(embed=e, ephemeral=True)


def _generar_preset_html() -> bytes:
    rows = []
    for cat in MODS_CATEGORIAS.values():
        for name, mid in cat["mods"]:
            url = STEAM_BASE.format(mid)
            rows.append(
                f'        <tr data-type="ModContainer">\n'
                f'          <td data-type="DisplayName">{name}</td>\n'
                f'          <td><span class="from-steam">Steam</span></td>\n'
                f'          <td><a href="{url}" data-type="Link">{url}</a></td>\n'
                f'        </tr>'
            )
    total = sum(len(c["mods"]) for c in MODS_CATEGORIAS.values())
    html = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html>\n'
        '  <!--Preset generado por General Lord — LORD-->\n'
        '  <head>\n'
        '    <meta name="arma:Type" content="preset" />\n'
        '    <meta name="arma:PresetName" content="LORD" />\n'
        '    <meta name="generator" content="Arma 3 Launcher - https://arma3.com" />\n'
        '    <title>Arma 3</title>\n'
        '    <style>\n'
        '      body{font-family:Roboto,Arial,sans-serif;background:#1a1a1a;color:#e0e0e0}\n'
        '      h1,h2{color:#c0a060} table{border-collapse:collapse;width:100%}\n'
        '      td{padding:4px 8px;border:1px solid #333}\n'
        '      .from-steam{color:#66aadd;font-weight:bold}\n'
        '      a{color:#88ccff}\n'
        '    </style>\n'
        '  </head>\n'
        '  <body>\n'
        '    <h1>Preset <strong>LORD</strong></h1>\n'
        f'    <p>Total: <strong>{total} mods</strong></p>\n'
        '    <h2>Mods</h2>\n'
        '    <div class="mod-list"><table>\n'
        + "\n".join(rows) + "\n"
        '    </table></div>\n'
        '  </body>\n'
        '</html>'
    )
    return html.encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW: LISTA DE MODS
# ─────────────────────────────────────────────────────────────────────────────
class ProtocoloModsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _embed(self, key: str) -> discord.Embed:
        cat = MODS_CATEGORIAS[key]
        e = discord.Embed(
            title=f"{cat['emoji']}  {cat['nombre']}  —  Lista de Mods",
            color=cat["color"],
        )
        lines = [f"• [{name}]({STEAM_BASE.format(mid)})" for name, mid in cat["mods"]]
        e.description = "\n".join(lines)
        e.set_footer(text=f"{len(cat['mods'])} mods  ·  Click en el nombre para ver en Steam Workshop")
        return e

    @discord.ui.button(label="🔧 Núcleo", style=discord.ButtonStyle.primary,
                       custom_id="gl_prot_mod_nucleo", row=0)
    async def nucleo(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("nucleo"), ephemeral=True)

    @discord.ui.button(label="✈️ Aviación", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_aviacion", row=0)
    async def aviacion(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("aviacion"), ephemeral=True)

    @discord.ui.button(label="🔫 Arsenal", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_arsenal", row=0)
    async def arsenal(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("arsenal"), ephemeral=True)

    @discord.ui.button(label="🎯 Mecánicas", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_mecanicas", row=0)
    async def mecanicas(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("mecanicas"), ephemeral=True)

    @discord.ui.button(label="🚁 Drones", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_drones", row=0)
    async def drones(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("drones"), ephemeral=True)

    @discord.ui.button(label="🤖 IA y Zeus", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_iazeus", row=1)
    async def iazeus(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("iazeus"), ephemeral=True)

    @discord.ui.button(label="🗺️ Mapas", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_mapas", row=1)
    async def mapas(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("mapas"), ephemeral=True)

    @discord.ui.button(label="💥 Efectos", style=discord.ButtonStyle.secondary,
                       custom_id="gl_prot_mod_efectos", row=1)
    async def efectos(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("efectos"), ephemeral=True)

    @discord.ui.button(label="🔒 Privados", style=discord.ButtonStyle.danger,
                       custom_id="gl_prot_mod_privados", row=1)
    async def privados(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(embed=self._embed("privados"), ephemeral=True)

    @discord.ui.button(label="📥 Descargar Preset Completo", style=discord.ButtonStyle.success,
                       custom_id="gl_prot_mod_descargar", row=2)
    async def descargar(self, interaction: discord.Interaction, _: discord.ui.Button):
        data = _generar_preset_html()
        archivo = discord.File(io.BytesIO(data), filename="LORD_preset.html")
        await interaction.response.send_message(
            content=(
                "**📦 Preset Oficial — LORD**\n"
                "Para importarlo: abre el **Arma 3 Launcher** → "
                "pestaña **Mods** → botón **Preset** → **Importar desde archivo**."
            ),
            file=archivo,
            ephemeral=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  COG
# ─────────────────────────────────────────────────────────────────────────────
class Protocolos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return

        canal = guild.get_channel(CANAL_PROTO_ID)
        if not canal:
            categoria = guild.get_channel(CATEGORIA_PROTO_ID)
            canal = await guild.create_text_channel(
                "protocolos",
                category=categoria if isinstance(categoria, discord.CategoryChannel) else None,
                reason="Canal de protocolos creado automáticamente",
            )
            print(f"[Protocolos] Canal creado: #{canal.name}")
        else:
            categoria = guild.get_channel(CATEGORIA_PROTO_ID)
            if isinstance(categoria, discord.CategoryChannel) and canal.category_id != CATEGORIA_PROTO_ID:
                await canal.edit(category=categoria)

        prot_data = cargar("protocolos.json")
        msg_id = prot_data.get("msg_id")
        if msg_id:
            try:
                await canal.fetch_message(int(msg_id))
                print("[Protocolos] Contenido ya publicado — sin cambios.")
                return
            except (discord.NotFound, discord.HTTPException):
                pass

        await self._publicar(canal)

    async def _publicar(self, canal: discord.TextChannel):
        await canal.purge(limit=200)

        total_mods = sum(len(v["mods"]) for v in MODS_CATEGORIAS.values())

        # ── CABECERA ──────────────────────────────────────────────────────────
        e0 = discord.Embed(title="📋  PROTOCOLOS  —  LORD", color=COLOR_MILITAR)
        e0.description = (
            "Centro de referencia táctica y operacional del clan.\n"
            "Cada sección tiene botones interactivos con los detalles completos.\n\n"
            "**💨 Granadas de Humo** — códigos de color M18\n"
            "**📻 Callsigns** — identificadores de plataformas\n"
            "**🎯 Zonas de Fuego** — reglas de enfrentamiento\n"
            "**🧭 Navegación** — brújula, MGRS y orientación sin GPS\n"
            f"**🖥️ Servidores** — Arma 3 y TeamSpeak 3\n"
            f"**📦 Mods** — preset oficial ({total_mods} mods en 9 categorías)"
        )
        e0.set_footer(text="LORD  ·  Protocolos Operacionales")
        first = await canal.send(embed=e0)

        # ── GRANADAS DE HUMO ──────────────────────────────────────────────────
        e1 = discord.Embed(title="💨  PROTOCOLO DE GRANADAS DE HUMO  —  M18", color=0x708090)
        e1.description = "Presiona cada color para ver el protocolo de uso completo.\n"
        e1.add_field(name="⚪ BLANCO",   value="Cortina táctica / Marcar posición", inline=True)
        e1.add_field(name="🟢 VERDE",    value="Zona segura / Evacuación médica",   inline=True)
        e1.add_field(name="🔴 ROJA",     value="Contacto enemigo / Fuego de apoyo", inline=True)
        e1.add_field(name="🔵 AZUL",     value="Fuerzas aliadas en la zona",        inline=True)
        e1.add_field(name="🟡 AMARILLO", value="Precaución / Zona de peligro",      inline=True)
        e1.add_field(name="🟠 NARANJA",  value="Zona civil + presencia enemiga",    inline=True)
        e1.set_footer(text="Coordina siempre por radio antes de tirar humo")
        await canal.send(embed=e1, view=ProtocoloHumoView())

        # ── CALLSIGNS ─────────────────────────────────────────────────────────
        e2 = discord.Embed(title="📻  PROTOCOLO DE CALLSIGNS", color=0x2C2C54)
        e2.description = (
            "Identificadores estándar de plataformas. "
            "Presiona una categoría para ver el protocolo de comunicación.\n"
        )
        e2.add_field(name="✈️ FALCON",        value="Aviones de combate",         inline=True)
        e2.add_field(name="🛩️ HERCULES",      value="Aviones de transporte",      inline=True)
        e2.add_field(name="🚁 VIPER",         value="Helicópteros de combate",    inline=True)
        e2.add_field(name="🚁 PELICAN",       value="Helicópteros de transporte", inline=True)
        e2.add_field(name="🚗 VICTOR",        value="MRAV / HUMVEES / Ligeros",   inline=True)
        e2.add_field(name="🛡️ HEAVY",         value="Tanques de batalla",         inline=True)
        e2.add_field(name="⚔️ STEEL",         value="IFV / BMP / APC",           inline=True)
        e2.add_field(name="🚤 NÁUTICO",       value="Lanchas y botes",            inline=True)
        e2.add_field(name="🚛 BURRITO/MULE",  value="Camiones y logística",       inline=True)
        e2.add_field(name="🚁 CUERVO",        value="Drones / UAV",               inline=True)
        e2.set_footer(text="* Otros vehículos recibirán callsign en el briefing de misión")
        await canal.send(embed=e2, view=ProtocoloCallsignsView())

        # ── ZONAS DE FUEGO ────────────────────────────────────────────────────
        e3 = discord.Embed(title="🎯  ZONAS DE FUEGO  —  REGLAS DE ENFRENTAMIENTO", color=0x556B2F)
        e3.description = (
            "El CO declara la zona activa al inicio de cada operación. "
            "Presiona cada zona para ver las ROE completas.\n"
        )
        e3.add_field(
            name="🟢 ZONA VERDE — Fuego Libre",
            value="Sin civiles · Enemigos confirmados\nEngage a discreción del TL",
            inline=True,
        )
        e3.add_field(
            name="🟠 ZONA NARANJA — Precaución",
            value="Civiles sospechados · Fuego amigo posible\nSolo en defensa directa",
            inline=True,
        )
        e3.add_field(
            name="🔴 ZONA ROJA — Fuego Prohibido",
            value="Civiles identificados · Área neutral\nRequiere orden del CO",
            inline=True,
        )
        e3.set_footer(text="Violar las ROE tiene consecuencias tácticas y de inmersión")
        await canal.send(embed=e3, view=ProtocoloZonasView())

        # ── NAVEGACIÓN ────────────────────────────────────────────────────────
        e4 = discord.Embed(title="🧭  ORIENTACIÓN Y NAVEGACIÓN", color=0x4169E1)
        e4.add_field(
            name="🧭 Brújula (Tecla K)",
            value=(
                "**N** November · **E** Eco · **S** Sierra · **W** Whiskey\n"
                "Azimuts por radio — dígitos sueltos: `086°` → *cero-ocho-seis*"
            ),
            inline=False,
        )
        e4.add_field(
            name="📍 MGRS — Estándar del clan",
            value=(
                "6 dígitos (3+3) → 100 m de precisión\n"
                "Orden: **Este primero, luego Norte** · Ejemplo: `037-142`"
            ),
            inline=False,
        )
        e4.add_field(
            name="🗺️ Sin GPS",
            value="Usa el mapa + brújula con 2 landmarks para triangular tu posición.",
            inline=False,
        )
        e4.set_footer(text="Perdido → reporta al TL de inmediato. El silencio mata.")
        await canal.send(embed=e4, view=ProtocoloNavView())

        # ── SERVIDOR Y CONEXIÓN ───────────────────────────────────────────────
        e5 = discord.Embed(title="🖥️  SERVIDORES  —  LORD", color=0x1B5E20)
        e5.description = (
            "Información de conexión oficial. "
            "Presiona un botón para ver la guía completa de cómo conectarte.\n"
        )
        e5.add_field(
            name="🎮  Arma 3",
            value=(
                "**IP:** `server.reapertaskforce.com`\n"
                "**Puerto:** `2317`\n"
                "**Contraseña:** `Reaper0925`"
            ),
            inline=True,
        )
        e5.add_field(
            name="🎤  TeamSpeak 3",
            value=(
                "**Servidor:** `alectotrans.myts3server.ovh`\n"
                "Obligatorio durante operaciones activas."
            ),
            inline=True,
        )
        e5.set_footer(text="LORD  ·  Servidores Operacionales 24/7")
        await canal.send(embed=e5, view=ProtocoloServidorView())

        # ── LISTA DE MODS ─────────────────────────────────────────────────────
        e6 = discord.Embed(title="📦  LISTA DE MODS  —  PRESET OFICIAL RTF", color=0x212121)
        e6.description = (
            f"El preset incluye **{total_mods} mods** organizados en 9 categorías.\n"
            "Presiona una categoría para ver los mods con links directos a **Steam Workshop**.\n"
        )
        for key, cat in MODS_CATEGORIAS.items():
            e6.add_field(
                name=f"{cat['emoji']}  {cat['nombre']}",
                value=f"`{len(cat['mods'])} mods`",
                inline=True,
            )
        e6.set_footer(text="Steam Workshop  ·  LORD  ·  Preset Oficial")
        await canal.send(embed=e6, view=ProtocoloModsView())

        guardar("protocolos.json", {"msg_id": str(first.id)})
        print(f"[Protocolos] Canal publicado en #{canal.name} — {total_mods} mods registrados.")


async def setup(bot):
    await bot.add_cog(Protocolos(bot))
