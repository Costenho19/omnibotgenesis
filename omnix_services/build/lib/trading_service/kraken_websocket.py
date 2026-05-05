"""
🌐 KRAKEN WEBSOCKET CLIENT - REAL-TIME FEEDS
Streaming en tiempo real para escalar a 100K+ usuarios

VENTAJAS vs POLLING:
- Latencia: <500ms vs 5-60s
- API Calls: 1 conexión vs miles de requests
- Escalabilidad: Alimenta a todos los usuarios simultáneamente
- Costo: 99% reducción en API usage

FEEDS DISPONIBLES:
- Ticker: Precio en tiempo real
- OHLC: Candles actualizados
- Trades: Todas las operaciones
- Book: Order book en tiempo real
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Callable, List, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class KrakenWebSocketClient:
    """
    Cliente WebSocket profesional para Kraken
    
    Maneja:
    - Reconexión automática
    - Múltiples suscripciones
    - Broadcast a todos los listeners
    - Thread-safe para uso concurrente
    """
    
    def __init__(self):
        self.ws_url = "wss://ws.kraken.com"
        self.ws = None
        self.running = False
        self.subscriptions = {}
        self.listeners = {}  # {channel: [callbacks]}
        
        # Estado
        self.connected = False
        self.last_ping = None
        
        # Thread para loop asyncio
        self._thread = None
        self._loop = None
        
        logger.info("🌐 Kraken WebSocket Client initialized")
    
    def start(self):
        """Iniciar WebSocket en thread separado"""
        if self.running:
            logger.warning("WebSocket already running")
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        
        logger.info("✅ WebSocket thread started")
    
    def stop(self):
        """Detener WebSocket"""
        self.running = False
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)
        
        logger.info("🛑 WebSocket stopped")
    
    def _run_async_loop(self):
        """Ejecutar loop asyncio en thread separado"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"WebSocket loop error: {e}")
        finally:
            self._loop.close()
    
    async def _connect_and_listen(self):
        """Conectar y escuchar mensajes"""
        retry_delay = 1
        max_retry_delay = 60
        
        while self.running:
            try:
                logger.info(f"🔌 Connecting to {self.ws_url}...")
                
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    self.ws = ws
                    self.connected = True
                    retry_delay = 1  # Reset delay on successful connection
                    
                    logger.info("✅ WebSocket connected to Kraken")
                    
                    # Re-subscribe a canales previos
                    await self._resubscribe_all()
                    
                    # Escuchar mensajes
                    async for message in ws:
                        # Convertir a string si es bytes
                        msg_str = message.decode('utf-8') if isinstance(message, bytes) else message
                        await self._handle_message(msg_str)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ WebSocket connection closed, reconnecting...")
                self.connected = False
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.connected = False
            
            if self.running:
                # Reconnect con backoff exponencial
                logger.info(f"🔄 Reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
    
    async def _disconnect(self):
        """Desconectar WebSocket"""
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.connected = False
    
    async def _handle_message(self, message: str):
        """Procesar mensaje recibido"""
        try:
            data = json.loads(message)
            
            # Eventos del sistema
            if isinstance(data, dict):
                if data.get('event') == 'heartbeat':
                    self.last_ping = datetime.now()
                    return
                
                if data.get('event') == 'systemStatus':
                    logger.info(f"📡 Kraken status: {data.get('status')}")
                    return
                
                if data.get('event') == 'subscriptionStatus':
                    logger.info(f"✅ Subscription: {data.get('status')}")
                    return
            
            # Datos de mercado (array format)
            if isinstance(data, list) and len(data) >= 2:
                channel_id = data[0]
                channel_data = data[1]
                channel_name = data[2] if len(data) > 2 else None
                pair = data[3] if len(data) > 3 else None
                
                # Broadcast a listeners (solo si channel_name existe)
                if channel_name:
                    await self._broadcast(channel_name, {
                        'channel': channel_name,
                        'pair': pair,
                        'data': channel_data,
                        'timestamp': datetime.now()
                    })
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _broadcast(self, channel: str, data: Dict):
        """Enviar datos a todos los listeners del canal"""
        if channel in self.listeners:
            for callback in self.listeners[channel]:
                try:
                    # Ejecutar callback (puede ser sync o async)
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in listener callback: {e}")
    
    async def _resubscribe_all(self):
        """Re-suscribir a todos los canales previos"""
        for channel, config in self.subscriptions.items():
            await self._subscribe_channel(channel, config)
    
    async def _subscribe_channel(self, channel: str, config: Dict):
        """Suscribirse a un canal"""
        if not self.ws or not self.connected:
            logger.warning("Cannot subscribe - WebSocket not connected")
            return
        
        try:
            message = {
                "event": "subscribe",
                **config
            }
            
            await self.ws.send(json.dumps(message))
            logger.info(f"📡 Subscribed to {channel}: {config.get('pair', 'all')}")
            
        except Exception as e:
            logger.error(f"Error subscribing to {channel}: {e}")
    
    def subscribe_ticker(self, pair: str, callback: Callable):
        """
        Suscribirse a ticker en tiempo real
        
        Args:
            pair: Par de trading (ej: "BTC/USD")
            callback: Función a llamar con cada update
        """
        channel = f"ticker_{pair}"
        
        # Guardar suscripción
        self.subscriptions[channel] = {
            "pair": [pair],
            "subscription": {"name": "ticker"}
        }
        
        # Agregar listener
        if channel not in self.listeners:
            self.listeners[channel] = []
        self.listeners[channel].append(callback)
        
        # Suscribir si ya conectado
        if self.connected and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._subscribe_channel(channel, self.subscriptions[channel]),
                self._loop
            )
        
        logger.info(f"✅ Ticker listener added for {pair}")
    
    def subscribe_ohlc(self, pair: str, interval: int, callback: Callable):
        """
        Suscribirse a OHLC (candles) en tiempo real
        
        Args:
            pair: Par de trading
            interval: Intervalo en minutos (1, 5, 15, 30, 60, 240, 1440)
            callback: Función a llamar con cada candle
        """
        channel = f"ohlc_{pair}_{interval}"
        
        self.subscriptions[channel] = {
            "pair": [pair],
            "subscription": {"name": "ohlc", "interval": interval}
        }
        
        if channel not in self.listeners:
            self.listeners[channel] = []
        self.listeners[channel].append(callback)
        
        if self.connected and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._subscribe_channel(channel, self.subscriptions[channel]),
                self._loop
            )
        
        logger.info(f"✅ OHLC listener added for {pair} ({interval}m)")
    
    def subscribe_trades(self, pair: str, callback: Callable):
        """Suscribirse a trades en tiempo real"""
        channel = f"trade_{pair}"
        
        self.subscriptions[channel] = {
            "pair": [pair],
            "subscription": {"name": "trade"}
        }
        
        if channel not in self.listeners:
            self.listeners[channel] = []
        self.listeners[channel].append(callback)
        
        if self.connected and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._subscribe_channel(channel, self.subscriptions[channel]),
                self._loop
            )
        
        logger.info(f"✅ Trades listener added for {pair}")
    
    def get_status(self) -> Dict:
        """Obtener estado del WebSocket"""
        return {
            'connected': self.connected,
            'running': self.running,
            'subscriptions': len(self.subscriptions),
            'listeners': sum(len(l) for l in self.listeners.values()),
            'last_ping': self.last_ping
        }


# Singleton global para compartir entre todos los usuarios
_global_ws_client = None

def get_kraken_websocket() -> KrakenWebSocketClient:
    """Obtener instancia global del WebSocket client"""
    global _global_ws_client
    
    if _global_ws_client is None:
        _global_ws_client = KrakenWebSocketClient()
        _global_ws_client.start()
    
    return _global_ws_client
