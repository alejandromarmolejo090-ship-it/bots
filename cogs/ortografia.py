"""Cog: Policía ortográfica — vergüenza pública para los que no saben escribir."""
import discord
from discord.ext import commands
import re, os, sys, random, datetime
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import cargar, guardar, COLOR_ROJO

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

try:
    from spellchecker import SpellChecker
    _spell = SpellChecker(language="es")
    _spell.word_frequency.load_words([
        "spawn", "sniper", "fragger", "clutch", "rush", "push", "camp", "camper",
        "flanquear", "flanqueo", "grenade", "frag", "lag", "ping", "server",
        "stream", "clip", "gameplay", "loadout", "squad", "okei", "jaja",
        "jajaja", "xd", "lol", "gg", "ok", "np", "btw", "weno", "bro",
        "parce", "dale", "sale", "rip", "meta", "buff", "nerf", "skin",
        "clan", "lord", "hq", "intel", "ops", "vai", "vaina",
    ])
    _SPELL_OK = True
except ImportError:
    _SPELL_OK = False
    print("[Ortografía] pyspellchecker no instalado — pip install pyspellchecker")

# ── Diccionario curado: errores típicos del español latinoamericano ─────────
# Cubre b/v, h, tildes, s/c/z, conjugaciones mal usadas
ERRORES: dict = {
    # B / V — confusión más común en Colombia y Latinoamérica
    "havia":      "había",
    "havia":      "había",
    "havía":      "había",
    "habia":      "había",
    "iva":        "iba",
    "ivan":       "iban",
    "ivas":       "ibas",
    "bamos":      "vamos",
    "boi":        "voy",
    "saver":      "saber",
    "sabia":      "sabía",
    "savias":     "sabías",
    "tubo":       "tuvo",
    "tubieras":   "tuvieras",
    "tubiera":    "tuviera",
    "tubieron":   "tuvieron",
    "haver":      "haber",
    "bolver":     "volver",
    "bolvi":      "volví",
    "bolvia":     "volvía",
    "bolviamos":  "volvíamos",
    "bivir":      "vivir",
    "bive":       "vive",
    "biven":      "viven",
    "bivia":      "vivía",
    "bivian":     "vivían",
    "aber":       "haber",
    "abria":      "abría",
    "abrigo":     "abrigo",   # correcto — no marcar

    # H — omisión o adición incorrecta
    "ablando":    "hablando",
    "ablar":      "hablar",
    "ablaste":    "hablaste",
    "abló":       "habló",
    "abla":       "habla",
    "ablan":      "hablan",
    "acer":       "hacer",
    "haser":      "hacer",
    "haces":      "haces",    # correcto
    "ases":       "haces",
    "asiendo":    "haciendo",
    "acia":       "hacia",
    "echo":       "hecho",
    "echos":      "hechos",
    "iciste":     "hiciste",
    "icieron":    "hicieron",
    "aiga":       "haya",
    "haiga":      "haya",
    "ubiera":     "hubiera",
    "ubieran":    "hubieran",
    "ubieron":    "hubieron",
    "ubo":        "hubo",
    "ube":        "hube",
    "ubiste":     "hubiste",

    # (tildes desactivadas — los soldados son muy perezosos para eso)

    # Conjugaciones mal hechas — muy comunes en informal
    "dijistes":   "dijiste",
    "vinistes":   "viniste",
    "fuistes":    "fuiste",
    "comistes":   "comiste",
    "pusistes":   "pusiste",
    "hicistes":   "hiciste",
    "trajistes":  "trajiste",
    "salistes":   "saliste",
    "llegastes":  "llegaste",
    "fui":        "fui",       # correcto
    "vine":       "vine",      # correcto

    # S / C / Z — ceceo o confusión
    "nesesito":   "necesito",
    "nesecito":   "necesito",
    "nesesidad":  "necesidad",
    "conosco":    "conozco",
    "conoser":    "conocer",
    "conosemos":  "conocemos",
    "nasio":      "nació",
    "nasieron":   "nacieron",
    "naser":      "nacer",
    "empesar":    "empezar",
    "empesar":    "empezar",
    "cruser":     "cruzar",

    # Otros errores frecuentes
    "tube":       "tuve",
    "truje":      "traje",
    "estructure": "estructura",
    "espesialmente": "especialmente",
    "expecialmente": "especialmente",
    "sinceramente": "sinceramente",  # correcto
    "entonce":    "entonces",
    "entonses":   "entonces",
    "osea":       "o sea",
    "ami":        "a mí",
    "ati":        "a ti",
    "porfa":      "por favor",  # slang — no marcar como error
    "vaina":      "vaina",      # correcto en Colombia
}

# Palabras del dict curado que SON correctas (no marcar como error)
_CORRECTAS = {v.lower() for v in ERRORES.values()} | {
    "vino", "vino", "novia", "novio", "abrigo", "fui", "vine", "vamos",
    "haces", "porfa", "vaina",
}

_RE_URL     = re.compile(r"https?://\S+", re.IGNORECASE)
_RE_MENTION = re.compile(r"<[@#!&]?\d+>|<a?:\w+:\d+>")
_RE_CMD     = re.compile(r"^[!/\.\?\\]")
_RE_WORD    = re.compile(r"\b[a-záéíóúüñ]{4,}\b", re.IGNORECASE)

_COOLDOWN_SEG = 600
_cooldowns: dict = {}
_procesados: set = set()
_MIN_FALTAS = 2

INSULTOS = [
    "¡{mention}, PEDAZO DE IGNORANTE REDOMADO! ¿En serio escribiste eso? "
    "¡Eso no es español, es el gemido de alguien que nunca abrió un libro en su puta vida! "
    "¡Eres un escándalo, una vergüenza para el clan y para tu familia entera!",

    "¡ATENCIÓN CLAN, {mention} HA VUELTO A ATACAR EL IDIOMA ESPAÑOL! "
    "¡Este ser infrahumano lleva años hablando español y sigue sin poder escribirlo! "
    "¡Eres lo más inculto que ha pisado este servidor, bestia iletrada sin remedio!",

    "¡{mention}, me has hecho llorar de vergüenza ajena con lo que acabas de escribir! "
    "¡Un chimpancé con las patas atadas escribe mejor que tú! "
    "¡Eres la vergüenza del clan, del idioma y de la especie humana, inútil sin remedio!",

    "¡POR DIOS, {mention}! ¿Qué mierda fue eso que escribiste?! "
    "¡Hasta el corrector automático está llorando porque contigo no hay solución! "
    "¡Eres un caso clínico de analfabetismo funcional, desgracia con uniforme!",

    "¡ESCÁNDALO MAYÚSCULO! {mention} acaba de violar el diccionario en público sin anestesia. "
    "¡Eres tan ignorante que el abecedario te tiene miedo! "
    "¡Inútil, bestia, iletrado — aprende a escribir antes de volver a existir!",

    "¡{mention}, lo que escribiste es tan asqueroso que me ardieron los ojos, el alma y el futuro! "
    "¡Eres la prueba viviente de que el sistema educativo fracasó contigo completamente! "
    "¡Pedazo de analfabeto crónico, vuelve al primer grado ya mismo!",

    "¡Dios mío todopoderoso, {mention}! ¡Con esa ortografía no pasarías ni el primer grado! "
    "¡Eres la razón por la que los profesores piden traslado! "
    "¡Un absoluto desastre humano con el teclado, bestia sin cultura ni vergüenza!",

    "¡MIREN TODOS A {mention}! ¡MÍRENLO! "
    "Este individuo se sienta frente al teclado todos los días y le declara la guerra al idioma español. "
    "¡Eres un fenómeno científico de la estupidez, un milagro de la ignorancia pura y dura!",

    "¡{mention}, cada vez que escribes así, muere un profesor en algún rincón del mundo! "
    "¡Llevas un rastro de educadores traumatizados detrás de ti! "
    "¡Eres un asesino en serie de la gramática, maldito iletrado sin consciencia!",

    "¡ALERTA ROJA ORTOGRÁFICA — NIVEL CATÁSTROFE! {mention} ha vuelto a las andadas. "
    "¡Escribe como si le hubieran enseñado las letras con un ladrillazo en la cabeza! "
    "¡Bestia inculta, animal sin educación, vergüenza pública de este clan!",

    "¡{mention}, tu ortografía es TAN horrible que el autocorrector renunció, "
    "el diccionario te bloqueó y la gramática te puso una orden de alejamiento! "
    "¡Eres irrecuperable, un pozo sin fondo de ignorancia, analfabeto funcional de pacotilla!",

    "¡{mention} acaba de mutilar el español en público con premeditación y alevosía! "
    "¡No tienes vergüenza, no tienes cultura, no tienes diccionario y claramente no tienes cerebro! "
    "¡El peor escritor de toda la historia de este clan, sin ninguna competencia posible!",

    "¡Increíble pero cierto — {mention} lleva vivo todos estos años sin haber aprendido a escribir! "
    "¡Eres la prueba de que se puede sobrevivir siendo un completo inútil lingüístico! "
    "¡Mastuerzo, bodoque, engendro ortográfico — ve a leer algo por primera vez en tu vida!",

    "¡{mention}! ¿Dónde aprendiste a escribir, en un gallinero?! "
    "¡Porque lo que acabas de soltar no existe en ningún idioma conocido por la humanidad! "
    "¡Eres una aberración gramatical con uniforme, el hazmerreír del clan y del diccionario!",

    "¡ATENCIÓN SOLDADOS! {mention} acaba de demostrar que tiene el coeficiente intelectual "
    "de una maceta cuando se trata de escribir. ¡Cada mensaje tuyo es un crimen de lesa ortografía! "
    "¡Desgracia andante, inculto redomado, burro de remate con teclado!",
]


def _detectar_y_corregir(texto: str) -> list:
    """
    Devuelve lista de tuplas (palabra_mal_escrita, corrección).
    Usa primero el diccionario curado (100% preciso) y luego pyspellchecker.
    """
    texto_limpio = _RE_URL.sub("", texto)
    texto_limpio = _RE_MENTION.sub("", texto_limpio)
    palabras = _RE_WORD.findall(texto_limpio)
    if not palabras:
        return []

    resultado = []
    vistas = set()

    for p in palabras:
        pl = p.lower()
        if pl in vistas or pl in _CORRECTAS:
            continue
        vistas.add(pl)

        # 1. Diccionario curado — corrección perfecta garantizada
        if pl in ERRORES:
            corr = ERRORES[pl]
            # Evitar marcar cosas que son correctas en el dict
            if corr.lower() != pl:
                resultado.append((p, corr))
            continue

        # 2. pyspellchecker — solo si la palabra es desconocida Y tiene 5+ letras
        if _SPELL_OK and len(pl) >= 5 and pl not in _CORRECTAS:
            desconocida = _spell.unknown([pl])
            if desconocida:
                sugerencia = _spell.correction(pl)
                # Solo mostrar si la sugerencia es razonablemente cercana (≤2 cambios)
                if sugerencia and sugerencia != pl and _distancia(pl, sugerencia) <= 2:
                    resultado.append((p, sugerencia))

    return resultado


def _distancia(a: str, b: str) -> int:
    """Distancia de Levenshtein simple."""
    if abs(len(a) - len(b)) > 3:
        return 99
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if a[i-1] == b[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def _correcciones_str(pares: list) -> str:
    lineas = []
    for mal, bien in pares[:6]:
        lineas.append(f"❌ ~~{mal}~~ → ✅ **{bien}**")
    return "\n".join(lineas) if lineas else "—"


async def _get_or_create_canal(guild: discord.Guild) -> Optional[discord.TextChannel]:
    config = cargar("config.json")
    cid = config.get("canal_verguenza_id")
    if cid:
        canal = guild.get_channel(int(cid))
        if canal:
            return canal
    try:
        canal = await guild.create_text_channel(
            "muro-de-la-ortografia",
            topic="Registro publico de soldados que no saben escribir. Verguenza eterna.",
            reason="Canal de vergüenza ortográfica — General Lord",
        )
        config["canal_verguenza_id"] = str(canal.id)
        guardar("config.json", config)
        print(f"[Ortografía] Canal creado: #{canal.name}")
        return canal
    except Exception as e:
        print(f"[Ortografía] No se pudo crear el canal: {e}")
        return None


class Ortografia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._canal: Optional[discord.TextChannel] = None

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        self._canal = await _get_or_create_canal(guild)
        if self._canal:
            print(f"[Ortografía] Policía activa — canal: #{self._canal.name}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or message.guild.id != GUILD_ID:
            return
        if _RE_CMD.match(message.content):
            return
        if len(message.content.strip()) < 10:
            return

        # Guard anti-duplicados
        if message.id in _procesados:
            return
        _procesados.add(message.id)
        if len(_procesados) > 500:
            try:
                _procesados.pop()
            except Exception:
                pass

        pares = _detectar_y_corregir(message.content)
        if len(pares) < _MIN_FALTAS:
            return

        uid = str(message.author.id)
        now = datetime.datetime.now().timestamp()

        datos = cargar("ortografia.json")
        if uid not in datos:
            datos[uid] = {"faltas": 0, "ejemplos": []}
        datos[uid]["faltas"] += len(pares)
        datos[uid]["ejemplos"] = (datos[uid]["ejemplos"] + [p[0] for p in pares])[-10:]
        total = datos[uid]["faltas"]
        guardar("ortografia.json", datos)

        if now - _cooldowns.get(uid, 0) < _COOLDOWN_SEG:
            return
        _cooldowns[uid] = now

        if not self._canal:
            self._canal = await _get_or_create_canal(message.guild)
        if not self._canal:
            return

        insulto = random.choice(INSULTOS).format(mention=message.author.mention)

        embed = discord.Embed(
            title="🚨  FALTA DE ORTOGRAFÍA DETECTADA",
            description=insulto,
            color=COLOR_ROJO,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(
            name="💬 Evidencia del crimen",
            value=f"*\"{message.content[:300]}\"*",
            inline=False,
        )
        embed.add_field(
            name="📚 Así se escribe, bestia — toma nota",
            value=_correcciones_str(pares),
            inline=False,
        )
        embed.add_field(
            name="📊 Crímenes acumulados",
            value=f"**{total}** falta{'s' if total != 1 else ''}",
            inline=True,
        )
        embed.add_field(
            name="📍 Canal del crimen",
            value=message.channel.mention,
            inline=True,
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text="Clan Lord · Policía Ortográfica · Vergüenza pública")

        await self._canal.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Ortografia(bot))
