from Scraper.Base_Scraper import NewsScraperBase
from urllib.parse import urljoin
import re

class VeinteMinutosScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('20minutos.es')

    def _scrape_list_articles(self, soup, base_url):
        results = []
        main = soup.find('main') or soup
        articles = main.find_all('article')[:30]
        for article in articles:
            title_tag = article.find(['h2', 'h3', 'h1'])
            a_tag = title_tag.find('a') if title_tag else article.find('a')
            if not a_tag:
                continue
            title = self.text.cleantext(a_tag.get('title') or a_tag.text)
            if not title or len(title) < 6:
                continue
            link = a_tag.get('href', '')
            if link.startswith('/'):
                link = urljoin('https://www.20minutos.es', link)
            elif not link.startswith('http'):
                continue

            list_author = ''
            auth_card = article.select_one('.autor, .byline, .meta__autor')
            if auth_card:
                list_author = self.text.cleantext(auth_card)

            time_tag = article.find('time')
            date_raw = time_tag.get('datetime') if time_tag else ''
            datetimestr = self.date.normalizedatetime(date_raw)

            details = self.scrape_article_details(link)
            final_title = details.get('title', title) or title
            final_author = details.get('author', list_author) or list_author

            articleid = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('20Minutos', datetimestr, final_title)

            ordered = self.article.create_ordered_article(
                '20 Minutos', articleid, datetimestr, details.get('tags', []),
                final_title, details.get('subtitle', ''), link, final_author,
                details.get('image', {'url': '', 'credits': ''}),
                details.get('body', '')
            )
            results.append(ordered)
        return results[:30]

    def _scrape_article_details(self, soup):
        # TITLE
        title_elem = soup.find('h1') or soup.find(['h2', 'h3'])
        title = self.text.cleantext(title_elem) if title_elem else ''

        # SUBTITLE
        # 20minutos usa varios patrones: p.lead, div.lead, h2.subtitulo, p.subtitle o metatags (og:description)
        subtitle_elem = (
            soup.select_one('p.lead') or
            soup.select_one('div.lead') or
            soup.select_one('p.subtitle') or
            soup.select_one('h2.subtitulo') or
            soup.select_one('.subtitle') or
            None
        )
        subtitle = self.text.cleantext(subtitle_elem) if subtitle_elem else ''
        # Fallbacks adicionales: meta description u og:description
        if not subtitle:
            meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', property='og:description') or soup.find('meta', property='og:description')
            if meta_desc:
                subtitle = (meta_desc.get('content') or '').strip()
        # Fallback: buscar en header palabras clave (ej. header p.lead o header h2)
        if not subtitle:
            header = soup.find('header') or soup.find('div', class_=re.compile(r'(entry-header|article-header|cabecera)'))
            if header:
                h_p = header.select_one('p.lead, p.subtitle, h2, h3')
                if h_p:
                    subtitle = self.text.cleantext(h_p)

        # AUTHOR
        author = ''
        auth = soup.select_one('a[rel="author"], .autor, .author, .byline')
        if auth:
            author = self.text.cleantext(auth)
        else:
            meta_author = soup.find('meta', attrs={'name': 'author'})
            if meta_author:
                author = meta_author.get('content', '').strip()

        # TAGS
        tags = []
        tag_container = soup.select_one('.tags, ul.tags, .etiquetas')
        if tag_container:
            tags = [self.text.cleantext(a) for a in tag_container.find_all('a')][:8]
        else:
            meta_tags = soup.find_all('meta', attrs={'property': 'article:tag'})
            tags = [t.get('content', '').strip() for t in meta_tags if t.get('content')] [:8]

        # BODY: 20minutos suele usar .article__body o .entry-content
        body_container = (soup.find('div', class_=re.compile(r'(article__body|entry-content|article-body|cuerpo|contenido)'))
                          or soup.find('article') or soup.find('main'))
        paragraphs = []
        if body_container:
            paragraphs = body_container.find_all('p')[:40]
        else:
            paragraphs = soup.find_all('p')[:40]

        body_parts = []
        for p in paragraphs:
            t = self.text.cleantext(p)
            if not t:
                continue
            low = t.lower()
            if 'publicidad' in low and len(t) < 60:
                continue
            if len(t.split()) < 6:
                continue
            body_parts.append(t)
        body = ' '.join(body_parts)[:6000]

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
    tm = VeinteMinutosScraper()
    app = NewsFlaskApp(tm, "20 Minutos", 5014, ["20minutos.es"])
    app.run()