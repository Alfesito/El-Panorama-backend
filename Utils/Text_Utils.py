from unidecode import unidecode
import re

class TextUtils:
    @staticmethod
    def cleantext(text):
        """Limpia acentos, espacios múltiples y normaliza texto."""
        if not text:  # ← None o '' → ''
            return ''
        if hasattr(text, 'text'):  # ← Elemento BeautifulSoup
            text = text.text
        cleaned = unidecode(str(text).strip())
        return re.sub(r'\s+', ' ', cleaned)
    
    @staticmethod
    def truncate_text(text, max_chars=3000):
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(' ', 1)[0] + '...'
