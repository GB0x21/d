import os
import asyncio
import logging
from telegram import Bot
from scraper.hd_scraper import HomeDepotScraper
from scraper.glitch_detector import GlitchDetector
from database.models import DatabaseManager

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# UTILIDAD: LIMPIAR VARIABLES DE ENTORNO
# ─────────────────────────────────────────────
def clean(value, default=None):
    if value is None:
        return default
    return value.replace('"', '').replace("'", '').strip()

# ─────────────────────────────────────────────
# CARGAR CONFIGURACIÓN (YA LIMPIA)
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = clean(os.getenv("TELEGRAM_TOKEN"), "YOUR_TELEGRAM_TOKEN")
CHAT_ID = clean(os.getenv("CHAT_ID"), "YOUR_CHAT_ID")

stores_raw = clean(os.getenv("HD_STORES"), "2010,2023,2045,2089")
HD_STORES = [s.strip() for s in stores_raw.split(",") if s.strip()]

HD_CHECK_INTERVAL = int(clean(os.getenv("HD_CHECK_INTERVAL"), "300"))
HD_PRICE_DROP_THRESHOLD = float(clean(os.getenv("HD_PRICE_DROP_THRESHOLD"), "0.90"))

# ─────────────────────────────────────────────
# FUNCIÓN PARA ENVIAR MENSAJES A TELEGRAM
# ─────────────────────────────────────────────
async def send_telegram_alert(bot, message):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )
        logger.info("✅ Alerta enviada a Telegram.")
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Telegram: {e}")

# ─────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────
async def main_loop():
    # Validación básica
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN" or CHAT_ID == "YOUR_CHAT_ID":
        logger.warning("*******************************************************")
        logger.warning("*** Configura TELEGRAM_TOKEN y CHAT_ID correctamente ***")
        logger.warning("*******************************************************")
        return

    # Inicializar bot de Telegram
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
    except Exception as e:
        logger.error(f"🚨 Error creando bot de Telegram: {e}")
        return

    # Inicializar componentes
    db_manager = DatabaseManager()
    scraper = HomeDepotScraper(HD_STORES)
    detector = GlitchDetector(db_manager, HD_PRICE_DROP_THRESHOLD)

    logger.info("🚀 Bot de Home Depot iniciado...")
    logger.info(f"🏪 Monitoreando tiendas: {HD_STORES}")
    logger.info(f"⏱ Intervalo: {HD_CHECK_INTERVAL} segundos")

    while True:
        try:
            logger.info("🔎 Iniciando ciclo de scraping...")
            items = scraper.check_all_stores()

            if not items:
                logger.warning("⚠️ No se encontraron productos.")
            else:
                logger.info(f"📦 Items encontrados: {len(items)}")

            for item in items:
                alert = detector.analyze_item(item)

                if alert:
                    logger.info(f"🔥 ¡Alerta detectada!: {alert['type']}")
                    await send_telegram_alert(bot, alert['message'])

            logger.info(f"✅ Ciclo completado. Esperando {HD_CHECK_INTERVAL} segundos...\n")
            await asyncio.sleep(HD_CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"💥 Error en el loop principal: {e}")
            await asyncio.sleep(60)

# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main_loop())
