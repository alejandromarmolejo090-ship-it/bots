"""Cog: Comandos para miembros regulares."""
import discord
from discord.ext import commands
from discord import app_commands
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, ahora, ahora_fmt, obtener_perfil, COLOR_MILITAR, COLOR_VERDE, COLOR_ROJO

GUILD_ID = int(os.getenv("GUILD_ID", "0"))
CANAL_MANDO_ID = int(os.getenv("CANAL_MANDO_ID", "0"))


class AusenciaModal(discord.ui.Modal, title="📋 Solicitud de Ausencia"):
    motivo    = discord.ui.TextInput(label="Motivo de la ausencia", style=discord.TextStyle.paragraph, max_length=400)
    inicio    = discord.ui.TextInput(label="Fecha de inicio (DD/MM/AAAA)", max_length=20)
    fin       = discord.ui.TextInput(label="Fecha de regreso (DD/MM/AAAA)", max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        ausencias = cargar("ausencias.json")
        uid = str(interaction.user.id)
        if uid not in ausencias:
            ausencias[uid] = []
        ausencias[uid].append({
            "motivo": self.motivo.value,
            "inicio": self.inicio.value,
            "fin": self.fin.value,
            "fecha_solicitud": ahora_fmt(),
            "estado": "aprobada",
        })
        guardar("ausencias.json", ausencias)

        perfiles = cargar("perfiles.json")
        if uid in perfiles:
            perfiles[uid]["ausencias"] = perfiles[uid].get("ausencias", 0) + 1
            guardar("perfiles.json", perfiles)

        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            embed = discord.Embed(
                title="📋 Nueva Solicitud de Ausencia",
                color=COLOR_MILITAR,
                timestamp=datetime.datetime.now(),
            )
            embed.add_field(name="👤 Miembro", value=interaction.user.mention, inline=True)
            embed.add_field(name="📅 Inicio", value=self.inicio.value, inline=True)
            embed.add_field(name="📅 Regreso", value=self.fin.value, inline=True)
            embed.add_field(name="📝 Motivo", value=self.motivo.value, inline=False)
            await canal_mando.send(embed=embed)

        await interaction.response.send_message(
            "✅ Ausencia registrada correctamente. El mando ha sido notificado.", ephemeral=True
        )


class SolicitarModal(discord.ui.Modal, title="📩 Solicitud al Mando"):
    asunto   = discord.ui.TextInput(label="Asunto de la solicitud", max_length=80)
    detalle  = discord.ui.TextInput(label="Detalle completo", style=discord.TextStyle.paragraph, max_length=600)

    async def on_submit(self, interaction: discord.Interaction):
        solicitudes = cargar("solicitudes.json")
        uid = str(interaction.user.id)
        if uid not in solicitudes:
            solicitudes[uid] = []
        solicitudes[uid].append({
            "asunto": self.asunto.value,
            "detalle": self.detalle.value,
            "fecha": ahora_fmt(),
            "estado": "pendiente",
        })
        guardar("solicitudes.json", solicitudes)

        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            embed = discord.Embed(
                title=f"📩 Solicitud: {self.asunto.value}",
                description=self.detalle.value,
                color=COLOR_MILITAR,
                timestamp=datetime.datetime.now(),
            )
            embed.set_footer(text=f"De: {interaction.user.display_name}")
            await canal_mando.send(embed=embed)

        await interaction.response.send_message(
            "✅ Solicitud enviada al mando. Te responderán a la brevedad.", ephemeral=True
        )


class ReportarModal(discord.ui.Modal, title="🚨 Reportar Incidencia"):
    tipo     = discord.ui.TextInput(label="Tipo (disciplina/técnico/otro)", max_length=40)
    descripcion = discord.ui.TextInput(label="Descripción detallada", style=discord.TextStyle.paragraph, max_length=600)
    implicados  = discord.ui.TextInput(label="Personas implicadas (opcional)", required=False, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        reportes = cargar("reportes.json")
        uid = str(interaction.user.id)
        if uid not in reportes:
            reportes[uid] = []
        reportes[uid].append({
            "tipo": self.tipo.value,
            "descripcion": self.descripcion.value,
            "implicados": self.implicados.value,
            "fecha": ahora_fmt(),
        })
        guardar("reportes.json", reportes)

        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            embed = discord.Embed(
                title=f"🚨 Reporte: {self.tipo.value}",
                description=self.descripcion.value,
                color=COLOR_ROJO,
                timestamp=datetime.datetime.now(),
            )
            if self.implicados.value:
                embed.add_field(name="👥 Implicados", value=self.implicados.value, inline=False)
            embed.set_footer(text=f"Reportado por: {interaction.user.display_name}")
            await canal_mando.send(embed=embed)

        await interaction.response.send_message(
            "✅ Reporte enviado al mando de forma confidencial.", ephemeral=True
        )


class Miembros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Muestra tu perfil o el de otro miembro")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def perfil(self, interaction: discord.Interaction, miembro: discord.Member = None):
        target = miembro or interaction.user
        p = obtener_perfil(target)
        puntos_data = cargar("puntos.json")
        uid = str(target.id)
        puntos = puntos_data.get(uid, {}).get("puntos", p.get("puntos", 0))

        embed = discord.Embed(
            title=f"🪖 Perfil — {target.display_name}",
            color=COLOR_MILITAR,
            timestamp=datetime.datetime.now(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🎖️ Rango", value=p.get("rango", "Sin rango"), inline=True)
        embed.add_field(name="⭐ Puntos de Honor", value=str(puntos), inline=True)
        embed.add_field(name="🎯 Misiones", value=str(p.get("misiones", 0)), inline=True)
        embed.add_field(name="📅 Ausencias", value=str(p.get("ausencias", 0)), inline=True)
        embed.add_field(name="⚠️ Sanciones", value=str(p.get("sanciones", 0)), inline=True)
        embed.add_field(name="📆 Ingreso", value=p.get("fecha_ingreso", "—")[:10], inline=True)

        sanciones_data = cargar("sanciones.json")
        historial = sanciones_data.get(uid, [])
        activas = [s for s in historial if s.get("activa", True)]
        if activas:
            embed.add_field(
                name="🔴 Sanciones activas",
                value="\n".join(f"• {s['motivo']}" for s in activas[-3:]),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="mis-puntos", description="Consulta tu historial de puntos de honor")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def mis_puntos(self, interaction: discord.Interaction):
        puntos_data = cargar("puntos.json")
        uid = str(interaction.user.id)
        data = puntos_data.get(uid, {"puntos": 0, "historial": []})
        embed = discord.Embed(
            title=f"⭐ Puntos de Honor — {interaction.user.display_name}",
            color=COLOR_MILITAR,
        )
        embed.add_field(name="Total", value=f"**{data['puntos']} puntos**", inline=False)
        historial = data.get("historial", [])[-10:]
        if historial:
            lineas = [f"`{h['fecha']}` +{h['cantidad']} — {h['motivo']}" for h in reversed(historial)]
            embed.add_field(name="Últimos movimientos", value="\n".join(lineas), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ausencia", description="Solicita una ausencia justificada")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ausencia(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AusenciaModal())

    @app_commands.command(name="solicitar", description="Envía una solicitud formal al mando")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def solicitar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SolicitarModal())

    @app_commands.command(name="reportar", description="Reporta una incidencia al mando")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def reportar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportarModal())

    @app_commands.command(name="ranking", description="Muestra el ranking de honor del clan")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking(self, interaction: discord.Interaction):
        puntos_data = cargar("puntos.json")
        if not puntos_data:
            await interaction.response.send_message("📭 No hay datos de puntos aún.", ephemeral=True)
            return

        ranking = sorted(puntos_data.items(), key=lambda x: x[1].get("puntos", 0), reverse=True)[:10]
        embed = discord.Embed(title="🏆 Ranking de Honor del Clan", color=COLOR_MILITAR)
        medallas = ["🥇", "🥈", "🥉"] + ["🎖️"] * 7
        lineas = []
        for i, (uid, data) in enumerate(ranking):
            member = interaction.guild.get_member(int(uid))
            nombre = member.display_name if member else f"ID:{uid}"
            lineas.append(f"{medallas[i]} **{nombre}** — {data.get('puntos', 0)} pts")
        embed.description = "\n".join(lineas)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Miembros(bot))
