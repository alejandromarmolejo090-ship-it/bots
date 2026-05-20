"""Cog: Comandos exclusivos del mando."""
import discord
from discord.ext import commands
from discord import app_commands
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (cargar, guardar, es_mando, ahora, ahora_fmt,
                   sumar_puntos, COLOR_MILITAR, COLOR_ROJO, COLOR_VERDE, COLOR_OSCURO)

GUILD_ID       = int(os.getenv("GUILD_ID", "0"))
CANAL_MANDO_ID = int(os.getenv("CANAL_MANDO_ID", "0"))

JERARQUIA = [
    "Civil", "Aspirante", "Recluta", "Soldado Raso",
    "Soldado", "Cabo", "Cabo Primero", "Coronel",
]


class SancionModal(discord.ui.Modal, title="⚠️ Registrar Sanción"):
    motivo    = discord.ui.TextInput(label="Motivo de la sanción", style=discord.TextStyle.paragraph, max_length=400)
    gravedad  = discord.ui.TextInput(label="Gravedad (leve/media/grave)", max_length=20)
    puntos    = discord.ui.TextInput(label="Puntos a descontar (número)", max_length=5)

    def __init__(self, objetivo: discord.Member):
        super().__init__()
        self.objetivo = objetivo

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pts = int(self.puntos.value)
        except ValueError:
            pts = 0

        uid = str(self.objetivo.id)
        sanciones = cargar("sanciones.json")
        if uid not in sanciones:
            sanciones[uid] = []
        sanciones[uid].append({
            "motivo": self.motivo.value,
            "gravedad": self.gravedad.value,
            "puntos": pts,
            "sancionado_por": str(interaction.user.id),
            "fecha": ahora_fmt(),
            "activa": True,
        })
        guardar("sanciones.json", sanciones)

        perfiles = cargar("perfiles.json")
        if uid in perfiles:
            perfiles[uid]["sanciones"] = perfiles[uid].get("sanciones", 0) + 1
            guardar("perfiles.json", perfiles)

        if pts > 0:
            puntos_data = cargar("puntos.json")
            if uid not in puntos_data:
                puntos_data[uid] = {"puntos": 0, "historial": []}
            puntos_data[uid]["puntos"] = max(0, puntos_data[uid]["puntos"] - pts)
            puntos_data[uid]["historial"].append({
                "cantidad": -pts,
                "motivo": f"Sanción: {self.motivo.value}",
                "fecha": ahora_fmt(),
            })
            guardar("puntos.json", puntos_data)

        embed = discord.Embed(
            title=f"⚠️ Sanción registrada — {self.objetivo.display_name}",
            color=COLOR_ROJO,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="Gravedad", value=self.gravedad.value, inline=True)
        embed.add_field(name="Puntos", value=f"-{pts}", inline=True)
        embed.add_field(name="Motivo", value=self.motivo.value, inline=False)
        embed.set_footer(text=f"Registrado por {interaction.user.display_name}")

        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            await canal_mando.send(embed=embed)

        try:
            await self.objetivo.send(
                embed=discord.Embed(
                    title="⚠️ Has recibido una sanción",
                    description=f"**Motivo:** {self.motivo.value}\n**Gravedad:** {self.gravedad.value}\n**Puntos descontados:** {pts}",
                    color=COLOR_ROJO,
                )
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message("✅ Sanción registrada.", ephemeral=True)


class TorneoModal(discord.ui.Modal, title="🏆 Crear Torneo"):
    nombre      = discord.ui.TextInput(label="Nombre del torneo", max_length=80)
    descripcion = discord.ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=400)
    fecha       = discord.ui.TextInput(label="Fecha (DD/MM/AAAA)", max_length=20)
    premio      = discord.ui.TextInput(label="Premio (puntos de honor)", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        torneos = cargar("torneos.json")
        tid = f"t{len(torneos)+1:04d}"
        try:
            pts = int(self.premio.value)
        except ValueError:
            pts = 0
        torneos[tid] = {
            "nombre": self.nombre.value,
            "descripcion": self.descripcion.value,
            "fecha": self.fecha.value,
            "premio_pts": pts,
            "participantes": [],
            "ganador": None,
            "creado_por": str(interaction.user.id),
            "fecha_creacion": ahora_fmt(),
        }
        guardar("torneos.json", torneos)

        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        embed = discord.Embed(
            title=f"🏆 TORNEO: {self.nombre.value.upper()}",
            description=self.descripcion.value,
            color=COLOR_MILITAR,
        )
        embed.add_field(name="📅 Fecha", value=self.fecha.value, inline=True)
        embed.add_field(name="🎁 Premio", value=f"{pts} puntos de honor", inline=True)
        embed.add_field(name="🆔 ID", value=tid, inline=True)
        if canal_mando:
            await canal_mando.send(embed=embed)
        await interaction.response.send_message(f"✅ Torneo `{self.nombre.value}` creado. ID: `{tid}`", ephemeral=True)


class Mando(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _check_mando(self, interaction):
        return es_mando(interaction)

    @app_commands.command(name="ascender", description="Asciende a un miembro al siguiente rango")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ascender(self, interaction: discord.Interaction, miembro: discord.Member, nuevo_rango: str):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede ascender miembros.", ephemeral=True)
            return

        rol_nuevo = discord.utils.get(interaction.guild.roles, name=nuevo_rango)
        if not rol_nuevo:
            await interaction.response.send_message(f"❌ Rango `{nuevo_rango}` no encontrado.", ephemeral=True)
            return

        rangos_existentes = [r for r in miembro.roles if r.name in JERARQUIA]
        for r in rangos_existentes:
            try:
                await miembro.remove_roles(r)
            except discord.Forbidden:
                pass

        await miembro.add_roles(rol_nuevo)
        sumar_puntos(str(miembro.id), 10, f"Ascenso al rango {nuevo_rango}")

        perfiles = cargar("perfiles.json")
        uid = str(miembro.id)
        if uid in perfiles:
            perfiles[uid]["rango"] = nuevo_rango
            guardar("perfiles.json", perfiles)

        embed = discord.Embed(
            title="🎖️ ASCENSO",
            description=f"{miembro.mention} ha sido ascendido a **{nuevo_rango}**.",
            color=COLOR_VERDE,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Autorizado por {interaction.user.display_name}")

        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            await canal_mando.send(embed=embed)

        try:
            await miembro.send(embed=discord.Embed(
                title="🎖️ ¡Has sido ascendido!",
                description=f"Tu nuevo rango es **{nuevo_rango}**. ¡Enhorabuena!",
                color=COLOR_VERDE,
            ))
        except discord.Forbidden:
            pass

        await interaction.response.send_message(f"✅ {miembro.display_name} ascendido a `{nuevo_rango}`.", ephemeral=True)

    @app_commands.command(name="baja", description="Da de baja a un miembro del clan")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def baja(self, interaction: discord.Interaction, miembro: discord.Member, motivo: str):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede dar de baja.", ephemeral=True)
            return

        uid = str(miembro.id)
        perfiles = cargar("perfiles.json")
        if uid in perfiles:
            perfiles[uid]["baja"] = True
            perfiles[uid]["motivo_baja"] = motivo
            perfiles[uid]["fecha_baja"] = ahora_fmt()
            guardar("perfiles.json", perfiles)

        rangos = [r for r in miembro.roles if r.name in JERARQUIA]
        for r in rangos:
            try:
                await miembro.remove_roles(r)
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="🚫 BAJA",
            description=f"{miembro.mention} ha sido dado de baja.\n**Motivo:** {motivo}",
            color=COLOR_ROJO,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Autorizado por {interaction.user.display_name}")
        canal_mando = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            await canal_mando.send(embed=embed)

        try:
            await miembro.send(embed=discord.Embed(
                title="🚫 Has sido dado de baja del clan",
                description=f"**Motivo:** {motivo}",
                color=COLOR_ROJO,
            ))
        except discord.Forbidden:
            pass

        await interaction.response.send_message(f"✅ {miembro.display_name} dado de baja.", ephemeral=True)

    @app_commands.command(name="sancionar", description="Registra una sanción para un miembro")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sancionar(self, interaction: discord.Interaction, miembro: discord.Member):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede sancionar.", ephemeral=True)
            return
        await interaction.response.send_modal(SancionModal(miembro))

    @app_commands.command(name="panel-mando", description="Panel de estado del clan para el mando")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def panel_mando(self, interaction: discord.Interaction):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Acceso restringido al mando.", ephemeral=True)
            return

        perfiles = cargar("perfiles.json")
        sanciones = cargar("sanciones.json")
        ops = cargar("operaciones.json")
        ausencias = cargar("asistencia.json")

        total_miembros = len(perfiles)
        total_ops = len(ops)
        total_sanciones = sum(len(v) for v in sanciones.values())
        bajas = sum(1 for p in perfiles.values() if p.get("baja"))

        embed = discord.Embed(
            title="🛡️ PANEL DE MANDO — Estado del Clan",
            color=COLOR_MILITAR,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="👥 Miembros registrados", value=str(total_miembros), inline=True)
        embed.add_field(name="⚔️ Operaciones totales", value=str(total_ops), inline=True)
        embed.add_field(name="⚠️ Sanciones totales", value=str(total_sanciones), inline=True)
        embed.add_field(name="🚫 Bajas", value=str(bajas), inline=True)

        top_pts = sorted(
            [(uid, p.get("puntos", 0)) for uid, p in perfiles.items()],
            key=lambda x: x[1], reverse=True
        )[:3]
        if top_pts:
            top_str = "\n".join(
                f"{i+1}. <@{uid}> — {pts} pts"
                for i, (uid, pts) in enumerate(top_pts)
            )
            embed.add_field(name="🏆 Top 3 Honor", value=top_str, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="armeria", description="Muestra el armamento permitido por rango")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def armeria(self, interaction: discord.Interaction, rango: str = None):
        armeria = cargar("armeria.json")
        embed = discord.Embed(title="🔫 ARMERÍA — Equipamiento Reglamentario", color=COLOR_MILITAR)

        if rango:
            armas = armeria.get(rango)
            if armas is None:
                await interaction.response.send_message(f"❌ Rango `{rango}` no encontrado.", ephemeral=True)
                return
            embed.add_field(
                name=f"🎖️ {rango}",
                value="\n".join(f"• {a}" for a in armas) if armas else "Sin armamento asignado",
                inline=False,
            )
        else:
            for r, armas in armeria.items():
                embed.add_field(
                    name=f"🎖️ {r}",
                    value="\n".join(f"• {a}" for a in armas) if armas else "Sin armamento",
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="dar-puntos", description="Añade puntos de honor a un miembro")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def dar_puntos(self, interaction: discord.Interaction, miembro: discord.Member, cantidad: int, motivo: str):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede otorgar puntos.", ephemeral=True)
            return
        sumar_puntos(str(miembro.id), cantidad, motivo)
        await interaction.response.send_message(
            f"✅ +{cantidad} puntos de honor otorgados a {miembro.mention}.\n📝 Motivo: {motivo}", ephemeral=True
        )
        try:
            await miembro.send(embed=discord.Embed(
                title="⭐ Puntos de Honor recibidos",
                description=f"**+{cantidad} puntos** — {motivo}",
                color=COLOR_VERDE,
            ))
        except discord.Forbidden:
            pass

    @app_commands.command(name="crear-torneo", description="Crea un torneo interno del clan")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def crear_torneo(self, interaction: discord.Interaction):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede crear torneos.", ephemeral=True)
            return
        await interaction.response.send_modal(TorneoModal())

    @app_commands.command(name="torneo-ganador", description="Registra el ganador de un torneo")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def torneo_ganador(self, interaction: discord.Interaction, torneo_id: str, ganador: discord.Member):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede registrar ganadores.", ephemeral=True)
            return
        torneos = cargar("torneos.json")
        if torneo_id not in torneos:
            await interaction.response.send_message(f"❌ Torneo `{torneo_id}` no encontrado.", ephemeral=True)
            return
        torneos[torneo_id]["ganador"] = str(ganador.id)
        guardar("torneos.json", torneos)
        pts = torneos[torneo_id].get("premio_pts", 0)
        if pts > 0:
            sumar_puntos(str(ganador.id), pts, f"Ganador del torneo {torneos[torneo_id]['nombre']}")
        await interaction.response.send_message(
            f"🏆 {ganador.mention} registrado como ganador del torneo `{torneos[torneo_id]['nombre']}`. +{pts} puntos.",
            ephemeral=False,
        )

    @app_commands.command(name="lista-sanciones", description="Lista las sanciones de un miembro")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def lista_sanciones(self, interaction: discord.Interaction, miembro: discord.Member):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Acceso restringido.", ephemeral=True)
            return
        sanciones = cargar("sanciones.json")
        uid = str(miembro.id)
        historial = sanciones.get(uid, [])
        if not historial:
            await interaction.response.send_message(f"✅ {miembro.display_name} no tiene sanciones.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"⚠️ Sanciones — {miembro.display_name}",
            color=COLOR_ROJO,
        )
        for i, s in enumerate(historial[-10:], 1):
            embed.add_field(
                name=f"#{i} — {s['fecha']} ({s.get('gravedad','—')})",
                value=f"**Motivo:** {s['motivo']}\n**Puntos:** -{s.get('puntos', 0)}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="alertas-inactividad", description="Lista miembros con pocas misiones")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def alertas_inactividad(self, interaction: discord.Interaction, umbral: int = 3):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Acceso restringido.", ephemeral=True)
            return
        perfiles = cargar("perfiles.json")
        inactivos = [
            (uid, p) for uid, p in perfiles.items()
            if p.get("misiones", 0) < umbral and not p.get("baja")
        ]
        if not inactivos:
            await interaction.response.send_message("✅ Todos los miembros tienen actividad suficiente.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"⚠️ Alertas de Inactividad (< {umbral} misiones)",
            color=COLOR_ROJO,
        )
        lineas = [f"<@{uid}> — {p.get('misiones', 0)} misiones | Rango: {p.get('rango','?')}" for uid, p in inactivos[:20]]
        embed.description = "\n".join(lineas)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sugerir-ascenso", description="Sugiere miembros listos para ascender")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sugerir_ascenso(self, interaction: discord.Interaction, min_puntos: int = 30, min_misiones: int = 5):
        if not self._check_mando(interaction):
            await interaction.response.send_message("❌ Acceso restringido.", ephemeral=True)
            return
        perfiles = cargar("perfiles.json")
        candidatos = [
            (uid, p) for uid, p in perfiles.items()
            if p.get("puntos", 0) >= min_puntos and p.get("misiones", 0) >= min_misiones
            and not p.get("baja")
        ]
        if not candidatos:
            await interaction.response.send_message("📭 Ningún miembro cumple los requisitos actualmente.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"🎖️ Candidatos para Ascenso (≥{min_puntos} pts, ≥{min_misiones} misiones)",
            color=COLOR_VERDE,
        )
        lineas = [
            f"<@{uid}> — {p.get('puntos',0)} pts | {p.get('misiones',0)} misiones | Rango: {p.get('rango','?')}"
            for uid, p in sorted(candidatos, key=lambda x: x[1].get("puntos", 0), reverse=True)[:15]
        ]
        embed.description = "\n".join(lineas)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Mando(bot))
