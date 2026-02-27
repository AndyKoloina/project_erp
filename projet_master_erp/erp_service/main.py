from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
import os
import time
import random

# --- CONFIGURATION BDD ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db/erp_db")

def wait_for_db():
    retries = 0
    while retries < 30:
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                pass
            print("✅ BDD Connectée.")
            return engine
        except:
            print("⏳ Attente BDD...")
            time.sleep(2)
            retries += 1
    raise Exception("Erreur connexion BDD")

engine = wait_for_db()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

# --- 1. MODÈLES DE DONNÉES (SQLAlchemy) ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    role = Column(String)

class Client(Base):
    """Module CRM"""
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    credit_limit = Column(Float, default=1000.0)
    current_debt = Column(Float, default=0.0)
    is_vip = Column(Boolean, default=False)

class Product(Base):
    """Module Gestion des Stocks"""
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    name = Column(String)
    price = Column(Float)
    purchase_price = Column(Float)
    stock_quantity = Column(Integer, default=0)
    safety_stock = Column(Integer, default=10)

class Order(Base):
    """Module Ventes & Facturation"""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    total_amount = Column(Float, default=0.0)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    discount_applied = Column(Float, default=0.0)
    
    order = relationship("Order", back_populates="items")

class StockMovement(Base):
    """Traçabilité des mouvements de stock"""
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    movement_type = Column(String) # 'IN', 'OUT'
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

class AuditLog(Base):
    """Journalisation et traçabilité"""
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    details = Column(String)
    user_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="ERP Distribution (SOA)", version="3.0")

# --- FONCTIONS UTILITAIRES ---
def log_action(db, action, details, user_id=None):
    db.add(AuditLog(action=action, details=details, user_id=user_id))

# --- DTOs ---
class OrderItemDTO(BaseModel):
    product_id: int
    quantity: int

class OrderCreateDTO(BaseModel):
    client_id: int
    items: list[OrderItemDTO]
    user_id: int

# --- ENDPOINTS ---

@app.post("/orders/")
def create_order(order_data: OrderCreateDTO):
    """Création d'une commande (Devis)"""
    db = SessionLocal()
    
    try:
        # 1. Vérifications Client
        client = db.query(Client).filter(Client.id == order_data.client_id).first()
        if not client:
            raise HTTPException(404, "Client introuvable")

        # 2. Règle métier : Blocage si impayés > Limite de crédit
        if client.current_debt > client.credit_limit:
            log_action(db, "BLOCKED_ORDER", f"Client {client.id} a dépassé sa limite de crédit.", order_data.user_id)
            db.commit()
            raise HTTPException(400, "Commande bloquée : Limite de crédit dépassée.")

        new_order = Order(client_id=client.id, created_by_id=order_data.user_id)
        db.add(new_order)
        db.flush()

        total = 0.0
        for item_data in order_data.items:
            product = db.query(Product).filter(Product.id == item_data.product_id).first()
            if not product:
                raise HTTPException(404, f"Produit {item_data.product_id} introuvable")
            
            discount = 0.10 if client.is_vip else 0.0
            final_price = product.price * (1 - discount)
            
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=final_price,
                discount_applied=discount
            )
            db.add(order_item)
            total += final_price * item_data.quantity

        new_order.total_amount = total
        log_action(db, "CREATE_ORDER", f"Commande {new_order.id} créée", order_data.user_id)
        
        db.commit()
        db.refresh(new_order)
        
        # --- EXTRACTION SÉCURISÉE DES DONNÉES ---
        final_order_id = new_order.id 
        final_total = total
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erreur interne: {str(e)}")
    finally:
        db.close()
        
    # --- LE RETURN EST EN DEHORS DE LA BDD ---
    return {"status": "PENDING", "order_id": final_order_id, "total": final_total}

@app.put("/orders/{order_id}/validate")
def validate_order(order_id: int, user_id: int):
    """Validation et sortie de stock"""
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order or order.status != "PENDING":
        raise HTTPException(400, "Commande invalide ou déjà traitée.")

    # 1. Vérification des stocks pour chaque article
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        
        # Règle métier : Interdiction si stock insuffisant
        if product.stock_quantity < item.quantity:
            log_action(db, "STOCK_ERROR", f"Rupture sur produit {product.sku} lors commande {order_id}", user_id)
            raise HTTPException(400, f"Stock insuffisant pour le produit {product.name}")

    # 2. Déduction des stocks et traçabilité
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock_quantity -= item.quantity
        
        # Mouvement de stock
        db.add(StockMovement(product_id=product.id, quantity=item.quantity, movement_type="OUT", user_id=user_id))
        
        # Alerte seuil de sécurité
        if product.stock_quantity < product.safety_stock:
            log_action(db, "ALERT_STOCK", f"Le produit {product.sku} est sous le seuil de sécurité !", user_id)

    order.status = "VALIDATED"
    
    # Mise à jour dette client
    client = db.query(Client).filter(Client.id == order.client_id).first()
    client.current_debt += order.total_amount

    log_action(db, "VALIDATE_ORDER", f"Commande {order_id} validée et stock déduit.", user_id)
    db.commit()
    db.close()
    return {"status": "VALIDATED", "msg": "Stocks mis à jour avec succès"}

@app.api_route("/seed/", methods=["GET", "POST"])
def seed_data():
    """Génération du Master Data pour la démo"""
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(username="admin", role="admin"))
            db.commit()
        
        admin = db.query(User).first()

        # Seed Produits
        if db.query(Product).count() == 0:
            produits = [
                Product(sku="EAN001", name="PC Portable Pro", price=1200.0, purchase_price=900.0, stock_quantity=50, safety_stock=5),
                Product(sku="EAN002", name="Souris Sans Fil", price=25.0, purchase_price=10.0, stock_quantity=200, safety_stock=20),
                Product(sku="EAN003", name="Écran 27 pouces", price=300.0, purchase_price=220.0, stock_quantity=2, safety_stock=10) # Bientôt en rupture
            ]
            db.add_all(produits)
            db.commit()

        # Seed Clients
        if db.query(Client).count() == 0:
            clients = [
                Client(name="Entreprise Alpha", email="contact@alpha.com", phone="0340011122", credit_limit=5000.0, is_vip=True),
                Client(name="Boutique Beta", email="hello@beta.com", phone="0330099988", credit_limit=500.0, current_debt=600.0) # Ce client sera bloqué
            ]
            db.add_all(clients)
            db.commit()
            
            log_action(db, "SEED", "Produits et Clients générés", admin.id)

        return {"msg": "Données de démo Master Data générées !"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()





@app.api_route("/seed_massive/", methods=["GET", "POST"])
def seed_massive_data():
    """Génère un gros volume de données pour les graphiques BI et l'IA"""
    db = SessionLocal()
    try:
        admin = db.query(User).first()
        if not admin:
            admin = User(username="admin", role="admin")
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # --- LA SÉCURITÉ EST ICI ---
        # On vérifie si les fausses données ont déjà été créées
        if db.query(Product).filter(Product.sku == "MASSIVE-001").first():
            return {"msg": "✅ Les données massives sont DÉJÀ présentes ! Inutile de les recréer. Vous pouvez lancer l'ETL."}

        # 1. Générer 5 Nouveaux Produits
        for i in range(1, 6):
            db.add(Product(sku=f"MASSIVE-00{i}", name=f"Produit Généré {i}", price=100.0*i, purchase_price=70.0*i, stock_quantity=10000, safety_stock=10))
        db.commit()

        # 2. Générer 10 Nouveaux Clients
        for i in range(1, 11):
            # On utilise un timestamp dans l'email/téléphone pour garantir l'unicité à 100% si on relance
            unique_id = random.randint(1000, 9999)
            db.add(Client(name=f"Client Démo {i}", email=f"demo_{unique_id}_{i}@mail.com", phone=f"034{unique_id}0{i}", credit_limit=50000.0, is_vip=(i % 3 == 0)))
        db.commit()

        # 3. Générer 50 Commandes Validées dans le passé (pour ARIMA)
        products = db.query(Product).filter(Product.sku.like("MASSIVE-%")).all()
        clients = db.query(Client).filter(Client.email.like("demo_%")).all()
        
        for _ in range(50):
            c = random.choice(clients)
            random_days_ago = random.randint(1, 90)
            past_date = datetime.utcnow() - timedelta(days=random_days_ago)
            
            order = Order(client_id=c.id, created_by_id=admin.id, status="VALIDATED", created_at=past_date)
            db.add(order)
            db.flush()
            
            total = 0
            for _ in range(random.randint(1, 3)):
                p = random.choice(products)
                qty = random.randint(1, 5)
                discount = 0.10 if c.is_vip else 0.0
                price = p.price * (1 - discount)
                
                db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=price, discount_applied=discount))
                total += price * qty
            
            order.total_amount = total
            
        db.commit()
        return {"msg": "✅ Super Seed terminé ! 50 commandes ont été générées."}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erreur Seed Massive: {str(e)}")
    finally:
        db.close()