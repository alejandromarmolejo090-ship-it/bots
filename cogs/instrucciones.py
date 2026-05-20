"""Cog: Canal de instrucciones del clan LORD."""
import discord
from discord.ext import commands
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, COLOR_MILITAR

GUILD_ID = int(os.getenv("GUILD_ID", "0"))


class Instrucciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return

        config = cargar("config.json")

        # ── Obtener o crear el canal ──────────────────────────────────────────
        canal_id = config.get("canal_instrucciones_id")
        canal    = guild.get_channel(int(canal_id)) if canal_id else None

        if not canal:
            try:
                canal = await guild.create_text_channel(
                    "instrucciones",
                    topic="Guia completa del clan LORD - lee esto antes de preguntar.",
                    reason="Canal de instrucciones creado por General Lord",
                )
                config["canal_instrucciones_id"] = str(canal.id)
                guardar("config.json", config)
                print(f"[Instrucciones] Canal creado: #{canal.name}")
            except Exception as e:
                print(f"[Instrucciones] No se pudo crear el canal: {e}")
                return

        # ── Guard: no republicar si ya existe ────────────────────────────────
        msg_id = config.get("instrucciones_msg_id")
        if msg_id:
            try:
                await canal.fetch_message(int(msg_id))
                print("[Instrucciones] Guía ya publicada — sin cambios.")
                return
            except (discord.NotFound, discord.HTTPException):
                pass

        await self._publicar(canal, config)

    async def _publicar(self, canal: discord.TextChannel, config: dict):
        await canal.purge(limit=30)

        # ══════════════════════════════════════════════════════════════════════
        # 0 · PORTADA
        # ══════════════════════════════════════════════════════════════════════
        e0 = discord.Embed(
            title="📖  GUÍA OFICIAL DEL CLAN LORD",
            description=(
                "Bienvenido al servidor del clan **LORD**. Este canal te explica "
                "**paso a paso** cómo usar el bot General Lord y todo lo que puedes "
                "hacer aquí.\n\n"
                "> 👶 Está escrito tan simple que cualquiera lo puede entender.\n"
                "> 📌 **Léelo completo antes de preguntar.**"
            ),
            color=COLOR_MILITAR,
        )
        e0.set_footer(text="LORD · General Lord Bot · Guía de uso")
        first = await canal.send(embed=e0)

        # ══════════════════════════════════════════════════════════════════════
        # 1 · PANEL DE MIEMBROS
        # ══════════════════════════════════════════════════════════════════════
        e1 = discord.Embed(
            title="👤  PANEL DE MIEMBROS — ¿Qué puedo hacer yo?",
            color=0x1E3A5F,
        )
        e1.description = (
            "Busca el canal del **Panel de Miembros** y verás una serie de botones. "
            "Cada uno hace algo diferente:\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e1.add_field(
            name="📋 Mi Perfil",
            value=(
                "Muestra tu **ficha personal** dentro del clan:\n"
                "• Tu rango actual\n"
                "• Cuántos puntos de honor tienes\n"
                "• Cuántas misiones has hecho\n"
                "• Si tienes sanciones activas\n"
                "*(Solo tú lo puedes ver — nadie más lo ve)*"
            ),
            inline=False,
        )
        e1.add_field(
            name="⭐ Mis Puntos",
            value=(
                "Ver tu **historial de puntos de honor**.\n"
                "Los puntos se ganan así:\n"
                "• +2 por confirmar asistencia a operación o entrenamiento\n"
                "• +2 por subir un clip o video\n"
                "• +5 por asistir a una operación registrada\n"
                "• +10 por ascenso\n"
                "• −3 por escribir en un canal restringido"
            ),
            inline=False,
        )
        e1.add_field(
            name="🏆 Ranking",
            value=(
                "Ve quiénes son los **top 10** con más puntos de honor del clan.\n"
                "¿Quieres salir ahí arriba? Participa activamente."
            ),
            inline=False,
        )
        e1.add_field(
            name="📅 Solicitar Ausencia",
            value=(
                "¿Vas a faltar varios días? Avísale al mando con este botón.\n"
                "Escribe el motivo, la fecha de inicio y cuándo vuelves.\n"
                "El mando lo verá automáticamente."
            ),
            inline=False,
        )
        e1.add_field(
            name="📩 Solicitar al Mando",
            value=(
                "¿Tienes algo que pedir o proponer? Usa este botón.\n"
                "Escribe tu asunto y el mando lo recibirá de forma privada."
            ),
            inline=False,
        )
        e1.add_field(
            name="🚨 Reportar Incidencia",
            value=(
                "¿Alguien se portó mal o pasó algo en el servidor?\n"
                "Repórtalo aquí. Es **completamente confidencial**."
            ),
            inline=False,
        )
        e1.set_footer(text="Todos los botones del Panel de Miembros son privados (solo tú ves la respuesta)")
        await canal.send(embed=e1)

        # ══════════════════════════════════════════════════════════════════════
        # 2 · CANAL DE FOTOS
        # ══════════════════════════════════════════════════════════════════════
        e2 = discord.Embed(
            title="📸  CANAL DE FOTOS — ¿Cómo subo una foto?",
            color=0xB42828,
        )
        e2.description = (
            "El canal de fotos es solo para imágenes.\n"
            "**Si escribes texto allí, el bot lo borrará y te regañará.** 🫡\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e2.add_field(
            name="📤 Paso 1 — Sube tu imagen",
            value="Adjunta una imagen (JPG, PNG, etc.) en el canal de fotos como si fuera un mensaje normal.",
            inline=False,
        )
        e2.add_field(
            name="📂 Paso 2 — Elige la categoría",
            value=(
                "El bot te preguntará en qué categoría va tu foto. "
                "Tienes **2 minutos** para elegir, si no se borra automáticamente.\n\n"
                "• ⚔️ **Operación** — Momentos de misiones reales\n"
                "• 🎯 **Entrenamiento** — Capturas de entrenamientos\n"
                "• 😂 **Meme** — Algo gracioso del juego\n"
                "• ⭐ **Momento Épico** — Algo increíble que pasó"
            ),
            inline=False,
        )
        e2.add_field(
            name="🗳️ Paso 3 — ¡La gente vota!",
            value=(
                "Tu foto aparece publicada y todos pueden votar:\n"
                "• 🔥 **Épico** — Si la foto es increíble\n"
                "• 👍 **Buena** — Si es una buena foto\n"
                "• 😂 **Meme** — Si es graciosa\n\n"
                "Con **5 votos 🔥** tu foto entra al **Hall of Fame** 🏆\n"
                "Cada semana se anuncia la **Foto de la Semana**."
            ),
            inline=False,
        )
        e2.set_footer(text="¡Puedes votar y cambiar tu voto cuando quieras!")
        await canal.send(embed=e2)

        # ══════════════════════════════════════════════════════════════════════
        # 3 · CANAL DE VIDEOS
        # ══════════════════════════════════════════════════════════════════════
        e3 = discord.Embed(
            title="🎬  CANAL DE VIDEOS — ¿Cómo subo un clip?",
            color=0x1E50A0,
        )
        e3.description = (
            "El canal de videos es solo para clips y videos del juego.\n"
            "Acepta archivos de video (mp4, mov, etc.) o links de:\n"
            "YouTube · Twitch · Medal.tv · Streamable · Vimeo\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e3.add_field(
            name="📤 Paso 1 — Sube o pega tu clip",
            value=(
                "• **Archivo de video**: arrástralo al canal igual que un mensaje.\n"
                "• **Link de YouTube/Twitch/etc.**: pega el enlace directamente."
            ),
            inline=False,
        )
        e3.add_field(
            name="📂 Paso 2 — Elige la categoría",
            value=(
                "El bot te pregunta en qué categoría va. Tienes **2 minutos**:\n\n"
                "• ⚔️ **Operación** — Clip de una misión\n"
                "• 🎯 **Habilidad** — Un momento de mucha destreza\n"
                "• 💀 **Fail** — Una cagada épica (ríete de ti mismo)\n"
                "• 😂 **Humor** — Algo gracioso"
            ),
            inline=False,
        )
        e3.add_field(
            name="🗳️ Paso 3 — Votación en vivo",
            value=(
                "El clip queda publicado con una barra de progreso que se actualiza en tiempo real:\n\n"
                "• 🔥 **Épico** — Para los clips increíbles\n"
                "• 👍 **Bueno** — Para los clips buenos\n"
                "• 💀 **Fail** — Para los clips graciosos\n\n"
                "Con **5 votos 🔥** entra al **Hall of Fame** 🏆\n"
                "El **Clip de la Semana** se anuncia cada domingo."
            ),
            inline=False,
        )
        e3.set_footer(text="+2 puntos de honor por cada clip que subas")
        await canal.send(embed=e3)

        # ══════════════════════════════════════════════════════════════════════
        # 4 · ENCUESTAS
        # ══════════════════════════════════════════════════════════════════════
        e4 = discord.Embed(
            title="📊  ENCUESTAS — ¿Cómo voto?",
            color=0x2EB86B,
        )
        e4.description = (
            "El mando publica encuestas en el canal de anuncios para conocer "
            "la opinión del clan. Participar es muy fácil:\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e4.add_field(
            name="🗳️ Cómo votar",
            value=(
                "Busca la encuesta activa en el canal de anuncios.\n"
                "Haz clic en el botón de la opción que quieras: **1️⃣, 2️⃣, 3️⃣ o 4️⃣**\n\n"
                "La barra de progreso se actualiza al instante para todos.\n"
                "**Puedes cambiar tu voto** haciendo clic en otra opción.\n"
                "**Para retirar tu voto** haz clic en la misma opción otra vez."
            ),
            inline=False,
        )
        e4.add_field(
            name="⏳ Cuándo se cierra",
            value=(
                "Cada encuesta tiene un tiempo límite que el mando decide.\n"
                "Cuando se cierre verás **🔒 ENCUESTA CERRADA** y aparecerá 👑 en la opción ganadora.\n"
                "Si intentas votar en una cerrada, el bot te avisará."
            ),
            inline=False,
        )
        e4.set_footer(text="Las encuestas son anónimas — nadie sabe quién votó qué")
        await canal.send(embed=e4)

        # ══════════════════════════════════════════════════════════════════════
        # 5 · OPERACIONES Y ENTRENAMIENTOS
        # ══════════════════════════════════════════════════════════════════════
        e5 = discord.Embed(
            title="⚔️  OPERACIONES Y ENTRENAMIENTOS — ¿Cómo confirmo asistencia?",
            color=0xB48C14,
        )
        e5.description = (
            "Cuando el mando crea una operación o entrenamiento, aparece un anuncio "
            "en el canal correspondiente. Así confirmas tu asistencia:\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e5.add_field(
            name="✅ Confirmar asistencia",
            value=(
                "Haz clic en el botón **✅ Confirmar asistencia** que aparece debajo del anuncio.\n"
                "Recibirás **+2 puntos de honor** por confirmar.\n\n"
                "Si ya confirmaste y quieres **cancelar**, haz clic otra vez en el mismo botón."
            ),
            inline=False,
        )
        e5.add_field(
            name="📅 Calendario de operaciones",
            value=(
                "En el canal de operaciones hay un calendario que se actualiza automáticamente "
                "con todas las operaciones programadas. Revísalo para saber qué viene próximamente."
            ),
            inline=False,
        )
        e5.add_field(
            name="🌍 Horarios por zona horaria",
            value=(
                "Los entrenamientos muestran la hora en **múltiples zonas horarias** automáticamente "
                "para que todos sepan a qué hora es en su país.\n"
                "La hora base siempre es **Colombia (UTC-5)**."
            ),
            inline=False,
        )
        e5.set_footer(text="+5 puntos de honor si el mando registra tu asistencia real a la operación")
        await canal.send(embed=e5)

        # ══════════════════════════════════════════════════════════════════════
        # 6 · REGLAS DE LOS CANALES
        # ══════════════════════════════════════════════════════════════════════
        e6 = discord.Embed(
            title="🚫  REGLAS DE LOS CANALES — Muy importante",
            color=0xCC2222,
        )
        e6.description = (
            "Hay canales donde **no se puede escribir** — son solo para que el bot "
            "publique cosas importantes. Si escribes allí:\n\n"
            "1. El bot **borra tu mensaje al instante**\n"
            "2. Te **regaña públicamente** con mucho carácter 😤\n"
            "3. Pierdes **-3 puntos de honor**\n"
            "4. Si te pasas de 3 infracciones, el bot **crea un canal dedicado "
            "para humillarte públicamente** (Muro de la Pena 🏛️)\n\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            "**Canales donde NO puedes escribir:**"
        )
        e6.add_field(name="📢 Anuncios", value="Solo el bot publica aquí. No comentes.", inline=True)
        e6.add_field(name="📅 Operaciones", value="Solo el bot pone el calendario.", inline=True)
        e6.add_field(name="🎯 Entrenamientos", value="Solo el bot pone los entrenamientos.", inline=True)
        e6.add_field(name="💬 Frases del día", value="Solo el bot publica la frase diaria.", inline=True)
        e6.add_field(name="📰 Boletín", value="Solo el bot publica el boletín semanal.", inline=True)
        e6.add_field(name="📸 Fotos", value="Solo imágenes — texto se borra.", inline=True)
        e6.add_field(name="🎬 Videos", value="Solo videos/links — texto se borra.", inline=True)
        e6.set_footer(text="Si tienes dudas sobre dónde escribir algo, usa el canal general 💬")
        await canal.send(embed=e6)

        # ══════════════════════════════════════════════════════════════════════
        # 7 · SISTEMA DE RANGOS
        # ══════════════════════════════════════════════════════════════════════
        e7 = discord.Embed(
            title="🎖️  SISTEMA DE RANGOS — ¿Cómo subo de rango?",
            color=0x1B5E20,
        )
        e7.description = (
            "El clan LORD tiene una jerarquía militar. Los rangos se otorgan "
            "por **decisión del mando** según tu participación y comportamiento.\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        )
        e7.add_field(
            name="🪖 Rangos de Tropa (Niveles I–VIII)",
            value=(
                "Donde todos empiezan.\n"
                "🔘 Aspirante → Recluta\n"
                "🟡 Soldado Raso → Soldado → Soldado Primero\n"
                "🟠 Cabo → Cabo Primero\n"
                "🔶 Sargento"
            ),
            inline=False,
        )
        e7.add_field(
            name="⭐ Rangos de Superiores (Niveles IX–XI)",
            value="⭐ Teniente → ⭐⭐ Capitán → ⭐⭐⭐ Coronel",
            inline=False,
        )
        e7.add_field(
            name="👑 Rango de Comando (Nivel XII)",
            value="👑 Comandante — Máxima jerarquía del clan.",
            inline=False,
        )
        e7.add_field(
            name="💡 ¿Cómo asciendo?",
            value=(
                "• Participando activamente en operaciones y entrenamientos\n"
                "• Acumulando puntos de honor\n"
                "• Demostrando compromiso y disciplina\n"
                "• El mando evalúa y ejecuta el ascenso desde su panel"
            ),
            inline=False,
        )
        e7.set_footer(text="Consulta el canal de rangos para ver la jerarquía completa")
        await canal.send(embed=e7)

        # ══════════════════════════════════════════════════════════════════════
        # 8 · RESUMEN RÁPIDO
        # ══════════════════════════════════════════════════════════════════════
        e8 = discord.Embed(
            title="⚡  RESUMEN RÁPIDO — Lo más importante",
            color=COLOR_MILITAR,
        )
        e8.description = (
            "Si no leíste nada de arriba, al menos lee esto:\n"
            "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            "✅ **Confirma asistencia** a operaciones y entrenamientos\n"
            "📸 **Solo fotos en el canal de fotos** — no texto\n"
            "🎬 **Solo videos en el canal de videos** — no texto\n"
            "🚫 **No escribas en canales restringidos** — el bot te borra y regaña\n"
            "👤 **Usa el Panel de Miembros** para ver tu perfil y puntos\n"
            "📊 **Vota en las encuestas** del canal de anuncios\n"
            "🎖️ **Sé activo** para subir de rango\n"
            "🤫 **¿Tienes problemas?** Usa el botón Reportar del Panel de Miembros\n\n"
            "> ❓ **¿Aún tienes dudas?** Pregunta en el canal general o usa "
            "el botón **📩 Solicitar al Mando** del Panel de Miembros."
        )
        e8.set_footer(text="LORD · ¡Bienvenido al clan, soldado!")
        await canal.send(embed=e8)

        # Guardar msg_id del primer embed para el guard
        config["instrucciones_msg_id"] = str(first.id)
        guardar("config.json", config)
        print(f"[Instrucciones] Guía publicada en #{canal.name}.")


async def setup(bot):
    await bot.add_cog(Instrucciones(bot))
