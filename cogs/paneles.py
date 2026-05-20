"""Cog: Paneles con botones — sin comandos slash."""
import discord
from discord.ext import commands
import datetime, uuid, re, os, sys, asyncio, io
import aiohttp
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (cargar, guardar, es_mando, ahora, ahora_fmt,
                   sumar_puntos, obtener_perfil,
                   COLOR_MILITAR, COLOR_VERDE, COLOR_ROJO, COLOR_OSCURO)

GUILD_ID                 = int(os.getenv("GUILD_ID", "0"))
CANAL_MANDO_ID           = int(os.getenv("CANAL_MANDO_ID", "0"))
CANAL_ANUNCIOS_ID        = int(os.getenv("CANAL_ANUNCIOS_ID", "0"))
CANAL_OPERACIONES_ID     = int(os.getenv("CANAL_OPERACIONES_ID", "0"))
CANAL_ENTRENAMIENTOS_ID  = int(os.getenv("CANAL_ENTRENAMIENTOS_ID", "0"))
CANAL_BRIEFING_ID        = int(os.getenv("CANAL_BRIEFING_ID", "0"))
CANAL_FOTOS_ID           = int(os.getenv("CANAL_FOTOS_ID", "0"))

JERARQUIA = ["Civil", "Aspirante", "Recluta", "Soldado Raso", "Soldado", "Cabo", "Cabo Primero", "Coronel"]
BANNER_DEFAULT = "https://i.imgur.com/4M34hi2.png"

TIPOS_ANUNCIO = {
    "urgente":     ("🚨", "URGENTE",      0xCC2222),
    "operacional": ("⚔️", "OPERACIONAL",  COLOR_MILITAR),
    "evento":      ("🎉", "EVENTO",        0xB48C14),
    "general":     ("📢", "GENERAL",       0x1E3A5F),
}

# Zonas horarias relativas a Colombia (UTC-5)
ZONAS = [
    ("🇲🇽", "México",            datetime.timedelta(hours=-1)),
    ("🌎",  "C. América",        datetime.timedelta(hours=-1)),
    ("🇳🇮", "Nic / C. Rica",     datetime.timedelta(hours=-1)),
    ("🇨🇴", "Colombia",          datetime.timedelta(hours=0)),
    ("🇵🇦", "Panamá / Perú / Ec",datetime.timedelta(hours=0)),
    ("🇨🇺", "Cuba",              datetime.timedelta(hours=0)),
    ("🇻🇪", "Venezuela",         datetime.timedelta(minutes=30)),
    ("🇩🇴", "RD / Puerto Rico",  datetime.timedelta(hours=1)),
    ("🇧🇴", "Bolivia / Paraguay",datetime.timedelta(hours=1)),
    ("🇦🇷", "Argentina / Uruguay",datetime.timedelta(hours=2)),
    ("🇨🇱", "Chile",             datetime.timedelta(hours=2)),
    ("🇪🇸", "España",            datetime.timedelta(hours=6)),
]


def resolver_miembro(guild: discord.Guild, texto: str):
    texto = texto.strip()
    m = re.match(r"<@!?(\d+)>", texto)
    if m:
        return guild.get_member(int(m.group(1)))
    try:
        return guild.get_member(int(texto))
    except ValueError:
        return discord.utils.find(
            lambda mb: mb.display_name.lower() == texto.lower(), guild.members
        )


# ══════════════════════════════════════════════════════
#  MODALES — MANDO
# ══════════════════════════════════════════════════════

class OperacionModal(discord.ui.Modal, title="⚔️ Nueva Operación"):
    nombre      = discord.ui.TextInput(label="Nombre de la operación", max_length=80)
    fecha       = discord.ui.TextInput(label="Fecha (DD/MM/AAAA)", max_length=20)
    hora        = discord.ui.TextInput(label="Hora (HH:MM)", max_length=10)
    mapa        = discord.ui.TextInput(label="Mapa / Zona", max_length=60)
    descripcion = discord.ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=400)

    async def on_submit(self, interaction: discord.Interaction):
        op_id = str(uuid.uuid4())[:8]
        embed = discord.Embed(
            title=f"⚔️ OPERACIÓN: {self.nombre.value.upper()}",
            description=self.descripcion.value,
            color=COLOR_MILITAR,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="📅 Fecha", value=self.fecha.value, inline=True)
        embed.add_field(name="⏰ Hora", value=self.hora.value, inline=True)
        embed.add_field(name="🗺️ Mapa", value=self.mapa.value, inline=True)
        embed.add_field(name="✅ Confirmados", value="Nadie aún — sé el primero", inline=False)
        embed.set_footer(text=f"ID: {op_id} • Publicado por {interaction.user.display_name}")

        canal_anuncios = interaction.guild.get_channel(CANAL_ANUNCIOS_ID)
        view = ConfirmarAsistencia(op_id)
        msg = await (canal_anuncios or interaction.channel).send(embed=embed, view=view)

        ops = cargar("operaciones.json")
        ops[op_id] = {
            "nombre": self.nombre.value, "fecha": self.fecha.value,
            "hora": self.hora.value, "mapa": self.mapa.value,
            "descripcion": self.descripcion.value, "confirmados": [],
            "creador": str(interaction.user.id),
            "message_id": str(msg.id), "channel_id": str(msg.channel.id),
            "fecha_creacion": ahora(),
        }
        guardar("operaciones.json", ops)

        canal_ops = interaction.guild.get_channel(CANAL_OPERACIONES_ID)
        if canal_ops:
            await actualizar_calendario(interaction.guild, canal_ops)

        await interaction.response.send_message(
            f"✅ Operación **{self.nombre.value}** publicada. ID: `{op_id}`", ephemeral=True
        )


class ActaModal(discord.ui.Modal, title="📝 Acta Post-Operación"):
    nombre_op  = discord.ui.TextInput(label="Nombre de la operación", max_length=80)
    resultado  = discord.ui.TextInput(label="Resultado (Victoria/Derrota/Empate)", max_length=20)
    bajas      = discord.ui.TextInput(label="Bajas propias y enemigas", max_length=200)
    errores    = discord.ui.TextInput(label="Errores cometidos", style=discord.TextStyle.paragraph, max_length=500)
    aciertos   = discord.ui.TextInput(label="Aciertos y puntos positivos", style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        res = self.resultado.value.lower()
        color = COLOR_VERDE if "victoria" in res else (COLOR_ROJO if "derrota" in res else COLOR_OSCURO)
        embed = discord.Embed(
            title=f"📋 ACTA — {self.nombre_op.value.upper()}",
            color=color, timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="🎯 Resultado", value=f"**{self.resultado.value}**", inline=True)
        embed.add_field(name="💀 Bajas", value=self.bajas.value, inline=True)
        embed.add_field(name="❌ Errores", value=self.errores.value, inline=False)
        embed.add_field(name="✅ Aciertos", value=self.aciertos.value, inline=False)
        embed.set_footer(text=f"Redactada por {interaction.user.display_name} • {ahora_fmt()}")
        canal = interaction.guild.get_channel(CANAL_ANUNCIOS_ID)
        if canal:
            await canal.send(embed=embed)
        await interaction.response.send_message("✅ Acta publicada.", ephemeral=True)


class AsistenciaModal(discord.ui.Modal, title="📋 Registrar Asistencia"):
    op_id_txt  = discord.ui.TextInput(label="ID de la operación", max_length=20)
    asistentes = discord.ui.TextInput(label="Asistentes (@mención o ID, separar con ,)", style=discord.TextStyle.paragraph, max_length=500)
    ausentes   = discord.ui.TextInput(label="Ausentes (opcional)", style=discord.TextStyle.paragraph, max_length=500, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        op_id = self.op_id_txt.value.strip()
        lista_a = [x.strip().strip("<@!>") for x in self.asistentes.value.split(",") if x.strip()]
        lista_b = [x.strip().strip("<@!>") for x in (self.ausentes.value or "").split(",") if x.strip()]
        asistencia = cargar("asistencia.json")
        asistencia[op_id] = {
            "asistio": lista_a, "ausente": lista_b,
            "registrado_por": str(interaction.user.id), "fecha": ahora_fmt(),
        }
        guardar("asistencia.json", asistencia)
        perfiles = cargar("perfiles.json")
        for uid in lista_a:
            sumar_puntos(uid, 5, f"Asistencia a operación {op_id}")
            if uid in perfiles:
                perfiles[uid]["misiones"] = perfiles[uid].get("misiones", 0) + 1
        guardar("perfiles.json", perfiles)
        await interaction.response.send_message(
            f"✅ Asistencia registrada para `{op_id}`.\n"
            f"✅ {len(lista_a)} asistentes · ❌ {len(lista_b)} ausentes · +5 pts cada asistente.",
            ephemeral=True,
        )


class AscenderModal(discord.ui.Modal, title="🎖️ Ascender Miembro"):
    miembro_txt = discord.ui.TextInput(label="@Mención o ID del miembro", max_length=100)
    nuevo_rango = discord.ui.TextInput(label="Nuevo rango", max_length=40, placeholder="Recluta / Soldado / Cabo / ...")

    async def on_submit(self, interaction: discord.Interaction):
        member = resolver_miembro(interaction.guild, self.miembro_txt.value)
        if not member:
            return await interaction.response.send_message("❌ Miembro no encontrado.", ephemeral=True)
        rol_nuevo = discord.utils.get(interaction.guild.roles, name=self.nuevo_rango.value)
        if not rol_nuevo:
            return await interaction.response.send_message(f"❌ Rango `{self.nuevo_rango.value}` no existe.", ephemeral=True)
        for r in [r for r in member.roles if r.name in JERARQUIA]:
            try:
                await member.remove_roles(r)
            except discord.Forbidden:
                pass
        await member.add_roles(rol_nuevo)
        sumar_puntos(str(member.id), 10, f"Ascenso a {self.nuevo_rango.value}")
        perfiles = cargar("perfiles.json")
        uid = str(member.id)
        if uid in perfiles:
            perfiles[uid]["rango"] = self.nuevo_rango.value
            guardar("perfiles.json", perfiles)
        embed = discord.Embed(
            title="🎖️ ASCENSO",
            description=f"{member.mention} ascendido a **{self.nuevo_rango.value}**.",
            color=COLOR_VERDE, timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Autorizado por {interaction.user.display_name}")
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            await canal_m.send(embed=embed)
        try:
            await member.send(embed=discord.Embed(
                title="🎖️ ¡Has sido ascendido!",
                description=f"Tu nuevo rango es **{self.nuevo_rango.value}**. ¡Enhorabuena!",
                color=COLOR_VERDE,
            ))
        except discord.Forbidden:
            pass
        await interaction.response.send_message(f"✅ {member.display_name} ascendido a `{self.nuevo_rango.value}`.", ephemeral=True)


class BajaModal(discord.ui.Modal, title="🚫 Dar de Baja"):
    miembro_txt = discord.ui.TextInput(label="@Mención o ID del miembro", max_length=100)
    motivo      = discord.ui.TextInput(label="Motivo de la baja", style=discord.TextStyle.paragraph, max_length=400)

    async def on_submit(self, interaction: discord.Interaction):
        member = resolver_miembro(interaction.guild, self.miembro_txt.value)
        if not member:
            return await interaction.response.send_message("❌ Miembro no encontrado.", ephemeral=True)
        uid = str(member.id)
        perfiles = cargar("perfiles.json")
        if uid in perfiles:
            perfiles[uid].update({"baja": True, "motivo_baja": self.motivo.value, "fecha_baja": ahora_fmt()})
            guardar("perfiles.json", perfiles)
        for r in [r for r in member.roles if r.name in JERARQUIA]:
            try:
                await member.remove_roles(r)
            except discord.Forbidden:
                pass
        embed = discord.Embed(
            title="🚫 BAJA",
            description=f"{member.mention} dado de baja.\n**Motivo:** {self.motivo.value}",
            color=COLOR_ROJO, timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Autorizado por {interaction.user.display_name}")
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            await canal_m.send(embed=embed)
        try:
            await member.send(embed=discord.Embed(
                title="🚫 Has sido dado de baja del clan",
                description=f"**Motivo:** {self.motivo.value}",
                color=COLOR_ROJO,
            ))
        except discord.Forbidden:
            pass
        await interaction.response.send_message(f"✅ {member.display_name} dado de baja.", ephemeral=True)


class SancionarModal(discord.ui.Modal, title="⚠️ Registrar Sanción"):
    miembro_txt = discord.ui.TextInput(label="@Mención o ID del miembro", max_length=100)
    motivo      = discord.ui.TextInput(label="Motivo de la sanción", style=discord.TextStyle.paragraph, max_length=400)
    gravedad    = discord.ui.TextInput(label="Gravedad (leve/media/grave)", max_length=20)
    puntos_txt  = discord.ui.TextInput(label="Puntos a descontar", max_length=5, placeholder="0")

    async def on_submit(self, interaction: discord.Interaction):
        member = resolver_miembro(interaction.guild, self.miembro_txt.value)
        if not member:
            return await interaction.response.send_message("❌ Miembro no encontrado.", ephemeral=True)
        try:
            pts = int(self.puntos_txt.value)
        except ValueError:
            pts = 0
        uid = str(member.id)
        sanciones = cargar("sanciones.json")
        if uid not in sanciones:
            sanciones[uid] = []
        sanciones[uid].append({
            "motivo": self.motivo.value, "gravedad": self.gravedad.value,
            "puntos": pts, "sancionado_por": str(interaction.user.id),
            "fecha": ahora_fmt(), "activa": True,
        })
        guardar("sanciones.json", sanciones)
        perfiles = cargar("perfiles.json")
        if uid in perfiles:
            perfiles[uid]["sanciones"] = perfiles[uid].get("sanciones", 0) + 1
            guardar("perfiles.json", perfiles)
        if pts > 0:
            pd = cargar("puntos.json")
            if uid not in pd:
                pd[uid] = {"puntos": 0, "historial": []}
            pd[uid]["puntos"] = max(0, pd[uid]["puntos"] - pts)
            pd[uid]["historial"].append({"cantidad": -pts, "motivo": f"Sanción: {self.motivo.value}", "fecha": ahora_fmt()})
            guardar("puntos.json", pd)
        embed = discord.Embed(
            title=f"⚠️ Sanción — {member.display_name}",
            color=COLOR_ROJO, timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="Gravedad", value=self.gravedad.value, inline=True)
        embed.add_field(name="Puntos", value=f"-{pts}", inline=True)
        embed.add_field(name="Motivo", value=self.motivo.value, inline=False)
        embed.set_footer(text=f"Por {interaction.user.display_name}")
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            await canal_m.send(embed=embed)
        try:
            await member.send(embed=discord.Embed(
                title="⚠️ Has recibido una sanción",
                description=f"**Motivo:** {self.motivo.value}\n**Gravedad:** {self.gravedad.value}\n**Puntos descontados:** {pts}",
                color=COLOR_ROJO,
            ))
        except discord.Forbidden:
            pass
        await interaction.response.send_message("✅ Sanción registrada.", ephemeral=True)


class DarPuntosModal(discord.ui.Modal, title="⭐ Dar Puntos de Honor"):
    miembro_txt = discord.ui.TextInput(label="@Mención o ID del miembro", max_length=100)
    cantidad    = discord.ui.TextInput(label="Cantidad de puntos", max_length=6)
    motivo      = discord.ui.TextInput(label="Motivo", max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        member = resolver_miembro(interaction.guild, self.miembro_txt.value)
        if not member:
            return await interaction.response.send_message("❌ Miembro no encontrado.", ephemeral=True)
        try:
            pts = int(self.cantidad.value)
        except ValueError:
            return await interaction.response.send_message("❌ Cantidad inválida.", ephemeral=True)
        sumar_puntos(str(member.id), pts, self.motivo.value)
        await interaction.response.send_message(
            f"✅ +{pts} puntos otorgados a {member.mention}.\n📝 {self.motivo.value}", ephemeral=True
        )
        try:
            await member.send(embed=discord.Embed(
                title="⭐ Puntos de Honor recibidos",
                description=f"**+{pts} puntos** — {self.motivo.value}",
                color=COLOR_VERDE,
            ))
        except discord.Forbidden:
            pass


class TorneoModal(discord.ui.Modal, title="🏆 Crear Torneo"):
    nombre      = discord.ui.TextInput(label="Nombre del torneo", max_length=80)
    descripcion = discord.ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, max_length=400)
    fecha       = discord.ui.TextInput(label="Fecha (DD/MM/AAAA)", max_length=20)
    premio      = discord.ui.TextInput(label="Premio en puntos de honor", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        torneos = cargar("torneos.json")
        tid = f"t{len(torneos)+1:04d}"
        try:
            pts = int(self.premio.value)
        except ValueError:
            pts = 0
        torneos[tid] = {
            "nombre": self.nombre.value, "descripcion": self.descripcion.value,
            "fecha": self.fecha.value, "premio_pts": pts,
            "participantes": [], "ganador": None,
            "creado_por": str(interaction.user.id), "fecha_creacion": ahora_fmt(),
        }
        guardar("torneos.json", torneos)
        embed = discord.Embed(
            title=f"🏆 TORNEO: {self.nombre.value.upper()}",
            description=self.descripcion.value,
            color=COLOR_MILITAR,
        )
        embed.add_field(name="📅 Fecha", value=self.fecha.value, inline=True)
        embed.add_field(name="🎁 Premio", value=f"{pts} puntos", inline=True)
        embed.add_field(name="🆔 ID", value=tid, inline=True)
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            await canal_m.send(embed=embed)
        await interaction.response.send_message(f"✅ Torneo **{self.nombre.value}** creado. ID: `{tid}`", ephemeral=True)


class ConfigCanalModal(discord.ui.Modal, title="⚙️ Canal Panel de Miembros"):
    canal_id = discord.ui.TextInput(label="ID del canal donde publicar el panel", max_length=25)

    async def on_submit(self, interaction: discord.Interaction):
        canal = interaction.guild.get_channel(int(self.canal_id.value.strip()))
        if not canal:
            return await interaction.response.send_message("❌ Canal no encontrado.", ephemeral=True)
        config = cargar("config.json")
        config["canal_miembros_id"] = int(self.canal_id.value.strip())
        guardar("config.json", config)
        await publicar_panel_miembros(interaction.guild, canal)
        await interaction.response.send_message(f"✅ Panel de miembros publicado en {canal.mention}.", ephemeral=True)


class ImagenCalendarioModal(discord.ui.Modal, title="🖼️ Imagen del Calendario"):
    url = discord.ui.TextInput(label="URL de la imagen (PNG/JPG)", max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        config = cargar("config.json")
        config["calendario_imagen"] = self.url.value.strip()
        guardar("config.json", config)
        canal_ops = interaction.guild.get_channel(CANAL_OPERACIONES_ID)
        if canal_ops:
            await actualizar_calendario(interaction.guild, canal_ops)
        await interaction.response.send_message("✅ Imagen del calendario actualizada.", ephemeral=True)


# ══════════════════════════════════════════════════════
#  VIEW: LIMPIAR CANAL
# ══════════════════════════════════════════════════════

class LimpiarCanalSelect(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=60)

        # Todos los canales de texto del servidor, ordenados por categoría y posición
        canales = sorted(
            [c for c in guild.text_channels],
            key=lambda c: (c.category.position if c.category else -1, c.position),
        )

        # Discord permite máximo 25 opciones en un Select
        options = []
        for canal in canales[:25]:
            cat = canal.category.name if canal.category else "Sin categoría"
            options.append(discord.SelectOption(
                label=f"#{canal.name}"[:100],
                value=str(canal.id),
                description=cat[:100],
            ))

        if not options:
            options = [discord.SelectOption(label="No hay canales", value="0")]

        sel = discord.ui.Select(placeholder="Elige el canal a limpiar...", options=options)
        sel.callback = self._on_select
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        canal_id = int(interaction.data["values"][0])
        canal = interaction.guild.get_channel(canal_id)
        if not canal:
            return await interaction.response.edit_message(content="❌ Canal no encontrado.", view=None)
        view = ConfirmarLimpiezaView(canal_id, canal.name)
        await interaction.response.edit_message(
            content=(
                f"⚠️  **¿Borrar TODOS los mensajes de #{canal.name}?**\n"
                "Incluye texto, imágenes y archivos. **No se puede deshacer.**"
            ),
            view=view,
        )


class ConfirmarLimpiezaView(discord.ui.View):
    def __init__(self, canal_id: int, canal_nombre: str = ""):
        super().__init__(timeout=30)
        self.canal_id     = canal_id
        self.canal_nombre = canal_nombre

    @discord.ui.button(label="Sí, borrar todo", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.canal_id)
        if not canal:
            return await interaction.response.edit_message(content="❌ Canal no encontrado.", view=None)
        self.stop()
        nombre = canal.name  # guardar antes de que desaparezca al clonar
        await interaction.response.edit_message(
            content=f"🗑️ Limpiando **#{nombre}**... puede tardar unos segundos.", view=None
        )
        asyncio.ensure_future(_limpiar_canal_task(canal, interaction.user))

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, _):
        self.stop()
        await interaction.response.edit_message(content="❌ Limpieza cancelada.", view=None)


def _actualizar_env(key: str, value: str):
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        nuevas = []
        for line in lines:
            if line.startswith(f"{key}="):
                nuevas.append(f"{key}={value}\n")
            else:
                nuevas.append(line)
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(nuevas)
    except Exception:
        pass


_ENV_CANAL_MAP = {
    "CANAL_MANDO_ID":          lambda: int(os.getenv("CANAL_MANDO_ID", "0")),
    "CANAL_FOTOS_ID":          lambda: int(os.getenv("CANAL_FOTOS_ID", "0")),
    "CANAL_OPERACIONES_ID":    lambda: int(os.getenv("CANAL_OPERACIONES_ID", "0")),
    "CANAL_ENTRENAMIENTOS_ID": lambda: int(os.getenv("CANAL_ENTRENAMIENTOS_ID", "0")),
    "CANAL_BRIEFING_ID":       lambda: int(os.getenv("CANAL_BRIEFING_ID", "0")),
    "CANAL_ANUNCIOS_ID":       lambda: int(os.getenv("CANAL_ANUNCIOS_ID", "0")),
}


async def _limpiar_canal_task(canal: discord.TextChannel, autor: discord.Member):
    guild  = canal.guild
    nombre = canal.name

    # Clonar canal con mismas configuraciones — instantáneo sin importar cuántos mensajes
    try:
        nuevo = await guild.create_text_channel(
            name=nombre,
            category=canal.category,
            topic=canal.topic or "",
            overwrites=canal.overwrites,
            reason=f"Limpieza por {autor.display_name}",
        )
        await nuevo.edit(position=canal.position)
        await canal.delete(reason=f"Limpieza por {autor.display_name}")
    except Exception as e:
        canal_mando = guild.get_channel(CANAL_MANDO_ID)
        if canal_mando:
            await canal_mando.send(f"❌ Error al limpiar #{nombre}: {e}", delete_after=15)
        return

    # Actualizar .env con nuevo ID
    for var, getter in _ENV_CANAL_MAP.items():
        if getter() == canal.id:
            _actualizar_env(var, str(nuevo.id))
            os.environ[var] = str(nuevo.id)
            break

    # Limpiar fotos.json si era el canal de fotos
    if canal.id == CANAL_FOTOS_ID or nuevo.name == "fotos":
        guardar("fotos.json", {})

    # Limpiar calendario_msg_id si era el canal de operaciones
    if canal.id == int(os.getenv("CANAL_OPERACIONES_ID", "0")):
        cfg = cargar("config.json")
        cfg.pop("calendario_msg_id", None)
        guardar("config.json", cfg)

    # Notificar en mando (usar nombre guardado, no mención — el canal original ya fue borrado)
    canal_mando = guild.get_channel(CANAL_MANDO_ID)
    if canal_mando:
        try:
            await canal_mando.send(
                f"✅ **#{nombre}** limpiado al instante por {autor.mention}.\n"
                f"🔄 Reiniciando bot para aplicar nuevo ID...",
                delete_after=15,
            )
        except Exception:
            pass

    # Reiniciar bot para que tome el nuevo ID del canal
    await asyncio.sleep(3)
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ══════════════════════════════════════════════════════
#  MODALES — ENTRENAMIENTO Y BRIEFING
# ══════════════════════════════════════════════════════

class EntrenamientoModal(discord.ui.Modal, title="🎯 Crear Entrenamiento"):
    tipo        = discord.ui.TextInput(label="Tipo de entrenamiento", max_length=60, placeholder="Táctica / Disparo / CQB / Estrategia...")
    fecha       = discord.ui.TextInput(label="Fecha (DD/MM/AAAA)", max_length=20)
    hora_co     = discord.ui.TextInput(label="Hora Colombia HH:MM (formato 24h)", max_length=10)
    descripcion = discord.ui.TextInput(label="Instrucciones / notas", style=discord.TextStyle.paragraph, max_length=400, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        # Parsear hora
        try:
            h, m = map(int, self.hora_co.value.strip().split(":"))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("❌ Hora inválida. Usa HH:MM en formato 24h (ej: 20:00).", ephemeral=True)

        # Parsear fecha
        base_dt = None
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                base_dt = datetime.datetime.strptime(self.fecha.value.strip(), fmt).replace(hour=h, minute=m)
                break
            except ValueError:
                continue
        if not base_dt:
            return await interaction.response.send_message("❌ Fecha inválida. Usa DD/MM/AAAA (ej: 25/05/2026).", ephemeral=True)

        # Construir embed con zonas horarias
        embed = discord.Embed(
            title=f"🎯  ENTRENAMIENTO — {self.tipo.value.upper()}",
            description=(
                f"📅 **{base_dt.strftime('%d/%m/%Y')}**\n"
                + (f"📋 {self.descripcion.value}\n" if self.descripcion.value else "")
                + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌐 **Horarios por zona horaria** *(base: Colombia)*"
            ),
            color=0x1B1F2E,
            timestamp=datetime.datetime.now(),
        )

        for bandera, nombre, delta in ZONAS:
            dt_local = base_dt + delta
            siguiente = " ✝" if dt_local.date() > base_dt.date() else ""
            hora_fmt = dt_local.strftime("%I:%M %p").lstrip("0")
            es_base = " ◄" if delta == datetime.timedelta(hours=0) and "Colombia" in nombre else ""
            embed.add_field(
                name=f"{bandera}  {nombre}",
                value=f"**{hora_fmt}**{siguiente}{es_base}",
                inline=True,
            )

        embed.set_footer(text=f"Publicado por {interaction.user.display_name} · Clan Lord")

        canal = interaction.guild.get_channel(CANAL_ENTRENAMIENTOS_ID)
        if not canal:
            return await interaction.response.send_message("❌ Canal de entrenamientos no encontrado.", ephemeral=True)

        view = ConfirmarEntrenamiento()
        await canal.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Entrenamiento **{self.tipo.value}** publicado en {canal.mention}.", ephemeral=True)


class BriefingModal(discord.ui.Modal, title="🗺️ Briefing de Misión"):
    mision   = discord.ui.TextInput(label="Nombre de la misión", max_length=80)
    objetivo = discord.ui.TextInput(label="Objetivo principal", style=discord.TextStyle.paragraph, max_length=300)
    zona     = discord.ui.TextInput(label="Zona de operaciones / Mapa", max_length=100)
    enemigo  = discord.ui.TextInput(label="Información enemiga", style=discord.TextStyle.paragraph, max_length=300)
    roe      = discord.ui.TextInput(label="Reglas de enfrentamiento (ROE)", style=discord.TextStyle.paragraph, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        canal = interaction.guild.get_channel(CANAL_BRIEFING_ID)
        if not canal:
            return await interaction.response.send_message("❌ Canal de briefing no encontrado.", ephemeral=True)

        embed = discord.Embed(
            title=f"🗺️  BRIEFING — {self.mision.value.upper()}",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "*Información clasificada de la misión. Estudia antes de la operación.*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x2C3E1A,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="🎯 Objetivo principal", value=self.objetivo.value, inline=False)
        embed.add_field(name="🗺️ Zona de operaciones", value=self.zona.value, inline=True)
        embed.add_field(name="⚠️ Información enemiga", value=self.enemigo.value, inline=False)
        embed.add_field(name="📋 Reglas de enfrentamiento", value=self.roe.value, inline=False)
        embed.set_footer(
            text=f"Redactado por {interaction.user.display_name} · Clan Lord",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )

        briefing_msg = await canal.send(embed=embed)

        await interaction.response.send_message(
            f"✅ Briefing **{self.mision.value}** publicado en {canal.mention}.\n\n"
            "📸 **¿Quieres añadir imágenes?**\n"
            f"Sube hasta **5 imágenes** directamente en {canal.mention} y se adjuntarán automáticamente.\n"
            "*(Tienes **5 minutos** — puedes subir varias de una vez o una por una)*",
            ephemeral=True,
        )

        # Referencia al embed y mision para el closure
        embed_ref   = embed
        mision_name = self.mision.value

        async def esperar_imagenes():
            imagenes = []       # list of (bytes, filename)
            msgs_borrar = []    # mensajes del usuario a borrar

            deadline = asyncio.get_event_loop().time() + 300  # 5 minutos

            def check(m):
                return (
                    m.author.id == interaction.user.id
                    and m.channel.id == canal.id
                    and any(
                        a.content_type and a.content_type.startswith("image/")
                        for a in m.attachments
                    )
                )

            async with aiohttp.ClientSession() as session:
                while len(imagenes) < 5:
                    remaining = deadline - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        break
                    try:
                        img_msg = await interaction.client.wait_for(
                            "message", check=check, timeout=remaining
                        )
                        msgs_borrar.append(img_msg)
                        for att in img_msg.attachments:
                            if (att.content_type
                                    and att.content_type.startswith("image/")
                                    and len(imagenes) < 5):
                                async with session.get(att.url) as resp:
                                    if resp.status == 200:
                                        data = await resp.read()
                                        imagenes.append((data, att.filename))
                    except asyncio.TimeoutError:
                        break

            # Borrar mensajes del usuario (las imágenes ya están descargadas)
            for m in msgs_borrar:
                try:
                    await m.delete()
                except Exception:
                    pass

            if not imagenes:
                return

            # Recrear el mensaje con las imágenes adjuntas
            try:
                await briefing_msg.delete()
            except Exception:
                pass

            # Primera imagen va dentro del embed, el resto como archivos extra
            primera_bytes, primera_nombre = imagenes[0]
            embed_ref.set_image(url=f"attachment://{primera_nombre}")

            archivos_primera = [discord.File(io.BytesIO(primera_bytes), filename=primera_nombre)]
            nuevo_msg = await canal.send(embed=embed_ref, files=archivos_primera)

            if len(imagenes) > 1:
                archivos_extra = [
                    discord.File(io.BytesIO(d), filename=fn)
                    for d, fn in imagenes[1:]
                ]
                await canal.send(
                    content=f"📎 Imágenes adicionales — **{mision_name}**",
                    files=archivos_extra,
                    reference=nuevo_msg,
                )

        asyncio.ensure_future(esperar_imagenes())


# ══════════════════════════════════════════════════════
#  MODALES — MIEMBROS
# ══════════════════════════════════════════════════════

class AusenciaModal(discord.ui.Modal, title="📋 Solicitud de Ausencia"):
    motivo = discord.ui.TextInput(label="Motivo de la ausencia", style=discord.TextStyle.paragraph, max_length=400)
    inicio = discord.ui.TextInput(label="Fecha de inicio (DD/MM/AAAA)", max_length=20)
    fin    = discord.ui.TextInput(label="Fecha de regreso (DD/MM/AAAA)", max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        ausencias = cargar("ausencias.json")
        if uid not in ausencias:
            ausencias[uid] = []
        ausencias[uid].append({
            "motivo": self.motivo.value, "inicio": self.inicio.value,
            "fin": self.fin.value, "fecha_solicitud": ahora_fmt(), "estado": "aprobada",
        })
        guardar("ausencias.json", ausencias)
        perfiles = cargar("perfiles.json")
        if uid in perfiles:
            perfiles[uid]["ausencias"] = perfiles[uid].get("ausencias", 0) + 1
            guardar("perfiles.json", perfiles)
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            embed = discord.Embed(title="📋 Solicitud de Ausencia", color=COLOR_MILITAR, timestamp=datetime.datetime.now())
            embed.add_field(name="👤 Miembro", value=interaction.user.mention, inline=True)
            embed.add_field(name="📅 Inicio", value=self.inicio.value, inline=True)
            embed.add_field(name="📅 Regreso", value=self.fin.value, inline=True)
            embed.add_field(name="📝 Motivo", value=self.motivo.value, inline=False)
            await canal_m.send(embed=embed)
        await interaction.response.send_message("✅ Ausencia registrada. El mando fue notificado.", ephemeral=True)


class SolicitudModal(discord.ui.Modal, title="📩 Solicitud al Mando"):
    asunto  = discord.ui.TextInput(label="Asunto de la solicitud", max_length=80)
    detalle = discord.ui.TextInput(label="Detalle completo", style=discord.TextStyle.paragraph, max_length=600)

    async def on_submit(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        solicitudes = cargar("solicitudes.json")
        if uid not in solicitudes:
            solicitudes[uid] = []
        solicitudes[uid].append({"asunto": self.asunto.value, "detalle": self.detalle.value, "fecha": ahora_fmt()})
        guardar("solicitudes.json", solicitudes)
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            embed = discord.Embed(
                title=f"📩 {self.asunto.value}",
                description=self.detalle.value,
                color=COLOR_MILITAR, timestamp=datetime.datetime.now(),
            )
            embed.set_footer(text=f"De: {interaction.user.display_name}")
            await canal_m.send(embed=embed)
        await interaction.response.send_message("✅ Solicitud enviada al mando.", ephemeral=True)


class ReporteModal(discord.ui.Modal, title="🚨 Reportar Incidencia"):
    tipo        = discord.ui.TextInput(label="Tipo (disciplina/técnico/otro)", max_length=40)
    descripcion = discord.ui.TextInput(label="Descripción detallada", style=discord.TextStyle.paragraph, max_length=600)
    implicados  = discord.ui.TextInput(label="Personas implicadas (opcional)", required=False, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        reportes = cargar("reportes.json")
        if uid not in reportes:
            reportes[uid] = []
        reportes[uid].append({
            "tipo": self.tipo.value, "descripcion": self.descripcion.value,
            "implicados": self.implicados.value, "fecha": ahora_fmt(),
        })
        guardar("reportes.json", reportes)
        canal_m = interaction.guild.get_channel(CANAL_MANDO_ID)
        if canal_m:
            embed = discord.Embed(
                title=f"🚨 Reporte: {self.tipo.value}",
                description=self.descripcion.value,
                color=COLOR_ROJO, timestamp=datetime.datetime.now(),
            )
            if self.implicados.value:
                embed.add_field(name="👥 Implicados", value=self.implicados.value, inline=False)
            embed.set_footer(text=f"Por: {interaction.user.display_name}")
            await canal_m.send(embed=embed)
        await interaction.response.send_message("✅ Reporte enviado de forma confidencial.", ephemeral=True)


# ══════════════════════════════════════════════════════
#  VIEW: CONFIRMAR ASISTENCIA A ENTRENAMIENTO
# ══════════════════════════════════════════════════════

class ConfirmarEntrenamiento(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Confirmar asistencia", style=discord.ButtonStyle.success, custom_id="gl_ent_confirmar")
    async def confirmar(self, interaction: discord.Interaction, _: discord.ui.Button):
        sumar_puntos(str(interaction.user.id), 2, "Confirmación de asistencia a entrenamiento")
        await interaction.response.send_message(
            "✅ Asistencia confirmada al entrenamiento. +2 puntos de honor.", ephemeral=True
        )


# ══════════════════════════════════════════════════════
#  VIEW: CONFIRMAR ASISTENCIA A OPERACIÓN
# ══════════════════════════════════════════════════════

class ConfirmarAsistencia(discord.ui.View):
    def __init__(self, op_id: str = ""):
        super().__init__(timeout=None)
        self.op_id = op_id

    @discord.ui.button(label="✅ Confirmar asistencia", style=discord.ButtonStyle.success, custom_id="gl_op_confirmar")
    async def confirmar(self, interaction: discord.Interaction, _: discord.ui.Button):
        ops = cargar("operaciones.json")
        op_id = next((oid for oid, op in ops.items() if op.get("message_id") == str(interaction.message.id)), None)
        if not op_id:
            return await interaction.response.send_message("❌ Operación no encontrada.", ephemeral=True)
        uid = str(interaction.user.id)
        confirmados = ops[op_id].get("confirmados", [])
        if uid in confirmados:
            confirmados.remove(uid)
            ops[op_id]["confirmados"] = confirmados
            guardar("operaciones.json", ops)
            await interaction.response.send_message("↩️ Confirmación retirada.", ephemeral=True)
        else:
            confirmados.append(uid)
            ops[op_id]["confirmados"] = confirmados
            guardar("operaciones.json", ops)
            sumar_puntos(uid, 2, "Confirmación de asistencia a operación")
            await interaction.response.send_message("✅ Asistencia confirmada. +2 puntos de honor.", ephemeral=True)


# ══════════════════════════════════════════════════════
#  MODAL + VIEW: PANEL DE ANUNCIOS
# ══════════════════════════════════════════════════════

class AnuncioModal(discord.ui.Modal):
    titulo    = discord.ui.TextInput(label="Título (opcional)", max_length=100, required=False)
    contenido = discord.ui.TextInput(label="Contenido del anuncio", style=discord.TextStyle.paragraph, max_length=1000)
    imagen    = discord.ui.TextInput(label="URL de imagen (opcional)", max_length=500, required=False)

    def __init__(self, tipo_key: str, mencion_key: str, canal_id=None):
        emoji, label, _ = TIPOS_ANUNCIO[tipo_key]
        super().__init__(title=f"{emoji} Anuncio {label.capitalize()}")
        self._tipo_key    = tipo_key
        self._mencion_key = mencion_key
        self._canal_id    = canal_id

    async def on_submit(self, interaction: discord.Interaction):
        emoji, label, color = TIPOS_ANUNCIO[self._tipo_key]
        menciones = {"everyone": "@everyone", "here": "@here", "none": ""}
        mencion_content = menciones.get(self._mencion_key, "")

        canal_destino = None
        if self._canal_id:
            canal_destino = interaction.guild.get_channel(self._canal_id)
        if not canal_destino:
            canal_destino = interaction.guild.get_channel(CANAL_ANUNCIOS_ID)
        if not canal_destino:
            canal_destino = interaction.channel

        titulo_val = self.titulo.value.strip() or f"Anuncio {label.capitalize()}"
        embed = discord.Embed(
            title=f"{emoji}  {titulo_val.upper()}",
            description=self.contenido.value,
            color=color,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Publicado por {interaction.user.display_name} · Clan Lord")
        if self.imagen.value.strip():
            embed.set_image(url=self.imagen.value.strip())

        allowed = (
            discord.AllowedMentions(everyone=True)
            if self._mencion_key in ("everyone", "here")
            else discord.AllowedMentions.none()
        )
        await canal_destino.send(
            content=mencion_content or None,
            embed=embed,
            allowed_mentions=allowed,
        )
        await interaction.response.send_message(
            f"✅ Anuncio **{label.capitalize()}** publicado en {canal_destino.mention}.", ephemeral=True
        )


class AnuncioSeleccionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self._tipo    = None
        self._mencion = None

        self._btns_tipo = {}
        for key, (emoji, label, _) in TIPOS_ANUNCIO.items():
            btn = discord.ui.Button(
                label=f"{emoji} {label.capitalize()}",
                style=discord.ButtonStyle.secondary,
                row=0,
            )
            btn.callback = self._make_tipo_cb(key)
            self._btns_tipo[key] = btn
            self.add_item(btn)

        self._btns_mencion = {}
        for key, emoji, label in [("everyone", "🔴", "@everyone"), ("here", "🟡", "@here"), ("none", "⚪", "Sin mención")]:
            btn = discord.ui.Button(
                label=f"{emoji} {label}",
                style=discord.ButtonStyle.secondary,
                row=1,
            )
            btn.callback = self._make_mencion_cb(key)
            self._btns_mencion[key] = btn
            self.add_item(btn)

        self._canal_id = None
        chan_sel = discord.ui.ChannelSelect(
            placeholder="📌 Canal destino (dejar vacío = #anuncios por defecto)",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            row=2,
        )
        chan_sel.callback = self._cb_canal
        self.add_item(chan_sel)

        self._btn_redactar = discord.ui.Button(
            label="✏️ Redactar Anuncio",
            style=discord.ButtonStyle.secondary,
            row=3,
            disabled=True,
        )
        self._btn_redactar.callback = self._cb_redactar
        self.add_item(self._btn_redactar)

    def _make_tipo_cb(self, key: str):
        async def cb(interaction: discord.Interaction):
            self._tipo = key
            for k, btn in self._btns_tipo.items():
                btn.style = discord.ButtonStyle.success if k == key else discord.ButtonStyle.secondary
            self._refresh_redactar()
            await interaction.response.edit_message(embed=self._embed(), view=self)
        return cb

    def _make_mencion_cb(self, key: str):
        async def cb(interaction: discord.Interaction):
            self._mencion = key
            for k, btn in self._btns_mencion.items():
                btn.style = discord.ButtonStyle.success if k == key else discord.ButtonStyle.secondary
            self._refresh_redactar()
            await interaction.response.edit_message(embed=self._embed(), view=self)
        return cb

    async def _cb_canal(self, interaction: discord.Interaction):
        values = interaction.data.get("values", [])
        self._canal_id = int(values[0]) if values else None
        await interaction.response.edit_message(embed=self._embed(), view=self)

    def _refresh_redactar(self):
        ready = bool(self._tipo and self._mencion)
        self._btn_redactar.disabled = not ready
        self._btn_redactar.style = discord.ButtonStyle.success if ready else discord.ButtonStyle.secondary

    async def _cb_redactar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AnuncioModal(self._tipo, self._mencion, self._canal_id))

    def _embed(self) -> discord.Embed:
        tipo_info = TIPOS_ANUNCIO.get(self._tipo)
        if tipo_info:
            t_emoji, t_label, t_color = tipo_info
            tipo_str = f"{t_emoji} **{t_label.capitalize()}**"
            color    = t_color
        else:
            tipo_str = "*Sin seleccionar*"
            color    = COLOR_MILITAR

        men_map     = {"everyone": "🔴 @everyone", "here": "🟡 @here", "none": "⚪ Sin mención"}
        mencion_str = men_map.get(self._mencion, "*Sin seleccionar*")
        canal_str   = f"<#{self._canal_id}>" if self._canal_id else "*#anuncios (por defecto)*"

        e = discord.Embed(
            title="📢  PANEL DE ANUNCIOS",
            description=(
                "✅ Todo listo — pulsa **✏️ Redactar Anuncio** para continuar."
                if (self._tipo and self._mencion)
                else "Elige el **tipo de anuncio** y la **mención** para continuar."
            ),
            color=color,
        )
        e.add_field(name="📌 Tipo", value=tipo_str, inline=True)
        e.add_field(name="🔔 Mención", value=mencion_str, inline=True)
        e.add_field(name="📡 Canal", value=canal_str, inline=True)
        e.set_footer(text="Solo tú ves este panel · Expira en 3 minutos")
        return e


# ══════════════════════════════════════════════════════
#  VIEW: PANEL DE MANDO
# ══════════════════════════════════════════════════════

class PanelMandoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _mando(self, interaction):
        return es_mando(interaction)

    @discord.ui.button(label="⚔️ Crear Operación", style=discord.ButtonStyle.primary, custom_id="gl_mando_crear_op", row=0)
    async def crear_op(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(OperacionModal())

    @discord.ui.button(label="📋 Registrar Asistencia", style=discord.ButtonStyle.primary, custom_id="gl_mando_asistencia", row=0)
    async def asistencia(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(AsistenciaModal())

    @discord.ui.button(label="📝 Acta Post-Op", style=discord.ButtonStyle.primary, custom_id="gl_mando_acta", row=0)
    async def acta(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(ActaModal())

    @discord.ui.button(label="🎖️ Ascender", style=discord.ButtonStyle.success, custom_id="gl_mando_ascender", row=1)
    async def ascender(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(AscenderModal())

    @discord.ui.button(label="🚫 Dar de Baja", style=discord.ButtonStyle.danger, custom_id="gl_mando_baja", row=1)
    async def baja(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(BajaModal())

    @discord.ui.button(label="⚠️ Sancionar", style=discord.ButtonStyle.danger, custom_id="gl_mando_sancionar", row=1)
    async def sancionar(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(SancionarModal())

    @discord.ui.button(label="⭐ Dar Puntos", style=discord.ButtonStyle.success, custom_id="gl_mando_puntos", row=1)
    async def dar_puntos(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(DarPuntosModal())

    @discord.ui.button(label="🏆 Crear Torneo", style=discord.ButtonStyle.secondary, custom_id="gl_mando_torneo", row=2)
    async def torneo(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(TorneoModal())

    @discord.ui.button(label="📊 Estado del Clan", style=discord.ButtonStyle.secondary, custom_id="gl_mando_estado", row=2)
    async def estado(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        perfiles = cargar("perfiles.json")
        ops = cargar("operaciones.json")
        pd = cargar("puntos.json")
        bajas = sum(1 for p in perfiles.values() if p.get("baja"))
        top = sorted(pd.items(), key=lambda x: x[1].get("puntos", 0), reverse=True)[:3]
        embed = discord.Embed(title="📊 Estado del Clan", color=COLOR_MILITAR, timestamp=datetime.datetime.now())
        embed.add_field(name="👥 Miembros", value=str(len(perfiles)), inline=True)
        embed.add_field(name="⚔️ Operaciones", value=str(len(ops)), inline=True)
        embed.add_field(name="🚫 Bajas", value=str(bajas), inline=True)
        if top:
            embed.add_field(
                name="🏆 Top Honor",
                value="\n".join(f"{i+1}. <@{uid}> — {d.get('puntos',0)} pts" for i,(uid,d) in enumerate(top)),
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🖼️ Imagen Calendario", style=discord.ButtonStyle.secondary, custom_id="gl_mando_img_cal", row=2)
    async def imagen_calendario(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(ImagenCalendarioModal())

    @discord.ui.button(label="🎯 Entrenamiento", style=discord.ButtonStyle.primary, custom_id="gl_mando_entrenamiento", row=3)
    async def entrenamiento(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(EntrenamientoModal())

    @discord.ui.button(label="🗺️ Briefing", style=discord.ButtonStyle.primary, custom_id="gl_mando_briefing", row=3)
    async def briefing(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(BriefingModal())

    @discord.ui.button(label="⚙️ Canal Miembros", style=discord.ButtonStyle.secondary, custom_id="gl_mando_cfg_canal", row=3)
    async def config_canal(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.send_modal(ConfigCanalModal())

    @discord.ui.button(label="📢 Anuncio", style=discord.ButtonStyle.primary, custom_id="gl_mando_anuncio", row=3)
    async def crear_anuncio(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        view = AnuncioSeleccionView()
        await interaction.response.send_message(embed=view._embed(), view=view, ephemeral=True)

    @discord.ui.button(label="🎓 Gestionar Cursos", style=discord.ButtonStyle.primary, custom_id="gl_mando_cursos", row=4)
    async def gestionar_cursos(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        from cogs.cursos import CursoAdminView
        e = discord.Embed(title="🎓 Gestión de Cursos", color=COLOR_MILITAR)
        e.description = (
            "Desde aquí puedes crear, monitorear y cancelar cursos de formación.\n\n"
            "**➕ Crear Nuevo Curso** — Selecciona tipo y duración, se publica en #entrenamientos\n"
            "**📊 Curso Activo** — Ve el estado del curso en progreso\n"
            "**🗑️ Cancelar** — Termina el curso activo y desbloquea #entrenamientos\n"
            "**📋 Progreso Global** — Cuántos han completado cada curso"
        )
        await interaction.response.send_message(embed=e, view=CursoAdminView(), ephemeral=True)

    @discord.ui.button(label="📊 Crear Encuesta", style=discord.ButtonStyle.primary, custom_id="gl_mando_encuesta", row=4)
    async def crear_encuesta(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        from cogs.encuestas import EncuestaModal
        await interaction.response.send_modal(EncuestaModal())

    @discord.ui.button(label="🗑️ Limpiar Canal", style=discord.ButtonStyle.danger, custom_id="gl_mando_limpiar", row=4)
    async def limpiar_canal(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        view = LimpiarCanalSelect(interaction.guild)
        await interaction.response.send_message(
            "🗑️ **Limpiar Canal** — Selecciona el canal que quieres vaciar por completo:",
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="📖 Instrucciones", style=discord.ButtonStyle.secondary, custom_id="gl_mando_instrucciones", row=4)
    async def instrucciones_mando(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self._mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)

        e1 = discord.Embed(
            title="📖  GUÍA DEL PANEL DE MANDO — Parte 1",
            description=(
                "Explicación de cada botón. Todo lo que hagas es **privado** (solo tú ves la respuesta).\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COLOR_MILITAR,
        )
        e1.add_field(
            name="⚔️ Crear Operación",
            value=(
                "Abre un formulario: escribe el **nombre, fecha (DD/MM/AAAA), hora (HH:MM), "
                "mapa y descripción**.\n"
                "→ Se publica en el canal de anuncios con botón de confirmación de asistencia."
            ),
            inline=False,
        )
        e1.add_field(
            name="📋 Registrar Asistencia",
            value=(
                "Después de una operación, escribe el **ID de la operación** y los **@ o IDs** "
                "de quienes asistieron (separados por coma).\n"
                "→ Cada asistente recibe **+5 puntos de honor** y se registra la misión en su perfil."
            ),
            inline=False,
        )
        e1.add_field(
            name="📝 Acta Post-Op",
            value=(
                "Redacta el resultado de la operación: **resultado** (Victoria/Derrota/Empate), "
                "**bajas**, **errores** y **aciertos**.\n"
                "→ Se publica en el canal de anuncios con el color según el resultado."
            ),
            inline=False,
        )
        e1.add_field(
            name="🎖️ Ascender",
            value=(
                "Escribe el **@ o ID del miembro** y el **nuevo rango** exactamente como existe el rol "
                "(ej: `Soldado`, `Cabo Primero`, `Coronel`).\n"
                "→ El bot le cambia el rol, anota el ascenso en su perfil y le envía un DM. **+10 pts** para el miembro."
            ),
            inline=False,
        )
        e1.add_field(
            name="🚫 Dar de Baja",
            value=(
                "Escribe el **@ o ID del miembro** y el **motivo** de la baja.\n"
                "→ Se le quitan todos los roles de rango, se archiva en su perfil y se le envía un DM."
            ),
            inline=False,
        )
        e1.add_field(
            name="⚠️ Sancionar",
            value=(
                "Escribe **@miembro, motivo, gravedad** (leve/media/grave) y "
                "**puntos a descontar** (pon 0 si no quieres descontar nada).\n"
                "→ Se registra la sanción, se descuentan los puntos y se le notifica al miembro por DM."
            ),
            inline=False,
        )
        e1.add_field(
            name="⭐ Dar Puntos",
            value=(
                "Escribe **@miembro, cantidad de puntos y motivo**.\n"
                "→ Se suman a su cuenta de honor al instante. El miembro recibe notificación por DM."
            ),
            inline=False,
        )
        e1.set_footer(text="Panel de Mando · Clan Lord · Solo visible para ti")

        e2 = discord.Embed(
            title="📖  GUÍA DEL PANEL DE MANDO — Parte 2",
            description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0x1B1F2E,
        )
        e2.add_field(
            name="🎯 Crear Entrenamiento",
            value=(
                "Escribe el **tipo** (CQB, Táctica, Disparo...), la **fecha** y la **hora en Colombia** (HH:MM, formato 24h).\n"
                "→ Se publica en el canal de entrenamientos con la hora convertida a **todas las zonas horarias** "
                "de Latinoamérica y España automáticamente."
            ),
            inline=False,
        )
        e2.add_field(
            name="🗺️ Briefing de Misión",
            value=(
                "Rellena el formulario: **nombre de misión, objetivo, zona/mapa, info enemiga y ROE**.\n"
                "→ Se publica en el canal de briefing. Tienes **5 minutos** para subir hasta **5 fotos** "
                "adicionales directamente en ese canal — el bot las adjunta al briefing."
            ),
            inline=False,
        )
        e2.add_field(
            name="⚙️ Canal Miembros",
            value=(
                "Pega el **ID del canal** donde quieres que aparezca el Panel de Miembros.\n"
                "→ El bot publica allí el panel automáticamente. Si ya existe uno, lo edita."
            ),
            inline=False,
        )
        e2.add_field(
            name="📢 Anuncio",
            value=(
                "Abre el **panel de anuncios** — elige tipo y mención antes de redactar:\n"
                "• **Tipos**: 🚨 Urgente · ⚔️ Operacional · 🎉 Evento · 📢 General\n"
                "• **Menciones**: 🔴 @everyone · 🟡 @here · ⚪ Sin mención\n"
                "→ Con ambos seleccionados pulsa **✏️ Redactar Anuncio** — rellena título, "
                "contenido, canal destino (opcional) e imagen (opcional) y se publica al instante."
            ),
            inline=False,
        )
        e2.add_field(
            name="🏆 Crear Torneo",
            value=(
                "Escribe **nombre, descripción, fecha y premio en puntos de honor**.\n"
                "→ Se registra el torneo y se anuncia en el canal de mando con su ID."
            ),
            inline=False,
        )
        e2.add_field(
            name="📊 Estado del Clan",
            value=(
                "Muestra un **resumen rápido**: total de miembros, número de operaciones, bajas registradas "
                "y el **top 3** de jugadores con más puntos de honor."
            ),
            inline=False,
        )
        e2.add_field(
            name="🖼️ Imagen Calendario",
            value=(
                "Pega una **URL de imagen** (PNG/JPG) para usarla como banner del calendario de operaciones.\n"
                "→ Se actualiza al instante en el canal de operaciones."
            ),
            inline=False,
        )
        e2.add_field(
            name="🎓 Gestionar Cursos",
            value=(
                "Abre el panel de cursos donde puedes:\n"
                "• **Crear** un nuevo curso (Básico, Médico, Drones, Aviación, CQB, Zeus, Comando)\n"
                "• **Ver el estado** del curso activo (inscriptos, progreso)\n"
                "• **Cancelar** el curso activo\n"
                "• **Ver progreso global** de todos los cursos"
            ),
            inline=False,
        )
        e2.add_field(
            name="📊 Crear Encuesta",
            value=(
                "Abre el formulario de encuesta: escribe la **pregunta**, las **opciones** "
                "(mínimo 2, máximo 4, una por línea), la **duración** (ej: `24h`, `7d`, `0` = sin límite) "
                "y opcionalmente el **ID del canal** donde publicarla.\n"
                "→ Se publica con barras de progreso en tiempo real. Se cierra automáticamente al vencer el tiempo."
            ),
            inline=False,
        )
        e2.add_field(
            name="🗑️ Limpiar Canal",
            value=(
                "Selecciona cualquier canal del servidor para **borrar todos sus mensajes** de golpe "
                "(clona el canal para que sea instantáneo).\n"
                "⚠️ **Irreversible.** El bot se reinicia para tomar el nuevo ID del canal."
            ),
            inline=False,
        )
        e2.set_footer(text="Panel de Mando · Clan Lord · Solo visible para ti")

        await interaction.response.send_message(embeds=[e1, e2], ephemeral=True)


# ══════════════════════════════════════════════════════
#  VIEW: ADMIN — LIMPIEZA RÁPIDA DEL CANAL DE MANDO
# ══════════════════════════════════════════════════════

class AdminLimpiarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🗑️ Limpiar Mensajes", style=discord.ButtonStyle.danger, custom_id="gl_admin_limpiar")
    async def limpiar(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not es_mando(interaction):
            return await interaction.response.send_message("❌ Sin permiso.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        borrados = await interaction.channel.purge(limit=500, check=lambda m: not m.author.bot)
        n = len(borrados)
        await interaction.followup.send(
            f"✅ {n} mensaje{'s' if n != 1 else ''} de miembros eliminado{'s' if n != 1 else ''}. Los paneles permanecen intactos.",
            ephemeral=True,
        )


# ══════════════════════════════════════════════════════
#  VIEW: PANEL DE MIEMBROS
# ══════════════════════════════════════════════════════

class PanelMiembrosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 Mi Perfil", style=discord.ButtonStyle.primary, custom_id="gl_mb_perfil", row=0)
    async def perfil(self, interaction: discord.Interaction, _: discord.ui.Button):
        p = obtener_perfil(interaction.user)
        pd = cargar("puntos.json")
        uid = str(interaction.user.id)
        puntos = pd.get(uid, {}).get("puntos", p.get("puntos", 0))
        sanciones_data = cargar("sanciones.json")
        activas = [s for s in sanciones_data.get(uid, []) if s.get("activa", True)]
        embed = discord.Embed(
            title=f"🪖 Perfil — {interaction.user.display_name}",
            color=COLOR_MILITAR, timestamp=datetime.datetime.now(),
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🎖️ Rango", value=p.get("rango", "Sin rango"), inline=True)
        embed.add_field(name="⭐ Puntos", value=str(puntos), inline=True)
        embed.add_field(name="🎯 Misiones", value=str(p.get("misiones", 0)), inline=True)
        embed.add_field(name="📅 Ausencias", value=str(p.get("ausencias", 0)), inline=True)
        embed.add_field(name="⚠️ Sanciones", value=str(p.get("sanciones", 0)), inline=True)
        embed.add_field(name="📆 Ingreso", value=p.get("fecha_ingreso", "—")[:10], inline=True)
        if activas:
            embed.add_field(name="🔴 Sanciones activas", value="\n".join(f"• {s['motivo']}" for s in activas[-3:]), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⭐ Mis Puntos", style=discord.ButtonStyle.primary, custom_id="gl_mb_puntos", row=0)
    async def mis_puntos(self, interaction: discord.Interaction, _: discord.ui.Button):
        pd = cargar("puntos.json")
        uid = str(interaction.user.id)
        data = pd.get(uid, {"puntos": 0, "historial": []})
        embed = discord.Embed(title=f"⭐ Puntos — {interaction.user.display_name}", color=COLOR_MILITAR)
        embed.add_field(name="Total acumulado", value=f"**{data['puntos']} puntos**", inline=False)
        hist = data.get("historial", [])[-8:]
        if hist:
            lineas = [
                f"`{h['fecha']}` **{'+' if h['cantidad'] >= 0 else ''}{h['cantidad']}** — {h['motivo']}"
                for h in reversed(hist)
            ]
            embed.add_field(name="Últimos movimientos", value="\n".join(lineas), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏆 Ranking", style=discord.ButtonStyle.secondary, custom_id="gl_mb_ranking", row=0)
    async def ranking(self, interaction: discord.Interaction, _: discord.ui.Button):
        pd = cargar("puntos.json")
        if not pd:
            return await interaction.response.send_message("📭 No hay datos aún.", ephemeral=True)
        top = sorted(pd.items(), key=lambda x: x[1].get("puntos", 0), reverse=True)[:10]
        medallas = ["🥇", "🥈", "🥉"] + ["🎖️"] * 7
        embed = discord.Embed(title="🏆 Ranking de Honor — Clan Lord", color=COLOR_MILITAR)
        lineas = []
        for i, (uid, data) in enumerate(top):
            mb = interaction.guild.get_member(int(uid))
            nombre = mb.display_name if mb else f"Miembro {uid[:6]}"
            lineas.append(f"{medallas[i]} **{nombre}** — {data.get('puntos', 0)} pts")
        embed.description = "\n".join(lineas)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📅 Solicitar Ausencia", style=discord.ButtonStyle.secondary, custom_id="gl_mb_ausencia", row=1)
    async def ausencia(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(AusenciaModal())

    @discord.ui.button(label="📩 Solicitar al Mando", style=discord.ButtonStyle.secondary, custom_id="gl_mb_solicitar", row=1)
    async def solicitar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(SolicitudModal())

    @discord.ui.button(label="🚨 Reportar Incidencia", style=discord.ButtonStyle.danger, custom_id="gl_mb_reportar", row=1)
    async def reportar(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(ReporteModal())


# ══════════════════════════════════════════════════════
#  HELPER: CALENDARIO
# ══════════════════════════════════════════════════════

def _estado_op(fecha_str, hora_str):
    dt = None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%y %H:%M", "%d/%m/%Y", "%d/%m/%y"):
        try:
            dt = datetime.datetime.strptime(f"{fecha_str} {hora_str}".strip(), fmt) if "%H" in fmt else datetime.datetime.strptime(fecha_str, fmt)
            break
        except ValueError:
            continue
    if dt is None:
        return "🟡", "Sin fecha"
    diff = (dt.date() - datetime.datetime.now().date()).days
    if diff < 0:   return "🔴", "Finalizada"
    if diff == 0:  return "🟢", "HOY"
    if diff <= 3:  return "🟠", f"En {diff}d"
    return "🔵", f"En {diff}d"


async def actualizar_calendario(guild: discord.Guild, canal: discord.TextChannel):
    ops = cargar("operaciones.json")
    config = cargar("config.json")
    banner_url = config.get("calendario_imagen", BANNER_DEFAULT)

    futuras, pasadas = [], []
    for op_id, op in ops.items():
        dt = None
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%y %H:%M", "%d/%m/%Y", "%d/%m/%y"):
            try:
                dt = datetime.datetime.strptime(f"{op['fecha']} {op['hora']}".strip(), fmt) if "%H" in fmt else datetime.datetime.strptime(op['fecha'], fmt)
                break
            except ValueError:
                continue
        if dt:
            (futuras if dt >= datetime.datetime.now() else pasadas).append((op_id, op))
        else:
            futuras.append((op_id, op))

    mostrar = (futuras + pasadas)[-6:]
    embed = discord.Embed(
        title="🗓️  CALENDARIO DE OPERACIONES",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Operaciones programadas del clan.\n"
            "Confirma tu asistencia en el anuncio correspondiente.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_MILITAR,
        timestamp=datetime.datetime.now(),
    )
    if not mostrar:
        embed.add_field(name="📭 Sin operaciones", value="No hay operaciones programadas aún.", inline=False)
    else:
        for _, op in mostrar:
            emoji, etiqueta = _estado_op(op.get("fecha", ""), op.get("hora", ""))
            n = len(op.get("confirmados", []))
            embed.add_field(
                name=f"{emoji}  {op.get('nombre','—').upper()}  ·  `{etiqueta}`",
                value=(
                    f"📅 **{op.get('fecha','—')}**  ·  ⏰ **{op.get('hora','—')}**\n"
                    f"🗺️ {op.get('mapa','—')}  ·  ✅ {n} confirmado{'s' if n != 1 else ''}"
                ),
                inline=False,
            )
    embed.set_image(url=banner_url)
    embed.set_footer(
        text=f"🕐 Actualizado: {ahora_fmt()}  ·  Clan Lord",
        icon_url=guild.icon.url if guild.icon else None,
    )

    # Intentar editar el mensaje guardado por ID (evita duplicados)
    cal_msg_id = config.get("calendario_msg_id")
    if cal_msg_id:
        try:
            msg = await canal.fetch_message(int(cal_msg_id))
            await msg.edit(embed=embed)
            return
        except (discord.NotFound, discord.HTTPException):
            pass  # Mensaje borrado, crear uno nuevo

    # Buscar en historial solo mensajes con "CALENDARIO" en el título
    async for msg in canal.history(limit=30):
        if (msg.author == guild.me
                and msg.embeds
                and "CALENDARIO" in (msg.embeds[0].title or "")):
            await msg.edit(embed=embed)
            config["calendario_msg_id"] = str(msg.id)
            guardar("config.json", config)
            return

    # Crear nuevo y guardar su ID
    nuevo = await canal.send(embed=embed)
    config["calendario_msg_id"] = str(nuevo.id)
    guardar("config.json", config)


# ══════════════════════════════════════════════════════
#  HELPER: PUBLICAR PANELES
# ══════════════════════════════════════════════════════

async def publicar_panel_mando(guild: discord.Guild):
    canal = guild.get_channel(CANAL_MANDO_ID)
    if not canal:
        return
    embed = discord.Embed(
        title="🛡️  PANEL DE MANDO",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Centro de control del clan. Usa los botones para gestionar "
            "operaciones, miembros y sanciones.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**🔵 Fila 1 — Operaciones**\n"
            "> ⚔️ Crear Operación  ·  📋 Registrar Asistencia  ·  📝 Acta\n\n"
            "**🟢 Fila 2 — Miembros**\n"
            "> 🎖️ Ascender  ·  🚫 Dar de Baja  ·  ⚠️ Sancionar  ·  ⭐ Dar Puntos\n\n"
            "**⚫ Fila 3 — General**\n"
            "> 🏆 Torneo  ·  📊 Estado  ·  🖼️ Imagen Calendario\n\n"
            "**🟣 Fila 4 — Entrenamientos y Configuración**\n"
            "> 🎯 Crear Entrenamiento  ·  🗺️ Briefing de Misión  ·  ⚙️ Canal Miembros  ·  📢 Anuncio\n\n"
            "**🔴 Fila 5 — Administración**\n"
            "> 🎓 Gestionar Cursos  ·  📊 Crear Encuesta  ·  🗑️ Limpiar Canal  ·  📖 Instrucciones"
        ),
        color=COLOR_MILITAR,
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Solo visible y operativo para el mando.")
    view = PanelMandoView()
    async for msg in canal.history(limit=20):
        if msg.author == guild.me and msg.embeds and "PANEL DE MANDO" in (msg.embeds[0].title or ""):
            await msg.edit(embed=embed, view=view)
            return
    await canal.send(embed=embed, view=view)


async def publicar_panel_admin(guild: discord.Guild):
    canal = guild.get_channel(CANAL_MANDO_ID)
    if not canal:
        return
    embed = discord.Embed(
        title="⚡  LIMPIEZA RÁPIDA",
        description=(
            "Vacía este canal al instante con un solo clic.\n"
            "El bot se reiniciará y republicará todos los paneles automáticamente.\n\n"
            "> ⚠️ Solo para administradores y alto mando."
        ),
        color=COLOR_ROJO,
    )
    embed.set_footer(text="Clan Lord · Acción irreversible · Solo mando")
    view = AdminLimpiarView()
    async for msg in canal.history(limit=20):
        if msg.author == guild.me and msg.embeds and "LIMPIEZA RÁPIDA" in (msg.embeds[0].title or ""):
            await msg.edit(embed=embed, view=view)
            return
    await canal.send(embed=embed, view=view)


async def publicar_panel_miembros(guild: discord.Guild, canal: discord.TextChannel):
    embed = discord.Embed(
        title="👤  PANEL DE MIEMBROS",
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Gestiona tu perfil, consulta tus puntos de honor y comunícate "
            "con el mando usando los botones de abajo.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_MILITAR,
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Clan Lord · Todos los datos son privados (ephemeral)")
    view = PanelMiembrosView()
    async for msg in canal.history(limit=20):
        if msg.author == guild.me and msg.embeds and "PANEL DE MIEMBROS" in (msg.embeds[0].title or ""):
            await msg.edit(embed=embed, view=view)
            return
    await canal.send(embed=embed, view=view)


# ══════════════════════════════════════════════════════
#  COG
# ══════════════════════════════════════════════════════

class Paneles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        # Panel mando
        await publicar_panel_mando(guild)
        # Panel de limpieza rápida del canal de mando
        await publicar_panel_admin(guild)
        # Panel miembros (si está configurado)
        config = cargar("config.json")
        cid = config.get("canal_miembros_id")
        if cid:
            canal = guild.get_channel(int(cid))
            if canal:
                await publicar_panel_miembros(guild, canal)
        # Calendario
        canal_ops = guild.get_channel(CANAL_OPERACIONES_ID)
        if canal_ops:
            await actualizar_calendario(guild, canal_ops)


async def setup(bot):
    await bot.add_cog(Paneles(bot))
