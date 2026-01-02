from Flask_App.Flask_App import NewsFlaskApp
from Scraper.Base_Scraper import NewsScraperBase
import re

class ElDiarioScraper(NewsScraperBase):
    def __init__(self):
        super().__init__('eldiario.es')
    
    def _scrape_list_articles(self, soup, base_url):
        """TU CÓDIGO ORIGINAL scrape_all_articles EXACTO"""
        results = []
        articles = soup.find_all('figure', class_='ni-figure')[:25]
        
        for article in articles:
            title_a = article.find('a')
            if not title_a:
                continue
            title = self.text.cleantext(title_a.text)
            
            link = title_a.get('href', '')
            if link.startswith('/'):
                link = 'https://www.eldiario.es' + link
            
            news_info = article.find('div', class_='news-info')
            author = ''
            date_raw = ''
            if news_info:
                info_wrapper = news_info.find('div', class_='info-wrapper')
                if info_wrapper:
                    authors_p = info_wrapper.find('p', class_='authors')
                    if authors_p:
                        author_link = authors_p.find('a')
                        author = self.text.cleantext(author_link.text) if author_link else ''
                
                time_tag = news_info.find('time')
                date_raw = time_tag.get('datetime') if time_tag else ''
            
            datetime_str = self.date.normalizedatetime(date_raw)
            details = self.scrape_article_details(link)
            final_title = details.get('title', title) or title
            final_author = details.get('author', author) or author
            
            article_id = self.idgen.generate_id_from_url(link) if link else self.idgen.generateshortid('ElDiario', datetime_str, final_title)
            
            ordered_article = self.article.create_ordered_article(
                'eldiario.es', article_id, datetime_str, details.get('tags', []),
                final_title, details.get('subtitle', ''), link, final_author,
                details.get('image', {'url': '', 'credits': ''}),
                details.get('body', '')
            )
            results.append(ordered_article)
        
        return results
    
    def _scrape_article_details(self, soup):
        """TU CÓDIGO ORIGINAL scrape_article_details EXACTO"""
        # TITLE
        title = self.text.cleantext(soup.find('h1', class_='title')) if soup.find('h1', class_='title') else ''
        subtitle = self.text.cleantext(soup.select_one('ul.footer li.subtitle--hasAnchor h2')) if soup.select_one('ul.footer li.subtitle--hasAnchor h2') else ''
        
        # AUTHOR 3 SELECTORES ROBUSTOS
        author = ''
        news_info = soup.find('div', class_='news-info')
        if news_info:
            info_wrapper = news_info.find('div', class_='info-wrapper')
            if info_wrapper:
                authors_p = info_wrapper.find('p', class_='authors')
                if authors_p:
                    author_link = authors_p.find('a')
                    author = self.text.cleantext(author_link) if author_link else ''
        
        if not author:
            authors_p = soup.find('p', class_='authors')
            if authors_p:
                author_link = authors_p.find('a')
                author = self.text.cleantext(author_link) if author_link else ''
        
        if not author:
            author_links = soup.find_all('a', href=re.compile(r'/autores/'))
            if author_links:
                author = self.text.cleantext(author_links[0])
        
        # TAGS
        tags = [self.text.cleantext(tag) for tag in soup.select('ul.tags-wrapper li a.tag-link')[:8]]
        
        # BODY
        body_paragraphs = soup.find_all('p', class_='article-text')[:12]
        body = ' '.join([self.text.cleantext(p) for p in body_paragraphs if len(self.text.cleantext(p)) > 30])[:3000]
        
        # IMAGEN ROBUSTA
        image = {'url': '', 'credits': ''}
        main_figure = soup.find('figure', class_='ni-figure')
        if main_figure:
            img = main_figure.find('img')
            if img and img.get('src') and 'static.eldiario.es' in img.get('src', ''):
                img_url = img.get('src')
                figcaption = main_figure.find('figcaption', class_='image-footer')
                credits = ''
                if figcaption:
                    author_span = figcaption.find('span', class_='author')
                    credits = self.text.cleantext(author_span) if author_span else ''
                image = {'url': img_url, 'credits': credits}
        
        img = soup.find('img', src=re.compile(r'static\.eldiario\.es.*\.jpg'))
        if img and not image['url']:
            image = {'url': img.get('src'), 'credits': ''}
        
        meta_image = soup.find('meta', property='og:image')
        if meta_image and not image['url']:
            image = {'url': meta_image.get('content', ''), 'credits': ''}
        
        return {
            'title': title,
            'subtitle': subtitle,
            'author': author or 'Redacción',
            'tags': tags,
            'body': body,
            'image': image
        }

# Flask 
if __name__ == '__main__':
    eldiario = ElDiarioScraper()
    app = NewsFlaskApp(eldiario, "eldiario", 5008, ["eldiario.es"])
    app.run()