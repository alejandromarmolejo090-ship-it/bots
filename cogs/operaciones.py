"""Cog: Operaciones, asistencia y actas."""
import discord
from discord.ext import commands
from discord import app_commands
import datetime, uuid, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, es_mando, ahora, ahora_fmt, sumar_puntos, COLOR_MILITAR, COLOR_VERDE, COLOR_OSCURO, COLOR_ROJO

# URL de imagen de banner para el calendario (se puede cambiar con /calendario-imagen)
CALENDARIO_IMAGE_KEY = "calendario_imagen"
BANNER_DEFAULT = "https://i.imgur.com/4M34hi2.png"

GUILD_ID = int(os.getenv("GUILD_ID", "0"))
CANAL_ANUNCIOS_ID    = int(os.getenv("CANAL_ANUNCIOS_ID", "0"))
CANAL_OPERACIONES_ID = int(os.getenv("CANAL_OPERACIONES_ID", "0"))


class ConfirmarAsistencia(discord.ui.View):
    def __init__(self, op_id: str):
        super().__init__(timeout=None)
        self.op_id = op_id

    @discord.ui.button(label="✅ Confirmar asistencia", style=discord.ButtonStyle.success, custom_id="op_confirmar")
    async def confirmar(self, interaction: discord.Interaction, _button: discord.ui.Button):
        ops = cargar("operaciones.json")
        op_id = None
        for oid, op in ops.items():
            if op.get("message_id") == str(interaction.message.id):
                op_id = oid
                break
        if not op_id:
            await interaction.response.send_message("❌ Operación no encontrada.", ephemeral=True)
            return
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


class ActaModal(discord.ui.Modal, title="📝 Acta Post-Operación"):
    nombre_op  = discord.ui.TextInput(label="Nombre de la operación", max_length=80)
    resultado  = discord.ui.TextInput(label="Resultado (Victoria/Derrota/Empate)", max_length=20)
    bajas      = discord.ui.TextInput(label="Bajas propias y enemigas", max_length=200)
    errores    = discord.ui.TextInput(label="Errores cometidos", style=discord.TextStyle.paragraph, max_length=500)
    aciertos   = discord.ui.TextInput(label="Aciertos y puntos positivos", style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        canal = interaction.guild.get_channel(CANAL_ANUNCIOS_ID)
        embed = discord.Embed(
            title=f"📋 ACTA DE OPERACIÓN — {self.nombre_op.value.upper()}",
            color=COLOR_MILITAR,
            timestamp=datetime.datetime.now(),
        )
        color = COLOR_VERDE if "victoria" in self.resultado.value.lower() else (0xB42828 if "derrota" in self.resultado.value.lower() else COLOR_OSCURO)
        embed.color = color
        embed.add_field(name="🎯 Resultado", value=f"**{self.resultado.value}**", inline=True)
        embed.add_field(name="💀 Bajas", value=self.bajas.value, inline=True)
        embed.add_field(name="❌ Errores", value=self.errores.value, inline=False)
        embed.add_field(name="✅ Aciertos", value=self.aciertos.value, inline=False)
        embed.set_footer(text=f"Redactada por {interaction.user.display_name} • {ahora_fmt()}")
        if canal:
            await canal.send(embed=embed)
        await interaction.response.send_message("✅ Acta publicada.", ephemeral=True)


class Operaciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="operacion-crear", description="Crea y publica una nueva operación")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def operacion_crear(self, interaction: discord.Interaction,
                               nombre: str, fecha: str, hora: str,
                               mapa: str, descripcion: str):
        if not es_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede crear operaciones.", ephemeral=True)
            return

        op_id = str(uuid.uuid4())[:8]
        embed = discord.Embed(
            title=f"⚔️ OPERACIÓN: {nombre.upper()}",
            description=descripcion,
            color=COLOR_MILITAR,
        )
        embed.add_field(name="📅 Fecha", value=fecha, inline=True)
        embed.add_field(name="⏰ Hora", value=hora, inline=True)
        embed.add_field(name="🗺️ Mapa", value=mapa, inline=True)
        embed.add_field(name="✅ Confirmados", value="Nadie aún — sé el primero", inline=False)
        embed.set_footer(text=f"ID: {op_id} • Publicado por {interaction.user.display_name}")
        embed.timestamp = datetime.datetime.now()

        canal_anuncios = interaction.guild.get_channel(CANAL_ANUNCIOS_ID)
        canal_ops      = interaction.guild.get_channel(CANAL_OPERACIONES_ID)

        view = ConfirmarAsistencia(op_id)
        msg = await (canal_anuncios or interaction.channel).send(embed=embed, view=view)

        ops = cargar("operaciones.json")
        ops[op_id] = {
            "nombre": nombre, "fecha": fecha, "hora": hora,
            "mapa": mapa, "descripcion": descripcion,
            "confirmados": [], "creador": str(interaction.user.id),
            "message_id": str(msg.id), "channel_id": str(msg.channel.id),
            "fecha_creacion": ahora(),
        }
        guardar("operaciones.json", ops)

        # Actualizar calendario
        if canal_ops:
            await self._actualizar_calendario(interaction.guild, canal_ops)

        await interaction.response.send_message(f"✅ Operación `{nombre}` publicada. ID: `{op_id}`", ephemeral=True)

    @app_commands.command(name="operacion-listar", description="Lista las próximas operaciones")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def operacion_listar(self, interaction: discord.Interaction):
        ops = cargar("operaciones.json")
        if not ops:
            await interaction.response.send_message("📭 No hay operaciones registradas.", ephemeral=True)
            return
        embed = discord.Embed(title="📅 Próximas Operaciones", color=COLOR_MILITAR)
        for op_id, op in list(ops.items())[-10:]:
            embed.add_field(
                name=f"⚔️ {op['nombre']}",
                value=f"📅 {op['fecha']} ⏰ {op['hora']} | 🗺️ {op['mapa']} | ✅ {len(op.get('confirmados', []))} confirmados",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="asistencia", description="Registra asistencia real de una operación")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def asistencia(self, interaction: discord.Interaction, op_id: str,
                          asistentes: str, ausentes: str):
        if not es_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede registrar asistencia.", ephemeral=True)
            return
        asistencia = cargar("asistencia.json")
        lista_asistentes = [uid.strip().strip("<@>!") for uid in asistentes.split(",") if uid.strip()]
        lista_ausentes   = [uid.strip().strip("<@>!") for uid in ausentes.split(",") if uid.strip()]

        asistencia[op_id] = {
            "asistio": lista_asistentes,
            "ausente": lista_ausentes,
            "registrado_por": str(interaction.user.id),
            "fecha": ahora_fmt(),
        }
        guardar("asistencia.json", asistencia)

        # Dar puntos a quienes asistieron
        perfiles = cargar("perfiles.json")
        for uid in lista_asistentes:
            sumar_puntos(uid, 5, f"Asistencia a operación {op_id}")
            if uid in perfiles:
                perfiles[uid]["misiones"] = perfiles[uid].get("misiones", 0) + 1
        guardar("perfiles.json", perfiles)

        await interaction.response.send_message(
            f"✅ Asistencia registrada para operación `{op_id}`.\n"
            f"Asistentes: {len(lista_asistentes)} | Ausentes: {len(lista_ausentes)}\n"
            f"+5 puntos de honor para cada asistente.",
            ephemeral=True,
        )

    @app_commands.command(name="acta", description="Redacta el acta de una operación finalizada")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def acta(self, interaction: discord.Interaction):
        if not es_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede redactar actas.", ephemeral=True)
            return
        await interaction.response.send_modal(ActaModal())

    def _estado_operacion(self, fecha_str: str, hora_str: str):
        """Devuelve (emoji, etiqueta, color) según si la op es futura, hoy o pasada."""
        try:
            dt = datetime.datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M")
        except ValueError:
            try:
                dt = datetime.datetime.strptime(fecha_str, "%d/%m/%Y")
            except ValueError:
                return "🟡", "Sin fecha", COLOR_MILITAR
        now = datetime.datetime.now()
        diff = (dt.date() - now.date()).days
        if diff < 0:
            return "🔴", "Finalizada", 0x555555
        elif diff == 0:
            return "🟢", "HOY", COLOR_VERDE
        elif diff <= 3:
            return "🟠", f"En {diff}d", 0xE07B00
        else:
            return "🔵", f"En {diff}d", COLOR_MILITAR

    async def _actualizar_calendario(self, guild: discord.Guild, canal: discord.TextChannel):
        ops = cargar("operaciones.json")
        config = cargar("config.json")
        banner_url = config.get(CALENDARIO_IMAGE_KEY, BANNER_DEFAULT)

        # Filtrar: mostrar solo las últimas 6 (priorizando futuras)
        todas = list(ops.items())
        futuras = []
        pasadas = []
        for op_id, op in todas:
            try:
                dt = datetime.datetime.strptime(f"{op['fecha']} {op['hora']}", "%d/%m/%Y %H:%M")
                if dt >= datetime.datetime.now():
                    futuras.append((op_id, op))
                else:
                    pasadas.append((op_id, op))
            except ValueError:
                futuras.append((op_id, op))

        # Mostrar primero las futuras, luego las pasadas recientes
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
            for op_id, op in mostrar:
                emoji_estado, etiqueta, _ = self._estado_operacion(op.get("fecha",""), op.get("hora",""))
                confirmados = len(op.get("confirmados", []))
                nombre = op.get("nombre", "—").upper()
                embed.add_field(
                    name=f"{emoji_estado}  {nombre}  ·  `{etiqueta}`",
                    value=(
                        f"📅 **Fecha:** {op.get('fecha','—')}  ·  ⏰ **Hora:** {op.get('hora','—')}\n"
                        f"🗺️ **Mapa:** {op.get('mapa','—')}\n"
                        f"✅ **Confirmados:** {confirmados} miembro{'s' if confirmados != 1 else ''}"
                    ),
                    inline=False,
                )

        embed.set_image(url=banner_url)
        embed.set_footer(
            text=f"🕐 Actualizado: {ahora_fmt()}  ·  Clan Lord",
            icon_url=guild.icon.url if guild.icon else discord.Embed.Empty,
        )

        async for msg in canal.history(limit=15):
            if msg.author == guild.me:
                await msg.edit(embed=embed)
                return
        await canal.send(embed=embed)

    @app_commands.command(name="calendario-imagen", description="Cambia la imagen del calendario de operaciones")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def calendario_imagen(self, interaction: discord.Interaction, url: str):
        if not es_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede cambiar la imagen.", ephemeral=True)
            return
        config = cargar("config.json")
        config[CALENDARIO_IMAGE_KEY] = url
        guardar("config.json", config)
        canal_ops = interaction.guild.get_channel(CANAL_OPERACIONES_ID)
        if canal_ops:
            await self._actualizar_calendario(interaction.guild, canal_ops)
        await interaction.response.send_message("✅ Imagen del calendario actualizada.", ephemeral=True)

    @app_commands.command(name="calendario-actualizar", description="Refresca el calendario de operaciones")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def calendario_actualizar(self, interaction: discord.Interaction):
        if not es_mando(interaction):
            await interaction.response.send_message("❌ Solo el mando puede refrescar el calendario.", ephemeral=True)
            return
        canal_ops = interaction.guild.get_channel(CANAL_OPERACIONES_ID)
        if not canal_ops:
            await interaction.response.send_message("❌ Canal de operaciones no encontrado.", ephemeral=True)
            return
        await self._actualizar_calendario(interaction.guild, canal_ops)
        await interaction.response.send_message("✅ Calendario actualizado.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Operaciones(bot))
