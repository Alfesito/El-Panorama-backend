 #!/usr/bin/env python3
"""
Google Trends España 24h/4h - 100% GitHub Actions Compatible
✅ Solo Google (X bloqueado en Actions)
✅ IDs secuenciales para ordenar
✅ JSON público listo
"""

import json
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
import re

async def scrape_trends(hours):
    """Google Trends - ESTABLE"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        url = f"https://trends.google.com/trending?geo=ES&hl=es&sort=search-volume&hours={hours}"
        await page.goto(url, wait_until='domcontentloaded', timeout=45000)  # 🔧 domcontentloaded
        
        await page.wait_for_selector('table.enOdEe-wZVHld-zg7Cn', timeout=30000)
        await page.wait_for_selector('tr[data-row-id]', timeout=20000)
        
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
                    'id': i + 1 if hours == '24' else i + 20,  # 1-19=24h, 20-39=4h
                    'title': title.strip(),
                    'source': f'google_{hours}h',
                    'volume': volume.strip(),
                    'timeframe': f"{time.strip()} ({hours}h)"
                })
            except:
                continue
        
        await browser.close()
        print(f"✅ Google {hours}h: {len(trends)} trends")
        return trends

async def main():
    print("🚀 GOOGLE TRENDS ESPAÑA INICIO")
    
    # Solo Google - 100% estable
    print("🔄 Google Trends 24h...")
    google_24h = await scrape_trends('24')
    
    print("🔄 Google Trends 4h...")
    google_4h = await scrape_trends('4')
    
    # 🔌 X DESACTIVADO (trends24.in bloquea GitHub Actions)
    xtrends = []
    print("⚠️ X Trends desactivado (GitHub Actions bloqueado)")
    
    all_trends = google_24h + google_4h + xtrends
    
    # Dedup + ordenar por ID
    seen_titles = {}
    unique_trends = []
    for trend in all_trends:
        title_key = re.sub(r'[^ws]', '', trend['title'].lower())
        if title_key not in seen_titles or trend['id'] < seen_titles[title_key]:
            seen_titles[title_key] = trend['id']
            unique_trends.append(trend)
    
    unique_trends.sort(key=lambda x: x['id'])
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'google_24h': len(google_24h),
            'google_4h': len(google_4h),
            'xtrends': 0,
            'unique_total': len(unique_trends)
        },
        'trends': unique_trends
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    with open('trends_google_es.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"
✅ FINAL: {len(unique_trends)} trends → trends_google_es.json")
    print("IDs: 1-19=24h | 20-39=4h")

if __name__ == "__main__":
    asyncio.run(main())