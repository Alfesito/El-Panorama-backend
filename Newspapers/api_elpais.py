from Scraper.Base_Scraper import NewsScraperBase

class ElPaisScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('El País')
    
    def _scrape_list_articles(self, soup, base_url):
        """TU CÓDIGO ORIGINAL scrape_all_articles EXACTO"""
        results = []
        main = soup.find('main')
        if not main:
            return [{'error': 'No se encontró <main>'}]
        
        sections = main.find_all('section')
        
        for section in sections:
            articles = section.find_all('article')
            for article in articles:
                h2_tag = article.find('h2')
                title_tag = h2_tag.find('a') if h2_tag else None
                list_title = self.text.cleantext(title_tag.text) if title_tag else ''
                link = title_tag.get('href') if title_tag else ''
                
                if not link or not list_title:
                    continue
                
                if link.startswith('/'):
                    link = 'https://elpais.com' + link
                
                metadata_div = article.find('div', recursive=False)
                author = ''
                date_raw = ''
                if metadata_div:
                    author_tags = metadata_div.find_all('a')
                    if author_tags:
                        author = self.text.cleantext(author_tags[0].text)
                    
                    date_spans = metadata_div.find_all('time')
                    if date_spans:
                        date_raw = date_spans[-1].get('datetime') or date_spans[-1].text.strip()
                
                datetime_str = self.date.normalizedatetime(date_raw)
                article_details = self.scrape_article_details(link)
                final_title = article_details.get('title', list_title) or list_title
                article_id = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('ElPais', datetime_str, final_title)
                
                ordered_article = self.article.create_ordered_article(
                    'El País', article_id, datetime_str, article_details.get('tags', []),
                    final_title, article_details.get('subtitle', ''), link, article_details.get('author', author),
                    article_details.get('image', {'url': '', 'credits': ''}),
                    article_details.get('body', '')
                )
                results.append(ordered_article)
        
        return results
    
    def _scrape_article_details(self, soup):
        """TU CÓDIGO ORIGINAL scrape_article_details EXACTO"""
        # TITLE: h1.at
        title_h1 = soup.find('h1', class_='at')
        title = self.text.cleantext(title_h1) if title_h1 else ''
        
        # SUBTITLE: p.ast
        subtitle_p = soup.find('p', class_='ast')
        subtitle = self.text.cleantext(subtitle_p) if subtitle_p else ''
        
        # AUTHOR: extraer de la zona de firma (a_md_a_n) o fallback general
        author = ''
        firma_link = soup.select_one('div.a_md_txt div[data-dtm-region="articulo_firma"] a.a_md_a_n') or soup.select_one('a.a_md_a_n')
        if firma_link:
            author = self.text.cleantext(firma_link)

        # TAGS: section[data-dtm-region="articulo/archivado-en"] li
        tags = []
        archived_section = soup.find('section', {'data-dtm-region': 'articulo_archivado-en'})
        if archived_section:
            tags = [self.text.cleantext(li) for li in archived_section.find_all('li')][:8]
        
        # BODY: div[data-dtm-region="articulo/cuerpo"] p[:15]
        body_paragraphs = []
        cuerpo_section = soup.find('div', {'data-dtm-region': 'articulo_cuerpo'})
        if cuerpo_section:
            body_paragraphs = cuerpo_section.find_all('p')[:15]
        else:
            body_paragraphs = soup.find_all('p', limit=15)
        
        body = ' '.join([self.text.cleantext(p) for p in body_paragraphs 
                        if len(self.text.cleantext(p)) > 30])[:3000]
        
        # IMAGEN ROBUSTA
        image = {'url': '', 'credits': ''}
        main_figure = soup.find('figure', class_='am am-h')
        if main_figure:
            img = main_figure.find('img')
            if img:
                img_url = (img.get('src') or 
                          img.get('data-src') or 
                          self.parse_srcset(img.get('srcset', '')))
                if img_url:
                    credits_span = main_figure.find('span', class_='amm')
                    credits = self.text.cleantext(credits_span) if credits_span else ''
                    image = {'url': img_url, 'credits': credits}
        
        figure = soup.find('figure')
        if figure and not image['url']:
            img = figure.find('img')
            if img:
                img_url = (img.get('src') or 
                          img.get('data-src') or 
                          self.parse_srcset(img.get('srcset', '')))
                credits_span = figure.find('span', class_='amm') or figure.find('figcaption')
                credits = self.text.cleantext(credits_span) if credits_span else ''
                image = {'url': img_url, 'credits': credits}
        
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
    
    def parse_srcset(self, srcset):
        """TU FUNCIÓN ORIGINAL parse_srcset"""
        if not srcset:
            return ''
        urls = srcset.split(',')[0].strip().split(' ')[0]
        if urls.startswith('http'):
            return urls
        return ''

# Flask 
if __name__ == '__main__':
    try:
        from Flask_App.Flask_App import NewsFlaskApp
    except Exception:
        from Flask_App import NewsFlaskApp
    elpais = ElPaisScraper()
    app = NewsFlaskApp(elpais, "El País", 5000, ["elpais.com"])
    app.run()
