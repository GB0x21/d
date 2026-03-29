# Home Depot Penny Item Bot

Este bot de Telegram está diseñado para rastrear "penny items" y liquidaciones en Home Depot, alertando sobre caídas de precios significativas en tiendas específicas del Bay Area.

## Características
- **Scraping de Liquidaciones**: Monitorea la sección "Clearance" de Home Depot.
- **Detección de Penny Items**: Identifica productos con precios de $0.01.
- **Historial de Precios**: Guarda un historial de precios por SKU para detectar glitches en tiempo real.
- **Alertas en Telegram**: Envía notificaciones instantáneas a un chat de Telegram cuando se detectan ofertas.
- **Configurable**: Fácilmente adaptable a diferentes tiendas y umbrales de descuento.

## Arquitectura
El bot está construido en Python y utiliza:
- `requests` para interactuar con la API de Home Depot (o simulación).
- `SQLAlchemy` para la gestión de la base de datos SQLite.
- `python-telegram-bot` para la interacción con Telegram.
- `undetected-chromedriver` y `selenium` como fallback para scraping si la API falla o es bloqueada.

## Configuración
1. **Clonar el Repositorio**:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd hd_penny_bot
   ```

2. **Variables de Entorno**: Crea un archivo `.env` en la raíz del proyecto con la siguiente configuración:
   ```ini
   TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
   CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
   HD_STORES="2010,2023,2045,2089"  # IDs de tiendas de Home Depot separadas por comas
   HD_CHECK_INTERVAL=300           # Intervalo de chequeo en segundos (ej. 300s = 5 minutos)
   HD_PRICE_DROP_THRESHOLD=0.90    # Umbral de caída de precio para alertar (ej. 0.90 = 90% de descuento)
   ```
   - `TELEGRAM_TOKEN`: Obtén este token de BotFather en Telegram.
   - `CHAT_ID`: El ID del chat o canal donde el bot enviará las alertas. Puedes obtenerlo enviando un mensaje a `@userinfobot` en Telegram.
   - `HD_STORES`: Una lista de IDs de tiendas de Home Depot. Puedes encontrar los IDs de tienda en la URL de Home Depot cuando navegas a una tienda específica.

## Instalación y Ejecución (Local)
1. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar el Bot**:
   ```bash
   python main.py
   ```

## Ejecución con Docker
1. **Construir la Imagen Docker**:
   ```bash
   docker build -t hd-penny-bot .
   ```

2. **Ejecutar el Contenedor Docker**: Asegúrate de que tu archivo `.env` esté configurado correctamente.
   ```bash
   docker run --env-file ./.env hd-penny-bot
   ```

## Uso del Bot (Telegram)
Actualmente, el bot envía alertas automáticamente. Se pueden añadir comandos en el futuro para interactuar con el bot (ej. `/status`, `/add_store`, `/check_sku`).

## Notas Importantes
- El scraping de sitios web puede estar sujeto a los Términos de Servicio del sitio. Utiliza este bot de manera responsable.
- Home Depot puede implementar medidas anti-scraping (ej. Cloudflare). La implementación actual incluye un placeholder para `undetected-chromedriver` que podría ser necesario para bypassar estas protecciones.
- La API interna de Home Depot puede cambiar sin previo aviso, lo que podría requerir actualizaciones en el código de scraping.

## Contribuciones
¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar el bot o encuentras algún problema, no dudes en abrir un issue o enviar un pull request.
