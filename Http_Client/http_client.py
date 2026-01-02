import requests
from random import uniform
import time

from .user_agents import get_random_user_agent, mutate_user_agent_prefix


class NewsHTTPClient:
    """Cliente HTTP simple para las peticiones de scraping."""

    def __init__(self, timeout=15, delay=0.5):
        self.timeout = timeout
        self.delay = delay  # Máximo 0.5s, pero usamos random(0, 0.5)

    def get(self, url, headers=None, ua_category: str = None, 
            mutate_ua_prefix: bool = False, allow_bots: bool = False, **kwargs):
        """Realiza una GET con rotación de User-Agent."""

        if headers is None:
            headers = {}

        # Si el usuario solicita explícitamente categoría 'bot' y no está permitido, fallar rápido
        if ua_category and ua_category.lower() in ('bot', 'bots') and not allow_bots:
            raise ValueError("ua_category 'bot' está deshabilitado. Pasa allow_bots=True para habilitarlo.")

        # Añadir User-Agent aleatorio si no viene en headers
        if 'User-Agent' not in {k.title(): v for k, v in headers.items()}:
            ua = get_random_user_agent(ua_category) if not (ua_category and ua_category.lower() in ('bot','bots')) else get_random_user_agent('bot')
            if mutate_ua_prefix:
                ua = mutate_user_agent_prefix(ua)
            headers['User-Agent'] = ua

        # 🎯 Delay ALEATORIO entre 0 y 0.5 segundos
        time.sleep(uniform(0, 0.5))

        return requests.get(url, headers=headers, timeout=self.timeout, **kwargs)
