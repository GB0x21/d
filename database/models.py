from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    sku = Column(String, primary_key=True)
    title = Column(String)
    url = Column(String)
    last_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    price_history = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, ForeignKey('products.sku'))
    store_id = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    product = relationship("Product", back_populates="price_history")

class DatabaseManager:
    def __init__(self, db_url="sqlite:///hd_bot.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def update_price(self, sku, title, url, store_id, current_price):
        session = self.Session()
        try:
            # Buscar o crear producto
            product = session.query(Product).filter_by(sku=sku).first()
            if not product:
                product = Product(sku=sku, title=title, url=url, last_price=current_price)
                session.add(product)
            else:
                product.last_price = current_price
                product.last_updated = datetime.datetime.utcnow()

            # Registrar historial
            history = PriceHistory(sku=sku, store_id=store_id, price=current_price)
            session.add(history)
            
            session.commit()
            return product
        except Exception as e:
            session.rollback()
            print(f"DB Error: {e}")
            return None
        finally:
            session.close()

    def get_previous_price(self, sku, store_id):
        session = self.Session()
        try:
            # Obtener el penúltimo precio registrado para este SKU y tienda
            history = session.query(PriceHistory)\
                .filter_by(sku=sku, store_id=store_id)\
                .order_by(PriceHistory.timestamp.desc())\
                .offset(1).first()
            return history.price if history else None
        finally:
            session.close()
