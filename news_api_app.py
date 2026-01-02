from flask import Flask, jsonify, request
from Newspapers.api_abc import ABCScraper
from Newspapers.api_elmundo import ElMundoScraper
from Newspapers.api_eldiario import ElDiarioScraper
from Newspapers.api_elpais import ElPaisScraper
from Newspapers.api_larazon import LaRazonScraper
from Newspapers.api_publico import PublicoScraper
from Newspapers.api_lavanguardia import LaVanguardiaScraper
from Newspapers.api_elespanol import ElEspanolScraper
from Newspapers.api_20minutos import VeinteMinutosScraper
from Newspapers.api_lavozdegalicia import LaVozDeGaliciaScraper

SCRAPERS = {
    'abc.es': ABCScraper(),
    'elmundo.es': ElMundoScraper(),
    'eldiario.es': ElDiarioScraper(),
    'elpais.com': ElPaisScraper(),
    'larazon.es': LaRazonScraper(),
    'publico.es': PublicoScraper(),
    'lavanguardia.com': LaVanguardiaScraper(),
    'elespanol.com': ElEspanolScraper(),
    'lavozdegalicia.es': LaVozDeGaliciaScraper(),
    '20minutos.es': VeinteMinutosScraper()
}

app = Flask(__name__)

@app.route('/scrape', methods=['GET'])
def scrape():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Requiere parámetro url'}), 400

    # Enriquecer detalles en cada artículo: siempre

    for domain, scraper in SCRAPERS.items():
        if domain in url.lower():
            print(f"🔍 {domain}: {url}")
            results = scraper.scrape_list_page(url)
            # Si no hay resultados (posible URL de artículo), intentar obtener detalles directos
            if not results:
                try:
                    details = scraper.scrape_article_details(url)
                    # Crear id determinístico a partir de la URL del artículo (MD5 + base62)
                    date_str = scraper.date.normalizedatetime()
                    article_id = scraper.idgen.generate_id_from_url(url)
                    ordered = scraper.article.create_ordered_article(
                        scraper.name,
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

            # Enriquecer todos los artículos antes de devolver
            enriched = []
            for art in results:
                try:
                    enriched.append(scraper.enrich_article(art))
                except Exception:
                    enriched.append(art)
            return jsonify(enriched)
    
    return jsonify({
        'error': 'Periódico no soportado',
        'soportados': list(SCRAPERS.keys()),
        'ejemplos': [
            'https://www.abc.es',
            'https://www.elmundo.es',
            'https://www.eldiario.es',
            'https://elpais.com',
            'https://www.larazon.es',
            'https://www.publico.es',
            'https://www.lavanguardia.com',
            'https://www.elespanol.com',
            'https://www.lavozdegalicia.es',
            'https://www.20minutos.es'
        ]
    }), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'OK',
        'total': len(SCRAPERS),
        'periódicos': list(SCRAPERS.keys())
    })

if __name__ == '__main__':
    print("🚀 NEWS API CENTRAL - 5 PERIÓDICOS")
    print("python news_api.py → puerto 5000")
    app.run(debug=True, port=5000)
