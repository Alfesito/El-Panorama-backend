from Scraper.Base_Scraper import NewsScraperBase
from urllib.parse import urljoin
import re

class PublicoScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('publico.es')

    def _scrape_list_articles(self, soup, base_url):
        results = []
        # Intentar encontrar listas de artículos en secciones principales
        main = soup.find('main') or soup
        articles = main.find_all('article')[:25]
        for article in articles:
            # título y enlace
            title_tag = article.find(['h2', 'h3', 'h1'])
            a_tag = title_tag.find('a') if title_tag else article.find('a')
            if not a_tag:
                continue
            title = self.text.cleantext(a_tag.get('title') or a_tag.text)
            if not title or len(title) < 8:
                continue
            link = a_tag.get('href', '')
            if link.startswith('/'):
                link = urljoin('https://www.publico.es', link)
            elif not link.startswith('http'):
                continue

            # autor en la tarjeta
            list_author = ''
            author_tag = article.select_one('.author, .nota__autor, .mod-autor a')
            if author_tag:
                list_author = self.text.cleantext(author_tag)

            # fecha si existe
            time_tag = article.find('time')
            date_raw = time_tag.get('datetime') if time_tag else ''
            datetimestr = self.date.normalizedatetime(date_raw)

            details = self.scrape_article_details(link)
            final_title = details.get('title', title) or title
            final_author = details.get('author', list_author) or list_author

            articleid = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('Publico', datetimestr, final_title)

            ordered = self.article.create_ordered_article(
                'Publico', articleid, datetimestr, details.get('tags', []),
                final_title, details.get('subtitle', ''), link, final_author,
                details.get('image', {'url': '', 'credits': ''}),
                details.get('body', '')
            )
            results.append(ordered)
        return results

    def _scrape_article_details(self, soup):
        # TITLE
        title_elem = soup.find('h1')
        title = self.text.cleantext(title_elem) if title_elem else ''

        # SUBTITLE
        subtitle_elem = (soup.select_one('h2.lead') or 
                         soup.select_one('p.lead') or 
                         soup.find('h2'))
        subtitle = self.text.cleantext(subtitle_elem) if subtitle_elem else ''

        # AUTHOR: buscar zona de firma o enlaces rel=author
        author = ''
        author_selector = ("div.author a, div.autor, span.autor, a[rel='author'], "
                           "div.nota__autor a, .nota__autor, div.a_md_txt a.a_md_a_n, a.a_md_a_n")
        auth_tag = soup.select_one(author_selector)
        if auth_tag:
            author = self.text.cleantext(auth_tag)
        else:
            # fallback meta
            meta_author = soup.find('meta', attrs={'name': 'author'})
            if meta_author:
                author = meta_author.get('content', '').strip()

        # TAGS: buscar listas de tags
        tags = []
        tag_cont = soup.select_one('ul.tags, ul.etiquetas, .tags, .etiquetas')
        if tag_cont:
            tags = [self.text.cleantext(a) for a in tag_cont.find_all('a')][:8]

        # BODY: buscar contenedores comunes
        body_container = (soup.find('div', itemprop='articleBody') or
                          soup.find('div', class_=re.compile(r'(article-body|nota-body|cuerpo|entrada)')) or
                          soup.find('article') or soup.find('main'))
        paragraphs = []
        if body_container:
            paragraphs = body_container.find_all('p')[:30]
        else:
            paragraphs = soup.find_all('p')[:30]

        body_parts = []
        for p in paragraphs:
            t = self.text.cleantext(p)
            if not t:
                continue
            low = t.lower()
            if 'publicidad' in low or 'anuncio' in low:
                continue
            if len(t) < 30:
                continue
            body_parts.append(t)
        body = ' '.join(body_parts)[:5000]

        # IMAGE: intentar usar helper y completar credits desde figcaption o alt
        image = self.image.extract_image(soup, [
            'figure img[src]', 'img[src].foto, img[src].imagen', 'meta[property="og:image"]'
        ])

        if not image.get('credits'):
            caption_text = ''
            caption_author = ''
            # buscar figcaption cercano a la imagen principal
            fig = soup.find('figure')
            figcap = None
            if fig:
                figcap = fig.find('figcaption') or fig.find_next_sibling('figcaption')
            if not figcap:
                figcap = soup.select_one('figcaption')

            if figcap:
                # algunos figcaption tienen span para texto y autor
                txt = figcap.get_text(separator=' ').strip()
                # intentar separar autor si hay
                # ejemplo: "Texto del pie — agencia"
                if '—' in txt:
                    parts = [p.strip() for p in txt.split('—', 1)]
                    caption_text = parts[0]
                    caption_author = parts[1] if len(parts) > 1 else ''
                else:
                    caption_text = txt
                    # intentar extraer span.author dentro de figcap
                    sp = figcap.select_one('.autor, .author')
                    if sp:
                        caption_author = self.text.cleantext(sp)

            # fallback alt
            if not caption_text:
                img_elem = soup.select_one('figure img') or soup.select_one('img')
                if img_elem:
                    caption_text = (img_elem.get('alt') or '').strip()

            image['credits'] = self.image.format_credits(caption_text, caption_author)

        return {
            'title': title,
            'subtitle': subtitle,
            'author': author,
            'tags': tags,
            'body': body,
            'image': image
        }


# Flask
if __name__ == '__main__':
    try:
        from Flask_App.Flask_App import NewsFlaskApp
    except Exception:
        from Flask_App import NewsFlaskApp
    publico = PublicoScraper()
    app = NewsFlaskApp(publico, "Público", 5010, ["publico.es"])
    app.run()
