#!/usr/bin/env python3
"""
Script para enviar mensajes al usuario vía Telegram Bot.
Uso: python send_telegram_message.py <USER_ID> "<mensaje>"
Ejemplo: python send_telegram_message.py 123456789 "Hola desde el agente!"
"""

import os
import sys
import asyncio
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_message_sync(user_id: int, message: str) -> bool:
    """Envía mensaje usando requests (síncrono)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": user_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        if response.json().get("ok"):
            print(f"✅ Mensaje enviado exitosamente a User ID: {user_id}")
            return True
        else:
            print(f"❌ Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("\n" + "="*60)
        print("❌ USO INCORRECTO")
        print("="*60)
        print("Uso: python send_telegram_message.py <USER_ID> \"<mensaje>\"")
        print("\nEjemplo:")
        print('  python send_telegram_message.py 123456789 "Hola Harold!"')
        print("="*60 + "\n")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    message = " ".join(sys.argv[2:])
    
    print("\n" + "="*60)
    print("📤 ENVIANDO MENSAJE VÍA TELEGRAM BOT")
    print("="*60)
    print(f"🆔 User ID: {user_id}")
    print(f"💬 Mensaje: {message[:100]}...")
    print("="*60 + "\n")
    
    success = send_message_sync(user_id, message)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
