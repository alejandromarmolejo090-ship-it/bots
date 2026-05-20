"""Bot principal: General Lord."""
import discord
from discord.ext import commands
import asyncio, os, sys
from dotenv import load_dotenv

load_dotenv()

TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

sys.path.insert(0, os.path.dirname(__file__))
from utils import cargar, guardar, perfil_base, COLOR_MILITAR

COGS = [
    "cogs.paneles",
    "cogs.automaticos",
    "cogs.fotos",
    "cogs.protocolos",
    "cogs.cursos",
    "cogs.rangos",
    "cogs.videos",
    "cogs.encuestas",
    "cogs.instrucciones",
]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"[General Lord] Conectado como {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_member_join(member: discord.Member):
    perfiles = cargar("perfiles.json")
    uid = str(member.id)
    if uid not in perfiles:
        perfiles[uid] = perfil_base(member)
        guardar("perfiles.json", perfiles)


async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[General Lord] Cog cargado: {cog}")
        except Exception as e:
            print(f"[General Lord] Error cargando {cog}: {e}")


async def main():
    async with bot:
        await load_cogs()

        # Registrar views persistentes
        from cogs.paneles import ConfirmarAsistencia, ConfirmarEntrenamiento, PanelMandoView, PanelMiembrosView, AdminLimpiarView
        from cogs.fotos import VotacionView
        from cogs.videos import VotacionVideoView
        bot.add_view(VotacionVideoView())
        from cogs.encuestas import EncuestaView2, EncuestaView3, EncuestaView4, EncuestaCerradaView
        bot.add_view(EncuestaView2())
        bot.add_view(EncuestaView3())
        bot.add_view(EncuestaView4())
        bot.add_view(EncuestaCerradaView())
        from cogs.protocolos import ProtocoloHumoView, ProtocoloCallsignsView, ProtocoloZonasView, ProtocoloNavView, ProtocoloServidorView, ProtocoloModsView
        from cogs.cursos import CursoBasicoPublicView, CursoActivoView, DudaResueltaView, CursoAdminView
        bot.add_view(ConfirmarAsistencia())
        bot.add_view(ConfirmarEntrenamiento())
        bot.add_view(PanelMandoView())
        bot.add_view(PanelMiembrosView())
        bot.add_view(AdminLimpiarView())
        bot.add_view(VotacionView())
        bot.add_view(CursoBasicoPublicView())
        bot.add_view(DudaResueltaView())
        bot.add_view(CursoAdminView())
        bot.add_view(ProtocoloHumoView())
        bot.add_view(ProtocoloCallsignsView())
        bot.add_view(ProtocoloZonasView())
        bot.add_view(ProtocoloNavView())
        bot.add_view(ProtocoloServidorView())
        bot.add_view(ProtocoloModsView())
        for tipo in ("medico", "drones", "aviacion", "cqb", "zeus", "comando"):
            bot.add_view(CursoActivoView(tipo))

        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
