from Scraper.Base_Scraper import NewsScraperBase
from urllib.parse import urljoin
import re

class ElEspanolScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('elespanol.com')

    def _scrape_list_articles(self, soup, base_url):
        results = []
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
                link = urljoin('https://www.elespanol.com', link)
            elif not link.startswith('http'):
                continue

            # autor en tarjeta
            list_author = ''
            auth_card = article.select_one('.author, .autor, .byline')
            if auth_card:
                list_author = self.text.cleantext(auth_card)

            # fecha
            time_tag = article.find('time')
            date_raw = time_tag.get('datetime') if time_tag else ''
            datetimestr = self.date.normalizedatetime(date_raw)

            details = self.scrape_article_details(link)
            final_title = details.get('title', title) or title
            final_author = details.get('author', list_author) or list_author

            articleid = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('ElEspanol', datetimestr, final_title)

            ordered = self.article.create_ordered_article(
                'El Español', articleid, datetimestr, details.get('tags', []),
                final_title, details.get('subtitle', ''), link, final_author,
                details.get('image', {'url': '', 'credits': ''}),
                details.get('body', '')
            )
            results.append(ordered)
        return results

    def _scrape_article_details(self, soup):
        # TITLE
        title_elem = soup.find(['h1', 'h2'])
        title = self.text.cleantext(title_elem) if title_elem else ''

        # SUBTITLE
        subtitle_elem = (soup.select_one('p.subtitulo') or soup.select_one('p.lead') or soup.find('h2'))
        subtitle = self.text.cleantext(subtitle_elem) if subtitle_elem else ''

        # AUTHOR
        author = ''
        auth = soup.select_one('a[rel="author"], .author, .autor, .byline')
        if auth:
            author = self.text.cleantext(auth)
        else:
            meta_author = soup.find('meta', attrs={'name': 'author'})
            if meta_author:
                author = meta_author.get('content', '').strip()

        # TAGS
        tags = []
        tag_container = soup.select_one('.tags, .etiquetas, ul.tags')
        if tag_container:
            tags = [self.text.cleantext(a) for a in tag_container.find_all('a')][:8]
        else:
            meta_tags = soup.find_all('meta', attrs={'property': 'article:tag'})
            tags = [t.get('content', '').strip() for t in meta_tags if t.get('content')] [:8]

        # BODY: buscar contenedores comunes y párrafos
        body_container = (soup.find('div', class_=re.compile(r'(article-body|contenido|cuerpo|article-content|article__body)')) or
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

        # IMAGE: usar helper y completar créditos desde figcaption o alt
        image = self.image.extract_image(soup, [
            'figure img[src]', 'img[src].foto, img[src].imagen', 'meta[property="og:image"]'
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
    es = ElEspanolScraper()
    app = NewsFlaskApp(es, "El Español", 5012, ["elespanol.com"])
    app.run()