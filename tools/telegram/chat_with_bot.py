#!/usr/bin/env python3
"""
Script interactivo para chatear con el bot desde la terminal.
El agente puede usar este script para enviar comandos al bot y ver respuestas.
"""

import os
import sys
import requests
import time

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class TelegramBotChat:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        
    def send_message(self, chat_id: int, text: str) -> bool:
        """Envía un mensaje al chat especificado."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json().get("ok", False)
        except:
            return False
    
    def get_updates(self, timeout: int = 30) -> list:
        """Obtiene actualizaciones del bot."""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": timeout
        }
        
        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                updates = data["result"]
                if updates:
                    self.last_update_id = updates[-1]["update_id"]
                return updates
            return []
        except:
            return []
    
    def get_bot_info(self) -> dict:
        """Obtiene información del bot."""
        url = f"{self.base_url}/getMe"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("ok"):
                return data["result"]
        except:
            pass
        return {}

def main():
    if len(sys.argv) < 2:
        print("\n" + "="*60)
        print("❌ FALTA TELEGRAM USER ID")
        print("="*60)
        print("Uso: python chat_with_bot.py <USER_ID>")
        print("\nSi no conoces tu User ID, ejecuta primero:")
        print("  python get_my_telegram_id.py")
        print("="*60 + "\n")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    bot = TelegramBotChat(TELEGRAM_BOT_TOKEN)
    
    bot_info = bot.get_bot_info()
    bot_username = bot_info.get("username", "Unknown")
    
    print("\n" + "="*60)
    print("🤖 CHAT CON BOT DE TELEGRAM")
    print("="*60)
    print(f"🤖 Bot: @{bot_username}")
    print(f"👤 User ID: {user_id}")
    print("\n📝 Comandos disponibles:")
    print("  /start        - Iniciar bot")
    print("  /status       - Ver estado del sistema")
    print("  /balance      - Ver balance paper trading")
    print("  /market       - Análisis de mercado")
    print("  /help         - Ver todos los comandos")
    print("  exit          - Salir del chat")
    print("="*60 + "\n")
    
    while True:
        try:
            message = input("💬 Tú: ").strip()
            
            if message.lower() in ["exit", "quit", "salir"]:
                print("\n👋 Chat finalizado.\n")
                break
            
            if not message:
                continue
            
            print("📤 Enviando mensaje...")
            success = bot.send_message(user_id, message)
            
            if success:
                print("✅ Mensaje enviado. Esperando respuesta del bot...")
                
                max_wait = 10
                for i in range(max_wait):
                    time.sleep(1)
                    updates = bot.get_updates(timeout=1)
                    
                    for update in updates:
                        if "message" in update:
                            msg = update["message"]
                            if msg.get("from", {}).get("is_bot"):
                                print(f"\n🤖 Bot: {msg.get('text', '[Sin texto]')}\n")
                                break
                    else:
                        continue
                    break
                else:
                    print("⏱️ No hay respuesta del bot (timeout)\n")
            else:
                print("❌ Error enviando mensaje\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrumpido.\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()
