from Scraper.Base_Scraper import NewsScraperBase
import re


class ElMundoScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('El Mundo')

    def _scrape_list_articles(self, soup, base_url):
        results = []

        # Lista portada
        articles = soup.find_all('article', class_=re.compile(r'ue-c-cover-content'))

        for i, article in enumerate(articles[:25]):
            # Título
            title_h2 = article.find('h2', class_='ue-c-cover-content__headline')
            title = self.text.cleantext(title_h2) if title_h2 else ''

            if not title or len(title) < 10:
                continue

            # Link
            whole_link = article.find('a', class_='ue-c-cover-content__link-whole-content')
            link = whole_link.get('href', '') if whole_link else ''

            if link.startswith('/'):
                link = 'https://www.elmundo.es' + link

            if not link.startswith('http'):
                continue

            # Autor rápido en la lista (fallback)
            author_links = article.find_all('a', href=re.compile(r'autores?'))
            author = self.text.cleantext(author_links[0]) if author_links else 'Redacción'

            # Tags / kicker
            kicker = article.find(class_=re.compile(r'ue-c-cover-content__kicker'))
            tags = [self.text.cleantext(kicker)] if kicker else ['General']

            # Intentar subtítulo desde la tarjeta de portada (si existe)
            subtitle = ''
            # buscar párrafo o elemento con resumen en el item
            p_summary = article.find('p')
            if p_summary:
                subtitle = self.text.cleantext(p_summary)

            # Intentar extraer imagen desde la tarjeta de portada
            image = {'url': '', 'credits': ''}
            img_tag = article.find('img')
            if img_tag:
                img_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-srcset') or img_tag.get('srcset') or ''
                if img_url and ',' in img_url:
                    img_url = img_url.split(',')[0].strip().split(' ')[0]
                image['url'] = img_url
                alt_text = img_tag.get('alt', '')
                # Poner alt en credits inicialmente (por si no se enriquece más tarde)
                image['credits'] = self.image.format_credits(alt_text) 
            # Fecha e ID (ID determinístico a partir de la URL cuando esté disponible)
            date_str = self.date.normalizedatetime()
            article_id = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('ElMundo', date_str, title)

            # Datos básicos sin detalle
            article_data = self.article.create_ordered_article(
                'El Mundo',          # source
                article_id,          # id
                date_str,            # date
                tags[:3],            # tags
                title,               # title
                subtitle,            # subtitle
                link,                # url
                author,              # author (se puede sobreescribir en detalle)
                image,               # image (se rellenará mejor al entrar en el artículo)
                ''                   # body (si no lo usas aquí)
            )
            results.append(article_data)

        return results[:25]

    def _scrape_article_details(self, soup):
        """Extrae subtítulo, autor y datos de imagen (url, credits, alt, description).

        Estrategia:
        - Subtítulo: prioriza `div.ue-c-article__standfirst > p`, si no existe busca
          el primer `p.ue-c-article__paragraph` dentro del header.
        - Autor: busca `.ue-c-article__author-name-item` (limpia texto y toma la primera línea).
        - Imagen: primer `figure` con clase `ue-c-article__media`, obtiene `img[src|data-src|srcset]`,
          `alt`, `figcaption .ue-c-article__media-author` (credits) y
          `.ue-c-article__media-description` (description).
        """

        # Subtítulo: preferir standfirst
        subtitle = ''
        standfirst = soup.find('div', class_='ue-c-article__standfirst')
        if standfirst:
            p = standfirst.find('p')
            subtitle = self.text.cleantext(p) if p else self.text.cleantext(standfirst)
        else:
            header = soup.find('div', class_='ue-l-article__header-content') or soup
            p = header.find('p', class_='ue-c-article__paragraph')
            subtitle = self.text.cleantext(p) if p else ''

        # Autor: preferir el nombre visible (limpiado)
        author = 'Redacción'
        author_div = soup.select_one('.ue-c-article__author-name-item')
        if author_div:
            raw_author = self.text.cleantext(author_div)
            # A veces contiene "Nombre\nEnviado especial ..." -> quedarnos con la primera línea
            author = raw_author.split('\n')[0].strip()
            if not author:
                author = 'Redacción'

        # Imagen: solo url y credits
        image = {'url': '', 'credits': ''}
        fig = soup.find('figure', class_=re.compile(r'ue-c-article__media'))
        if fig:
            img = fig.find('img')
            if img:
                url = img.get('src') or img.get('data-src') or ''
                if not url:
                    srcset = img.get('srcset') or img.get('data-srcset') or ''
                    if srcset:
                        # elegir la primera URL del srcset
                        url = srcset.split(',')[0].strip().split(' ')[0]
                image['url'] = url
                alt_text = img.get('alt', '').strip()

            cap_author = fig.select_one('.ue-c-article__media-author')
            cap_text = self.text.cleantext(cap_author) if cap_author else ''

            desc = fig.select_one('.ue-c-article__media-description')
            desc_text = self.text.cleantext(desc) if desc else ''

            # Unir credits, alt y description en un solo campo `credits`
            image['credits'] = self.image.format_credits(cap_text, alt_text, desc_text)
        # Tags: kicker si existe
        tags = []
        kicker = soup.select_one('.ue-c-article__kicker')
        if kicker:
            tags = [self.text.cleantext(kicker)]

        # Title: si se quisiera, podemos extraer el h1
        title_h1 = soup.find('h1', class_='ue-c-article__headline')
        title = self.text.cleantext(title_h1) if title_h1 else ''

        # Body: buscar contenedor principal del artículo y concatenar párrafos válidos
        body = ''
        body_container = soup.find('div', attrs={'data-section': 'articleBody'}) or soup.find('div', class_=re.compile(r'ue-l-article__body'))
        if body_container:
            paragraphs = []
            for p in body_container.find_all('p'):
                # omitir párrafos que estén dentro de listings, taboola, cover-content o newsletters
                skip = False
                for anc in p.find_parents():
                    cls = anc.get('class') or []
                    if any(re.search(r'listing|taboola|cover-content|newsletter', c) for c in cls):
                        skip = True
                        break
                if skip:
                    continue
                text = self.text.cleantext(p)
                if text:
                    paragraphs.append(text)
            body = '\n\n'.join(paragraphs)

        return {
            'title': title,
            'subtitle': subtitle,
            'author': author,
            'tags': tags,
            'body': body,
            'image': image
        }

    # Enriquecimiento de artículo: usar la implementación por defecto de la clase base (merge conservador)
    # (No se redefine aquí para evitar sobrescribir datos extraídos desde la portada.)

    # Ejemplo de helper si tu Base_Scraper no lo tiene aún
    def fetch_article_details(self, url):
        """
        Descarga el HTML de un artículo y devuelve el dict de _scrape_article_details.
        Llama a esto cuando el usuario entra en un artículo concreto.
        """
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        return self._scrape_article_details(soup)


# Flask
if __name__ == '__main__':
    try:
        from Flask_App.Flask_App import NewsFlaskApp
    except Exception:
        from Flask_App import NewsFlaskApp

    elmundo = ElMundoScraper()
    app = NewsFlaskApp(elmundo, "El Mundo", 5008, ["elmundo.es"])
    app.run()
