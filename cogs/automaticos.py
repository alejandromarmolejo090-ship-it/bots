"""Cog: Tareas automáticas programadas."""
import discord
from discord.ext import commands, tasks
import datetime, random, os, sys, asyncio, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, ahora_fmt, sumar_puntos, COLOR_MILITAR, COLOR_VERDE, COLOR_OSCURO

GUILD_ID                 = int(os.getenv("GUILD_ID", "0"))
CANAL_FRASES_ID          = int(os.getenv("CANAL_FRASES_ID", "0"))
CANAL_BOLETIN_ID         = int(os.getenv("CANAL_BOLETIN_ID", "0"))
CANAL_MANDO_ID           = int(os.getenv("CANAL_MANDO_ID", "0"))
CANAL_OPERACIONES_ID     = int(os.getenv("CANAL_OPERACIONES_ID", "0"))
CANAL_ENTRENAMIENTOS_ID  = int(os.getenv("CANAL_ENTRENAMIENTOS_ID", "0"))
CANAL_BRIEFING_ID        = int(os.getenv("CANAL_BRIEFING_ID", "0"))
CANAL_ANUNCIOS_ID        = int(os.getenv("CANAL_ANUNCIOS_ID", "0"))
CANAL_FOTOS_ID           = int(os.getenv("CANAL_FOTOS_ID", "0"))
CANAL_VIDEOS_ID          = int(os.getenv("CANAL_VIDEOS_ID", "0"))

REGANOS_CANAL = [
    "🎖️ {mention} ¡SILENCIO, MIERDA! Este canal es zona restringida. ¡Un paso atrás antes de que te ponga a limpiar letrinas con la lengua!",
    "🎖️ {mention} ¿Quién coño te dio permiso de escribir aquí, pedazo de escoria? ¡Este canal no es tu puto WhatsApp!",
    "🎖️ {mention} ¡Treinta años en el ejército y no había visto un imbécil tan redomado! ¡FUERA DE MI CANAL, BASURA!",
    "🎖️ {mention} ¡Por la puta madre que te parió! ¿Eres idiota o simplemente practicas? ¡Canal restringido, cabrón!",
    "🎖️ {mention} ¡Tu mensaje fue ejecutado y tú deberías seguirlo! ¡Zona restringida, pedazo de mierda con patas!",
    "🎖️ {mention} ¡Aquí no se habla, aquí se OBEDECE, hijo de la gran puta! ¡Mensaje borrado igual que tus neuronas!",
    "🎖️ {mention} ¡Dios mío del cielo! ¿Qué cerebro de ameba te llevó a escribir aquí? ¡FUERA, INÚTIL DE MIERDA!",
    "🎖️ {mention} ¡Esto no es tu grupo de mamás, pedazo de inepto! ¡Vete a cagar a otro canal, coño!",
    "🎖️ {mention} ¡Me cago en tu linaje militar! ¿Quién te reclutó, un ciego? ¡CANAL RESTRINGIDO, ANIMAL!",
    "🎖️ {mention} ¡Soldado de mierda! Tu coeficiente intelectual es tan bajo que necesitas escalera para subir a cero. ¡FUERA!",
    "🎖️ {mention} ¡Eres tan inútil que si te mandara a comprar pan volvías con una patata! ¡Zona prohibida, pedazo de idiota!",
    "🎖️ {mention} ¡La concha de tu madre! ¿Escribir aquí? ¡Te van a dar de baja deshonrosa por mierda de cerebro!",
    "🎖️ {mention} ¡Cállate el hocico y sal de mi canal antes de que te mande a limpiar el campo de tiro con un hisopo!",
    "🎖️ {mention} ¡Recluta de pacotilla! Tienes menos neuronas que un fusil sin bala. ¡CANAL RESTRINGIDO, IMBÉCIL!",
    "🎖️ {mention} ¡Por los cojones de Simón Bolívar! ¿Qué clase de animal escribe aquí? ¡Mensaje destruido, igual que tu dignidad!",
    "🎖️ {mention} ¡Cara de culo! ¿Nadie te enseñó a leer las normas? ¡Este canal no es para gente como tú, que claramente no sabe ni amarrarse los zapatos!",
    "🎖️ {mention} ¡Me tienes hasta los huevos! ¡Canal restringido significa CERRAR LA MALDITA BOCA, pedazo de engendro!",
    "🎖️ {mention} ¡Eres tan pendejo que probablemente te perdiste yendo al baño! ¡FUERA DE AQUÍ, CABRÓN!",
    "🎖️ {mention} ¡Apaguen las luces que este inútil no merece ni la electricidad! Canal restringido. ¡A callar, maldita sea!",
    "🎖️ {mention} ¡Grandísimo idiota! Si el talento fuera pólvora no tendrías ni para volar un pedo. ¡FUERA DE MI CANAL!",
    "🎖️ {mention} ¡Pedazo de cerebro de mosquito! ¿Escribir aquí? ¡Te voy a mandar a pelar papa con los dientes por insubordinado!",
    "🎖️ {mention} ¡Eres la razón por la que los generales beben! ¡Canal restringido, so pendejo, que no se te olvide!",
    "🎖️ {mention} ¡Maldito iletrado! ¿Sabes leer o también eso se te escapa? ¡ZONA PROHIBIDA, ANIMAL DE MONTE!",
    "🎖️ {mention} ¡Ni en mis peores pesadillas imaginé un recluta tan rematadamente estúpido! ¡FUERA, COÑO!",
    "🎖️ {mention} ¡Oye, cabeza de chorlito! Este canal tiene normas. Pena que tú no tengas cerebro para entenderlas. ¡LARGO!",
    "🎖️ {mention} ¡Qué puta vergüenza de soldado! ¡Si fueras explosivo no tendrías ni para levantar una ceja! ¡Mensaje eliminado!",
    "🎖️ {mention} ¡Pareces sacado de una recluta de payasos! ¡Canal restringido, so imbécil! ¡A firmes y a callar de una puta vez!",
    "🎖️ {mention} ¡Eres tan inútil que si te pusiera de centinela se escaparían hasta los muertos! ¡FUERA DE AQUÍ!",
    "🎖️ {mention} ¡Me cago en todo lo que te rodea! ¿Canal restringido no significa nada para tu cabeza de alcornoque?",
    "🎖️ {mention} ¡Deja de contaminar este canal con tu estupidez, pedazo de desastre ambulante! ¡FUERA, MIERDA!",
    "🎖️ {mention} ¡Recluta de los cojones! ¿Quién te parió y por qué no te devolvió? ¡Canal restringido, imbécil redomado!",
    "🎖️ {mention} ¡Eres tan torpe que si te mandaran a vigilar el horizonte perderías el horizonte! ¡ZONA PROHIBIDA!",
    "🎖️ {mention} ¡Por la cresta! ¿Escribir aquí? ¡Tienes más cuajo que cerebro, so animal! ¡Mensaje eliminado con asco!",
    "🎖️ {mention} ¡Escucha bien, bestia sin modales: este canal no es tu muro de Facebook! ¡CIERRA EL PICO Y LARGO!",
    "🎖️ {mention} ¡Grandísimo inútil del carajo! Ni los reclutas del primer día cometen esta cagada. ¡FUERA!",
    "🎖️ {mention} ¡Me has hecho perder más neuronas que una borrachera de tres días! ¡Canal restringido, pedazo de idiota!",
    "🎖️ {mention} ¡Eres la mancha en el uniforme de este clan! ¡ZONA RESTRINGIDA, ANIMAL! ¡Mensaje destruido con placer!",
    "🎖️ {mention} ¡Cállate ese choclo que tienes por boca! Este canal no es para gente con tu nivel de estupidez. ¡FUERA!",
    "🎖️ {mention} ¡Joder, qué inútil tan completo! ¿Te cayó el cable del cerebro? ¡Canal prohibido, pedazo de fenómeno!",
    "🎖️ {mention} ¡Soldadito de mierda! Si la estupidez doliera estarías en UCI permanente. ¡FUERA DE AQUÍ AHORA!",
    "🎖️ {mention} ¡Qué manera tan espectacular de demostrar que eres un completo inútil! ¡Canal restringido, so bestia!",
    "🎖️ {mention} ¡Me has arruinado el día, pedazo de necio! ¡Zona prohibida! ¡Vete a escribir a un canal que esté a tu nivel intelectual, o sea, ninguno!",
    "🎖️ {mention} ¡Eres tan bruto que para ser idiota necesitarías estudiar! ¡CANAL RESTRINGIDO, FUERA DE AQUÍ!",
    "🎖️ {mention} ¡Cabrón! ¿Acaso naciste sin manual de instrucciones? ¡Este canal tiene normas que hasta un mono entiende!",
    "🎖️ {mention} ¡Habrase visto tamaño atrevimiento! ¡Canal restringido significa que TÚ NO ESCRIBES AQUÍ, pedazo de engendro!",
    "🎖️ {mention} ¡Qué asco de soldado! Tu madre debería estar avergonzada. ¡ZONA PROHIBIDA, IMBÉCIL DE LOS COJONES!",
    "🎖️ {mention} ¡Treinta años mandando tropas y nunca vi tanta idiotez concentrada en un solo ser! ¡FUERA, ANIMAL!",
    "🎖️ {mention} ¡Recluta de tres al cuarto! ¿Quién coño te enseñó a leer las normas? ¡Canal restringido, pedazo de basura!",
    "🎖️ {mention} ¡Eres la prueba viviente de que la evolución a veces va para atrás! ¡FUERA DE MI CANAL, INÚTIL!",
    "🎖️ {mention} ¡Maldita sea tu estampa! ¿Escribir aquí? ¡Voy a mandarte a hacer guardias bajo la lluvia por el resto de tu miserable existencia!",
    "🎖️ {mention} ¡Pedazo de animal sin domesticar! ¡Este canal es zona restringida! ¡Abre los ojos o te los abro yo de un grito!",
]

# ══════════════════════════════════════════════════════
#  MURO DE LA PENA
# ══════════════════════════════════════════════════════

MURO_UMBRAL       = 3    # infracciones para entrar al muro
PUNTOS_INFRACCION = -3   # puntos que se descuentan por infracción
UMBRAL_SILENCIO   = -15  # puntos negativos que activan el silencio

NIVELES_MURO = [
    (21, 5, "💀 INÚTIL CÓSMICO SUPREMO", 0x8B0000),
    (16, 4, "🐂 Bestia Sin Remedio",      0xFF0000),
    (11, 3, "🦧 Idiota de Gala",          0xFF4500),
    (6,  2, "🤡 Imbécil Certificado",     0xFFA500),
    (3,  1, "🐢 Recluta Torpe",           0x888888),
]

NOMBRES_MURO = {
    1: ["burro-novato",         "idiota-primerizo",    "recluta-inutil",       "caso-perdido",       "sin-cerebro"],
    2: ["cerebro-de-pollo",     "imbecil-certificado", "bestia-sin-modales",   "neanderthal-digital","sin-neuronas"],
    3: ["analfabeto-de-gala",   "caso-clinico",        "desastre-con-patas",   "idiota-avanzado",    "bestia-analfabeta"],
    4: ["vergüenza-del-clan",   "inutil-profesional",  "cerebro-de-mosquito",  "bestia-prehistorica","campeon-del-fracaso"],
    5: ["dios-del-fracaso",     "inutil-cosmico",      "rey-de-los-pendejos",  "campeon-idiotez",    "error-de-la-creacion"],
}

SENTENCIAS_MURO = {
    1: ("«Soldado {nombre}. Llevas {count} infracciones. Eres un idiota aficionado, pero llevas un ritmo "
        "preocupante. Disfruta del muro, recluta torpe. Aún tienes remedio... quizás.»"),
    2: ("«{nombre}. {count} veces. Ya no hay excusa ni diagnóstico que justifique tanta estupidez. "
        "El mando te declara oficialmente IMBÉCIL CERTIFICADO. Enhorabuena, pedazo de inútil.»"),
    3: ("«¡{nombre}! ¡{count} infracciones! ¡NI EN LA ACADEMIA DE LOS PENDEJOS APROBARÍAS! "
        "Idiota de Gala. Un ejemplar digno de museo. La ciencia quiere estudiar tu cerebro... "
        "o lo que queda de él. MURO NIVEL CRÍTICO ACTIVADO.»"),
    4: ("«{nombre}... {count} veces. He visto mulas con doctorado comparadas contigo. "
        "BESTIA SIN REMEDIO. Caso clínico irreversible. He llorado en mi despacho por ti, "
        "y no lo hago ni por mis soldados caídos. VERGÜENZA GALÁCTICA.»"),
    5: ("«{nombre}. {count} infracciones. NIVEL CINCO. INÚTIL CÓSMICO SUPREMO. "
        "Has alcanzado el pináculo absoluto de la incompetencia humana. Los libros de historia "
        "te recordarán como advertencia para las generaciones futuras. "
        "El universo mismo está avergonzado de haberte creado. MÁXIMA IGNOMINIA ACTIVADA. »"),
}

INSULTOS_MURO = [
    "¡Si tu cerebro fuera dinamita no tendrías ni para volar un chicle!",
    "¡Eres tan inútil que si te pusieran de adorno en una vitrina espantarías a los clientes!",
    "¡He visto lentejas con más inteligencia táctica que tú!",
    "¡Eres la razón por la que el ejército necesita psicólogos!",
    "¡Si la estupidez fuera un deporte olímpico, serías descalificado por dopaje de idiotez!",
    "¡Eres tan torpe que te tropiezas con las rayas del piso!",
    "¡Necesitarías un mapa y una brújula para encontrar tu propio cerebro!",
]


def _get_nivel(count: int):
    for umbral, nivel, titulo, color in NIVELES_MURO:
        if count >= umbral:
            return nivel, titulo, color
    return None, None, None


def _build_embed_muro(member: discord.Member, count: int) -> discord.Embed:
    nivel, titulo, color = _get_nivel(count)
    stars = "⭐" * nivel + "☆" * (5 - nivel)
    sentencia = SENTENCIAS_MURO[nivel].format(nombre=member.display_name, count=count)
    insulto   = random.choice(INSULTOS_MURO)

    embed = discord.Embed(
        title="🏛️  MURO DE LA PENA — SENTENCIA PÚBLICA",
        description=(
            f"*El General ha dictado sentencia:*\n\n"
            f">>> {sentencia}\n\n"
            f"*— {insulto}*"
        ),
        color=color,
        timestamp=datetime.datetime.now(),
    )
    embed.add_field(name="👤 Condenado",         value=member.mention,                  inline=True)
    embed.add_field(name="⚠️ Infracciones",       value=f"**{count}**",                  inline=True)
    embed.add_field(name="🧠 Nivel de Estupidez", value=f"**{titulo}**  `({nivel}/5)`",  inline=False)
    embed.add_field(name="Medidor de Idiotez",   value=stars,                           inline=False)
    embed.add_field(name="⏳ Duración del muro",  value="**24 horas**",                  inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Clan Lord — Justicia Suprema del General")
    return embed


async def _silenciar_recluta(guild: discord.Guild, member: discord.Member, puntos: int):
    # No silenciar si ya está en timeout
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if member.timed_out_until and member.timed_out_until > now_utc:
        return

    try:
        until = now_utc + datetime.timedelta(minutes=3)
        await member.edit(timed_out_until=until, reason=f"Puntos negativos ({puntos}pts) — silencio automático")
    except Exception:
        return

    canal_mando = guild.get_channel(CANAL_MANDO_ID)
    if not canal_mando:
        return

    embed = discord.Embed(
        title="🔇 SILENCIO AUTOMÁTICO — ORDEN DEL GENERAL",
        description=(
            f"{member.mention} ha sido **silenciado en todos los canales por 3 minutos**.\n\n"
            f"*«{member.display_name}, te has ganado el silencio a pulso. "
            f"Con **{puntos} puntos** en el marcador, eres oficialmente "
            f"una vergüenza galáctica. CIERRA ESA BOCA por 3 malditos minutos, "
            f"pedazo de inútil redomado.»*"
        ),
        color=0x1A1A1A,
        timestamp=datetime.datetime.now(),
    )
    embed.add_field(name="⭐ Puntos actuales", value=f"**{puntos}**", inline=True)
    embed.add_field(name="⏱️ Duración",        value="**3 minutos**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Clan Lord — Silencio de emergencia")
    await canal_mando.send(embed=embed)


async def _auto_borrar_muro(canal: discord.TextChannel, uid: str, delay: float = 86400.0):
    await asyncio.sleep(delay)
    try:
        await canal.delete(reason="Muro de la Pena — 24h cumplidas")
    except Exception:
        pass
    infracciones = cargar("infracciones.json")
    if uid in infracciones:
        infracciones[uid].pop("muro_canal_id", None)
        infracciones[uid].pop("muro_expira",   None)
        guardar("infracciones.json", infracciones)


async def _crear_o_actualizar_muro(guild: discord.Guild, member: discord.Member, count: int):
    nivel, _, _ = _get_nivel(count)
    if nivel is None:
        return

    infracciones = cargar("infracciones.json")
    uid  = str(member.id)
    data = infracciones.get(uid, {})
    embed = _build_embed_muro(member, count)

    # ── Actualizar canal existente ──────────────────────
    canal_id = data.get("muro_canal_id")
    if canal_id:
        canal_muro = guild.get_channel(int(canal_id))
        if canal_muro:
            try:
                async for msg in canal_muro.history(limit=15):
                    if msg.author == guild.me and msg.embeds:
                        await msg.edit(embed=embed)
                        return
            except Exception:
                pass
            try:
                await canal_muro.send(embed=embed)
            except Exception:
                pass
            return

    # ── Crear canal nuevo ───────────────────────────────
    nombre_limpio = re.sub(r"[^a-z0-9\-]", "", member.display_name.lower().replace(" ", "-"))[:14]
    prefijo       = random.choice(NOMBRES_MURO.get(nivel, NOMBRES_MURO[1]))
    nombre_canal  = f"{prefijo}-{nombre_limpio}" if nombre_limpio else f"{prefijo}-{str(member.id)[:6]}"
    nombre_canal  = nombre_canal[:100]

    canal_ref = guild.get_channel(CANAL_MANDO_ID)
    categoria = canal_ref.category if canal_ref else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True,  send_messages=False),
        guild.me:           discord.PermissionOverwrite(read_messages=True,  send_messages=True, manage_messages=True),
        member:             discord.PermissionOverwrite(read_messages=True,  send_messages=False),
    }

    try:
        canal_nuevo = await guild.create_text_channel(
            nombre_canal,
            category=categoria,
            overwrites=overwrites,
            reason=f"Muro de la Pena — {member.display_name}",
        )
    except Exception:
        return

    expira = datetime.datetime.now() + datetime.timedelta(days=1)
    data["muro_canal_id"] = str(canal_nuevo.id)
    data["muro_expira"]   = expira.strftime("%d/%m/%Y %H:%M")
    infracciones[uid] = data
    guardar("infracciones.json", infracciones)

    await canal_nuevo.send(embed=embed)
    asyncio.ensure_future(_auto_borrar_muro(canal_nuevo, uid))


FRASES = [
    "🎯 *«La disciplina es el alma de un ejército.»* — George Washington",
    "⚔️ *«En la victoria, el mérito es de todos. En la derrota, la responsabilidad también.»*",
    "🛡️ *«Un soldado preparado es un soldado invencible.»*",
    "🗺️ *«El terreno y la táctica deciden la batalla antes de que empiece.»*",
    "💪 *«La fuerza no viene de ganar, viene de seguir cuando crees que no puedes.»*",
    "🤝 *«El trabajo en equipo divide el esfuerzo y multiplica el éxito.»*",
    "🎖️ *«El honor se gana en el campo, no en las palabras.»*",
    "🔥 *«La valentía no es ausencia de miedo, es seguir adelante a pesar de él.»*",
    "📋 *«Improvisa, adapta, supera.»* — Gunnery Sgt. Tom Highway",
    "🌟 *«Un clan fuerte comienza con miembros comprometidos.»*",
]


class Automaticos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.frase_diaria.start()
        self.boletin_semanal.start()
        self.recordatorio_inactividad.start()
        self.mvp_mensual.start()

    def cog_unload(self):
        self.frase_diaria.cancel()
        self.boletin_semanal.cancel()
        self.recordatorio_inactividad.cancel()
        self.mvp_mensual.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        """Al arrancar, garantiza permisos de borrado y limpia muros expirados."""
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return

        # Asegurar que el bot puede borrar mensajes en todos los canales restringidos
        for cid in [CANAL_OPERACIONES_ID, CANAL_ENTRENAMIENTOS_ID,
                    CANAL_BRIEFING_ID, CANAL_ANUNCIOS_ID,
                    CANAL_FRASES_ID, CANAL_BOLETIN_ID]:
            if not cid:
                continue
            canal = guild.get_channel(cid)
            if canal:
                try:
                    await canal.set_permissions(
                        guild.me,
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                    )
                except Exception:
                    pass

        infracciones = cargar("infracciones.json")
        now     = datetime.datetime.now()
        changed = False
        for uid, data in list(infracciones.items()):
            canal_id   = data.get("muro_canal_id")
            expira_str = data.get("muro_expira")
            if not (canal_id and expira_str):
                continue
            try:
                expira = datetime.datetime.strptime(expira_str, "%d/%m/%Y %H:%M")
                canal  = guild.get_channel(int(canal_id))
                if now >= expira:
                    if canal:
                        await canal.delete(reason="Muro expirado (limpieza al iniciar)")
                    data.pop("muro_canal_id", None)
                    data.pop("muro_expira",   None)
                    changed = True
                elif canal:
                    remaining = max(60.0, (expira - now).total_seconds())
                    asyncio.ensure_future(_auto_borrar_muro(canal, uid, delay=remaining))
            except Exception:
                pass
        if changed:
            guardar("infracciones.json", infracciones)

    @tasks.loop(hours=24)
    async def frase_diaria(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        canal = guild.get_channel(CANAL_FRASES_ID)
        if not canal:
            return
        frase = random.choice(FRASES)
        embed = discord.Embed(
            description=frase,
            color=COLOR_OSCURO,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Frase del día — {ahora_fmt()}")
        await canal.send(embed=embed)

    @frase_diaria.before_loop
    async def before_frase(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        await discord.utils.sleep_until(target)

    @tasks.loop(hours=168)
    async def boletin_semanal(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        canal = guild.get_channel(CANAL_BOLETIN_ID)
        if not canal:
            return

        ops = cargar("operaciones.json")
        perfiles = cargar("perfiles.json")
        puntos_data = cargar("puntos.json")

        embed = discord.Embed(
            title="📰 BOLETÍN SEMANAL — Clan Lord",
            color=COLOR_MILITAR,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="👥 Miembros activos", value=str(len(perfiles)), inline=True)
        embed.add_field(name="⚔️ Operaciones totales", value=str(len(ops)), inline=True)

        if puntos_data:
            top = sorted(puntos_data.items(), key=lambda x: x[1].get("puntos", 0), reverse=True)[:3]
            top_str = "\n".join(
                f"{i+1}. <@{uid}> — {d.get('puntos',0)} pts"
                for i, (uid, d) in enumerate(top)
            )
            embed.add_field(name="🏆 Top Honor", value=top_str, inline=False)

        ops_semana = list(ops.items())[-3:]
        if ops_semana:
            embed.add_field(
                name="📅 Últimas operaciones",
                value="\n".join(f"• {op['nombre']} ({op['fecha']})" for _, op in ops_semana),
                inline=False,
            )

        embed.set_footer(text=f"Generado automáticamente — {ahora_fmt()}")
        await canal.send(embed=embed)

    @boletin_semanal.before_loop
    async def before_boletin(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        days_until_monday = (7 - now.weekday()) % 7 or 7
        target = (now + datetime.timedelta(days=days_until_monday)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        await discord.utils.sleep_until(target)

    # Mínimo de misiones para no ser marcado inactivo.
    # Sube este número cuando el clan lleve varias semanas usando el bot.
    UMBRAL_INACTIVIDAD = 1

    @tasks.loop(hours=168)  # Una vez por semana
    async def recordatorio_inactividad(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        canal = guild.get_channel(CANAL_MANDO_ID)
        if not canal:
            return

        perfiles = cargar("perfiles.json")
        inactivos = [
            uid for uid, p in perfiles.items()
            if p.get("misiones", 0) < self.UMBRAL_INACTIVIDAD and not p.get("baja")
        ]
        if not inactivos:
            return

        embed = discord.Embed(
            title="⚠️ Alerta de Inactividad Semanal",
            description=(
                f"Los siguientes miembros no tienen misiones registradas por el bot todavía.\n"
                f"*(Umbral actual: {self.UMBRAL_INACTIVIDAD} misión mínima)*"
            ),
            color=COLOR_OSCURO,
        )
        menciones = " ".join(f"<@{uid}>" for uid in inactivos[:20])
        embed.add_field(name="Miembros", value=menciones or "—", inline=False)
        embed.set_footer(text=f"Revisión automática — {ahora_fmt()}")
        await canal.send(embed=embed)

    @recordatorio_inactividad.before_loop
    async def before_recordatorio(self):
        await self.bot.wait_until_ready()
        # Esperar 7 días antes del primer disparo para no alertar nada en el arranque
        target = datetime.datetime.now() + datetime.timedelta(days=7)
        target = target.replace(hour=10, minute=0, second=0, microsecond=0)
        await discord.utils.sleep_until(target)

    @tasks.loop(hours=720)
    async def mvp_mensual(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        canal = guild.get_channel(CANAL_BOLETIN_ID)
        if not canal:
            return

        puntos_data = cargar("puntos.json")
        if not puntos_data:
            return

        top = sorted(puntos_data.items(), key=lambda x: x[1].get("puntos", 0), reverse=True)
        if not top:
            return

        mvp_uid, mvp_data = top[0]
        mvp_pts = mvp_data.get("puntos", 0)
        sumar_puntos(mvp_uid, 20, "MVP del Mes — bonus automático")

        embed = discord.Embed(
            title="🌟 MVP DEL MES",
            description=f"<@{mvp_uid}> es el **MVP del mes** con **{mvp_pts} puntos de honor**.\n¡Felicitaciones y +20 puntos de bonus!",
            color=COLOR_VERDE,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Calculado automáticamente — {ahora_fmt()}")
        await canal.send(embed=embed)

    @mvp_mensual.before_loop
    async def before_mvp(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        if now.month == 12:
            target = datetime.datetime(now.year + 1, 1, 1, 12, 0, 0)
        else:
            target = datetime.datetime(now.year, now.month + 1, 1, 12, 0, 0)
        await discord.utils.sleep_until(target)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        CANALES_RESTRINGIDOS = {
            CANAL_OPERACIONES_ID,
            CANAL_ENTRENAMIENTOS_ID,
            CANAL_BRIEFING_ID,
            CANAL_ANUNCIOS_ID,
            CANAL_FRASES_ID,
            CANAL_BOLETIN_ID,
            CANAL_FOTOS_ID,
            CANAL_VIDEOS_ID,
        }

        if message.channel.id not in CANALES_RESTRINGIDOS:
            return

        # ── Borrar mensaje ──────────────────────────────
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except Exception:
            try:
                await message.channel.purge(limit=1, check=lambda m: m.id == message.id, bulk=False)
            except Exception:
                pass

        # ── Registrar infracción ────────────────────────
        infracciones = cargar("infracciones.json")
        uid  = str(message.author.id)
        if uid not in infracciones:
            infracciones[uid] = {"count": 0}
        infracciones[uid]["count"] = infracciones[uid].get("count", 0) + 1
        count = infracciones[uid]["count"]
        guardar("infracciones.json", infracciones)

        # ── Descontar puntos ────────────────────────────
        sumar_puntos(uid, PUNTOS_INFRACCION, f"Infracción en canal restringido (#{message.channel.name})")
        pd = cargar("puntos.json")
        puntos_actuales = pd.get(uid, {}).get("puntos", 0)

        # ── Regaño en el canal ──────────────────────────
        regano = random.choice(REGANOS_CANAL).format(mention=message.author.mention)
        try:
            await message.channel.send(regano, delete_after=12)
        except Exception:
            pass

        # ── Silencio si puntos muy negativos ───────────
        if puntos_actuales <= UMBRAL_SILENCIO:
            asyncio.ensure_future(_silenciar_recluta(message.guild, message.author, puntos_actuales))

        # ── Muro de la Pena si supera el umbral ────────
        if count >= MURO_UMBRAL:
            asyncio.ensure_future(_crear_o_actualizar_muro(message.guild, message.author, count))


async def setup(bot):
    await bot.add_cog(Automaticos(bot))
