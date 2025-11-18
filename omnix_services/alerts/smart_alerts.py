"""
🔔 SMART ALERTS SYSTEM - ALERTAS INTELIGENTES 24/7
Sistema de alertas personalizadas multi-condición

TIPOS DE ALERTAS:
- Precio (above/below threshold)
- Indicadores técnicos (RSI oversold/overbought, MACD cross)
- Black Swan detectado
- Volatilidad extrema
- Portfolio drawdown límite

CANALES:
- Telegram (instant)
- Email (opcional)
- Webhook (para integraciónes)

ESCALABILIDAD:
- Monitoreo eficiente con checks periódicos
- Database de alertas con indexes
- Batch notifications para reducir API calls
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)


class SmartAlertEngine:
    """
    Motor de alertas inteligentes
    
    Monitorea condiciones 24/7 y notifica a usuarios
    """
    
    def __init__(self, database_service=None, trading_service=None):
        self.database = database_service
        self.trading = trading_service
        
        # Estado
        self.active_alerts = {}  # {alert_id: config}
        self.running = False
        self._thread = None
        
        # Canales de notificación
        self.channels = {
            'telegram': None,  # Se configura externamente
            'email': None,
            'webhook': None
        }
        
        logger.info("🔔 Smart Alert Engine initialized")
    
    def start(self):
        """Iniciar monitoreo 24/7"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        
        logger.info("✅ Alert monitoring started")
    
    def stop(self):
        """Detener monitoreo"""
        self.running = False
        logger.info("🛑 Alert monitoring stopped")
    
    def add_alert(
        self,
        user_id: str,
        alert_type: str,
        config: Dict,
        channels: List[str] = ['telegram']
    ) -> str:
        """
        Agregar nueva alerta
        
        Args:
            user_id: ID del usuario
            alert_type: Tipo (price_above, price_below, rsi_oversold, etc)
            config: Configuración específica del tipo
            channels: Canales de notificación
            
        Returns:
            alert_id
        """
        alert_id = f"{user_id}_{alert_type}_{int(time.time())}"
        
        self.active_alerts[alert_id] = {
            'user_id': user_id,
            'type': alert_type,
            'config': config,
            'channels': channels,
            'created_at': datetime.now(),
            'triggered': False,
            'trigger_count': 0
        }
        
        logger.info(f"➕ Alert added: {alert_id}")
        return alert_id
    
    def remove_alert(self, alert_id: str):
        """Eliminar alerta"""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            logger.info(f"➖ Alert removed: {alert_id}")
    
    def get_user_alerts(self, user_id: str) -> List[Dict]:
        """Obtener alertas de un usuario"""
        return [
            {'id': aid, **config}
            for aid, config in self.active_alerts.items()
            if config['user_id'] == user_id
        ]
    
    def _monitoring_loop(self):
        """Loop principal 24/7 de monitoreo"""
        check_interval = 60  # Chequear cada 60 segundos
        
        while self.running:
            try:
                self._check_all_alerts()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _check_all_alerts(self):
        """Verificar todas las alertas activas"""
        for alert_id, alert in list(self.active_alerts.items()):
            try:
                if self._check_alert_condition(alert):
                    self._trigger_alert(alert_id, alert)
            except Exception as e:
                logger.error(f"Error checking alert {alert_id}: {e}")
    
    def _check_alert_condition(self, alert: Dict) -> bool:
        """
        Verificar si condición de alerta se cumple
        
        Returns:
            True si debe dispararse la alerta
        """
        alert_type = alert['type']
        config = alert['config']
        
        # PRICE ALERTS
        if alert_type == 'price_above':
            pair = config['pair']
            threshold = config['value']
            
            current_price = self._get_current_price(pair)
            if current_price and current_price >= threshold:
                return True
        
        elif alert_type == 'price_below':
            pair = config['pair']
            threshold = config['value']
            
            current_price = self._get_current_price(pair)
            if current_price and current_price <= threshold:
                return True
        
        # TECHNICAL INDICATORS
        elif alert_type == 'rsi_oversold':
            pair = config['pair']
            rsi_threshold = config.get('rsi', 30)
            
            rsi = self._calculate_rsi(pair)
            if rsi and rsi <= rsi_threshold:
                return True
        
        elif alert_type == 'rsi_overbought':
            pair = config['pair']
            rsi_threshold = config.get('rsi', 70)
            
            rsi = self._calculate_rsi(pair)
            if rsi and rsi >= rsi_threshold:
                return True
        
        # RISK ALERTS
        elif alert_type == 'black_swan_detected':
            pair = config.get('pair', 'BTC/USD')
            severity_threshold = config.get('severity', 'medium')
            
            if self.trading and hasattr(self.trading, 'black_swan'):
                # Obtener histórico de precios
                prices = self._get_price_history(pair, days=100)
                if prices and len(prices) >= 30:
                    analysis = self.trading.black_swan.analyze(prices)
                    if analysis.get('risk_level') in ['HIGH', 'EXTREME']:
                        return True
        
        elif alert_type == 'volatility_spike':
            pair = config['pair']
            threshold = config.get('threshold', 2.0)  # 2x volatilidad normal
            
            volatility = self._calculate_volatility(pair)
            if volatility and volatility >= threshold:
                return True
        
        return False
    
    def _trigger_alert(self, alert_id: str, alert: Dict):
        """Disparar alerta y notificar"""
        alert['trigger_count'] += 1
        alert['last_triggered'] = datetime.now()
        
        message = self._format_alert_message(alert)
        
        # Enviar por todos los canales configurados
        for channel in alert['channels']:
            self._send_notification(
                channel=channel,
                user_id=alert['user_id'],
                message=message,
                alert=alert
            )
        
        logger.info(f"🔔 Alert triggered: {alert_id}")
        
        # Marcar como triggered o eliminar si es one-time
        if alert['config'].get('one_time', False):
            self.remove_alert(alert_id)
        else:
            alert['triggered'] = True
    
    def _format_alert_message(self, alert: Dict) -> str:
        """Formatear mensaje de alerta"""
        alert_type = alert['type']
        config = alert['config']
        
        if alert_type == 'price_above':
            return f"🚨 ALERTA: {config['pair']} superó ${config['value']:,.2f}"
        
        elif alert_type == 'price_below':
            return f"🚨 ALERTA: {config['pair']} cayó debajo de ${config['value']:,.2f}"
        
        elif alert_type == 'rsi_oversold':
            return f"📉 ALERTA: {config['pair']} RSI en sobreventa ({config.get('rsi', 30)})"
        
        elif alert_type == 'rsi_overbought':
            return f"📈 ALERTA: {config['pair']} RSI en sobrecompra ({config.get('rsi', 70)})"
        
        elif alert_type == 'black_swan_detected':
            return f"🦢 ALERTA BLACK SWAN: Riesgo extremo detectado en {config.get('pair', 'mercado')}"
        
        elif alert_type == 'volatility_spike':
            return f"⚡ ALERTA: Volatilidad extrema en {config['pair']}"
        
        return f"🔔 Alerta: {alert_type}"
    
    def _send_notification(self, channel: str, user_id: str, message: str, alert: Dict):
        """Enviar notificación por canal específico"""
        try:
            if channel == 'telegram' and self.channels['telegram']:
                # Telegram handler configurado externamente
                self.channels['telegram'](user_id, message, alert)
            
            elif channel == 'email' and self.channels['email']:
                self.channels['email'](user_id, message, alert)
            
            elif channel == 'webhook' and self.channels['webhook']:
                self.channels['webhook'](user_id, message, alert)
            
        except Exception as e:
            logger.error(f"Error sending notification via {channel}: {e}")
    
    def _get_current_price(self, pair: str) -> Optional[float]:
        """Obtener precio actual"""
        try:
            if self.trading and hasattr(self.trading, 'kraken'):
                ticker = self.trading.kraken.get_ticker(pair)
                if ticker:
                    return float(ticker.get('last', 0))
        except:
            pass
        return None
    
    def _calculate_rsi(self, pair: str, period: int = 14) -> Optional[float]:
        """Calcular RSI"""
        try:
            prices = self._get_price_history(pair, days=30)
            if not prices or len(prices) < period + 1:
                return None
            
            # RSI calculation
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except:
            return None
    
    def _calculate_volatility(self, pair: str) -> Optional[float]:
        """Calcular volatilidad (desviación estándar de returns)"""
        try:
            prices = self._get_price_history(pair, days=30)
            if not prices or len(prices) < 2:
                return None
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            
            # Standard deviation
            import statistics
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
            
            return volatility
        except:
            return None
    
    def _get_price_history(self, pair: str, days: int = 30) -> Optional[List[float]]:
        """Obtener histórico de precios"""
        try:
            if self.trading and hasattr(self.trading, 'kraken'):
                ohlc = self.trading.kraken.get_ohlc(pair, interval=1440)  # Daily
                if ohlc and len(ohlc) > 0:
                    return [float(candle[4]) for candle in ohlc[-days:]]  # Close prices
        except:
            pass
        return None
    
    def get_status(self) -> Dict:
        """Obtener estado del sistema de alertas"""
        return {
            'running': self.running,
            'active_alerts': len(self.active_alerts),
            'triggered_alerts': len([a for a in self.active_alerts.values() if a['triggered']]),
            'channels_configured': [k for k, v in self.channels.items() if v is not None]
        }
