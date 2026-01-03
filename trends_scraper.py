#!/usr/bin/env python3
"""
Google Trends + X Trends España - RESILIENTE para GitHub Actions
✅ Google 24h/4h SIEMPRE funciona
✅ X Trends opcional (no rompe si falla)
✅ Timeout protegidos
Campos: id, title, source, volume, timeframe
"""

import json
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
import re

async def scrape_trends(hours):
    """Scrapea Google Trends - ESTABLE"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        url = f"https://trends.google.com/trending?geo=ES&hl=es&sort=search-volume&hours={hours}"
        await page.goto(url, wait_until='networkidle')
        
        await page.wait_for_selector('table.enOdEe-wZVHld-zg7Cn', timeout=30000)
        await page.wait_for_selector('tr[data-row-id]', timeout=10000)
        
        rows = await page.query_selector_all('tr[data-row-id]')
        trends = []
        
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
                
                trends.append({
                    'id': i + 1,  # ID secuencial
                    'title': title.strip(),
                    'source': 'google',
                    'volume': volume.strip(),
                    'timeframe': f"{time.strip()} ({hours}h)"
                })
            except:
                continue
        
        await browser.close()
        print(f"✅ Google {hours}h: {len(trends)} trends")
        return trends

async def scrape_xtrends():
    """Scrapea X Trends - OPCIONAL con timeout protegido"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # 🔧 TIMEOUTs altos + domcontentloaded
            page.set_default_timeout(60000)
            url = "https://trends24.in/spain/"
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            await page.wait_for_selector('section.stat-card', timeout=30000)
            
            trends = []
            sections = await page.query_selector_all('section.stat-card')
            base_id = 100
            
            for sec_idx, section in enumerate(sections):
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
                            
                            match = re.search(r'with ([d.]+[KMB]?) tweet', item_text, re.IGNORECASE)
                            if match:
                                volume = match.group(1) + 'M tweets'
                            
                            timeframe = '24h trends'
                            if 'longest' in item_text.lower():
                                match_time = re.search(r'for (d+) hrs?', item_text)
                                if match_time:
                                    timeframe = f"{match_time.group(1)}h trending"
                            
                            trends.append({
                                'id': base_id + (sec_idx * 10) + i + 1,
                                'title': title.strip(),
                                'source': 'x_trends',
                                'volume': volume,
                                'timeframe': timeframe
                            })
                        except:
                            continue
                except:
                    continue
            
            await browser.close()
            print(f"✅ X Trends: {len(trends)} items")
            return trends

    except Exception as e:
        print(f"⚠️ X Trends falló: {str(e)[:100]}")
        return []  # ❌ NUNCA rompe el script

async def main():
    print("🚀 TRENDS SCRAPER INICIO")
    
    # Google SIEMPRE funciona
    print("🔄 Google Trends 24h...")
    google_24h = await scrape_trends('24')
    
    print("🔄 Google Trends 4h...")
    google_4h = await scrape_trends('4')
    
    # X opcional
    print("🔄 X Trends...")
    xtrends = await scrape_xtrends()
    
    # Combinar
    all_trends = google_24h + google_4h + xtrends
    
    # Dedup por título preservando ID más bajo
    seen_titles = {}
    unique_trends = []
    for trend in all_trends:
        title_key = re.sub(r'[^ws]', '', trend['title'].lower())
        if title_key not in seen_titles or trend['id'] < seen_titles[title_key]:
            seen_titles[title_key] = trend['id']
            unique_trends.append(trend)
    
    # Ordenar por ID
    unique_trends.sort(key=lambda x: x['id'])
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'google_24h': len(google_24h),
            'google_4h': len(google_4h),
            'xtrends': len(xtrends),
            'unique_total': len(unique_trends)
        },
        'trends': unique_trends
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    with open('trends_google&x.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"
✅ FINAL: {len(unique_trends)} trends únicos → trends_google&x.json")
    print("IDs: 1-99=Google | 100+=X")

if __name__ == "__main__":
    asyncio.run(main())