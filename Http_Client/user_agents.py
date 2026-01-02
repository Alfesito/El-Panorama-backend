"""Lista extensa de User-Agents agrupada y funciones utilitarias.

Incluye muchas variantes: desktop, mobile, tablet, bots, headless, curl/wget, electron y SmartTV.
Exporta funciones:
- get_random_user_agent(category=None)
- get_all_user_agents()
- get_user_agents_by_category(category)
- get_categories()
- get_sequential_user_agent_generator(category=None)

Diseñado para usarse desde `NewsHTTPClient`. Añade cobertura amplia para pruebas y simulación de distintos dispositivos.
"""
from random import choice
import itertools

# Desktop: Chrome, Firefox, Safari, Edge, Opera, Vivaldi, Brave
_DESKTOP = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) OPR/82.0.4396.61',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Brave/1.50.0 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Vivaldi/6.0 Chrome/120.0.0.0 Safari/537.36'
]

# Mobile: iPhone, Android Chrome, Samsung Browser, UC Browser
_MOBILE = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 SamsungBrowser/20.0',
    'Mozilla/5.0 (Linux; U; Android 10; es-es; SM-A505FN Build/QP1A) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.106 Mobile Safari/537.36 UCBrowser/13.3.8.1306'
]

# Tablet: iPad, Android tablets
_TABLET = [
    'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Android 12; Tablet; rv:120.0) Gecko/120.0 Firefox/120.0',
    'Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/20.0 Chrome/120.0 Safari/537.36'
]

# Headless and command-line tools
_HEADLESS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'curl/7.79.1',
    'Wget/1.21.3 (linux-gnu)'
]

# Electron / Node based apps
_ELECTRON = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Electron/25.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Electron/24.0.0 Chrome/118.0.0.0 Safari/537.36'
]

# SmartTV / Set-top boxes
_SMARTTV = [
    'Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 TV Safari/537.36',
    'Mozilla/5.0 (Web0S; Linux; LG NetCast) AppleWebKit/537.36 (KHTML, like Gecko) Web0S/2.0 Safari/537.36',
    'Roku/DVP-9.20 (Roku 3)'
]

# Mapear categorías a listas (case-insensitive keys)
_CATEGORIES = {
    'desktop': _DESKTOP,
    'mobile': _MOBILE,
    'tablet': _TABLET,
    'headless': _HEADLESS,
    'electron': _ELECTRON,
    'smarttv': _SMARTTV,
    # alias y subcategorías
    'chrome': [ua for ua in _DESKTOP if 'Chrome' in ua],
    'firefox': [ua for ua in _DESKTOP if 'Firefox' in ua],
    'safari': [ua for ua in _DESKTOP if 'Safari' in ua and 'Chrome' not in ua],
    'edge': [ua for ua in _DESKTOP if 'Edg' in ua],
    'opera': [ua for ua in _DESKTOP if 'OPR/' in ua],
    'samsung': [ua for ua in _MOBILE + _TABLET if 'SamsungBrowser' in ua or 'SAMSUNG' in ua],
    'curl': [ua for ua in _HEADLESS if ua.lower().startswith('curl')],
    'wget': [ua for ua in _HEADLESS if ua.lower().startswith('wget')]
}

# Lista combinada (note: *excluye* bots por defecto)
_ALL = _DESKTOP + _MOBILE + _TABLET #+ _HEADLESS + _ELECTRON + _SMARTTV


def get_categories():
    """Devuelve las categorías disponibles."""
    return list(_CATEGORIES.keys())


def get_all_user_agents(include_bots: bool = False):
    """Devuelve todas las user-agents conocidas.

    Por defecto **excluye** las user-agents tipo bot/sistema. Para incluir bots,
    pasa `include_bots=True`.
    """
    pool = list(_ALL)
    if include_bots:
        pool = pool
    return pool


def get_user_agents_by_category(category: str):
    """Devuelve la lista de user-agents para la categoría dada (case-insensitive)."""
    if not category:
        return get_all_user_agents()
    return list(_CATEGORIES.get(category.lower(), []))


def get_random_user_agent(category: str = None):
    """Devuelve una user-agent aleatoria.

    Si `category` es None se selecciona de todas; si es una categoría conocida se selecciona de esa categoría.
    """
    pool = get_user_agents_by_category(category) if category else get_all_user_agents()
    if not pool:
        pool = get_all_user_agents()
    return choice(pool)


# Prefijos alternativos que pueden reemplazar el "Mozilla/5.0" para diversidad adicional
# Incluye los prefijos más usados: Chrome/HeadlessChrome, Edg (Edge), Safari, Opera (OPR/),
# Dalvik/Android, AndroidWebView, Python-urllib, python-requests, Go-http-client, curl, wget,
# así como agentes antiguos o de herramientas (Lynx, W3C validator).
_PREFIX_ALTERNATIVES = [
    'Mozilla/5.0',
    'Mozilla/4.0',
    'Chrome/120.0.0.0',
    'HeadlessChrome/120.0.0.0',
    'Edg/120.0.0.0',
    'Safari/605.1.15',
    'OPR/82.0.4396.61',
    'Dalvik/2.1.0',
    'AndroidWebView/120.0.0.0',
    'Python-urllib/3.10',
    'python-requests/2.31.0',
    'Go-http-client/1.1',
    'curl/7.79.1',
    'Wget/1.21.3',
    'Lynx/2.8.9rel.1 libwww-FM/2.14',
    'W3C_Validator/1.3',
    'AppName/1.0'
]


def mutate_user_agent_prefix(ua: str, allow_empty_prefix: bool = False) -> str:
    """Devuelve una versión del User-Agent con el prefijo (antes del primer espacio)
    aleatoriamente reemplazado por uno de los valores en `_PREFIX_ALTERNATIVES`.

    - Si el UA no contiene espacios (p. ej. 'curl/7.79.1'), devuelve la cadena original
      a menos que `allow_empty_prefix` sea True, en cuyo caso se antepone un prefijo.
    - No toca UAs de tipo bot a menos que se solicite explícitamente.
    """
    if not ua or not isinstance(ua, str):
        return ua

    # UAs tipo bot o simples (sin espacios) no los tocamos por defecto
    if ua.lower().startswith('curl') or ua.lower().startswith('wget') or 'bot' in ua.lower():
        return ua

    parts = ua.split(' ', 1)
    if len(parts) == 1:
        if not allow_empty_prefix:
            return ua
        prefix = choice(_PREFIX_ALTERNATIVES)
        return f"{prefix} {ua}"

    # Reemplazar el prefix (p. ej. 'Mozilla/5.0') por uno aleatorio
    new_prefix = choice(_PREFIX_ALTERNATIVES)
    return f"{new_prefix} {parts[1]}"


def get_sequential_user_agent_generator(category: str = None):
    """Devuelve un generador cíclico (itertools.cycle) que itera por la categoría dada.

    Útil para tests reproducibles o simular distintos agentes en secuencia.
    """
    pool = get_user_agents_by_category(category) if category else get_all_user_agents()
    if not pool:
        pool = get_all_user_agents()
    return itertools.cycle(pool)
