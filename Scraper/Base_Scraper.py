from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from Http_Client.http_client import NewsHTTPClient
from Utils.Text_Utils import TextUtils
from Utils.Date_Utils import DateUtils
from Utils.Id_Utils import IDUtils
from Utils.Article_Utils import ArticleUtils
from Utils.Image_Utils import ImageUtils

class NewsScraperBase(ABC):
    def __init__(self, name):
        self.name = name
        self.http = NewsHTTPClient()
        self.text = TextUtils()
        self.date = DateUtils()
        self.idgen = IDUtils()
        self.article = ArticleUtils()
        self.image = ImageUtils()
    
    def get_page(self, url):
        """ÚNICA función HTTP simple con validación URL."""
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"URL inválida: {url}. Debe empezar con http:// o https://")
        
        resp = self.http.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')

    
    def scrape_list_page(self, url):
        """Llama SOLO a método específico de subclase."""
        soup = self.get_page(url)
        return self._scrape_list_articles(soup, url)
    
    def scrape_article_details(self, url):
        """Llama SOLO a método específico de subclase."""
        soup = self.get_page(url)
        return self._scrape_article_details(soup)

    def enrich_article(self, article):
        """Implementación por defecto para enriquecer un artículo de lista.

        - Si `article` no tiene `url`, devuelve el artículo sin cambios.
        - Llama a `scrape_article_details` y fusiona los campos relevantes.
        """
        if not article or not article.get('url'):
            return article

        try:
            details = self.scrape_article_details(article['url'])
        except Exception:
            return article

        # Solo sobrescribir campos cuando los detalles contengan valores no vacíos.
        article['subtitle'] = details.get('subtitle') or article.get('subtitle', '')
        article['author'] = details.get('author') or article.get('author', 'Redacción')
        article['title'] = details.get('title') or article.get('title', '')
        article['tags'] = details.get('tags') or article.get('tags', [])
        article['body'] = details.get('body') or article.get('body', '')

        # Mezclar imagenes: conservar datos de la tarjeta si detalle no aporta valores
        existing_image = article.get('image') or {'url': '', 'credits': ''}
        details_image = details.get('image') or {}
        merged_image = existing_image.copy()
        for k, v in details_image.items():
            if v:  # sólo sobrescribir si el campo no está vacío
                merged_image[k] = v

        # Normalizar y juntar todos los campos relevantes en `credits`
        parts = [
            existing_image.get('credits', ''),
            existing_image.get('alt', ''),
            existing_image.get('description', ''),
            details_image.get('credits', ''),
            details_image.get('alt', ''),
            details_image.get('description', '')
        ]
        credits = self.image.format_credits(*parts)

        # Devolver solo url y credits
        final_image = {
            'url': merged_image.get('url', ''),
            'credits': credits
        }

        article['image'] = final_image

        return article
    
    @abstractmethod
    def _scrape_list_articles(self, soup, base_url):
        """EACH scraper define EXACTAMENTE cómo."""
        pass
    
    @abstractmethod
    def _scrape_article_details(self, soup):
        """EACH scraper define EXACTAMENTE cómo."""
        pass
