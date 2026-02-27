import pandas as pd
from sqlalchemy import create_engine, text
import os
import time
import schedule
import threading
from fastapi import FastAPI, BackgroundTasks

# --- CONFIGURATION ---
SRC_URL = os.getenv("SRC_DB_URL", "postgresql://admin:password@db/erp_db")
TGT_URL = os.getenv("TGT_DB_URL", "postgresql://admin:password@db/bi_warehouse")

app = FastAPI(
    title="ETL Manager (Distribution)",
    description="Extraction de l'ERP vers le Data Warehouse (Modèle en Étoile)",
    version="3.0"
)

etl_status = {
    "last_run": "Jamais",
    "status": "En attente",
    "rows_loaded": 0
}

# --- FONCTION UTILITAIRE : SAISON ---
def get_season(month):
    if month in [12, 1, 2]:
        return "Hiver"
    elif month in [3, 4, 5]:
        return "Printemps"
    elif month in [6, 7, 8]:
        return "Été"
    else:
        return "Automne"

# --- LOGIQUE MÉTIER ETL ---
def run_etl_logic():
    global etl_status
    print("--- 🔄 Démarrage ETL (Star Schema) ---")
    etl_status["status"] = "Extraction en cours..."
    
    try:
        src_engine = create_engine(SRC_URL)
        tgt_engine = create_engine(TGT_URL)

        # ==========================================
        # 1. EXTRACTION (Depuis l'ERP)
        # ==========================================
        query = """
        SELECT 
            o.id as order_id, o.created_at as date_commande, o.client_id,
            oi.product_id, oi.quantity, oi.unit_price, oi.discount_applied,
            p.sku, p.name as product_name, p.purchase_price,
            c.name as client_name, c.is_vip
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN clients c ON o.client_id = c.id
        WHERE o.status = 'VALIDATED'
        """
        with src_engine.connect() as conn:
            df_raw = pd.read_sql(query, conn)
        
        if df_raw.empty:
            print("Aucune commande validée à traiter.")
            etl_status["status"] = "Terminé (Vide)"
            return

        etl_status["status"] = "Transformation en cours..."

        # ==========================================
        # 2. TRANSFORMATION (Création des Dimensions)
        # ==========================================
        
        # --- Dim_Temps ---
        df_raw['date_commande'] = pd.to_datetime(df_raw['date_commande'])
        dim_temps = pd.DataFrame({'date_key': df_raw['date_commande'].dt.date.unique()})
        dim_temps['date_key'] = pd.to_datetime(dim_temps['date_key'])
        dim_temps['annee'] = dim_temps['date_key'].dt.year
        dim_temps['mois'] = dim_temps['date_key'].dt.month
        dim_temps['jour'] = dim_temps['date_key'].dt.day
        dim_temps['saison'] = dim_temps['mois'].apply(get_season)

        # --- Dim_Produit ---
        dim_produit = df_raw[['product_id', 'sku', 'product_name', 'purchase_price']].drop_duplicates()

        # --- Dim_Client ---
        dim_client = df_raw[['client_id', 'client_name', 'is_vip']].drop_duplicates()
        dim_client['segment'] = dim_client['is_vip'].apply(lambda x: 'VIP' if x else 'Standard')
        # Ajout d'une géographie fictive pour respecter le CDC
        dim_client['geographie'] = 'National'

        # --- Dim_Magasin ---
        # Comme l'ERP actuel n'a pas de multi-magasins, on crée une dimension par défaut
        dim_magasin = pd.DataFrame({
            'magasin_id': [1],
            'nom_magasin': ['Boutique Centrale'],
            'ville': ['Antananarivo']
        })

        # ==========================================
        # 3. TRANSFORMATION (Création de la Table de Faits)
        # ==========================================
        fact_ventes = df_raw.copy()
        
        # Calcul des indicateurs (Mesures)
        fact_ventes['date_key'] = fact_ventes['date_commande'].dt.date
        fact_ventes['magasin_id'] = 1 # Lien vers Dim_Magasin
        fact_ventes['montant_ht'] = fact_ventes['quantity'] * fact_ventes['unit_price']
        fact_ventes['cout_total'] = fact_ventes['quantity'] * fact_ventes['purchase_price']
        fact_ventes['marge'] = fact_ventes['montant_ht'] - fact_ventes['cout_total']

        # Sélection finale des colonnes pour la table de faits
        fact_ventes = fact_ventes[[
            'order_id', 'date_key', 'client_id', 'product_id', 'magasin_id',
            'quantity', 'montant_ht', 'marge'
        ]]

        etl_status["status"] = "Chargement en cours..."

        # ==========================================
        # 4. CHARGEMENT (Vers le Data Warehouse)
        # ==========================================
        with tgt_engine.connect() as conn:
            dim_temps.to_sql('dim_temps', conn, if_exists='replace', index=False)
            dim_produit.to_sql('dim_produit', conn, if_exists='replace', index=False)
            dim_client.to_sql('dim_client', conn, if_exists='replace', index=False)
            dim_magasin.to_sql('dim_magasin', conn, if_exists='replace', index=False)
            fact_ventes.to_sql('fact_ventes', conn, if_exists='replace', index=False)
        
        count = len(fact_ventes)
        print(f"✅ ETL Terminé : {count} faits de ventes chargés.")
        etl_status["rows_loaded"] = count
        etl_status["status"] = "Succès"
        etl_status["last_run"] = time.strftime("%H:%M:%S")
        
    except Exception as e:
        print(f"❌ Erreur ETL: {e}")
        etl_status["status"] = f"Erreur: {str(e)}"

# --- SCHEDULER (Automatisation) ---
def run_scheduler():
    schedule.every(1).minutes.do(run_etl_logic)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
def start_scheduler():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

# --- ENDPOINTS (Swagger) ---
@app.get("/")
def health_check():
    return {"status": "Online"}

@app.get("/status")
def get_status():
    return etl_status

@app.post("/trigger")
def trigger_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_etl_logic)
    return {"msg": "ETL lancé en arrière-plan vers le Data Warehouse !"}