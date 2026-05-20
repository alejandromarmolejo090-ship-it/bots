"""Cog: Sistema de fotos — votación, categorías, Hall of Fame y foto de la semana."""
import discord
from discord.ext import commands, tasks
import datetime, io, os, sys, random
import aiohttp
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, ahora_fmt, COLOR_MILITAR, COLOR_VERDE, COLOR_ROJO

GUILD_ID       = int(os.getenv("GUILD_ID", "0"))
CANAL_FOTOS_ID = int(os.getenv("CANAL_FOTOS_ID", "0"))

HOF_UMBRAL = 5   # votos 🔥 para entrar al Hall of Fame

REGANOS_FOTOS = [
    "🎖️ {mention} ¡RECLUTA DE MIERDA! ¿Un texto en el canal de FOTOS? ¡Aprende a leer, pedazo de analfabeto!",
    "🎖️ {mention} ¡Por los cañones de Bolívar y la concha de su madre! ¿TEXTO en el canal de IMÁGENES? ¡Imbécil redomado!",
    "🎖️ {mention} ¡Me cago en todo tu árbol genealógico! ¿Dónde está la foto, animal? ¡Texto aquí y te mando a pelar papas con los dientes!",
    "🎖️ {mention} ¡FOTO O CIERRA ESE HOCICO! Tu mensaje fue destruido igual que tus esperanzas de ser útil algún día.",
    "🎖️ {mention} ¡Este canal no es tu puto chat de amigos, pedazo de engendro! ¡Sube una imagen o DESAPARECE!",
    "🎖️ {mention} ¡Treinta años en el ejército y nunca vi tanta idiotez! ¿Texto en fotos? ¡Eres un desastre ambulante!",
    "🎖️ {mention} ¡Mensaje destruido, dignidad destruida, cerebro buscado! Solo fotos aquí, ¡so animal de monte!",
    "🎖️ {mention} ¡Grandísimo imbécil! ¿Escribir aquí? ¡Este canal es de FOTOS, no de tus novelitas baratas de mierda!",
    "🎖️ {mention} ¡Por los cojones del mismísimo diablo! ¿Qué clase de cerebro de gambas tienes para escribir aquí?",
    "🎖️ {mention} ¡Canal de FOTOS, pedazo de idiota! F-O-T-O-S. ¿Necesitas que te lo deletree más lento, bestia?",
    "🎖️ {mention} ¡Me tienes hasta los huevos! ¡Texto en el canal de fotos! ¡Eres tan inútil que me duele mirarte!",
    "🎖️ {mention} ¡Qué atrevimiento tan colosal de mierda! ¿Texto aquí? ¡Te voy a mandar a guardia nocturna por idiota!",
    "🎖️ {mention} ¡Recluta de pacotilla! Si la estupidez fuera una operación militar tú serías el único superviviente. ¡FOTO O NADA!",
    "🎖️ {mention} ¡Joder con el imbécil! ¿Alguien le puede explicar a este animal que las fotos llevan IMAGEN? ¡FUERA!",
    "🎖️ {mention} ¡Qué puta vergüenza! Texto en el canal de fotos. ¡Si tuvieras dos cerebros los dos estarían solos!",
    "🎖️ {mention} ¡Cállate ese choclo que tienes por boca y sube una FOTO, so inútil de los cojones!",
    "🎖️ {mention} ¡Eres tan bruto que probablemente le mandas audios a los sordos! ¡FOTO O LARGARTE, CABRÓN!",
    "🎖️ {mention} ¡Me cago en tu linaje, en tu reclutamiento y en quien te dejó entrar al clan! ¡Solo fotos, animal!",
    "🎖️ {mention} ¡Pedazo de neanderthal digitalizado! ¿No sabes lo que es una FOTO? ¡Mensaje eliminado con asco!",
    "🎖️ {mention} ¡Dios mío del cielo y de la mierda! ¿Texto en el canal de fotos? ¡Eres mi peor pesadilla hecha recluta!",
    "🎖️ {mention} ¡Habrase visto semejante inútil! Imagen. Foto. Captura. ¡Algo con PÍXELES, pedazo de cerebro de mosquito!",
    "🎖️ {mention} ¡Qué manera tan espectacular de demostrar que eres un completo idiota! ¡FOTO, no texto, bestia!",
    "🎖️ {mention} ¡Eres la razón por la que los generales se dan a la bebida! ¡Solo fotos aquí, so imbécil!",
    "🎖️ {mention} ¡Canal de fotos significa FOTOS, no tus pensamientos de mierda escritos! ¡A callar y a subir imagen!",
    "🎖️ {mention} ¡Maldita sea tu estampa y la de quien te enseñó a usar Discord! ¡FOTO O FUERA, PENDEJO!",
    "🎖️ {mention} ¡Texto en fotos! ¡Si fueras explosivo no tendrías ni para levantar una ceja de lo inútil que eres!",
    "🎖️ {mention} ¡Qué asco de recluta! ¿Acaso crees que las palabras tienen píxeles? ¡IMAGEN, ANIMAL DE MONTE!",
    "🎖️ {mention} ¡Oye, cabeza de chorlito rematado! Aquí van FOTOS. ¿O también eso se te escapa, pedazo de inútil?",
    "🎖️ {mention} ¡Soldado de tres al cuarto! Tu mensaje fue ejecutado igual que tus neuronas: sin contemplaciones.",
    "🎖️ {mention} ¡Por la cresta y por todo lo que hay debajo! ¿Texto en fotos? ¡Eres mi deshonra como comandante!",
    "🎖️ {mention} ¡Increíble! ¡Ni los reclutas más torpes cometen esta cagada tan monumental! ¡Solo fotos, imbécil!",
    "🎖️ {mention} ¡Qué nivel tan abismal de estupidez! ¿Texto en el canal de fotos? ¡Vete a escribir a un cuaderno, bestia!",
    "🎖️ {mention} ¡Me has arruinado el día con tu incompetencia descomunal! ¡FOTO o te mando a fregar el cuartel!",
    "🎖️ {mention} ¡Eres tan lento que si compitiera tu cerebro con un caracol, ganaría el caracol por paliza!  ¡FOTO!",
    "🎖️ {mention} ¡Cabrón sin remedio! ¿Qué parte de canal de FOTOS no entra en esa cabeza hueca que tienes?",
    "🎖️ {mention} ¡Texto aquí! ¡Dios mío! ¡Eres tan inútil que si te pusieran a vigilar un espejo te escaparías!",
    "🎖️ {mention} ¡Pedazo de fenómeno de la naturaleza! Solo en este clan existe alguien capaz de escribir texto en fotos.",
    "🎖️ {mention} ¡Voy a necesitar una copa después de esto! ¿TEXTO? ¡Canal de fotos, so descerebrado de mierda!",
    "🎖️ {mention} ¡Eres la prueba viviente de que la imbecilidad no tiene límite! ¡SOLO FOTOS, PEDAZO DE ANIMAL!",
    "🎖️ {mention} ¡Qué inútil tan gloriosamente completo! Tu texto fue borrado. Tu dignidad también. ¡Sube una foto, bestia!",
    "🎖️ {mention} ¡Recluta de los cojones! Si pusiera tu cerebro en un dedal sobraría sitio para un elefante. ¡FOTO!",
    "🎖️ {mention} ¡Maldito iletrado! ¿No decía CANAL DE FOTOS? ¿O también leer está fuera de tus capacidades, animal?",
    "🎖️ {mention} ¡Cómo es posible tanta estupidez en un ser humano! ¡Mensaje liquidado, igual que tu autoestima debería estar!",
    "🎖️ {mention} ¡Grandísimo bobo! Tus palabras no valen ni el aire que ocupan aquí. ¡Imagen o silencio, pedazo de necio!",
    "🎖️ {mention} ¡Que Dios me dé paciencia porque fuerzas ya me están faltando! ¡FOTO, NO TEXTO, SO IDIOTA!",
    "🎖️ {mention} ¡Eres tan obtuso que si te pusieran de ángulo en geometría serías el más recto del cementerio! ¡FOTO!",
    "🎖️ {mention} ¡Habrase visto semejante esperpento! Texto en fotos. ¡Eres mi mayor fracaso como comandante, cabrón!",
    "🎖️ {mention} ¡Me cago en la pólvora que te disparó al mundo! ¿TEXTO? ¡Solo fotos aquí, pedazo de desastre con piernas!",
    "🎖️ {mention} ¡Increíble, impresionante e imperdonable! ¡Texto en el canal de fotos! ¡FUERA DE AQUÍ, IMBÉCIL CÓSMICO!",
    "🎖️ {mention} ¡Eres tan inútil que si te mandaran a comprar munición volverías con chicles! ¡FOTO O NADA, ANIMAL!",
    "🎖️ {mention} ¡Qué espectáculo tan dantesco de incompetencia! Solo imagen aquí. ¡A ver si la próxima vez lo entiende, bestia!",
]

CATEGORIAS = {
    "operacion":     ("⚔️", "Operación",       0xB48C14),
    "entrenamiento": ("🎯", "Entrenamiento",    0x1E50A0),
    "meme":          ("😂", "Meme",             0x2EB86B),
    "epico":         ("⭐", "Momento Épico",    0xB42828),
}


# ══════════════════════════════════════════════════════
#  VIEW: SELECCIÓN DE CATEGORÍA (no persistente)
# ══════════════════════════════════════════════════════

class CategoriaView(discord.ui.View):
    def __init__(self, uploader: discord.Member, img_bytes: bytes, img_filename: str, msg_original: discord.Message):
        super().__init__(timeout=120)
        self.uploader      = uploader
        self.img_bytes     = img_bytes
        self.img_filename  = img_filename
        self.msg_original  = msg_original
        self.msg_selector  = None   # referencia al mensaje con los botones
        self.publicado     = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.uploader.id:
            await interaction.response.send_message(
                "❌ Solo quien subió la foto puede elegir la categoría.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for msg in [self.msg_original, self.msg_selector]:
            try:
                if msg:
                    await msg.delete()
            except Exception:
                pass

    async def _publicar(self, interaction: discord.Interaction, cat_key: str):
        if self.publicado:
            return
        self.publicado = True
        self.stop()

        cat_emoji, cat_nombre, cat_color = CATEGORIAS[cat_key]

        # Borrar original y selector
        for msg in [self.msg_original, self.msg_selector]:
            try:
                if msg:
                    await msg.delete()
            except Exception:
                pass

        # Construir embed
        embed = discord.Embed(
            title=f"{cat_emoji}  {cat_nombre.upper()}",
            description=f"📸 Subida por {self.uploader.mention}",
            color=cat_color,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="🔥 Épico",  value="**0**", inline=True)
        embed.add_field(name="👍 Buena",  value="**0**", inline=True)
        embed.add_field(name="😂 Meme",   value="**0**", inline=True)
        embed.set_image(url=f"attachment://{self.img_filename}")
        embed.set_footer(text=f"Clan Lord · {ahora_fmt()}")

        archivo = discord.File(io.BytesIO(self.img_bytes), filename=self.img_filename)
        msg_foto = await interaction.channel.send(
            embed=embed,
            file=archivo,
            view=VotacionView(),
        )

        # Guardar en fotos.json
        fotos = cargar("fotos.json")
        fotos[str(msg_foto.id)] = {
            "uploader_id": str(self.uploader.id),
            "categoria":   cat_key,
            "channel_id":  str(interaction.channel.id),
            "img_filename": self.img_filename,
            "fecha":       ahora_fmt(),
            "votos":       {},
            "hall_of_fame": False,
        }
        guardar("fotos.json", fotos)

        await interaction.response.send_message("✅ ¡Foto publicada!", ephemeral=True)

    @discord.ui.button(label="⚔️ Operación",    style=discord.ButtonStyle.primary,   row=0)
    async def cat_op(self, interaction, _):   await self._publicar(interaction, "operacion")

    @discord.ui.button(label="🎯 Entrenamiento", style=discord.ButtonStyle.primary,   row=0)
    async def cat_ent(self, interaction, _):  await self._publicar(interaction, "entrenamiento")

    @discord.ui.button(label="😂 Meme",          style=discord.ButtonStyle.success,   row=0)
    async def cat_mem(self, interaction, _):  await self._publicar(interaction, "meme")

    @discord.ui.button(label="⭐ Momento Épico", style=discord.ButtonStyle.danger,    row=0)
    async def cat_epi(self, interaction, _):  await self._publicar(interaction, "epico")


# ══════════════════════════════════════════════════════
#  VIEW: VOTACIÓN (persistente)
# ══════════════════════════════════════════════════════

class VotacionView(discord.ui.View):
    def __init__(self, fires=0, goods=0, memes=0):
        super().__init__(timeout=None)
        # Actualizar etiquetas con conteos actuales
        self.children[0].label = f"🔥 Épico  {fires}"
        self.children[1].label = f"👍 Buena  {goods}"
        self.children[2].label = f"😂 Meme   {memes}"

    @discord.ui.button(label="🔥 Épico  0", style=discord.ButtonStyle.danger,     custom_id="gl_foto_fire")
    async def votar_fire(self, interaction: discord.Interaction, _): await self._votar(interaction, "fire")

    @discord.ui.button(label="👍 Buena  0", style=discord.ButtonStyle.success,    custom_id="gl_foto_good")
    async def votar_good(self, interaction: discord.Interaction, _): await self._votar(interaction, "good")

    @discord.ui.button(label="😂 Meme   0", style=discord.ButtonStyle.secondary,  custom_id="gl_foto_meme")
    async def votar_meme(self, interaction: discord.Interaction, _): await self._votar(interaction, "meme")

    async def _votar(self, interaction: discord.Interaction, tipo: str):
        fotos  = cargar("fotos.json")
        msg_id = str(interaction.message.id)
        uid    = str(interaction.user.id)

        if msg_id not in fotos:
            return await interaction.response.send_message("❌ Foto no registrada.", ephemeral=True)

        votos = fotos[msg_id].get("votos", {})

        if votos.get(uid) == tipo:
            del votos[uid]
            respuesta = "↩️ Voto retirado."
        else:
            votos[uid] = tipo
            respuesta = "✅ ¡Voto registrado!"

        fotos[msg_id]["votos"] = votos
        guardar("fotos.json", fotos)

        fires = sum(1 for v in votos.values() if v == "fire")
        goods = sum(1 for v in votos.values() if v == "good")
        memes = sum(1 for v in votos.values() if v == "meme")

        # Actualizar embed y botones
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="🔥 Épico",  value=f"**{fires}**", inline=True)
        embed.set_field_at(1, name="👍 Buena",  value=f"**{goods}**", inline=True)
        embed.set_field_at(2, name="😂 Meme",   value=f"**{memes}**", inline=True)

        nueva_view = VotacionView(fires, goods, memes)
        await interaction.response.edit_message(embed=embed, view=nueva_view)

        await interaction.followup.send(respuesta, ephemeral=True)

        # ¿Entra al Hall of Fame?
        if fires >= HOF_UMBRAL and not fotos[msg_id].get("hall_of_fame"):
            fotos[msg_id]["hall_of_fame"] = True
            guardar("fotos.json", fotos)
            await self._publicar_hof(interaction, fotos[msg_id], msg_id, fires)

    async def _publicar_hof(self, interaction: discord.Interaction, foto: dict, msg_id: str, fires: int):
        config  = cargar("config.json")
        hof_id  = config.get("canal_hof_id")
        if not hof_id:
            return
        canal_hof = interaction.guild.get_channel(int(hof_id))
        if not canal_hof:
            return

        cat_emoji = CATEGORIAS.get(foto.get("categoria", "epico"), ("⭐",))[0]
        embed = discord.Embed(
            title=f"🏆  HALL OF FAME  {cat_emoji}",
            description=(
                f"<@{foto['uploader_id']}> alcanzó **{fires} votos 🔥** y entra al Hall of Fame.\n\n"
                f"[📸 Ver foto original](https://discord.com/channels/{interaction.guild.id}/{foto['channel_id']}/{msg_id})"
            ),
            color=0xFFD700,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Clan Lord · Hall of Fame · {ahora_fmt()}")
        await canal_hof.send(embed=embed)


# ══════════════════════════════════════════════════════
#  COG
# ══════════════════════════════════════════════════════

class Fotos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.foto_semana.start()

    def cog_unload(self):
        self.foto_semana.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        # Garantizar permiso de borrado en canal de fotos
        canal_fotos = guild.get_channel(CANAL_FOTOS_ID)
        if canal_fotos:
            try:
                await canal_fotos.set_permissions(
                    guild.me,
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                )
            except Exception:
                pass
        await self._asegurar_canal_hof(guild)

    async def _asegurar_canal_hof(self, guild: discord.Guild):
        config = cargar("config.json")
        if config.get("canal_hof_id"):
            return  # ya existe
        canal_fotos = guild.get_channel(CANAL_FOTOS_ID)
        category    = canal_fotos.category if canal_fotos else None
        try:
            canal_hof = await guild.create_text_channel(
                "hall-of-fame",
                category=category,
                topic="Las mejores fotos del clan Lord",
                reason="Creado automaticamente por General Lord",
            )
            config["canal_hof_id"] = str(canal_hof.id)
            guardar("config.json", config)
            print("[General Lord] Canal Hall of Fame creado.")
        except Exception as e:
            print(f"[General Lord] No se pudo crear canal HoF: {type(e).__name__}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or message.channel.id != CANAL_FOTOS_ID:
            return

        # Filtrar mensajes sin imagen
        imagenes = [
            a for a in message.attachments
            if a.content_type and a.content_type.startswith("image/")
        ]
        if not imagenes:
            try:
                await message.delete()
            except Exception:
                pass
            try:
                regano = random.choice(REGANOS_FOTOS).format(mention=message.author.mention)
                await message.channel.send(regano, delete_after=10)
            except Exception:
                pass
            return

        # Descargar la primera imagen antes de mostrar el selector
        att = imagenes[0]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(att.url) as resp:
                    if resp.status != 200:
                        return
                    img_bytes = await resp.read()
        except Exception:
            return

        view = CategoriaView(message.author, img_bytes, att.filename, message)
        selector = await message.channel.send(
            f"📂 {message.author.mention} — **¿Qué categoría le pones a tu foto?**\n"
            "*(Tienes 2 minutos para elegir, si no se borra automáticamente)*",
            view=view,
        )
        view.msg_selector = selector

    # ── Foto de la semana (cada lunes a las 12:00) ──────────────────

    @tasks.loop(hours=168)
    async def foto_semana(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        config   = cargar("config.json")
        hof_id   = config.get("canal_hof_id")
        if not hof_id:
            return
        canal_hof = guild.get_channel(int(hof_id))
        if not canal_hof:
            return

        fotos = cargar("fotos.json")
        semana_pasada = datetime.datetime.now() - datetime.timedelta(days=7)

        candidatas = []
        for msg_id, foto in fotos.items():
            try:
                fecha_foto = datetime.datetime.strptime(foto["fecha"], "%d/%m/%Y %H:%M")
            except Exception:
                continue
            if fecha_foto >= semana_pasada:
                total_votos = len(foto.get("votos", {}))
                fires = sum(1 for v in foto.get("votos", {}).values() if v == "fire")
                candidatas.append((msg_id, foto, fires * 2 + total_votos))

        if not candidatas:
            return

        ganadora_id, ganadora, _ = max(candidatas, key=lambda x: x[2])
        fires = sum(1 for v in ganadora.get("votos", {}).values() if v == "fire")
        goods = sum(1 for v in ganadora.get("votos", {}).values() if v == "good")
        memes = sum(1 for v in ganadora.get("votos", {}).values() if v == "meme")

        cat_emoji = CATEGORIAS.get(ganadora.get("categoria", "epico"), ("⭐",))[0]
        embed = discord.Embed(
            title="📸  FOTO DE LA SEMANA",
            description=(
                f"{cat_emoji} Categoría: **{CATEGORIAS.get(ganadora.get('categoria','epico'), ('','Desconocida'))[1]}**\n"
                f"📸 Subida por <@{ganadora['uploader_id']}>\n\n"
                f"🔥 {fires}  ·  👍 {goods}  ·  😂 {memes}\n\n"
                f"[Ver foto original](https://discord.com/channels/{guild.id}/{ganadora['channel_id']}/{ganadora_id})"
            ),
            color=0xFFD700,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Clan Lord · Semana del {semana_pasada.strftime('%d/%m')} al {datetime.datetime.now().strftime('%d/%m/%Y')}")
        await canal_hof.send(embed=embed)

    @foto_semana.before_loop
    async def before_foto_semana(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        # Próximo lunes a las 12:00
        days_until_monday = (7 - now.weekday()) % 7 or 7
        target = (now + datetime.timedelta(days=days_until_monday)).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        await discord.utils.sleep_until(target)


async def setup(bot):
    await bot.add_cog(Fotos(bot))
