from typing import Dict, Optional
from database.models import DatabaseManager

class GlitchDetector:
    def __init__(self, db_manager: DatabaseManager, price_drop_threshold: float = 0.90):
        self.db = db_manager
        self.threshold = price_drop_threshold

    def analyze_item(self, item: Dict) -> Optional[Dict]:
        """
        Analiza un item para detectar si es un penny item o un glitch de precio.
        Retorna un diccionario con la alerta si se detecta algo, de lo contrario None.
        """
        sku = item['sku']
        current_price = item['price']
        original_price = item.get('original_price', 0)
        store_id = item['store_id']
        
        # 1. Detección de Penny Item ($0.01)
        if current_price <= 0.01:
            return {
                "type": "PENNY_ITEM",
                "message": f"🚨 ¡PENNY ITEM DETECTADO! 🚨\n{item['title']}\nPrecio: $0.01\nTienda: {store_id}\nSKU: {sku}\nURL: {item['url']}"
            }

        # 2. Detección de Glitch por caída drástica (90%+)
        if original_price > 0:
            discount = 1 - (current_price / original_price)
            if discount >= self.threshold:
                return {
                    "type": "PRICE_GLITCH",
                    "message": f"🔥 ¡GLITCH DE PRECIO! ({discount*100:.0f}% OFF) 🔥\n{item['title']}\nPrecio: ${current_price} (Antes: ${original_price})\nTienda: {store_id}\nSKU: {sku}\nURL: {item['url']}"
                }

        # 3. Comparación con historial (Caída repentina en la última hora)
        prev_price = self.db.get_previous_price(sku, store_id)
        if prev_price and current_price < prev_price:
            drop = 1 - (current_price / prev_price)
            if drop >= 0.50: # Si bajó más del 50% respecto a la última hora
                return {
                    "type": "REAL_TIME_DROP",
                    "message": f"⚡️ ¡CAÍDA DE PRECIO EN TIEMPO REAL! ⚡️\n{item['title']}\nPrecio: ${current_price} (Hace 1h: ${prev_price})\nTienda: {store_id}\nSKU: {sku}\nURL: {item['url']}"
                }

        # Actualizar base de datos con el nuevo precio
        self.db.update_price(sku, item['title'], item['url'], store_id, current_price)
        
        return None
