from flask import Flask, jsonify, request

class NewsFlaskApp:
    """Flask app reutilizable para cualquier scraper."""
    
    def __init__(self, scraper_instance, name, port=5000, domains=None):
        self.scraper = scraper_instance
        self.name = name
        self.port = port
        self.domains = domains or [name.lower().replace(' ', '').replace('.', '')]
        self.app = Flask(__name__)
        self._register_routes()
    
    def _register_routes(self):
        @self.app.route('/scrape', methods=['GET'])
        def scrape():
            url = request.args.get('url')
            if not url:
                return jsonify({'error': f'Requiere parámetro url para {self.name}'}), 400

            for domain in self.domains:
                if domain in url.lower():
                    results = self.scraper.scrape_list_page(url)

                    # Si no hay resultados (posible URL de artículo), intentar obtener detalles directos
                    if not results:
                        try:
                            details = self.scraper.fetch_article_details(url)
                            # Crear id determinístico a partir de la URL del artículo (MD5 + base62)
                            date_str = self.scraper.date.normalizedatetime()
                            article_id = self.scraper.idgen.generate_id_from_url(url)
                            ordered = self.scraper.article.create_ordered_article(
                                self.name,
                                article_id,
                                date_str,
                                details.get('tags', []),
                                details.get('title', ''),
                                details.get('subtitle', ''),
                                url,
                                details.get('author', 'Redacción'),
                                details.get('image', {'url': '', 'credits': ''}),
                                details.get('body', '')
                            )
                            return jsonify([ordered])
                        except Exception as e:
                            return jsonify({'error': 'No se encontraron artículos y falló extracción de detalle', 'message': str(e)}), 500

                    # Enriquecer cada artículo llamando a `enrich_article` (siempre)
                    enriched = []
                    for art in results:
                        try:
                            enriched.append(self.scraper.enrich_article(art))
                        except Exception:
                            enriched.append(art)
                    return jsonify(enriched)

            return jsonify({
                'error': f'Requiere url {self.name}', 
                'dominios': self.domains
            }), 400


        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'OK',
                'scraper': self.name,
                'domains': self.domains,
                'port': self.port
            })
    
    def run(self, debug=True, host='127.0.0.1'):
        print(f"🚀 {self.name} Scraper - http://{host}:{self.port}/scrape")
        self.app.run(debug=debug, port=self.port, host=host)
