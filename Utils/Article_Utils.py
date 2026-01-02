from collections import OrderedDict

class ArticleUtils:
    @staticmethod
    def create_ordered_article(newspaper, articleid, date, tags, title, subtitle, url, author, image, body):
        """Crea OrderedDict con orden EXACTO de tus scrapers."""
        return OrderedDict([
            ('id', articleid),
            ('newspaper', newspaper),
            ('date', date),
            ('tags', tags[:8] if tags else []),
            ('title', title),
            ('subtitle', subtitle or ''),
            ('url', url),
            ('author', author),
            ('image', image or {'url': '', 'credits': ''}),
            ('body', body[:3000])
        ])
