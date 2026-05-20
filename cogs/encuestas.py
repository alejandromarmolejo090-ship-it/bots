"""Cog: Encuestas dinámicas — creadas desde el Panel de Mando."""
import discord
from discord.ext import commands
import datetime, os, sys, asyncio, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, ahora_fmt, es_mando, COLOR_MILITAR

GUILD_ID           = int(os.getenv("GUILD_ID", "0"))
CANAL_ENCUESTAS_ID = int(os.getenv("CANAL_ENCUESTAS_ID", "0"))
CANAL_ANUNCIOS_ID  = int(os.getenv("CANAL_ANUNCIOS_ID", "0"))

NUMS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
BAR  = 15   # longitud de la barra


# ── Helpers ───────────────────────────────────────────────────────────────────

def _barra(pct: float) -> str:
    llenas = round(pct / 100 * BAR)
    return "█" * llenas + "░" * (BAR - llenas)


def _parsear_duracion(texto: str) -> int | None:
    """Devuelve segundos. None = sin límite."""
    texto = texto.strip().lower()
    if not texto or texto in ("0", "-", "∞", "sin limite", "sin límite"):
        return None
    sufijos = {"h": 3600, "d": 86400, "m": 60}
    for suf, factor in sufijos.items():
        if texto.endswith(suf):
            try:
                return int(texto[:-1]) * factor
            except ValueError:
                pass
    try:
        return int(texto) * 3600
    except ValueError:
        return 86400   # default 24 h


def _build_embed(enc: dict, cerrada: bool = False) -> discord.Embed:
    opciones = enc["opciones"]
    votos    = enc.get("votos", {})
    total    = len(votos)
    conteos  = [sum(1 for v in votos.values() if v == i) for i in range(len(opciones))]
    max_c    = max(conteos) if total else 0

    color = 0x4B4B4B if cerrada else COLOR_MILITAR
    titulo = "🔒  ENCUESTA CERRADA" if cerrada else "📊  ENCUESTA EN CURSO"

    embed = discord.Embed(
        title=titulo,
        description=f"**{enc['pregunta']}**\n{'━' * 32}",
        color=color,
        timestamp=datetime.datetime.now(),
    )

    for i, (opc, cnt) in enumerate(zip(opciones, conteos)):
        pct    = (cnt / total * 100) if total else 0
        barra  = _barra(pct)
        corona = "  👑" if (cerrada and cnt == max_c and total > 0) else ""
        embed.add_field(
            name=f"{NUMS[i]}  {opc}{corona}",
            value=f"`{barra}` **{pct:.0f}%** · {cnt} voto{'s' if cnt != 1 else ''}",
            inline=False,
        )

    cierre = enc.get("cierre_fmt", "Sin límite")
    estado = "✅ Finalizada" if cerrada else f"⏳ Cierra: {cierre}"
    embed.set_footer(
        text=f"Clan Lord · {total} voto{'s' if total != 1 else ''} · {estado}"
    )
    return embed


async def _cerrar_encuesta(bot, msg_id: str, delay: float = 0.0):
    if delay > 0:
        await asyncio.sleep(delay)

    encuestas = cargar("encuestas.json")
    if msg_id not in encuestas or encuestas[msg_id].get("cerrada"):
        return

    encuestas[msg_id]["cerrada"] = True
    guardar("encuestas.json", encuestas)
    enc = encuestas[msg_id]

    try:
        guild = bot.get_guild(GUILD_ID)
        canal = guild.get_channel(int(enc["canal_id"]))
        msg   = await canal.fetch_message(int(msg_id))
        await msg.edit(embed=_build_embed(enc, cerrada=True), view=EncuestaCerradaView())
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  MODAL DE CREACIÓN
# ══════════════════════════════════════════════════════

class EncuestaModal(discord.ui.Modal, title="📊 Crear Encuesta"):
    pregunta = discord.ui.TextInput(
        label="Pregunta",
        max_length=200,
        placeholder="¿Cuál es tu misión favorita?",
    )
    opciones_txt = discord.ui.TextInput(
        label="Opciones (una por línea — mín 2, máx 4)",
        style=discord.TextStyle.paragraph,
        max_length=320,
        placeholder="Operaciones nocturnas\nAsalto urbano\nInfiltración",
    )
    duracion = discord.ui.TextInput(
        label="Duración (ej: 24h · 7d · 0=sin límite)",
        max_length=10,
        placeholder="24h",
        required=False,
    )
    canal_txt = discord.ui.TextInput(
        label="ID del canal donde publicar (opcional)",
        max_length=25,
        required=False,
        placeholder="Deja vacío para usar el canal de encuestas",
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Parsear opciones
        opciones = [o.strip() for o in self.opciones_txt.value.splitlines() if o.strip()][:4]
        if len(opciones) < 2:
            return await interaction.response.send_message(
                "❌ Debes escribir al menos **2 opciones** (una por línea).", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)

        # Parsear duración
        segundos  = _parsear_duracion(self.duracion.value or "24h")
        if segundos:
            cierre_dt  = datetime.datetime.now() + datetime.timedelta(seconds=segundos)
            cierre_fmt = cierre_dt.strftime("%d/%m/%Y %H:%M")
        else:
            cierre_dt  = None
            cierre_fmt = "Sin límite"

        # Resolver canal destino
        canal = None
        if self.canal_txt.value.strip():
            try:
                canal = interaction.guild.get_channel(int(self.canal_txt.value.strip()))
            except ValueError:
                pass
        if not canal and CANAL_ENCUESTAS_ID:
            canal = interaction.guild.get_channel(CANAL_ENCUESTAS_ID)
        if not canal and CANAL_ANUNCIOS_ID:
            canal = interaction.guild.get_channel(CANAL_ANUNCIOS_ID)
        if not canal:
            canal = interaction.channel

        n   = len(opciones)
        enc = {
            "pregunta":   self.pregunta.value.strip(),
            "opciones":   opciones,
            "votos":      {},
            "cerrada":    False,
            "cierre_dt":  cierre_dt.strftime("%d/%m/%Y %H:%M") if cierre_dt else None,
            "cierre_fmt": cierre_fmt,
            "canal_id":   None,
            "msg_id":     None,
            "creador_id": str(interaction.user.id),
            "fecha":      ahora_fmt(),
        }

        view = {2: EncuestaView2, 3: EncuestaView3, 4: EncuestaView4}.get(n, EncuestaView3)()

        msg = await canal.send(embed=_build_embed(enc), view=view)

        enc["canal_id"] = str(canal.id)
        enc["msg_id"]   = str(msg.id)

        encuestas = cargar("encuestas.json")
        encuestas[str(msg.id)] = enc
        guardar("encuestas.json", encuestas)

        if cierre_dt:
            delay = (cierre_dt - datetime.datetime.now()).total_seconds()
            asyncio.ensure_future(_cerrar_encuesta(interaction.client, str(msg.id), delay))

        await interaction.followup.send(
            f"✅ Encuesta publicada en {canal.mention}\n"
            f"📊 {n} opciones · Cierre: **{cierre_fmt}**",
            ephemeral=True,
        )


# ══════════════════════════════════════════════════════
#  LÓGICA DE VOTO COMPARTIDA
# ══════════════════════════════════════════════════════

async def _votar(interaction: discord.Interaction, idx: int):
    encuestas = cargar("encuestas.json")
    msg_id    = str(interaction.message.id)

    if msg_id not in encuestas:
        return await interaction.response.send_message(
            "❌ Esta encuesta ya no existe o fue eliminada.\n"
            "Las encuestas activas las encuentras en el canal de anuncios.",
            ephemeral=True,
        )

    enc = encuestas[msg_id]

    if enc.get("cerrada"):
        return await interaction.response.send_message(
            "🔒 Esta encuesta ya está **cerrada**. ¡No se aceptan más votos!\n"
            "Pendiente de las próximas encuestas en el canal de anuncios.",
            ephemeral=True,
        )

    if idx >= len(enc["opciones"]):
        return await interaction.response.send_message("❌ Opción no disponible.", ephemeral=True)

    uid   = str(interaction.user.id)
    votos = enc.get("votos", {})
    opc   = enc["opciones"][idx]

    if votos.get(uid) == idx:
        del votos[uid]
        resp = "↩️ Voto retirado."
    else:
        votos[uid] = idx
        resp = f"✅ Votaste por **{opc}**."

    encuestas[msg_id]["votos"] = votos
    guardar("encuestas.json", encuestas)

    await interaction.response.edit_message(embed=_build_embed(enc))
    await interaction.followup.send(resp, ephemeral=True)


async def _cerrar_manual(interaction: discord.Interaction):
    if not es_mando(interaction):
        return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
    await interaction.response.defer()
    await _cerrar_encuesta(interaction.client, str(interaction.message.id))


# ══════════════════════════════════════════════════════
#  VIEWS PERSISTENTES (una por número de opciones)
# ══════════════════════════════════════════════════════

class EncuestaView2(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc2_op1", row=0)
    async def op1(self, i, _): await _votar(i, 0)

    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc2_op2", row=0)
    async def op2(self, i, _): await _votar(i, 1)

    @discord.ui.button(label="🔒 Cerrar encuesta", style=discord.ButtonStyle.danger,
                        custom_id="gl_enc2_cerrar", row=1)
    async def cerrar(self, i, _): await _cerrar_manual(i)


class EncuestaView3(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc3_op1", row=0)
    async def op1(self, i, _): await _votar(i, 0)

    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc3_op2", row=0)
    async def op2(self, i, _): await _votar(i, 1)

    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc3_op3", row=0)
    async def op3(self, i, _): await _votar(i, 2)

    @discord.ui.button(label="🔒 Cerrar encuesta", style=discord.ButtonStyle.danger,
                        custom_id="gl_enc3_cerrar", row=1)
    async def cerrar(self, i, _): await _cerrar_manual(i)


class EncuestaView4(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc4_op1", row=0)
    async def op1(self, i, _): await _votar(i, 0)

    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc4_op2", row=0)
    async def op2(self, i, _): await _votar(i, 1)

    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc4_op3", row=0)
    async def op3(self, i, _): await _votar(i, 2)

    @discord.ui.button(label="4️⃣", style=discord.ButtonStyle.primary,   custom_id="gl_enc4_op4", row=0)
    async def op4(self, i, _): await _votar(i, 3)

    @discord.ui.button(label="🔒 Cerrar encuesta", style=discord.ButtonStyle.danger,
                        custom_id="gl_enc4_cerrar", row=1)
    async def cerrar(self, i, _): await _cerrar_manual(i)


class EncuestaCerradaView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Encuesta cerrada", style=discord.ButtonStyle.secondary,
                        custom_id="gl_enc_cerrada", disabled=True)
    async def btn(self, i, _): pass


# ══════════════════════════════════════════════════════
#  COG
# ══════════════════════════════════════════════════════

class Encuestas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Retoma cierres automáticos pendientes tras reinicio."""
        encuestas = cargar("encuestas.json")
        now = datetime.datetime.now()
        for msg_id, enc in encuestas.items():
            if enc.get("cerrada") or not enc.get("cierre_dt"):
                continue
            try:
                cierre = datetime.datetime.strptime(enc["cierre_dt"], "%d/%m/%Y %H:%M")
                delay  = max(0.0, (cierre - now).total_seconds())
                asyncio.ensure_future(_cerrar_encuesta(self.bot, msg_id, delay))
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(Encuestas(bot))
