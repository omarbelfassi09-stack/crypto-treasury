import streamlit as st
import numpy as np
import requests
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="CryptoTreasury", page_icon="₿", layout="wide")

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1e1e3c, #2d2d6b);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>₿ CryptoTreasury</h1>
    <p>Plateforme de gestion des risques crypto pour entreprises</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_prix():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd,eur",
        "include_24hr_change": "true"
    }
    r = requests.get(url, params=params)
    return r.json()

prix = get_prix()
prix_btc = prix["bitcoin"]["eur"]
prix_eth = prix["ethereum"]["eur"]
var_btc_24h = prix["bitcoin"]["eur_24h_change"]
var_eth_24h = prix["ethereum"]["eur_24h_change"]

col1, col2, col3 = st.columns(3)
col1.metric("Bitcoin (BTC)", f"{prix_btc:,.0f} EUR", f"{var_btc_24h:+.2f}% / 24h")
col2.metric("Ethereum (ETH)", f"{prix_eth:,.0f} EUR", f"{var_eth_24h:+.2f}% / 24h")
col3.metric("Mise a jour", datetime.now().strftime("%H:%M:%S"), "Temps reel")

st.divider()

st.subheader("Parametres de votre portefeuille")
col1, col2, col3 = st.columns(3)
with col1:
    nom_entreprise = st.text_input("Nom de l'entreprise", "Mon Entreprise SAS")
with col2:
    montant_btc = st.number_input("Quantite BTC", min_value=0.0, value=2.0, step=0.1)
with col3:
    montant_eth = st.number_input("Quantite ETH", min_value=0.0, value=10.0, step=1.0)

valeur_btc = montant_btc * prix_btc
valeur_eth = montant_eth * prix_eth
valeur_totale = valeur_btc + valeur_eth

vol_journaliere = 0.70 / np.sqrt(365)
var_95 = valeur_totale * vol_journaliere * 1.645
var_99 = valeur_totale * vol_journaliere * 2.326

st.divider()
st.subheader("Analyse de risque en temps reel")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Valeur totale", f"{valeur_totale:,.0f} EUR")
col2.metric("VaR 95% (1 jour)", f"-{var_95:,.0f} EUR")
col3.metric("VaR 99% (1 jour)", f"-{var_99:,.0f} EUR")
col4.metric("Volatilite annuelle", "70%")

st.divider()
st.subheader("Simulation Monte Carlo — 30 jours")

if st.button("Lancer la simulation"):
    with st.spinner("Simulation de 1000 scenarios en cours..."):
        simulations = 1000
        jours = 30
        resultats = []
        for i in range(simulations):
            valeur = valeur_totale
            for j in range(jours):
                choc = np.random.normal(0.001, vol_journaliere)
                valeur = valeur * (1 + choc)
            resultats.append(valeur)
        
        resultats = np.array(resultats)
        mediane = np.median(resultats)
        pire_cas = np.percentile(resultats, 5)
        meilleur_cas = np.percentile(resultats, 95)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=resultats,
            nbinsx=50,
            marker_color="#4f46e5",
            opacity=0.7,
            name="Scenarios"
        ))
        fig.add_vline(x=valeur_totale, line_dash="dash", line_color="black", annotation_text="Valeur actuelle")
        fig.add_vline(x=pire_cas, line_dash="dash", line_color="red", annotation_text="Pire cas 5%")
        fig.add_vline(x=mediane, line_dash="dash", line_color="green", annotation_text="Mediane")
        fig.update_layout(
            title="Distribution des scenarios sur 30 jours",
            xaxis_title="Valeur du portefeuille (EUR)",
            yaxis_title="Nombre de scenarios",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Scenario pessimiste (5%)", f"{pire_cas:,.0f} EUR", f"{((pire_cas-valeur_totale)/valeur_totale*100):+.1f}%")
        col2.metric("Scenario median", f"{mediane:,.0f} EUR", f"{((mediane-valeur_totale)/valeur_totale*100):+.1f}%")
        col3.metric("Scenario optimiste (95%)", f"{meilleur_cas:,.0f} EUR", f"{((meilleur_cas-valeur_totale)/valeur_totale*100):+.1f}%")

st.divider()
st.subheader("Scenarios de stress (MiCA Art. 76)")
col1, col2, col3 = st.columns(3)
col1.metric("Baisse -30%", f"{valeur_totale*0.70:,.0f} EUR", "-30%")
col2.metric("Baisse -50%", f"{valeur_totale*0.50:,.0f} EUR", "-50%")
col3.metric("Hausse +30%", f"{valeur_totale*1.30:,.0f} EUR", "+30%")

st.divider()
st.divider()
st.subheader("Generer le rapport PDF")
col1, col2, col3 = st.columns(3)
with col1:
    nom_rapport = st.text_input("Nom de l'entreprise pour le rapport", "Mon Entreprise SAS")
with col2:
    btc_rapport = st.number_input("BTC pour le rapport", min_value=0.0, value=montant_btc, step=0.1)
with col3:
    eth_rapport = st.number_input("ETH pour le rapport", min_value=0.0, value=montant_eth, step=1.0)

if st.button("Generer le rapport PDF"):
    from fpdf import FPDF
    from io import BytesIO
    
    valeur_btc_r = btc_rapport * prix_btc
    valeur_eth_r = eth_rapport * prix_eth
    valeur_totale_r = valeur_btc_r + valeur_eth_r
    var_95_r = valeur_totale_r * vol_journaliere * 1.645
    var_99_r = valeur_totale_r * vol_journaliere * 2.326
    poids_r = 10.0
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    
    pdf.set_fill_color(30, 30, 60)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_y(8)
    pdf.cell(0, 10, "CryptoTreasury", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Rapport de risque crypto - Tresorerie d'entreprise", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_y(42)
    pdf.set_text_color(30, 30, 60)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"Entreprise : {nom_rapport}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    now = datetime.now().strftime("%d/%m/%Y a %H:%M")
    pdf.cell(0, 6, f"Date : {now}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    def section(titre):
        pdf.set_fill_color(240, 242, 255)
        pdf.set_text_color(30, 30, 60)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  {titre}", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(2)
    
    def ligne(label, valeur):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(90, 7, label)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 60)
        pdf.cell(0, 7, valeur, new_x="LMARGIN", new_y="NEXT")
    
    section("1. Exposition actuelle")
    ligne("Bitcoin :", f"{btc_rapport} BTC x {prix_btc:,.0f} EUR = {valeur_btc_r:,.0f} EUR")
    ligne("Ethereum :", f"{eth_rapport} ETH x {prix_eth:,.0f} EUR = {valeur_eth_r:,.0f} EUR")
    ligne("Valeur totale :", f"{valeur_totale_r:,.0f} EUR")
    pdf.ln(4)
    
    section("2. Mesures de risque (IFRS 9)")
    ligne("VaR 95% sur 1 jour :", f"-{var_95_r:,.0f} EUR")
    ligne("VaR 99% sur 1 jour :", f"-{var_99_r:,.0f} EUR")
    pdf.ln(4)
    
    section("3. Scenarios de stress (MiCA Art. 76)")
    ligne("Baisse -30% :", f"{valeur_totale_r*0.70:,.0f} EUR")
    ligne("Baisse -50% :", f"{valeur_totale_r*0.50:,.0f} EUR")
    ligne("Hausse +30% :", f"{valeur_totale_r*1.30:,.0f} EUR")
    pdf.ln(4)
    
    section("4. Conformite reglementaire")
    ligne("IFRS 9 :", "Actifs a la juste valeur (FVTPL)")
    ligne("MiCA Art. 76 :", "Stress tests effectues")
    pdf.ln(8)
    
    pdf.set_fill_color(30, 30, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 8, "  Genere par CryptoTreasury - Document confidentiel",
             new_x="LMARGIN", new_y="NEXT", fill=True)
    
    pdf_bytes = bytes(pdf.output())
    
    st.download_button(
        label="Telecharger le rapport PDF",
        data=pdf_bytes,
        file_name=f"rapport_{nom_rapport.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )
    st.success("Rapport genere avec succes !")
st.caption("CryptoTreasury — Donnees fournies par CoinGecko — Conforme IFRS 9 et MiCA")
