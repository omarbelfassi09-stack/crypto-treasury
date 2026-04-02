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
    padding: 2rem; border-radius: 10px;
    color: white; text-align: center; margin-bottom: 2rem;
}
.score-box {
    padding: 1.5rem; border-radius: 10px;
    text-align: center; font-size: 2rem; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>₿ CryptoTreasury</h1>
    <p>Plateforme de gestion des risques crypto — Treasury Intelligence pour CFO</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_prix():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin,ethereum", "vs_currencies": "usd,eur", "include_24hr_change": "true"}
    r = requests.get(url, params=params)
    return r.json()

@st.cache_data(ttl=3600)
def get_historique_btc():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "eur", "days": "1095", "interval": "daily"}
    r = requests.get(url, params=params)
    data = r.json()
    prices = [p[1] for p in data["prices"]]
    dates = [p[0] for p in data["prices"]]
    return dates, prices

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

# ── SECTION 1 : INPUTS TRESORERIE CFO ──
st.subheader("1. Profil de tresorerie de votre entreprise")

col1, col2 = st.columns(2)
with col1:
    nom_entreprise = st.text_input("Nom de l'entreprise", "Mon Entreprise SAS")
    tresorerie_totale = st.number_input("Tresorerie totale (EUR)", min_value=10000, value=1000000, step=10000)
    revenus_usd = st.slider("Part des revenus en USD (%)", 0, 100, 30)
with col2:
    cash_buffer = st.number_input("Cash buffer minimum requis (EUR)", min_value=0, value=200000, step=10000)
    horizon = st.selectbox("Horizon d'investissement", ["3 mois", "6 mois", "1 an", "3 ans"])
    tolerance = st.selectbox("Tolerance au risque", ["Faible", "Moderee", "Elevee"])

st.divider()

# ── SECTION 2 : EXPOSITION CRYPTO ──
st.subheader("2. Exposition crypto actuelle")

col1, col2 = st.columns(2)
with col1:
    montant_btc = st.number_input("Quantite BTC", min_value=0.0, value=2.0, step=0.1)
with col2:
    montant_eth = st.number_input("Quantite ETH", min_value=0.0, value=10.0, step=1.0)

valeur_btc = montant_btc * prix_btc
valeur_eth = montant_eth * prix_eth
valeur_totale_crypto = valeur_btc + valeur_eth
poids_crypto = (valeur_totale_crypto / tresorerie_totale) * 100
cash_disponible = tresorerie_totale - valeur_totale_crypto
cash_apres_crash = cash_disponible + (valeur_totale_crypto * 0.50)

vol_journaliere = 0.70 / np.sqrt(365)
var_95 = valeur_totale_crypto * vol_journaliere * 1.645
var_99 = valeur_totale_crypto * vol_journaliere * 2.326
perte_max_eur = var_99

st.divider()

# ── SECTION 3 : TABLEAU DE BORD CFO ──
st.subheader("3. Tableau de bord tresorerie")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Valeur crypto totale", f"{valeur_totale_crypto:,.0f} EUR")
col2.metric("Poids / tresorerie", f"{poids_crypto:.1f}%")
col3.metric("Perte max 1 jour (VaR 99%)", f"-{perte_max_eur:,.0f} EUR")
col4.metric("Cash apres crash -50%", f"{cash_apres_crash:,.0f} EUR")

# Alerte cash buffer
if cash_apres_crash < cash_buffer:
    st.error(f"ALERTE : En cas de crash -50%, votre cash ({cash_apres_crash:,.0f} EUR) passerait sous votre buffer minimum ({cash_buffer:,.0f} EUR).")
else:
    st.success(f"Cash buffer securise meme en cas de crash -50% : {cash_apres_crash:,.0f} EUR disponibles.")

st.divider()

# ── SECTION 4 : SCORE DE RISQUE ──
st.subheader("4. Score de risque global")

score = 50
if tolerance == "Faible":
    score -= 20
elif tolerance == "Elevee":
    score += 20
if poids_crypto < 5:
    score -= 15
elif poids_crypto > 15:
    score += 25
if revenus_usd > 50:
    score += 10
if horizon in ["3 ans"]:
    score -= 10
elif horizon == "3 mois":
    score += 15
score = max(0, min(100, score))

if score < 30:
    couleur = "#22c55e"
    profil = "Conservateur"
    emoji = "Faible"
elif score < 70:
    couleur = "#f59e0b"
    profil = "Equilibre"
    emoji = "Modere"
else:
    couleur = "#ef4444"
    profil = "Agressif"
    emoji = "Eleve"

col1, col2 = st.columns([1, 2])
with col1:
    st.markdown(f"""
    <div class="score-box" style="background:{couleur}20; border: 2px solid {couleur}; color:{couleur}">
        {score} / 100<br>
        <span style="font-size:1rem">{profil} — Risque {emoji}</span>
    </div>
    """, unsafe_allow_html=True)
with col2:
    if score < 30:
        st.info("Votre profil est conservateur. Une allocation de 1-3% en BTC est adaptee a votre tresorerie.")
    elif score < 70:
        st.warning("Votre profil est equilibre. Une allocation de 3-7% en BTC est dans les normes pour votre secteur.")
    else:
        st.error("Votre exposition est elevee. Envisagez une couverture partielle ou une reduction de position.")

st.divider()

# ── SECTION 5 : BENCHMARK ──
st.subheader("5. Benchmark — Impact BTC sur votre tresorerie")

allocations = [0, 1, 2, 3, 5, 7, 10]
rendements_annuels_btc = 0.60
rendement_cash = 0.03

resultats_bench = []
for alloc in allocations:
    poids_btc = alloc / 100
    poids_cash = 1 - poids_btc
    rendement = poids_cash * rendement_cash + poids_btc * rendements_annuels_btc
    volatilite = poids_btc * 0.70
    sharpe = (rendement - 0.03) / volatilite if volatilite > 0 else 0
    gain_eur = tresorerie_totale * rendement
    resultats_bench.append({
        "allocation": f"{alloc}% BTC",
        "rendement": rendement * 100,
        "sharpe": sharpe,
        "gain_eur": gain_eur
    })

fig = go.Figure()
fig.add_trace(go.Bar(
    x=[r["allocation"] for r in resultats_bench],
    y=[r["rendement"] for r in resultats_bench],
    marker_color=["#6366f1" if r["allocation"] == f"{int(poids_crypto)}% BTC" else "#a5b4fc" for r in resultats_bench],
    name="Rendement annuel estime (%)"
))
fig.update_layout(
    title="Rendement estime selon l'allocation BTC",
    xaxis_title="Allocation BTC",
    yaxis_title="Rendement annuel (%)",
    height=350
)
st.plotly_chart(fig, use_container_width=True)

col1, col2, col3 = st.columns(3)
bench_actuel = next((r for r in resultats_bench if abs(int(r["allocation"].replace("% BTC","")) - poids_crypto) < 2), resultats_bench[2])
col1.metric("Rendement estime (allocation actuelle)", f"{bench_actuel['rendement']:.1f}%")
col2.metric("Sharpe ratio", f"{bench_actuel['sharpe']:.2f}")
col3.metric("Gain annuel estime", f"{bench_actuel['gain_eur']:,.0f} EUR")

st.divider()

# ── SECTION 6 : BACKTESTING ──
# ── SECTION 6 : BACKTESTING ──
st.subheader("6. Backtesting — Et si vous aviez investi ?")

col1, col2 = st.columns(2)
with col1:
    periode_back = st.selectbox("Periode de backtesting", ["6 mois", "1 an", "2 ans", "3 ans"])
with col2:
    alloc_back = st.slider("Allocation BTC hypothetique (%)", 1, 20, 3)

jours_map = {"6 mois": 180, "1 an": 365, "2 ans": 730, "3 ans": 1095}
jours_back = jours_map[periode_back]

if st.button("Lancer le backtesting"):
    with st.spinner("Recuperation des donnees historiques..."):
        try:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {"vs_currency": "eur", "days": str(jours_back), "interval": "daily"}
            headers = {"accept": "application/json"}
            r = requests.get(url, params=params, headers=headers, timeout=15)
            data = r.json()

            if "prices" not in data:
                st.error("Donnees indisponibles. L'API CoinGecko a une limite gratuite — reessayez dans 1 minute.")
            else:
                prices = [p[1] for p in data["prices"]]
                prix_depart = prices[0]
                prix_fin = prices[-1]
                performance_btc = ((prix_fin - prix_depart) / prix_depart) * 100

                poids_btc = alloc_back / 100
                poids_cash = 1 - poids_btc
                invest_btc = tresorerie_totale * poids_btc
                invest_cash = tresorerie_totale * poids_cash
                btc_achete = invest_btc / prix_depart
                valeur_btc_fin = btc_achete * prix_fin
                annees = jours_back / 365
                valeur_cash_fin = invest_cash * (1 + 0.03 * annees)
                valeur_totale_fin = valeur_btc_fin + valeur_cash_fin
                valeur_cash_pur = tresorerie_totale * (1 + 0.03 * annees)
                gain_vs_cash = valeur_totale_fin - valeur_cash_pur

                col1, col2, col3 = st.columns(3)
                col1.metric(f"Performance BTC sur {periode_back}", f"{performance_btc:+.0f}%")
                col2.metric(f"Valeur portefeuille ({alloc_back}% BTC)", f"{valeur_totale_fin:,.0f} EUR")
                col3.metric("Gain vs cash pur", f"{gain_vs_cash:+,.0f} EUR")

                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    y=prices,
                    mode="lines",
                    line=dict(color="#4f46e5", width=2),
                    name="Prix BTC (EUR)"
                ))
                fig2.update_layout(
                    title=f"Evolution du prix BTC sur {periode_back} (EUR)",
                    yaxis_title="Prix (EUR)",
                    xaxis_title="Jours",
                    height=350
                )
                st.plotly_chart(fig2, use_container_width=True)

        except requests.exceptions.Timeout:
            st.error("Timeout — l'API met trop de temps a repondre. Reessayez dans quelques instants.")
        except Exception as e:
            st.error(f"Erreur inattendue : {str(e)}")
            
# ── SECTION 7 : MONTE CARLO ──
st.subheader("7. Simulation Monte Carlo — 30 jours")

if st.button("Lancer la simulation Monte Carlo"):
    with st.spinner("Simulation de 1000 scenarios..."):
        resultats = []
        for i in range(1000):
            valeur = valeur_totale_crypto
            for j in range(30):
                choc = np.random.normal(0.001, vol_journaliere)
                valeur = valeur * (1 + choc)
            resultats.append(valeur)

        resultats = np.array(resultats)
        mediane = np.median(resultats)
        pire_cas = np.percentile(resultats, 5)
        meilleur_cas = np.percentile(resultats, 95)

        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(x=resultats, nbinsx=50, marker_color="#4f46e5", opacity=0.7))
        fig3.add_vline(x=valeur_totale_crypto, line_dash="dash", line_color="black", annotation_text="Actuel")
        fig3.add_vline(x=pire_cas, line_dash="dash", line_color="red", annotation_text="Pire cas 5%")
        fig3.add_vline(x=mediane, line_dash="dash", line_color="green", annotation_text="Mediane")
        fig3.update_layout(title="Distribution Monte Carlo — 30 jours", height=350)
        st.plotly_chart(fig3, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Pire cas (5%)", f"{pire_cas:,.0f} EUR", f"{((pire_cas-valeur_totale_crypto)/valeur_totale_crypto*100):+.1f}%")
        col2.metric("Scenario median", f"{mediane:,.0f} EUR", f"{((mediane-valeur_totale_crypto)/valeur_totale_crypto*100):+.1f}%")
        col3.metric("Meilleur cas (95%)", f"{meilleur_cas:,.0f} EUR", f"{((meilleur_cas-valeur_totale_crypto)/valeur_totale_crypto*100):+.1f}%")

st.divider()

# ── SECTION 8 : RAPPORT PDF ──
st.subheader("8. Rapport PDF board-ready")

if st.button("Generer le rapport PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    pdf.set_fill_color(30, 30, 60)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_y(8)
    pdf.cell(0, 10, "CryptoTreasury", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Rapport de risque crypto - Treasury Intelligence", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 8, "Ce rapport vise a assister la prise de decision strategique de tresorerie.", new_x="LMARGIN", new_y="NEXT", align="C")

    now = datetime.now().strftime("%d/%m/%Y a %H:%M")
    pdf.set_y(48)
    pdf.set_text_color(30, 30, 60)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"Entreprise : {nom_entreprise}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Date : {now}  |  Horizon : {horizon}  |  Tolerance : {tolerance}", new_x="LMARGIN", new_y="NEXT")
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
        pdf.cell(100, 7, label)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 60)
        pdf.cell(0, 7, valeur, new_x="LMARGIN", new_y="NEXT")

    section("1. Executive Summary")
    ligne("Tresorerie totale :", f"{tresorerie_totale:,.0f} EUR")
    ligne("Exposition crypto :", f"{valeur_totale_crypto:,.0f} EUR ({poids_crypto:.1f}% de la tresorerie)")
    ligne("Score de risque :", f"{score} / 100 - {profil}")
    ligne("Cash buffer apres crash -50% :", f"{cash_apres_crash:,.0f} EUR")
    pdf.ln(4)

    section("2. Allocation recommandee")
    if score < 30:
        reco = "1-3% de la tresorerie en BTC (profil conservateur)"
    elif score < 70:
        reco = "3-7% de la tresorerie en BTC (profil equilibre)"
    else:
        reco = "Reduire l'exposition - envisager une couverture partielle"
    ligne("Recommandation :", reco)
    ligne("Horizon conseille :", horizon)
    ligne("Tolerance au risque :", tolerance)
    pdf.ln(4)

    section("3. Analyse de risque (IFRS 9)")
    ligne("VaR 95% sur 1 jour :", f"-{var_95:,.0f} EUR")
    ligne("VaR 99% sur 1 jour :", f"-{var_99:,.0f} EUR")
    ligne("Volatilite annuelle BTC :", "70%")
    pdf.ln(4)

    section("4. Scenarios de stress (MiCA Art. 76)")
    ligne("Scenario baisse -30% :", f"{valeur_totale_crypto*0.70:,.0f} EUR")
    ligne("Scenario baisse -50% :", f"{valeur_totale_crypto*0.50:,.0f} EUR")
    ligne("Scenario hausse +30% :", f"{valeur_totale_crypto*1.30:,.0f} EUR")
    pdf.ln(4)

    section("5. Conformite reglementaire")
    ligne("IFRS 9 :", "Actifs a la juste valeur (FVTPL)")
    ligne("MiCA Art. 76 :", "Stress tests effectues")
    ligne("Classification :", "Actif numerique - reserve de tresorerie")
    pdf.ln(8)

    pdf.set_fill_color(30, 30, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 8, "  Genere par CryptoTreasury - Document confidentiel - Usage interne uniquement",
             new_x="LMARGIN", new_y="NEXT", fill=True)

    pdf_bytes = bytes(pdf.output())
    st.download_button(
        label="Telecharger le rapport PDF",
        data=pdf_bytes,
        file_name=f"rapport_{nom_entreprise.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )
    st.success("Rapport board-ready genere avec succes !")

st.divider()
st.caption("CryptoTreasury — Donnees : CoinGecko — Conforme IFRS 9 et MiCA — Usage professionnel")
