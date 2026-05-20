"""Cog: Sistema de videos — clips, highlights y fails del clan."""
import discord
from discord.ext import commands, tasks
import datetime, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, ahora_fmt, sumar_puntos, COLOR_MILITAR

GUILD_ID        = int(os.getenv("GUILD_ID", "0"))
CANAL_VIDEOS_ID = int(os.getenv("CANAL_VIDEOS_ID", "0"))

HOF_UMBRAL = 5   # votos 🔥 para entrar al Hall of Fame

CATEGORIAS = {
    "operacion": ("⚔️", "Operación",    0xB48C14),
    "habilidad": ("🎯", "Habilidad",     0x1E50A0),
    "fail":      ("💀", "Fail Épico",   0xCC2222),
    "humor":     ("😂", "Humor / Meme", 0x2EB86B),
}

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".wmv", ".flv", ".gifv"}

URL_RE = re.compile(
    r"https?://(?:www\.)?(?:"
    r"youtube\.com/(?:watch|shorts|clip)|"
    r"youtu\.be/|"
    r"twitch\.tv/|"
    r"clips\.twitch\.tv/|"
    r"medal\.tv/|"
    r"streamable\.com/|"
    r"vimeo\.com/"
    r")\S+",
    re.IGNORECASE,
)


def _detectar_video(message: discord.Message):
    """Devuelve (tipo, url): tipo='file'|'url' o (None, None) si no hay video."""
    for att in message.attachments:
        ext = os.path.splitext(att.filename.lower())[1]
        if ext in VIDEO_EXTS:
            return "file", att.url
    m = URL_RE.search(message.content)
    if m:
        return "url", m.group(0)
    return None, None


def _stars(epico: int) -> str:
    if epico >= 10: return "🔥🔥🔥🔥🔥"
    if epico >= 7:  return "🔥🔥🔥🔥⭐"
    if epico >= 5:  return "🔥🔥🔥⭐⭐"
    if epico >= 3:  return "🔥🔥⭐⭐⭐"
    if epico >= 1:  return "🔥⭐⭐⭐⭐"
    return "⭐⭐⭐⭐⭐"


# ══════════════════════════════════════════════════════
#  VIEW: SELECTOR DE CATEGORÍA (no persistente)
# ══════════════════════════════════════════════════════

class CategoriaVideoView(discord.ui.View):
    def __init__(self, uploader: discord.Member, video_url: str,
                 msg_original: discord.Message, tipo: str):
        super().__init__(timeout=120)
        self.uploader     = uploader
        self.video_url    = video_url
        self.msg_original = msg_original
        self.tipo         = tipo
        self.msg_selector = None
        self.publicado    = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.uploader.id:
            await interaction.response.send_message(
                "❌ Solo quien subió el video puede elegir la categoría.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        try:
            if self.msg_selector:
                await self.msg_selector.delete()
        except Exception:
            pass

    async def _publicar(self, interaction: discord.Interaction, cat_key: str):
        if self.publicado:
            return
        self.publicado = True
        self.stop()

        cat_emoji, cat_nombre, cat_color = CATEGORIAS[cat_key]

        try:
            if self.msg_selector:
                await self.msg_selector.delete()
        except Exception:
            pass

        if self.tipo == "url":
            desc = f"🎬 Subido por {self.uploader.mention}\n{self.video_url}"
        else:
            desc = (
                f"🎬 Subido por {self.uploader.mention}\n"
                f"[📎 Ver video adjunto]({self.video_url})"
            )

        embed = discord.Embed(
            title=f"{cat_emoji}  {cat_nombre.upper()}",
            description=desc,
            color=cat_color,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="🔥 Épico", value="**0**", inline=True)
        embed.add_field(name="👍 Bueno", value="**0**", inline=True)
        embed.add_field(name="💀 Fail",  value="**0**", inline=True)
        embed.add_field(name="⭐ Rating", value=_stars(0), inline=False)
        embed.set_footer(text=f"Clan Lord · {ahora_fmt()} · Vota con los botones de abajo")

        msg_embed = await interaction.channel.send(embed=embed, view=VotacionVideoView())

        videos = cargar("videos.json")
        videos[str(msg_embed.id)] = {
            "uploader_id": str(self.uploader.id),
            "categoria":   cat_key,
            "channel_id":  str(interaction.channel.id),
            "video_url":   self.video_url,
            "tipo":        self.tipo,
            "fecha":       ahora_fmt(),
            "votos":       {},
            "hall_of_fame": False,
        }
        guardar("videos.json", videos)

        sumar_puntos(str(self.uploader.id), 2, f"Clip publicado — {cat_nombre}")
        await interaction.response.send_message(
            f"✅ ¡Clip publicado en **{cat_nombre}**! +2 puntos de honor.", ephemeral=True
        )

    @discord.ui.button(label="⚔️ Operación",  style=discord.ButtonStyle.primary,   row=0)
    async def cat_op(self, i, _):   await self._publicar(i, "operacion")

    @discord.ui.button(label="🎯 Habilidad",   style=discord.ButtonStyle.primary,   row=0)
    async def cat_hab(self, i, _):  await self._publicar(i, "habilidad")

    @discord.ui.button(label="💀 Fail",         style=discord.ButtonStyle.danger,    row=0)
    async def cat_fail(self, i, _): await self._publicar(i, "fail")

    @discord.ui.button(label="😂 Humor",         style=discord.ButtonStyle.success,   row=0)
    async def cat_hum(self, i, _):  await self._publicar(i, "humor")


# ══════════════════════════════════════════════════════
#  VIEW: VOTACIÓN (persistente)
# ══════════════════════════════════════════════════════

class VotacionVideoView(discord.ui.View):
    def __init__(self, epico=0, bueno=0, fail=0):
        super().__init__(timeout=None)
        self.children[0].label = f"🔥 Épico  {epico}"
        self.children[1].label = f"👍 Bueno  {bueno}"
        self.children[2].label = f"💀 Fail   {fail}"

    @discord.ui.button(label="🔥 Épico  0", style=discord.ButtonStyle.danger,    custom_id="gl_vid_epico")
    async def votar_epico(self, interaction, _): await self._votar(interaction, "epico")

    @discord.ui.button(label="👍 Bueno  0", style=discord.ButtonStyle.success,   custom_id="gl_vid_bueno")
    async def votar_bueno(self, interaction, _): await self._votar(interaction, "bueno")

    @discord.ui.button(label="💀 Fail   0", style=discord.ButtonStyle.secondary, custom_id="gl_vid_fail")
    async def votar_fail(self, interaction, _):  await self._votar(interaction, "fail")

    async def _votar(self, interaction: discord.Interaction, tipo: str):
        videos = cargar("videos.json")
        msg_id = str(interaction.message.id)
        uid    = str(interaction.user.id)

        if msg_id not in videos:
            return await interaction.response.send_message("❌ Video no registrado.", ephemeral=True)

        votos = videos[msg_id].get("votos", {})

        if votos.get(uid) == tipo:
            del votos[uid]
            respuesta = "↩️ Voto retirado."
        else:
            votos[uid] = tipo
            respuesta = "✅ ¡Voto registrado!"

        videos[msg_id]["votos"] = votos
        guardar("videos.json", videos)

        epico = sum(1 for v in votos.values() if v == "epico")
        bueno = sum(1 for v in votos.values() if v == "bueno")
        fail  = sum(1 for v in votos.values() if v == "fail")

        # Título dinámico según votos épico acumulados
        embed = interaction.message.embeds[0]
        base = embed.title
        for badge in (" 🔥 CLIP DEL MES", " 🏅 DESTACADO"):
            base = base.replace(badge, "")
        if epico >= 10:
            embed.title = base + " 🔥 CLIP DEL MES"
        elif epico >= 5:
            embed.title = base + " 🏅 DESTACADO"
        else:
            embed.title = base

        embed.set_field_at(0, name="🔥 Épico", value=f"**{epico}**", inline=True)
        embed.set_field_at(1, name="👍 Bueno", value=f"**{bueno}**", inline=True)
        embed.set_field_at(2, name="💀 Fail",  value=f"**{fail}**",  inline=True)
        embed.set_field_at(3, name="⭐ Rating", value=_stars(epico), inline=False)

        nueva_view = VotacionVideoView(epico, bueno, fail)
        await interaction.response.edit_message(embed=embed, view=nueva_view)
        await interaction.followup.send(respuesta, ephemeral=True)

        # Dar puntos al uploader por votos épicos recibidos
        if tipo == "epico":
            uploader_id = videos[msg_id].get("uploader_id")
            if uploader_id and uploader_id != uid:
                sumar_puntos(uploader_id, 1, "Voto épico recibido en un clip")

        # Hall of Fame
        if epico >= HOF_UMBRAL and not videos[msg_id].get("hall_of_fame"):
            videos[msg_id]["hall_of_fame"] = True
            guardar("videos.json", videos)
            await self._publicar_hof(interaction, videos[msg_id], msg_id, epico)

    async def _publicar_hof(self, interaction: discord.Interaction,
                             video: dict, msg_id: str, epico: int):
        config    = cargar("config.json")
        hof_id    = config.get("canal_hof_id")
        if not hof_id:
            return
        canal_hof = interaction.guild.get_channel(int(hof_id))
        if not canal_hof:
            return
        cat_emoji = CATEGORIAS.get(video.get("categoria", "habilidad"), ("🎬",))[0]
        embed = discord.Embed(
            title=f"🏆  HALL OF FAME  {cat_emoji}  🎬",
            description=(
                f"<@{video['uploader_id']}> alcanzó **{epico} votos 🔥** y entra al Hall of Fame.\n\n"
                f"[🎬 Ver clip](https://discord.com/channels/"
                f"{interaction.guild.id}/{video['channel_id']}/{msg_id})"
            ),
            color=0xFFD700,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Clan Lord · Hall of Fame · Clips · {ahora_fmt()}")
        await canal_hof.send(embed=embed)


# ══════════════════════════════════════════════════════
#  COG
# ══════════════════════════════════════════════════════

class Videos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clip_semana.start()

    def cog_unload(self):
        self.clip_semana.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or not CANAL_VIDEOS_ID:
            return
        if message.channel.id != CANAL_VIDEOS_ID:
            return

        tipo, url = _detectar_video(message)

        if not tipo:
            try:
                await message.delete()
            except Exception:
                pass
            await message.channel.send(
                f"🎬 {message.author.mention} — Aquí solo se permiten videos o clips "
                "(archivo mp4/mov/webm o enlace de YouTube/Twitch/Medal.tv).",
                delete_after=8,
            )
            return

        view = CategoriaVideoView(message.author, url, message, tipo)
        selector = await message.channel.send(
            f"🎬 {message.author.mention} — **¿Qué categoría le pones a tu clip?**\n"
            "*(Tienes 2 minutos para elegir o se elimina el selector)*",
            view=view,
        )
        view.msg_selector = selector

    # ── Clip de la semana (cada domingo a las 20:00) ──────────────────────────

    @tasks.loop(hours=168)
    async def clip_semana(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        config    = cargar("config.json")
        hof_id    = config.get("canal_hof_id")
        if not hof_id:
            return
        canal_hof = guild.get_channel(int(hof_id))
        if not canal_hof:
            return

        videos = cargar("videos.json")
        hace_7_dias = datetime.datetime.now() - datetime.timedelta(days=7)

        candidatos = []
        for msg_id, video in videos.items():
            try:
                fecha = datetime.datetime.strptime(video["fecha"], "%d/%m/%Y %H:%M")
            except Exception:
                continue
            if fecha >= hace_7_dias:
                epico = sum(1 for v in video.get("votos", {}).values() if v == "epico")
                bueno = sum(1 for v in video.get("votos", {}).values() if v == "bueno")
                candidatos.append((msg_id, video, epico * 2 + bueno, epico, bueno))

        if not candidatos:
            return

        ganador_id, ganador, _, epico, bueno = max(candidatos, key=lambda x: x[2])
        fail = sum(1 for v in ganador.get("votos", {}).values() if v == "fail")
        cat_key   = ganador.get("categoria", "habilidad")
        cat_emoji = CATEGORIAS.get(cat_key, ("🎬",))[0]
        cat_nom   = CATEGORIAS.get(cat_key, ("", "Desconocida"))[1]

        embed = discord.Embed(
            title="🎬  CLIP DE LA SEMANA  🏆",
            description=(
                f"{cat_emoji} Categoría: **{cat_nom}**\n"
                f"🎮 Subido por <@{ganador['uploader_id']}>\n\n"
                f"🔥 {epico}  ·  👍 {bueno}  ·  💀 {fail}\n"
                f"{_stars(epico)}\n\n"
                f"[🎬 Ver clip](https://discord.com/channels/"
                f"{guild.id}/{ganador['channel_id']}/{ganador_id})"
            ),
            color=0xFFD700,
            timestamp=datetime.datetime.now(),
        )
        hace = hace_7_dias.strftime("%d/%m")
        hoy  = datetime.datetime.now().strftime("%d/%m/%Y")
        embed.set_footer(text=f"Clan Lord · Semana del {hace} al {hoy}")
        await canal_hof.send(embed=embed)

        sumar_puntos(ganador["uploader_id"], 10, "Clip de la Semana — bonus automático")

    @clip_semana.before_loop
    async def before_clip_semana(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        days_until_sunday = (6 - now.weekday()) % 7 or 7
        target = (now + datetime.timedelta(days=days_until_sunday)).replace(
            hour=20, minute=0, second=0, microsecond=0
        )
        await discord.utils.sleep_until(target)


async def setup(bot):
    await bot.add_cog(Videos(bot))
