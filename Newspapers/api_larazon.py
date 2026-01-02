from Scraper.Base_Scraper import NewsScraperBase
import re

class LaRazonScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('larazon.es')
    
    def _scrape_list_articles(self, soup, base_url):
        """TU CÓDIGO ORIGINAL scrape_all_articles_larazon EXACTO"""
        results = []
        main_tag = soup.find('main')
        if not main_tag:
            return [{'error': 'No main LaRazon'}]
        
        articles = main_tag.find_all('article', limit=25)
        for article in articles:
            h2_tag = article.find('h2')
            if not h2_tag: 
                continue
            a_tag = h2_tag.find('a')
            if not a_tag: 
                continue
            
            title = self.text.cleantext(a_tag.text.strip())
            link = a_tag.get('href', '')
            if link.startswith('/'): 
                link = 'https://www.larazon.es' + link
            
            metadata_div = article.find('div', class_='article__author')
            list_author = ''
            if metadata_div:
                author_link = metadata_div.find('a')
                list_author = self.text.cleantext(author_link.text) if author_link else ''
            
            time_tag = article.find('time', attrs={'data-module-launcher-config': True})
            date_raw = time_tag.get('data-module-launcher-config') if time_tag else ''
            datetime_str = self.date.normalizedatetime(date_raw)
            
            details = self.scrape_article_details(link)
            final_title = details.get('title', title) or title
            final_author = details.get('author', list_author) or list_author
            
            article_id = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('LaRazon', datetime_str, final_title)
            
            ordered_article = self.article.create_ordered_article(
                'larazon.es', article_id, datetime_str, details.get('tags', []),
                final_title, details.get('subtitle', ''), link, final_author,
                details.get('image', {'url': '', 'credits': ''}),
                details.get('body', '')
            )
            results.append(ordered_article)
        
        return results[:25]
    
    def _scrape_article_details(self, soup):
        """TU CÓDIGO ORIGINAL scrape_article_details_larazon EXACTO"""
        # TITLE: h1.article-maintitle
        title_h1 = soup.find('h1', class_='article-maintitle')
        title = self.text.cleantext(title_h1) if title_h1 else ''
        
        # SUBTÍTULO CORREGIDO: h2.article-main__description
        subtitle_h2 = soup.find('h2', class_='article-main__description')
        subtitle = self.text.cleantext(subtitle_h2) if subtitle_h2 else ''
        
        # AUTHOR
        author_div = soup.find('div', class_='article-authorname')
        author = ''
        if author_div:
            author_link = author_div.find('a')
            author = self.text.cleantext(author_link) if author_link else ''
        
        # TAGS: ul.article-tags-list li a
        tag_list = soup.find('ul', class_='article-tags-list')
        tags = []
        if tag_list:
            tags = [self.text.cleantext(li.find('a').text.strip()) 
                   for li in tag_list.find_all('li') if li.find('a')][:8]
        
        # BODY: múltiples fallbacks para capturar párrafos del artículo
        body_paragraphs = []
        # Buscar contenedor habitual o usar <article>/<main> como fallback
        body_container = (soup.find('div', id='intext') or
                          soup.find('div', class_=re.compile(r'article-maincontent|article-main|article-body')) or
                          soup.find('article') or soup.find('main'))
        if body_container:
            # Preferir párrafos dentro del contenedor
            body_paragraphs = body_container.find_all('p')[:20]
        else:
            # fallback a cualquier párrafo de la página
            body_paragraphs = soup.find_all('p')[:20]
        
        body_texts = []
        for p in body_paragraphs:
            t = self.text.cleantext(p)
            if not t:
                continue
            low = t.lower()
            if 'publicidad' in low or 'anuncio' in low:
                continue
            # aceptar párrafos más cortos (umbral 30) para evitar perder contenidos legítimos
            if len(t) < 30:
                continue
            body_texts.append(t)
        body = ' '.join(body_texts)[:4000]
        
        # IMAGEN: picture img[fotografias-2.larazon.es]
        image = {'url': '', 'credits': ''}
        picture = soup.find('picture')
        if picture:
            img = picture.find('img')
            if img and img.get('src') and 'fotografias-2.larazon.es' in img.get('src', ''):
                img_url = img.get('src')
                figcaption = picture.find_next('figcaption')
                credits = self.text.cleantext(figcaption.get_text(strip=True)) if figcaption else ''
                image = {'url': img_url, 'credits': credits}
        
        img = soup.find('img', src=re.compile(r'fotografias.*larazon\.es'))
        if img and not image['url']:
            image = {'url': img.get('src'), 'credits': ''}
        
        meta_image = soup.find('meta', property='og:image')
        if meta_image and not image['url']:
            image = {'url': meta_image.get('content', ''), 'credits': ''}
        
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
    larazon = LaRazonScraper()
    app = NewsFlaskApp(larazon, "La Razon", 5007, ["larazon.es"])
    app.run()
