"""
News Scraper Service para OMNIX V5.4 ULTRA
===========================================

Sistema de scraping y análisis de noticias crypto usando IA.
Integrado con Telegram commands para análisis en tiempo real.

Features:
- Scraping de artículos crypto (CoinDesk, CoinTelegraph, etc)
- Análisis de sentimiento con GPT-4
- Extracción de señales de trading
- Detección de tendencias del mercado

Autor: Harold Nunes
Fecha: 2024-11-16
"""

import re
import logging
import requests
from typing import Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NewsScraperService:
    """
    Servicio de scraping de noticias crypto con análisis IA
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        logger.info("📰 News Scraper Service inicializado")
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """
        Scrapea un artículo y extrae contenido relevante
        
        Args:
            url: URL del artículo a scrapear
            
        Returns:
            Dict con título, contenido, y metadata
        """
        try:
            logger.info(f"🔍 Scrapeando artículo: {url}")
            
            # Fetch article
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract article content
            content = self._extract_content(soup)
            
            # Extract metadata
            published_date = self._extract_date(soup)
            
            if not content:
                logger.warning("⚠️ No se pudo extraer contenido del artículo")
                return None
            
            article_data = {
                'url': url,
                'title': title,
                'content': content,
                'published_date': published_date,
                'word_count': len(content.split()),
                'success': True
            }
            
            logger.info(f"✅ Artículo scrapeado: {len(content)} caracteres")
            return article_data
            
        except requests.RequestException as e:
            logger.error(f"❌ Error scrapeando URL: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"❌ Error general scraping: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_title(self, soup) -> str:
        """Extrae el título del artículo"""
        # Try common title tags
        title_selectors = [
            ('h1', {}),
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
            ('title', {})
        ]
        
        for tag, attrs in title_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', 'Sin título')
                return element.get_text(strip=True)
        
        return 'Sin título'
    
    def _extract_content(self, soup) -> str:
        """Extrae el contenido principal del artículo"""
        # Remove unwanted elements
        for unwanted in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            unwanted.decompose()
        
        # Try common article selectors
        content_selectors = [
            ('article', {}),
            ('div', {'class': re.compile('article|content|post|entry')}),
            ('div', {'id': re.compile('article|content|post')}),
        ]
        
        for tag, attrs in content_selectors:
            container = soup.find(tag, attrs)
            if container:
                # Get all paragraphs
                paragraphs = container.find_all('p')
                content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
                if content:
                    return content
        
        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
        return content
    
    def _extract_date(self, soup) -> Optional[str]:
        """Extrae la fecha de publicación"""
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publish-date'}),
            ('time', {'datetime': True}),
        ]
        
        for tag, attrs in date_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content')
                return element.get('datetime') or element.get_text(strip=True)
        
        return None
    
    def analyze_with_ai(self, article_data: Dict, ai_client) -> Dict:
        """
        Analiza el artículo usando GPT-4 para extraer señales de trading
        
        Args:
            article_data: Datos del artículo scrapeado
            ai_client: Cliente OpenAI o Gemini
            
        Returns:
            Dict con análisis de sentimiento y señales
        """
        if not article_data.get('success'):
            return {'error': 'Artículo no válido'}
        
        try:
            # Truncar contenido si es muy largo
            content = article_data['content'][:3000]
            
            prompt = f"""Analiza este artículo de noticias crypto y extrae:

Título: {article_data['title']}

Contenido:
{content}

Proporciona:
1. Sentimiento general (BULLISH/BEARISH/NEUTRAL) y score 0-10
2. Señales de trading específicas mencionadas
3. Criptomonedas mencionadas
4. Impacto potencial en el mercado (HIGH/MEDIUM/LOW)
5. Resumen ejecutivo en 2-3 líneas

Formato de respuesta:
SENTIMIENTO: [BULLISH/BEARISH/NEUTRAL] (X/10)
SEÑALES: 
- [señal 1]
- [señal 2]
CRYPTOS: BTC, ETH, etc
IMPACTO: [HIGH/MEDIUM/LOW]
RESUMEN: [resumen corto]
"""
            
            # Usar GPT-4 si está disponible
            if hasattr(ai_client, 'chat'):
                response = ai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un analista experto de mercados crypto."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                analysis = response.choices[0].message.content
            else:
                # Fallback a formato simple
                analysis = "Análisis no disponible"
            
            return {
                'success': True,
                'article_title': article_data['title'],
                'article_url': article_data['url'],
                'analysis': analysis,
                'word_count': article_data['word_count']
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_trending_news(self, source='coindesk') -> list:
        """
        Obtiene las noticias trending de una fuente
        
        Args:
            source: 'coindesk', 'cointelegraph', o 'cryptonews'
            
        Returns:
            Lista de URLs de artículos trending
        """
        try:
            if source == 'coindesk':
                base_url = 'https://www.coindesk.com'
                response = requests.get(f"{base_url}/markets", headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article links
                articles = soup.find_all('a', href=re.compile('/markets/'))
                urls = []
                for article in articles[:5]:  # Top 5
                    href = article.get('href')
                    if href and not href.startswith('http'):
                        href = base_url + href
                    if href and href not in urls:
                        urls.append(href)
                
                return urls
            
            # Otros sources se pueden agregar aquí
            return []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo trending news: {e}")
            return []
