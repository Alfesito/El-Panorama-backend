import hashlib

# Alfabeto base62 (0-9 A-Z a-z) — sólo caracteres alfanuméricos, por tanto URL-safe
_BASE62_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

class IDUtils:
    @staticmethod
    def _int_to_base62(num: int, length: int) -> str:
        """Convierte un entero a base62 y lo rellena a la longitud indicada.

        Devuelve siempre una cadena de `length` caracteres (p. ej. 6).
        """
        if num < 0:
            raise ValueError("num must be non-negative")
        base = len(_BASE62_ALPHABET)
        chars = []
        while num > 0:
            num, rem = divmod(num, base)
            chars.append(_BASE62_ALPHABET[rem])
        # Rellenar con '0' (carácter 0 del alfabeto) si hace falta
        while len(chars) < length:
            chars.append(_BASE62_ALPHABET[0])
        return ''.join(reversed(chars))[:length]

    @staticmethod
    def generate_id_from_url(url: str, length: int = 6) -> str:
        """Genera un ID determinístico y URL-safe a partir de una URL.

        Algoritmo (resumen):
        1) Calcular MD5 de la URL (digest de 16 bytes).
        2) Convertir el digest a entero (big-endian).
        3) Tomar el entero módulo 62**length para limitar el espacio (exactamente length chars).
        4) Codificar el resultado en base62 y rellenar a `length` caracteres.

        Propiedades:
        - Determinístico: la misma URL siempre produce el mismo ID.
        - URL-safe: sólo usa caracteres alfanuméricos (0-9A-Za-z).
        - Compacto: length=6 → 62**6 ≈ 56.8 mil millones de combinaciones.
        - Resistencia a colisiones práctica: usar MD5 reduce la probabilidad de colisión
          en comparación con truncar la URL directamente; sin embargo, 6 caracteres
          siguen limitando la entropía (si necesitas menor probabilidad de colisión,
          aumenta `length` a 7 u 8).

        Nota: MD5 no es seguro criptográficamente frente a colisiones intencionadas, pero
        para generar IDs derivados de URLs en un sistema de scraping (no para seguridad)
        es una solución práctica, rápida y determinística.

        Ejemplo: generate_id_from_url('https://elpais.com/...') -> '1Az9B0'
        """
        if not url:
            raise ValueError("URL vacía no puede generar ID")

        digest = hashlib.md5(url.encode('utf-8')).digest()
        digest_int = int.from_bytes(digest, byteorder='big', signed=False)
        mod = 62 ** length
        reduced = digest_int % mod
        return IDUtils._int_to_base62(reduced, length)

    @staticmethod
    def generateshortid(newspaper, datetimestr, title, url: str = None, length: int = 6):
        """Compatibilidad hacia atrás: genera un ID de `length` caracteres.

        Si se pasa `url`, se delega en `generate_id_from_url` (recomendado).
        Si no, se usa una versión determinística basada en MD5 del contenido
        `{datetimestr}{title[:30]}{newspaper}` para mantener comportamiento previo.
        """
        if url:
            return IDUtils.generate_id_from_url(url, length)
        content = f"{datetimestr}{title[:30]}{newspaper}"
        digest = hashlib.md5(content.encode('utf-8')).digest()
        digest_int = int.from_bytes(digest, byteorder='big', signed=False)
        reduced = digest_int % (62 ** length)
        return IDUtils._int_to_base62(reduced, length)
