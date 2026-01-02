from bs4 import BeautifulSoup

class ImageUtils:
    @staticmethod
    def extract_image(soup, specific_selectors=None):
        """Busca imagen principal con créditos. Fallbacks múltiples."""
        if specific_selectors:
            # Selectores específicos por periódico
            for selector in specific_selectors:
                img = soup.select_one(selector)
                if img and img.get('src'):
                    return {'url': img['src'], 'credits': ''}
        
        # OG fallback universal
        og_image = soup.find('meta', property='og:image')
        if og_image:
            return {'url': og_image.get('content', ''), 'credits': ''}
        
        return {'url': '', 'credits': ''}

    @staticmethod
    def format_credits(*parts):
        """Combina partes relacionadas con la imagen (credits, alt, description) en un único string limpio.

        - Elimina entradas vacías y las repite en orden de aparición.
        - Usa ' — ' como separador.
        """
        seen = set()
        out = []
        for p in parts:
            if not p:
                continue
            s = str(p).strip()
            if not s:
                continue
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        return ' — '.join(out)