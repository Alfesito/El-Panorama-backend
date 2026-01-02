from Scraper.Base_Scraper import NewsScraperBase
from urllib.parse import urljoin
import re

class LaVanguardiaScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('lavanguardia.com')

    def _scrape_list_articles(self, soup, base_url):
        results = []
        main = soup.find('main') or soup
        articles = main.find_all('article')[:25]
        for article in articles:
            title_tag = article.find(['h2', 'h3', 'h1'])
            a_tag = title_tag.find('a') if title_tag else article.find('a')
            if not a_tag:
                continue
            title = self.text.cleantext(a_tag.get('title') or a_tag.text)
            if not title or len(title) < 8:
                continue
            link = a_tag.get('href', '')
            if link.startswith('/'):
                link = urljoin('https://www.lavanguardia.com', link)
            elif not link.startswith('http'):
                continue

            # autor en card
            list_author = ''
            auth_card = article.select_one('.author, .byline, .nota__autor, .autor')
            if auth_card:
                list_author = self.text.cleantext(auth_card)

            time_tag = article.find('time')
            date_raw = time_tag.get('datetime') if time_tag else ''
            datetimestr = self.date.normalizedatetime(date_raw)

            details = self.scrape_article_details(link)
            final_title = details.get('title', title) or title
            final_author = details.get('author', list_author) or list_author

            articleid = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('LaVanguardia', datetimestr, final_title)

            ordered = self.article.create_ordered_article(
                'La Vanguardia', articleid, datetimestr, details.get('tags', []),
                final_title, details.get('subtitle', ''), link, final_author,
                details.get('image', {'url': '', 'credits': ''}),
                details.get('body', '')
            )
            results.append(ordered)
        return results[:25]

    def _scrape_article_details(self, soup):
        # TITLE
        title_elem = soup.find('h1')
        title = self.text.cleantext(title_elem) if title_elem else ''

        # SUBTITLE
        subtitle_elem = (soup.select_one('p.lead') or soup.select_one('h2.subtitulo') or soup.find('h2'))
        subtitle = self.text.cleantext(subtitle_elem) if subtitle_elem else ''

        # AUTHOR: buscar a[rel=author] o .byline o meta[name=author]
        author = ''
        auth = soup.select_one('a[rel="author"], .byline a, .byline, .autor, .nota__autor a')
        if auth:
            author = self.text.cleantext(auth)
        else:
            meta_author = soup.find('meta', attrs={'name': 'author'})
            if meta_author:
                author = meta_author.get('content', '').strip()

        # TAGS
        tags = []
        tag_cont = soup.select_one('ul.tags, ul.etiquetas, .tags, .article-tags')
        if tag_cont:
            tags = [self.text.cleantext(a) for a in tag_cont.find_all('a')][:8]
        else:
            # meta tag fallback
            meta_tags = soup.find_all('meta', attrs={'property': 'article:tag'})
            tags = [t.get('content', '').strip() for t in meta_tags if t.get('content')] [:8]

        # BODY: buscar contenedores habituales y el bloque específico de La Vanguardia
        body_container = (soup.find('div', class_='article-modules') or
                          soup.find('div', itemprop='articleBody') or
                          soup.find('div', class_=re.compile(r'(article-modules|article-body|cuerpo|content|entry|contenido)')) or
                          soup.find('article') or soup.find('main'))
        paragraphs = []
        if body_container:
            # Priorizar párrafos con clase 'paragraph' dentro del módulo, si no hay, tomar cualquier <p>
            paragraphs = body_container.find_all('p', class_=re.compile(r'paragraph')) or body_container.find_all('p')
            paragraphs = paragraphs[:30]
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
            # aceptar párrafos más cortos (umbral 30) y conservar el ritmo original
            if len(t) < 30:
                continue
            body_parts.append(t)
        body = ' '.join(body_parts)[:5000]

        # IMAGE
        image = self.image.extract_image(soup, [
            'figure img[src]', 'img[src].imagen, img[src].foto', 'meta[property="og:image"]'
        ])
        if not image.get('credits'):
            caption_text = ''
            caption_author = ''
            fig = soup.find('figure')
            figcap = None
            if fig:
                figcap = fig.find('figcaption') or fig.find_next_sibling('figcaption')
            if not figcap:
                figcap = soup.select_one('figcaption')

            if figcap:
                txt = figcap.get_text(separator=' ').strip()
                if '—' in txt:
                    parts = [p.strip() for p in txt.split('—', 1)]
                    caption_text = parts[0]
                    caption_author = parts[1] if len(parts) > 1 else ''
                else:
                    caption_text = txt
                    sp = figcap.select_one('.autor, .author')
                    if sp:
                        caption_author = self.text.cleantext(sp)

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
    lv = LaVanguardiaScraper()
    app = NewsFlaskApp(lv, "La Vanguardia", 5011, ["lavanguardia.com"])
    app.run()
