import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os

# --- LIAISON AVEC LE DOCKER-COMPOSE ---
ANALYTICS_API_URL = os.getenv("ANALYTICS_API_URL", "http://analytics:8001")
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

st.set_page_config(page_title="Dashboard Décisionnel - Groupe 4", layout="wide")

st.title("📊 ERP & BI : Pilotage Décisionnel Intelligent")
st.markdown("*Distribution Commerciale - Master 1 (Groupe 4)*")

tab1, tab2, tab3 = st.tabs(["👥 Segmentation Client (RFM)", "📈 Prédictions des Ventes (ARIMA)", "🤖 Reporting IA (NLG)"])

# --- ONGLET 1 : DATA MINING (RFM) ---
with tab1:
    st.header("Analyse RFM & Clustering K-Means")
    if st.button("Lancer la segmentation"):
        with st.spinner("Calcul des clusters en cours..."):
            res = requests.get(f"{ANALYTICS_API_URL}/mining/rfm")
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict) and "status" in data:
                    st.warning(data["status"])
                else:
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    fig = px.scatter(df, x="recence", y="frequence", size="montant_total", color="segment",
                                     title="Répartition des Segments Clients (VIP vs Risque)",
                                     color_discrete_map={"VIP": "green", "Occasionnels": "blue", "À risque": "red"})
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Erreur de connexion au service Analytics.")

# --- ONGLET 2 : PRÉDICTIONS (ARIMA) ---
with tab2:
    st.header("Prédiction des Ventes sur 3 Mois")
    if st.button("Lancer les prédictions (ARIMA)"):
        with st.spinner("Modélisation des séries temporelles..."):
            res = requests.get(f"{ANALYTICS_API_URL}/mining/predictions")
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "mock":
                    st.info(data["message"])
                
                df_pred = pd.DataFrame(data["data"])
                df_pred.columns = ["Période", "Chiffre d'Affaires Prévu (€)"]
                
                st.dataframe(df_pred)
                fig2 = px.line(df_pred, x="Période", y="Chiffre d'Affaires Prévu (€)", markers=True,
                               title="Tendance des Ventes Futures", line_shape="spline")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.error("Erreur lors des prédictions.")

# --- ONGLET 3 : IA & NLG ---
with tab3:
    st.header("Génération de Rapport Assisté par IA")
    st.markdown("Ce module analyse les KPIs actuels et génère un commentaire stratégique (avec système de secours Anti-Crash).")
    
    if st.button("🤖 Générer le Rapport Mensuel"):
        with st.spinner("Analyse des données en cours..."):
            try:
                # 1. Récupération des vrais chiffres depuis votre base de données
                kpi_res = requests.get(f"{ANALYTICS_API_URL}/kpis")
                if kpi_res.status_code == 200:
                    kpis = kpi_res.json()
                    ca = kpis.get("ca_total", 0)
                    marge = kpis.get("marge_totale", 0)

                    # --- LE PLAN B (Le rapport généré localement si l'API plante) ---
                    fallback_text = f"Analyse stratégique automatique : Sur la période en cours, l'entreprise a enregistré un Chiffre d'Affaires total de {ca}€, dégageant une Marge Nette de {marge}€. La rentabilité globale est positive. Recommandation métier : Nous suggérons de cibler les clients du segment 'Occasionnels' avec des promotions spécifiques pour augmenter la fréquence d'achat et sécuriser cette marge."

                    if not HF_TOKEN or HF_TOKEN == "":
                        st.success("Rapport généré avec succès (Mode Local/Secours) !")
                        st.info(f'"{fallback_text}"')
                    else:
                        # --- LE PLAN A (On essaie de joindre Hugging Face) ---
                        try:
                            HF_API_URL = "https://router.huggingface.co/hf-inference/models/HuggingFaceH4/zephyr-7b-beta"
                            prompt = f"Rédige un résumé financier en une phrase. CA = {ca}€, Marge = {marge}€."
                            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                            
                            # Timeout de 5 secondes pour ne pas faire attendre l'utilisateur
                            hf_res = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=5)
                            
                            if hf_res.status_code == 200:
                                texte_ia = hf_res.json()[0]['generated_text'].replace(prompt, "").strip()
                                st.success("Rapport généré par l'IA Distante !")
                                st.info(f'"{texte_ia}"')
                            else:
                                # Si HF renvoie une erreur (ex: 404), on affiche le Plan B !
                                st.warning(f"Le serveur IA distant est indisponible (Erreur {hf_res.status_code}). Basculement automatique sur le système de secours.")
                                st.success("Rapport généré avec succès !")
                                st.info(f'"{fallback_text}"')
                                
                        except Exception:
                            # Si internet coupe totalement, on affiche le Plan B !
                            st.warning("Délai d'attente dépassé. Basculement automatique sur le système de secours.")
                            st.success("Rapport généré avec succès !")
                            st.info(f'"{fallback_text}"')
                else:
                    st.error("Impossible de récupérer les KPIs depuis l'Analytics.")
            except Exception as e:
                st.error(f"Le service Analytics est injoignable : {e}")