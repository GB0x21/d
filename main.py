import os
import time
import asyncio
import logging
from telegram import Bot
from scraper.hd_scraper import HomeDepotScraper
from scraper.glitch_detector import GlitchDetector
from database.models import DatabaseManager

# Configuración básica
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar configuración (en producción usar .env)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")
HD_STORES = os.getenv("HD_STORES", "2010,2023,2045,2089").split(",")
HD_CHECK_INTERVAL = int(os.getenv("HD_CHECK_INTERVAL", 300))
HD_PRICE_DROP_THRESHOLD = float(os.getenv("HD_PRICE_DROP_THRESHOLD", 0.90))

async def send_telegram_alert(bot, message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info("Alerta enviada a Telegram.")
    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}")

async def main_loop():
    # Inicializar componentes
    db_manager = DatabaseManager()
    scraper = HomeDepotScraper(HD_STORES)
    detector = GlitchDetector(db_manager, HD_PRICE_DROP_THRESHOLD)
    bot = Bot(token=TELEGRAM_TOKEN)

    logger.info("Bot de Home Depot iniciado...")
    logger.info(f"Monitoreando tiendas: {HD_STORES}")

    while True:
        try:
            logger.info("Iniciando ciclo de scraping...")
            items = scraper.check_all_stores()
            
            for item in items:
                alert = detector.analyze_item(item)
                if alert:
                    logger.info(f"¡Alerta detectada!: {alert['type']}")
                    await send_telegram_alert(bot, alert['message'])
            
            logger.info(f"Ciclo completado. Esperando {HD_CHECK_INTERVAL} segundos...")
            await asyncio.sleep(HD_CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error en el loop principal: {e}")
            await asyncio.sleep(60) # Esperar un minuto antes de reintentar

if __name__ == "__main__":
    # En un entorno real, se usaría una librería como python-dotenv para cargar el .env
    # Por simplicidad, aquí se asume que las variables de entorno están seteadas.
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN" or CHAT_ID == "YOUR_CHAT_ID":
        logger.warning("*******************************************************")
        logger.warning("*** Por favor, configura TELEGRAM_TOKEN y CHAT_ID ***")
        logger.warning("*******************************************************")
    else:
        asyncio.run(main_loop())
