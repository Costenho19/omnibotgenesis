"""
OMNIX V5.1 - Stripe Payment Integration
Sistema de pagos para suscripciones PRO y ENTERPRISE
"""

import os
import stripe
from flask import request, redirect, jsonify
import logging

logger = logging.getLogger('OMNIX')

# Configurar Stripe API Key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

# Obtener dominio de Replit
YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
if os.environ.get('REPLIT_DEPLOYMENT'):
    YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
elif os.environ.get('REPLIT_DOMAINS'):
    YOUR_DOMAIN = os.environ.get('REPLIT_DOMAINS').split(',')[0]

class StripePaymentManager:
    """Gestor de pagos con Stripe para OMNIX"""
    
    def __init__(self):
        self.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
        self.stripe_available = bool(self.api_key)
        
        if self.stripe_available:
            stripe.api_key = self.api_key
            logger.info("💳 Stripe Payment System ACTIVADO")
        else:
            logger.warning("⚠️ STRIPE_SECRET_KEY no configurada - Pagos desactivados")
    
    # PRECIOS OMNIX (Crear estos Price IDs en Stripe Dashboard)
    PRICES = {
        'pro_monthly': 'price_XXXXX',  # $29/mes - Harold debe crear esto en Stripe
        'enterprise_monthly': 'price_XXXXX',  # $129/mes - Harold debe crear esto en Stripe
        'pro_yearly': 'price_XXXXX',  # $290/año (2 meses gratis)
        'enterprise_yearly': 'price_XXXXX',  # $1,290/año (2 meses gratis)
    }
    
    def create_checkout_session(self, plan_type='pro_monthly', user_id=None):
        # Crear sesión de checkout de Stripe - Returns URL o None si error
        if not self.stripe_available:
            logger.error("❌ Stripe no configurado")
            return None
        
        try:
            price_id = self.PRICES.get(plan_type)
            
            if not price_id or price_id == 'price_XXXXX':
                logger.error(f"❌ Price ID no configurado para {plan_type}")
                return None
            
            # Metadata para trackear usuario
            metadata = {}
            if user_id:
                metadata['telegram_user_id'] = str(user_id)
            
            # Crear sesión de checkout
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',  # Modo suscripción recurrente
                success_url=f'https://{YOUR_DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'https://{YOUR_DOMAIN}/cancel',
                metadata=metadata,
                allow_promotion_codes=True,  # Permitir códigos promocionales
                billing_address_collection='required',  # Requerir dirección de facturación
            )
            
            logger.info(f"✅ Sesión de checkout creada: {checkout_session.id} - Plan: {plan_type}")
            return checkout_session.url
            
        except Exception as e:
            logger.error(f"❌ Error creando checkout session: {e}")
            return None
    
    def verify_payment(self, session_id):
        # Verificar si un pago fue exitoso - Returns dict con info o None si error
        if not self.stripe_available:
            return None
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                return {
                    'paid': True,
                    'customer_id': session.customer,
                    'subscription_id': session.subscription,
                    'amount_total': session.amount_total,
                    'currency': session.currency,
                    'metadata': session.metadata
                }
            else:
                return {'paid': False}
                
        except Exception as e:
            logger.error(f"❌ Error verificando pago: {e}")
            return None
    
    def cancel_subscription(self, subscription_id):
        # Cancelar suscripción - Returns True si cancelado, False si error
        if not self.stripe_available:
            return False
        
        try:
            stripe.Subscription.delete(subscription_id)
            logger.info(f"✅ Suscripción cancelada: {subscription_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error cancelando suscripción: {e}")
            return False
    
    def get_customer_subscriptions(self, customer_id):
        # Obtener suscripciones activas de un cliente - Returns lista o None si error
        if not self.stripe_available:
            return None
        
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active'
            )
            return subscriptions.data
        except Exception as e:
            logger.error(f"❌ Error obteniendo suscripciones: {e}")
            return None


def setup_stripe_routes(app):
    # Configurar rutas Flask para Stripe
    stripe_manager = StripePaymentManager()
    
    @app.route('/create-checkout/<plan>', methods=['POST', 'GET'])
    def create_checkout(plan):
        # Crear sesión de checkout para plan específico
        user_id = request.args.get('user_id')  # ID de Telegram del usuario
        
        checkout_url = stripe_manager.create_checkout_session(
            plan_type=plan,
            user_id=user_id
        )
        
        if checkout_url:
            return redirect(checkout_url, code=303)
        else:
            return jsonify({'error': 'No se pudo crear sesión de pago'}), 500
    
    @app.route('/success')
    def payment_success():
        # Página de éxito después del pago
        session_id = request.args.get('session_id')
        
        if session_id:
            payment_info = stripe_manager.verify_payment(session_id)
            
            if payment_info and payment_info.get('paid'):
                return f"""
                <html>
                    <head><title>Pago Exitoso - OMNIX</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>✅ ¡Pago Exitoso!</h1>
                        <p>Tu suscripción a OMNIX ha sido activada.</p>
                        <p>Vuelve a Telegram para empezar a usar las funciones PRO.</p>
                        <p><strong>ID de Suscripción:</strong> {payment_info.get('subscription_id')}</p>
                        <hr>
                        <p><em>Sistema OMNIX V5.1 - Harold Nunes</em></p>
                    </body>
                </html>
                """
        
        return """
        <html>
            <head><title>Verificando Pago - OMNIX</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>🔄 Verificando Pago...</h1>
                <p>Por favor espera mientras verificamos tu pago.</p>
            </body>
        </html>
        """
    
    @app.route('/cancel')
    def payment_cancel():
        # Página de cancelación
        return """
        <html>
            <head><title>Pago Cancelado - OMNIX</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Pago Cancelado</h1>
                <p>No se procesó ningún pago.</p>
                <p>Puedes intentarlo nuevamente cuando quieras.</p>
                <p><a href="https://t.me/OMNIX_bot">Volver a Telegram</a></p>
                <hr>
                <p><em>Sistema OMNIX V5.1 - Harold Nunes</em></p>
            </body>
        </html>
        """
    
    @app.route('/webhook', methods=['POST'])
    def stripe_webhook():
        # Webhook para recibir eventos de Stripe (Suscripciones renovadas, canceladas, etc.)
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        # TODO: Verificar firma del webhook con STRIPE_WEBHOOK_SECRET
        # TODO: Procesar eventos (subscription.created, subscription.deleted, etc.)
        
        logger.info(f"📥 Webhook recibido de Stripe")
        
        return jsonify({'status': 'received'}), 200
    
    logger.info("✅ Rutas de Stripe configuradas")
