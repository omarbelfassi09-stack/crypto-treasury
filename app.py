import streamlit as st
import numpy as np
import requests
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import anthropic
from supabase import create_client

st.set_page_config(page_title="CryptoTreasury", page_icon="₿", layout="wide")

# ── CONNEXION SUPABASE ──
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ── STYLES ──
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
.auth-box {
    max-width: 420px; margin: 3rem auto;
    background: white; border: 1px solid #eee;
    border-radius: 12px; padding: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ── GESTION SESSION ──
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# ── FONCTIONS AUTH ──
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        return True, None
    except Exception as e:
        return False, str(e)

def register(email, password, entreprise):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({
                "id": res.user.id,
                "email": email,
                "entreprise": entreprise,
                "plan": "free"
            }).execute()
            st.session_state.user = res.user
        return True, None
    except Exception as e:
        return False, str(e)

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# ── PAGE AUTH ──
if st.session_state.user is None:
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="font-size:2rem; color:#1e1e3c;">₿ CryptoTreasury</h1>
        <p style="color:#666;">Plateforme de gestion des risques crypto pour entreprises</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.radio("", ["Se connecter", "Creer un compte"], horizontal=True, label_visibility="collapsed")

        if mode == "Se connecter":
            st.markdown("#### Connexion")
            email = st.text_input("Email professionnel")
            password = st.text_input("Mot de passe", type="password")

            if st.button("Se connecter", use_container_width=True):
                if email and password:
                    ok, err = login(email, password)
                    if ok:
                        st.success("Connexion reussie !")
                        st.rerun()
                    else:
                        st.error("Email ou mot de passe incorrect.")
                else:
                    st.warning("Veuillez remplir tous les champs.")

            st.divider()
            st.markdown("""
            <div style="text-align:center;">
                <a href="https://omarbelfassi09-stack.github.io/crypto-treasury/" 
                   style="color:#666; font-size:0.85rem;">
                   Retour a la page d'accueil
                </a>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("#### Creer un compte gratuit")
            entreprise = st.text_input("Nom de votre entreprise")
            email = st.text_input("Email professionnel")
            password = st.text_input("Mot de passe", type="password")
            password2 = st.text_input("Confirmer le mot de passe", type="password")

            if st.button("Creer mon compte", use_container_width=True):
                if not all([entreprise, email, password, password2]):
                    st.warning("Veuillez remplir tous les champs.")
                elif password != password2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caracteres.")
                else:
                    ok, err = register(email, password, entreprise)
                    if ok:
                        st.success("Compte cree avec succes ! Verifiez votre email pour confirmer.")
                        st.rerun()
                    else:
                        st.error(f"Erreur : {err}")

# ── APPLICATION PRINCIPALE ──
else:
    # Header avec logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
        <div class="main-header">
            <h1>₿ CryptoTreasury</h1>
            <p>Plateforme de gestion des risques crypto — Treasury Intelligence pour CFO</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        user_email = st.session_state.user.email
        st.markdown(f"<small style='color:#666'>{user_email}</small>", unsafe_allow_html=True)
        if st.button("Deconnexion"):
            logout()

    # ── DONNÉES MARCHÉ ──
    @st.cache_data(ttl=60)
    def get_prix():
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum", "vs_currencies": "usd,eur", "include_24hr_change": "true"}
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

    # ── SECTION 1 : INPUTS TRESORERIE ──
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

    st.divider()

    # ── SECTION 3 : TABLEAU DE BORD ──
    st.subheader("3. Tableau de bord tresorerie")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valeur crypto totale", f"{valeur_totale_crypto:,.0f} EUR")
    col2.metric("Poids / tresorerie", f"{poids_crypto:.1f}%")
    col3.metric("VaR 99% (1 jour)", f"-{var_99:,.0f} EUR")
    col4.metric("Cash apres crash -50%", f"{cash_apres_crash:,.0f} EUR")

    if cash_apres_crash < cash_buffer:
        st.error(f"ALERTE : Cash apres crash ({cash_apres_crash:,.0f} EUR) sous le buffer minimum ({cash_buffer:,.0f} EUR).")
    else:
        st.success(f"Cash buffer securise apres crash -50% : {cash_apres_crash:,.0f} EUR.")

    st.divider()

    # ── SECTION 4 : SCORE ──
    st.subheader("4. Score de risque global")
    score = 50
    if tolerance == "Faible": score -= 20
    elif tolerance == "Elevee": score += 20
    if poids_crypto < 5: score -= 15
    elif poids_crypto > 15: score += 25
    if revenus_usd > 50: score += 10
    if horizon == "3 ans": score -= 10
    elif horizon == "3 mois": score += 15
    score = max(0, min(100, score))

    if score < 30: couleur, profil = "#22c55e", "Conservateur"
    elif score < 70: couleur, profil = "#f59e0b", "Equilibre"
    else: couleur, profil = "#ef4444", "Agressif"

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div class="score-box" style="background:{couleur}20; border:2px solid {couleur}; color:{couleur}">
            {score} / 100<br><span style="font-size:1rem">{profil}</span>
        </div>""", unsafe_allow_html=True)
    with col2:
        if score < 30: st.info("Profil conservateur. Allocation recommandee : 1-3% en BTC.")
        elif score < 70: st.warning("Profil equilibre. Allocation recommandee : 3-7% en BTC.")
        else: st.error("Exposition elevee. Envisagez une couverture partielle.")

    st.divider()

    # ── SECTION 5 : BENCHMARK ──
    st.subheader("5. Benchmark — Impact BTC sur votre tresorerie")
    allocations = [0, 1, 2, 3, 5, 7, 10]
    resultats_bench = []
    for alloc in allocations:
        poids_btc = alloc / 100
        rendement = (1 - poids_btc) * 0.03 + poids_btc * 0.60
        volatilite = poids_btc * 0.70
        sharpe = (rendement - 0.03) / volatilite if volatilite > 0 else 0
        resultats_bench.append({"allocation": f"{alloc}% BTC", "rendement": rendement * 100, "sharpe": sharpe, "gain_eur": tresorerie_totale * rendement})

    fig = go.Figure()
    fig.add_trace(go.Bar(x=[r["allocation"] for r in resultats_bench], y=[r["rendement"] for r in resultats_bench], marker_color="#4f46e5"))
    fig.update_layout(title="Rendement estime selon l'allocation BTC", xaxis_title="Allocation BTC", yaxis_title="Rendement annuel (%)", height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── SECTION 6 : BACKTESTING ──
    st.subheader("6. Backtesting — Et si vous aviez investi ?")
    col1, col2 = st.columns(2)
    with col1:
        periode_back = st.selectbox("Periode", ["6 mois", "1 an", "2 ans", "3 ans"])
    with col2:
        alloc_back = st.slider("Allocation BTC hypothetique (%)", 1, 20, 3)

    jours_map = {"6 mois": 180, "1 an": 365, "2 ans": 730, "3 ans": 1095}
    jours_back = jours_map[periode_back]

    if st.button("Lancer le backtesting"):
        with st.spinner("Recuperation des donnees historiques..."):
            try:
                url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
                params = {"vs_currency": "eur", "days": str(jours_back), "interval": "daily"}
                r = requests.get(url, params=params, timeout=15)
                data = r.json()
                if "prices" not in data:
                    st.error("Donnees indisponibles. Reessayez dans 1 minute.")
                else:
                    prices = [p[1] for p in data["prices"]]
                    perf = ((prices[-1] - prices[0]) / prices[0]) * 100
                    btc_achete = (tresorerie_totale * alloc_back / 100) / prices[0]
                    valeur_fin = btc_achete * prices[-1] + (tresorerie_totale * (1 - alloc_back/100)) * (1 + 0.03 * jours_back/365)
                    gain = valeur_fin - tresorerie_totale * (1 + 0.03 * jours_back/365)
                    col1, col2, col3 = st.columns(3)
                    col1.metric(f"Performance BTC", f"{perf:+.0f}%")
                    col2.metric("Valeur portefeuille", f"{valeur_fin:,.0f} EUR")
                    col3.metric("Gain vs cash pur", f"{gain:+,.0f} EUR")
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(y=prices, mode="lines", line=dict(color="#4f46e5", width=2)))
                    fig2.update_layout(title=f"Prix BTC sur {periode_back}", height=300)
                    st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

    st.divider()

    # ── SECTION 7 : MONTE CARLO ──
    st.subheader("7. Simulation Monte Carlo — 30 jours")
    if st.button("Lancer la simulation Monte Carlo"):
        with st.spinner("Simulation de 1000 scenarios..."):
            resultats = np.array([
                valeur_totale_crypto * np.prod(1 + np.random.normal(0.001, vol_journaliere, 30))
                for _ in range(1000)
            ])
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
            col2.metric("Median", f"{mediane:,.0f} EUR", f"{((mediane-valeur_totale_crypto)/valeur_totale_crypto*100):+.1f}%")
            col3.metric("Meilleur cas (95%)", f"{meilleur_cas:,.0f} EUR", f"{((meilleur_cas-valeur_totale_crypto)/valeur_totale_crypto*100):+.1f}%")

    st.divider()

    # ── SECTION 8 : ALERTES ──
    st.subheader("8. Alertes et seuils personnalises")
    col1, col2 = st.columns(2)
    with col1:
        seuil_perte = st.number_input("Perte maximale acceptable (EUR)", min_value=0, value=20000, step=1000)
        seuil_poids = st.slider("Poids crypto maximum (%)", 1, 30, 10)
    with col2:
        seuil_var = st.number_input("VaR journaliere maximale (EUR)", min_value=0, value=10000, step=500)
        seuil_crash = st.slider("Seuil d'alerte crash (%)", 10, 60, 30)

    alerte1 = var_99 > seuil_var
    alerte2 = poids_crypto > seuil_poids
    alerte3 = (valeur_totale_crypto * seuil_crash/100) > seuil_perte
    alerte4 = cash_apres_crash < cash_buffer

    col1, col2 = st.columns(2)
    with col1:
        if alerte1: st.error(f"VaR ({var_99:,.0f} EUR) depasse votre seuil ({seuil_var:,.0f} EUR)")
        else: st.success(f"VaR dans les limites")
        if alerte2: st.error(f"Poids crypto ({poids_crypto:.1f}%) depasse votre seuil ({seuil_poids}%)")
        else: st.success(f"Poids crypto dans les limites")
    with col2:
        if alerte3: st.error(f"Perte crash -{seuil_crash}% depasse votre tolerance")
        else: st.success(f"Perte crash dans votre tolerance")
        if alerte4: st.error(f"Cash buffer insuffisant apres crash -50%")
        else: st.success(f"Cash buffer securise")

    st.divider()

    # ── SECTION 9 : HEDGING ──
    st.subheader("9. Module hedging et couverture")
    col1, col2 = st.columns(2)
    with col1:
        pct_hedge = st.slider("Pourcentage de couverture (%)", 0, 100, 50)
        cout_hedge = st.slider("Cout annuel de la couverture (%)", 1, 10, 3)
    with col2:
        valeur_non_couverte = valeur_totale_crypto * (1 - pct_hedge/100)
        var_99_hedge = valeur_non_couverte * vol_journaliere * 2.326
        reduction_var = ((var_99 - var_99_hedge) / var_99) * 100 if var_99 > 0 else 0
        cout_eur = valeur_totale_crypto * (pct_hedge/100) * (cout_hedge/100)
        st.metric("VaR 99% apres couverture", f"-{var_99_hedge:,.0f} EUR", f"{-reduction_var:.0f}%")
        st.metric("Cout annuel", f"{cout_eur:,.0f} EUR")

    fig_h = go.Figure()
    fig_h.add_trace(go.Bar(name="Sans couverture", x=["VaR 95%", "VaR 99%"], y=[var_95, var_99], marker_color="#ef4444"))
    fig_h.add_trace(go.Bar(name=f"Avec couverture {pct_hedge}%", x=["VaR 95%", "VaR 99%"], y=[valeur_non_couverte*vol_journaliere*1.645, var_99_hedge], marker_color="#22c55e"))
    fig_h.update_layout(barmode="group", height=300, title="Impact couverture sur VaR")
    st.plotly_chart(fig_h, use_container_width=True)

    st.divider()

    # ── SECTION 10 : RECOMMANDATION ──
    st.subheader("10. Recommandation strategique")
    tresorerie_investissable = tresorerie_totale - cash_buffer
    if tolerance == "Faible": alloc_min, alloc_max = 1, 3
    elif tolerance == "Moderee": alloc_min, alloc_max = 3, 7
    else: alloc_min, alloc_max = 7, 15
    if horizon == "3 mois": alloc_max = min(alloc_max, 3)
    if revenus_usd > 50: alloc_max += 2
    alloc_recommandee = (alloc_min + alloc_max) / 2
    montant_recommande = tresorerie_investissable * (alloc_recommandee / 100)
    ecart = montant_recommande - valeur_totale_crypto

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e1e3c,#2d2d6b);padding:2rem;border-radius:10px;color:white;margin-bottom:1rem;">
        <h3 style="color:white;margin-bottom:1rem;">Recommandation personnalisee</h3>
        <p style="font-size:1.1rem;">Profil <strong>{tolerance}</strong> | Horizon <strong>{horizon}</strong> | Allocation recommandee : <strong>{alloc_min}-{alloc_max}% en BTC</strong></p>
        <p style="opacity:0.85;">Montant optimal : <strong>{montant_recommande:,.0f} EUR</strong> ({montant_recommande/prix_btc:.3f} BTC)</p>
    </div>""", unsafe_allow_html=True)

    if ecart > 0: st.warning(f"Vous pourriez ajouter {ecart:,.0f} EUR de BTC pour atteindre l'allocation optimale.")
    elif ecart < 0: st.warning(f"Votre exposition depasse l'optimal de {abs(ecart):,.0f} EUR.")
    else: st.success("Position optimale.")

    st.divider()

    # ── SECTION 11 : ANALYSE IA ──
    st.subheader("11. Analyse IA — Powered by Claude")
    if st.button("Generer l'analyse IA"):
        with st.spinner("Claude analyse votre portefeuille..."):
            try:
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                prompt = f"""Tu es un expert en gestion de tresorerie d'entreprise et crypto-actifs, specialise IFRS 9 et MiCA.

Profil entreprise :
- Tresorerie : {tresorerie_totale:,.0f} EUR | Cash buffer : {cash_buffer:,.0f} EUR
- Revenus USD : {revenus_usd}% | Horizon : {horizon} | Tolerance : {tolerance}
- BTC : {montant_btc} ({valeur_btc:,.0f} EUR) | ETH : {montant_eth} ({valeur_eth:,.0f} EUR)
- Poids crypto : {poids_crypto:.1f}% | Score risque : {score}/100 ({profil})
- VaR 99% : {var_99:,.0f} EUR | Cash apres crash -50% : {cash_apres_crash:,.0f} EUR
- BTC : {prix_btc:,.0f} EUR ({var_btc_24h:+.2f}%/24h)

Genere une analyse strategique en francais avec :
1. Evaluation globale (2-3 phrases)
2. Les 3 points de vigilance
3. Recommandation d'allocation chiffree
4. Actions concretes dans les 30 prochains jours
5. Verdict final en une phrase

Ton : CFO s'adressant a son conseil d'administration."""

                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                analyse = message.content[0].text
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1e1e3c,#2d2d6b);padding:2rem;border-radius:10px;color:white;">
                    <h3 style="color:white;margin-bottom:1rem;">Analyse IA — {nom_entreprise}</h3>
                    <div style="line-height:1.8;">{analyse.replace(chr(10), '<br>')}</div>
                </div>""", unsafe_allow_html=True)
                st.success("Analyse generee avec succes — powered by Claude AI")
            except Exception as e:
                st.error(f"Erreur API : {str(e)}")

    st.divider()

    # ── SECTION 12 : RAPPORT PDF ──
    st.subheader("12. Rapport PDF board-ready")
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
        pdf.set_y(48)
        pdf.set_text_color(30, 30, 60)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, f"Entreprise : {nom_entreprise}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"Date : {datetime.now().strftime('%d/%m/%Y a %H:%M')} | Horizon : {horizon} | Tolerance : {tolerance}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        def section(t):
            pdf.set_fill_color(240, 242, 255)
            pdf.set_text_color(30, 30, 60)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, f"  {t}", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(2)

        def ligne(l, v):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(100, 7, l)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 60)
            pdf.cell(0, 7, v, new_x="LMARGIN", new_y="NEXT")

        section("1. Executive Summary")
        ligne("Tresorerie totale :", f"{tresorerie_totale:,.0f} EUR")
        ligne("Exposition crypto :", f"{valeur_totale_crypto:,.0f} EUR ({poids_crypto:.1f}%)")
        ligne("Score de risque :", f"{score}/100 - {profil}")
        ligne("Cash apres crash -50% :", f"{cash_apres_crash:,.0f} EUR")
        pdf.ln(4)

        section("2. Allocation recommandee")
        if score < 30: reco = "1-3% de la tresorerie en BTC"
        elif score < 70: reco = "3-7% de la tresorerie en BTC"
        else: reco = "Reduire l'exposition - envisager couverture"
        ligne("Recommandation :", reco)
        ligne("Montant optimal :", f"{montant_recommande:,.0f} EUR")
        pdf.ln(4)

        section("3. Mesures de risque (IFRS 9)")
        ligne("VaR 95% (1 jour) :", f"-{var_95:,.0f} EUR")
        ligne("VaR 99% (1 jour) :", f"-{var_99:,.0f} EUR")
        pdf.ln(4)

        section("4. Scenarios de stress (MiCA Art. 76)")
        ligne("Baisse -30% :", f"{valeur_totale_crypto*0.70:,.0f} EUR")
        ligne("Baisse -50% :", f"{valeur_totale_crypto*0.50:,.0f} EUR")
        ligne("Hausse +30% :", f"{valeur_totale_crypto*1.30:,.0f} EUR")
        pdf.ln(4)

        section("5. Conformite reglementaire")
        ligne("IFRS 9 :", "Actifs a la juste valeur (FVTPL)")
        ligne("MiCA Art. 76 :", "Stress tests effectues")
        pdf.ln(8)

        pdf.set_fill_color(30, 30, 60)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 8, "  Genere par CryptoTreasury - Document confidentiel", new_x="LMARGIN", new_y="NEXT", fill=True)

        pdf_bytes = bytes(pdf.output())
        st.download_button(
            label="Telecharger le rapport PDF",
            data=pdf_bytes,
            file_name=f"rapport_{nom_entreprise.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
        st.success("Rapport genere avec succes !")

    st.divider()
    st.caption("CryptoTreasury — Donnees : CoinGecko — Conforme IFRS 9 et MiCA — Usage professionnel")
