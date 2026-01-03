#!/usr/bin/env python3
"""
Google Trends + X Trends España - CON ID PARA ORDENAR
IDs: 1-99=Google (24h/4h) | 100+=X Trends
Campos: id, title, source, volume, timeframe
"""

import json
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
import re


async def scrape_trends(hours):
    """Scrapea Google Trends"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        url = f"https://trends.google.com/trending?geo=ES&hl=es&sort=search-volume&hours={hours}"
        await page.goto(url, wait_until='networkidle', timeout=45000)
        
        await page.wait_for_selector('table.enOdEe-wZVHld-zg7Cn', timeout=30000)
        await page.wait_for_selector('tr[data-row-id]', timeout=20000)
        
        rows = await page.query_selector_all('tr[data-row-id]')
        trends = []
        
        base_id = 1 if hours == '24' else 20  # 1-19=24h, 20-39=4h
        
        for i, row in enumerate(rows[:15]):
            try:
                title_elem = await row.query_selector('div.mZ3RIc')
                title = await title_elem.inner_text() if title_elem else ''
                
                if not title.strip():
                    continue
                
                volume_elem = await row.query_selector('div.lqv0Cb, div.qNpYPd')
                volume = await volume_elem.inner_text() if volume_elem else '0'
                
                time_elem = await row.query_selector('div.A7jE4')
                time = await time_elem.inner_text() if time_elem else ''
                
                trend = {
                    'id': base_id + i,
                    'title': title.strip(),
                    'source': 'google',
                    'volume': volume.strip(),
                    'timeframe': f"{time.strip()} ({hours}h)"
                }
                trends.append(trend)
            except:
                continue
        
        await browser.close()
        print(f"Google {hours}h: {len(trends)} trends")
        return trends


async def scrape_xtrends():
    """Scrapea X Trends desde múltiples fuentes (fallback)"""
    sources = [
        ("https://trends24.in/spain/", 'h2', 'section.stat-card', scrape_trends24),
        ("https://getdaytrends.com/spain/", '[data-testid="trend"]', None, scrape_getdaytrends),
    ]
    
    xtrends = []
    base_id = 100
    
    for idx, (url, selector1, selector2, scraper) in enumerate(sources):
        try:
            print(f"🔄 Probando X Trends fuente {idx+1}: {url}")
            trends = await scraper(url, selector1, selector2, base_id + (idx * 50))
            if trends:
                print(f"✅ X Trends fuente {idx+1}: {len(trends)} trends")
                xtrends.extend(trends[:20])  # Máximo 20 por fuente
                break  # Usar primera fuente que funcione
        except Exception as e:
            print(f"❌ X Trends fuente {idx+1} falló: {str(e)[:100]}")
            continue
    
    if not xtrends:
        print("⚠️ Todas las fuentes X Trends fallaron - usando fallback")
        # Fallback: trends vacíos pero con estructura correcta
        xtrends = []
    
    print(f"X Trends total: {len(xtrends)}")
    return xtrends


async def scrape_trends24(url, selector1, selector2, base_id):
    """Scraping específico para trends24.in"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        await page.wait_for_selector(selector1, timeout=30000)
        
        trends = []
        sections = await page.query_selector_all(selector2)
        
        for sec_idx, section in enumerate(sections[:3]):  # Máximo 3 secciones
            try:
                list_elem = await section.query_selector('ol.stat-card-list')
                if not list_elem:
                    continue
                
                items = await list_elem.query_selector_all('li.stat-card-item')
                
                for i, item in enumerate(items[:10]):
                    try:
                        link_elem = await item.query_selector('a.trend-link')
                        title = await link_elem.inner_text() if link_elem else ''
                        
                        if not title.strip():
                            continue
                        
                        item_text = await item.inner_text()
                        volume = 'N/A'
                        
                        match = re.search(r'with ([\d.]+[KMB]?) tweet', item_text, re.IGNORECASE)
                        if match:
                            volume = match.group(1) + 'M tweets'
                        
                        timeframe = '24h trends'
                        if 'longest' in item_text.lower():
                            match_time = re.search(r'for (\d+) hrs?', item_text)
                            if match_time:
                                timeframe = f"{match_time.group(1)}h trending"
                        
                        trend = {
                            'id': base_id + (sec_idx * 10) + i + 1,
                            'title': title.strip(),
                            'source': 'x_trends',
                            'volume': volume,
                            'timeframe': timeframe
                        }
                        trends.append(trend)
                    except:
                        continue
            except:
                continue
        
        await browser.close()
        return trends


async def scrape_getdaytrends(url, selector1, selector2, base_id):
    """Scraping específico para getdaytrends.com"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        await page.wait_for_selector(selector1, timeout=30000)
        
        trends = []
        items = await page.query_selector_all(selector1)
        
        for i, item in enumerate(items[:25]):
            try:
                title_elem = await item.query_selector('div[data-testid="trend-name"]')
                title = await title_elem.inner_text() if title_elem else ''
                
                if not title.strip():
                    continue
                
                volume_elem = await item.query_selector('[data-testid="tweets"]')
                volume = await volume_elem.inner_text() if volume_elem else 'N/A'
                
                trend = {
                    'id': base_id + i,
                    'title': title.strip(),
                    'source': 'x_trends',
                    'volume': volume,
                    'timeframe': '24h trends'
                }
                trends.append(trend)
            except:
                continue
        
        await browser.close()
        return trends


async def main():
    print("🚀 GOOGLE TRENDS + X TRENDS ESPAÑA")
    
    print("🔄 Scraping Google Trends 24h...")
    google_24h = await scrape_trends('24')
    
    print("🔄 Scraping Google Trends 4h...")
    google_4h = await scrape_trends('4')
    
    print("🔄 Scraping X Trends...")
    xtrends = await scrape_xtrends()
    
    # Combinar y ordenar por ID
    all_trends = google_24h + google_4h + xtrends
    
    # Eliminar duplicados preservando el más bajo ID
    seen_titles = {}
    unique_trends = []
    for trend in all_trends:
        title_key = re.sub(r'[^\w\s]', '', trend['title'].lower())
        if title_key not in seen_titles or trend['id'] < seen_titles[title_key]:
            seen_titles[title_key] = trend['id']
            unique_trends.append(trend)
    
    # Ordenar por ID
    unique_trends.sort(key=lambda x: x['id'])
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'google_total': len(google_24h) + len(google_4h),
            'xtrends_total': len(xtrends),
            'unique_total': len(unique_trends)
        },
        'trends': unique_trends
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    with open('trends_google&x.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Guardado: trends_google&x.json")
    print(f"📊 IDs: 1-99=Google | 100+=X | Total: {len(unique_trends)}")


if __name__ == "__main__":
    asyncio.run(main())
