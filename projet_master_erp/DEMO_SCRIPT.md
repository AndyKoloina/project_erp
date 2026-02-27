# 🎬 Script de Présentation Vidéo : ERP & BI Intelligent

Ce document sert de guide pour l'enregistrement de votre vidéo de démonstration.

## 🛠️ Stack Technique & Architecture

Avant de commencer la démo, voici ce que nous utilisons :

- **Backend (ERP & Analytics)** : FastAPI (Python) - *Performance et documentation automatique.*
- **Intégration (ETL)** : Pandas - *Puissant pour la transformation de données.*
- **Base de Données** : PostgreSQL - *Robuste pour le transactionnel et le warehouse.*
- **Data Mining** : Scikit-Learn (Clustering K-Means) & Statsmodels (Arima).
- **Intelligence Artificielle** : API Hugging Face (Modèle Zephyr/Llama) pour le reporting narratif.
- **Frontend** : Streamlit - *Développement rapide de dashboards data.*
- **BI Pure** : Metabase - *Exploration visuelle des données.*
- **Infrastructure** : Docker Compose - *Orchestration multi-services.*

---

## 🎤 Script de la Vidéo (Parole)

### Introduction (0:00 - 0:30)
"Bonjour à tous ! Aujourd'hui, nous allons vous présenter notre projet de Master 1 : un système ERP intelligent couplé à une pile décisionnelle complète. Notre équipe, le Groupe 4, a conçu une architecture micro-services robuste permettant de piloter une activité de distribution de bout en bout."

### Présentation de l'Architecture (0:30 - 1:00)
"Le projet repose sur 6 services Docker. Les données transactionnelles naissent dans notre ERP sous FastAPI, sont transformées vers un Data Warehouse via un service ETL automatisé, puis analysées par un moteur Analytics spécialisé dans le data mining et les prédictions."

### Étape 1 : Initialisation & Seeding (1:00 - 2:30)
"Passons à la pratique. Nous commençons par initialiser notre environnement. En un clic sur notre endpoint de seeding, nous générons automatiquement nos produits, nos clients, et surtout un historique massif de 50 commandes passées pour permettre à l'IA d'avoir assez de matière pour ses prédictions."
*(Action : Montrer le clic sur les liens /seed et /seed_massive dans le guide)*

### Étape 2 : Le Flux ETL (2:30 - 3:30)
"Une fois les données créées, notre service ETL entre en jeu. Il extrait les données brutes de l'ERP, les nettoie, et les structure en Schéma en Étoile dans notre Data Warehouse. C'est ici que nous créons nos dimensions Temps, Client et Produit."
*(Action : Montrer le déclenchement de l'ETL et le status 'Succès')*

### Étape 3 : Dashboard & Intelligence Artificielle (3:30 - 5:00)
"Voici le cœur visuel du projet : notre Dashboard Streamlit. 
- Dans l'onglet **Segmentation**, l'algorithme K-Means identifie automatiquement nos clients VIP et ceux à risque. 
- Dans l'onglet **Prédictions**, le modèle ARIMA anticipe nos ventes sur les 3 prochains mois. 
- Enfin, notre module **IA Reporting** analyse ces chiffres et rédige un résumé stratégique en langage naturel via une API distante."
*(Action : Montrer les trois onglets et la génération du rapport IA)*

### Conclusion (5:00 - 5:30)
"Ce projet démontre comment l'IA et la BI peuvent transformer des données brutes en outils de décision stratégique. Merci de votre attention !"

---

## 💡 Conseils pour l'enregistrement
1.  **Transition fluide** : Ouvrez tous les onglets (Guide, Dashboard, Swagger) à l'avance.
2.  **Zoom** : N'hésitez pas à zoomer sur le tableau de bord Streamlit pour que les graphiques soient bien visibles.
3.  **Ton** : Gardez un ton enthousiaste et professionnel.
