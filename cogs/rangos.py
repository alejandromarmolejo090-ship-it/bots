"""Cog: Rangos — Jerarquía oficial del clan."""
import discord
from discord.ext import commands
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, COLOR_MILITAR

GUILD_ID        = int(os.getenv("GUILD_ID", "0"))
CANAL_RANGOS_ID = 1489366416636514354


class Rangos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return

        canal = guild.get_channel(CANAL_RANGOS_ID)
        if not canal:
            print(f"[Rangos] Canal {CANAL_RANGOS_ID} no encontrado.")
            return

        data = cargar("rangos.json")
        msg_id = data.get("msg_id")
        if msg_id:
            try:
                await canal.fetch_message(int(msg_id))
                print("[Rangos] Contenido ya publicado — sin cambios.")
                return
            except (discord.NotFound, discord.HTTPException):
                pass

        await self._publicar(canal)

    async def _publicar(self, canal: discord.TextChannel):
        await canal.purge(limit=50)

        # ── CABECERA MOTIVACIONAL ─────────────────────────────────────────────
        e0 = discord.Embed(title="🎖️  SISTEMA DE RANGOS  —  LORD", color=COLOR_MILITAR)
        e0.description = (
            "En nuestro clan, cada rango representa mucho más que un título: es el reflejo del "
            "esfuerzo, la constancia y el compromiso que cada miembro demuestra día a día. "
            "Ascender no es solo una meta, es un camino que se construye con **disciplina**, "
            "**trabajo en equipo** y la voluntad de superarse constantemente.\n\n"
            "Cada misión cumplida, cada apoyo brindado a un compañero y cada logro alcanzado "
            "te acerca un paso más hacia el siguiente nivel. Aquí valoramos a quienes no se "
            "rinden, a quienes buscan mejorar y a quienes inspiran a otros a hacer lo mismo.\n\n"
            "Recuerda que todo gran comandante comenzó siendo recluta. Tu progreso depende de "
            "tu actitud, tu dedicación y tu capacidad para crecer dentro del clan. Sigue "
            "adelante, demuestra de lo que eres capaz y alcanza el rango que te corresponde.\n\n"
            "> 🔥 **El siguiente nivel te espera… ¿estás listo para conquistarlo?**"
        )
        e0.set_footer(text="LORD  ·  Todo gran comandante comenzó siendo recluta")
        first = await canal.send(embed=e0)

        # ── RANGOS DE TROPA ───────────────────────────────────────────────────
        e1 = discord.Embed(title="🪖  RANGOS DE TROPA", color=0x2C3A47)
        e1.description = (
            "*La base del clan. Aquí se forja el carácter, la disciplina y el trabajo en equipo.*\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e1.add_field(
            name="🔘  Nivel I",
            value="**Aspirante**\n`Asp.`",
            inline=True,
        )
        e1.add_field(
            name="🔘  Nivel II",
            value="**Recluta**\n`Rcl.`",
            inline=True,
        )
        e1.add_field(name="​", value="​", inline=True)
        e1.add_field(
            name="🟡  Nivel III",
            value="**Soldado Raso**\n`Sld. R.`",
            inline=True,
        )
        e1.add_field(
            name="🟡  Nivel IV",
            value="**Soldado**\n`Sld.`",
            inline=True,
        )
        e1.add_field(
            name="🟡  Nivel V",
            value="**Soldado Primero**\n`Sld. 1`",
            inline=True,
        )
        e1.add_field(
            name="🟠  Nivel VI",
            value="**Cabo**\n`Cb.`",
            inline=True,
        )
        e1.add_field(
            name="🟠  Nivel VII",
            value="**Cabo Primero**\n`Cb. 1`",
            inline=True,
        )
        e1.add_field(
            name="🔶  Nivel VIII",
            value="**Sargento**\n`Sgt.`",
            inline=True,
        )
        e1.set_footer(text="8 rangos  ·  Niveles I — VIII")
        await canal.send(embed=e1)

        # ── RANGOS DE SUPERIORES ──────────────────────────────────────────────
        e2 = discord.Embed(title="⭐  RANGOS DE SUPERIORES", color=0x1B5E20)
        e2.description = (
            "*Reservados para quienes han demostrado liderazgo, conocimiento táctico "
            "y compromiso sostenido con el clan.*\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e2.add_field(
            name="⭐  Nivel IX",
            value="**Teniente**\n`Tte.`",
            inline=True,
        )
        e2.add_field(
            name="⭐⭐  Nivel X",
            value="**Capitán**\n`Cpt.`",
            inline=True,
        )
        e2.add_field(
            name="⭐⭐⭐  Nivel XI",
            value="**Coronel**\n`Crnl.`",
            inline=True,
        )
        e2.set_footer(text="3 rangos  ·  Niveles IX — XI")
        await canal.send(embed=e2)

        # ── RANGO DE COMANDO ──────────────────────────────────────────────────
        e3 = discord.Embed(title="👑  RANGO DE COMANDO", color=0xB8860B)
        e3.description = (
            "*El rango más alto del clan. Máxima responsabilidad sobre las operaciones, "
            "la estrategia y el bienestar de todos los miembros.*\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e3.add_field(
            name="👑  Nivel XII",
            value="**Comandante**\n`Cmdt.`",
            inline=False,
        )
        e3.set_footer(text="Nivel XII  ·  Máxima jerarquía  ·  LORD")
        await canal.send(embed=e3)

        guardar("rangos.json", {"msg_id": str(first.id)})
        print(f"[Rangos] Publicado en #{canal.name}.")


async def setup(bot):
    await bot.add_cog(Rangos(bot))
