# 📖 Guide de Démonstration : ERP & BI Intelligent

Ce projet est une solution complète de gestion (ERP) couplée à une pile décisionnelle (BI) et d'Intelligence Artificielle.

## 🏗️ Architecture du Projet

Le système est composé de **6 services** orchestrés par Docker :

1.  **🐘 Base de Données (PostgreSQL)** : Stockage central des données ERP et du Data Warehouse.
2.  **🚀 ERP Service (FastAPI)** : Gestion des ventes, clients et stocks.
3.  **🔄 ETL Service (Pandas)** : Automatisation de l'extraction et transformation vers le schéma en étoile.
4.  **🧠 Analytics Service (Scikit-Learn)** : Moteur de Data Mining (RFM, ARIMA).
5.  **📊 Dashboard IA (Streamlit)** : Interface utilisateur avec reporting assisté par IA (NLG).
6.  **📉 Metabase** : Outil de BI en libre-service pour l'exploration visuelle.

---

## 🚀 Installation Rapide

1.  Assurez-vous d'avoir un fichier `.env` à la racine avec les variables nécessaires (DB_USER, DB_PASS, etc.).
2.  Lancez l'infrastructure :
    ```bash
    docker-compose up -d --build
    ```

---

## 🎬 Étapes de la Démonstration

### 1️⃣ Initialisation des Données (Master Data)
Populez l'ERP avec les premiers produits et clients.
-   **Action** : Effectuer une requête POST sur `http://localhost:8000/seed/`
-   **Outil** : Navigateur ou Postman.

### 2️⃣ Génération de Données Massives
Générez 50+ commandes historiques pour alimenter les modèles d'IA.
-   **Action** : Effectuer une requête POST sur `http://localhost:8000/seed_massive/`

### 3️⃣ Lancement de l'ETL
Transférez les données de l'ERP vers le Data Warehouse BI (Schéma en étoile).
-   **Action** : Effectuer une requête POST sur `http://localhost:8002/trigger`
-   **Vérification** : Consultez `http://localhost:8002/status` pour voir les lignes chargées.

### 4️⃣ Analyse & Data Mining
Le service analytics traite maintenant les données du Warehouse.
-   **Segmentation RFM** : `http://localhost:8001/mining/rfm`
-   **Prédictions ARIMA** : `http://localhost:8001/mining/predictions`

### 5️⃣ Dashboard Interactif & IA
Accédez à l'interface visuelle (`http://localhost:8501`).
-   **Onglet RFM** : Visualisez les segments clients (VIP, Risque).
-   **Onglet Prédictions** : Consultez les tendances de ventes futures.
-   **Onglet IA** : Générez un rapport narratif automatique basé sur les KPIs.

### 6️⃣ Exploration BI (Metabase)
Pour une analyse plus poussée : `http://localhost:3000`.
-   Connectez-vous à la base `bi_warehouse` pour créer vos propres graphiques.

---

## 🔗 Liens Utiles

| Service | URL / Port | Documentation API |
| :--- | :--- | :--- |
| **ERP** | [localhost:8000](http://localhost:8000) | [/docs](http://localhost:8000/docs) |
| **ETL** | [localhost:8002](http://localhost:8002) | [/docs](http://localhost:8002/docs) |
| **Analytics** | [localhost:8001](http://localhost:8001) | [/docs](http://localhost:8001/docs) |
| **Dashboard** | [localhost:8501](http://localhost:8501) | - |
| **Metabase** | [localhost:3000](http://localhost:3000) | - |
