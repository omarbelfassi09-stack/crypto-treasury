import streamlit as st
import numpy as np
import requests
import plotly.graph_objects as go
import anthropic
from fpdf import FPDF
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="CryptoTreasury", page_icon="₿", layout="wide")

# ── CONNEXION SUPABASE ──
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ── GESTION SESSION ──
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "app"

# ── FONCTIONS AUTH ──
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.session_state.page = "app"
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
                "plan": "starter"
            }).execute()
            st.session_state.user = res.user
            st.session_state.page = "app"
        return True, None
    except Exception as e:
        return False, str(e)

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.page = "app"
    st.rerun()

# ════════════════════════════════════════
# ── PAGE AUTH (si non connecté) ──
# ════════════════════════════════════════
if st.session_state.user is None:

    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e1e3c, #2d2d6b);
        padding: 2rem; border-radius: 10px;
        color: white; text-align: center; margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1>₿ CryptoTreasury</h1>
        <p>Plateforme de gestion des risques crypto — Treasury Intelligence pour CFO</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.get("auth_plan"):
            plan = st.session_state.auth_plan
            if plan == "pro":
                st.info("Plan Pro selectionne — 299 EUR / mois")
            elif plan == "enterprise":
                st.info("Plan Enterprise — Notre equipe vous contactera")

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
                        st.success("Compte cree ! Verifiez votre email pour confirmer.")
                        st.rerun()
                    else:
                        st.error(f"Erreur : {err}")

        st.divider()
        st.markdown("""
        <div style="text-align:center;">
            <p style="color:#888; font-size:0.85rem;">
            Starter gratuit — Plan Professional a partir de 99 EUR/mois<br>
            Conforme IFRS 9 et MiCA
            </p>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════
# ── APPLICATION PRINCIPALE ──
# ════════════════════════════════════════
else:

    # ── LECTURE DU PLAN UTILISATEUR ──
    if True:
        try:
            profil_data = supabase.table("profiles")\
                .select("plan, entreprise")\
                .eq("id", st.session_state.user.id)\
                .execute()
            if profil_data.data:
                st.session_state.plan_utilisateur = profil_data.data[0]["plan"]
                st.session_state.entreprise_utilisateur = profil_data.data[0].get("entreprise", "")
            else:
                st.session_state.plan_utilisateur = "starter"
        except:
            st.session_state.plan_utilisateur = "starter"

    plan = st.session_state.plan_utilisateur

    def bloc_pro(nom_fonctionnalite, plan_requis="professional"):
        plans_ordre = ["starter", "professional", "corporate", "enterprise"]
        plan_actuel_index = plans_ordre.index(plan) if plan in plans_ordre else 0
        plan_requis_index = plans_ordre.index(plan_requis) if plan_requis in plans_ordre else 1
        if plan_actuel_index < plan_requis_index:
            st.markdown(f"""
            <div style="background: #f8f9ff; border: 1px dashed #1e1e3c; border-radius: 10px;
                 padding: 1.5rem; text-align: center; margin: 1rem 0;">
                <p style="color: #1e1e3c; font-weight: 600; margin-bottom: 0.5rem;">
                    Fonctionnalite reservee au plan {plan_requis.capitalize()}
                </p>
                <p style="color: #666; font-size: 0.9rem; margin-bottom: 1rem;">
                    Passez au plan superieur pour acceder a {nom_fonctionnalite}.
                </p>
                <a href="mailto:contact@cryptotreasury.com"
                   style="background: #1e1e3c; color: white; padding: 0.6rem 1.5rem;
                   border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 0.9rem;">
                   Passer au plan {plan_requis.capitalize()}
                </a>
            </div>
            """, unsafe_allow_html=True)
            return False
        return True

    # ── NAVBAR ──
    col1, col2 = st.columns([5, 1])
    with col1:
        plan_couleurs = {
            "starter": "#22c55e",
            "professional": "#3b82f6",
            "corporate": "#8b5cf6",
            "enterprise": "#f7931a"
        }
        couleur_plan = plan_couleurs.get(plan, "#22c55e")
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:1rem; padding:0.5rem 0;">
            <span style="font-size:1.4rem; font-weight:700; color:#1e1e3c;">₿ CryptoTreasury</span>
            <span style="background:{couleur_plan}20; color:{couleur_plan}; font-size:0.75rem;
                  font-weight:600; padding:3px 10px; border-radius:20px; border:1px solid {couleur_plan}40;">
                {plan.capitalize()}
            </span>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<small style='color:#888'>{st.session_state.user.email}</small>", unsafe_allow_html=True)
        if st.button("Deconnexion"):
            logout()

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
    st.subheader("6. Backtesting — Et si vous aviez investi ?")
    if bloc_pro("le backtesting historique", "professional"):
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
                            y=prices, mode="lines",
                            line=dict(color="#4f46e5", width=2),
                            name="Prix BTC (EUR)"
                        ))
                        fig2.update_layout(
                            title=f"Evolution du prix BTC sur {periode_back} (EUR)",
                            yaxis_title="Prix (EUR)", xaxis_title="Jours", height=350
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                except requests.exceptions.Timeout:
                    st.error("Timeout — reessayez dans quelques instants.")
                except Exception as e:
                    st.error(f"Erreur inattendue : {str(e)}")
    st.divider()

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
        pdf.cell(0, 8, "  Genere par CryptoTreasury - Document confidentiel - Usage interne uniquement", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf_bytes = bytes(pdf.output())
        st.download_button(
            label="Telecharger le rapport PDF",
            data=pdf_bytes,
            file_name=f"rapport_{nom_entreprise.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
        st.success("Rapport board-ready genere avec succes !")
        try:
            supabase.table("rapports").insert({
                "user_id": st.session_state.user.id,
                "entreprise": nom_entreprise,
                "tresorerie_totale": tresorerie_totale,
                "valeur_crypto": float(valeur_totale_crypto),
                "poids_crypto": float(poids_crypto),
                "var_99": float(var_99),
                "score_risque": score,
                "profil": profil
            }).execute()
        except Exception as e:
            pass

    st.divider()

    # ── SECTION 9 : ALERTES PERSONNALISEES ──
    st.subheader("9. Alertes et seuils personnalises")
    if bloc_pro("les alertes personnalisees", "professional"):
        col1, col2 = st.columns(2)
        with col1:
            seuil_perte = st.number_input("Perte maximale acceptable (EUR)", min_value=0, value=20000, step=1000)
            seuil_poids = st.slider("Poids crypto maximum acceptable (%)", 1, 30, 10)
            email_alertes = st.text_input("Email pour recevoir les alertes", value=st.session_state.user.email)
        with col2:
            seuil_var = st.number_input("VaR journaliere maximale acceptable (EUR)", min_value=0, value=10000, step=500)
            seuil_crash = st.slider("Seuil d'alerte crash (%)", 10, 60, 30)
            seuil_variation_btc = st.slider("Alerte variation BTC 24h (%)", 5, 30, 10)

        alerte1 = var_99 > seuil_var
        alerte2 = poids_crypto > seuil_poids
        alerte3 = (valeur_totale_crypto * (seuil_crash/100)) > seuil_perte
        alerte4 = cash_apres_crash < cash_buffer
        alerte5 = abs(var_btc_24h) > seuil_variation_btc
        alerte6 = var_btc_24h < -20

        st.markdown("##### Etat de vos alertes")
        col1, col2 = st.columns(2)
        with col1:
            if alerte1: st.error(f"VaR ({var_99:,.0f} EUR) depasse votre seuil ({seuil_var:,.0f} EUR)")
            else: st.success("VaR dans les limites acceptables")
            if alerte2: st.error(f"Poids crypto ({poids_crypto:.1f}%) depasse votre seuil ({seuil_poids}%)")
            else: st.success("Poids crypto dans les limites")
            if alerte5: st.warning(f"BTC a varie de {var_btc_24h:+.2f}% en 24h — seuil : {seuil_variation_btc}%")
            else: st.success(f"Variation BTC 24h normale : {var_btc_24h:+.2f}%")
        with col2:
            if alerte3: st.error(f"Perte crash -{seuil_crash}% depasse votre tolerance")
            else: st.success("Perte crash dans votre tolerance")
            if alerte4: st.error("Cash buffer insuffisant apres crash -50%")
            else: st.success("Cash buffer securise")
            if alerte6: st.error(f"CRASH DETECTE : BTC en baisse de {var_btc_24h:.2f}% en 24h")
            else: st.success("Pas de crash detecte")

        nb_alertes = sum([alerte1, alerte2, alerte3, alerte4, alerte5, alerte6])
        if nb_alertes == 0:
            st.info("Aucune alerte active — votre portefeuille respecte tous vos seuils.")
        elif nb_alertes <= 2:
            st.warning(f"{nb_alertes} alerte(s) active(s) — revoyez votre exposition.")
        else:
            st.error(f"{nb_alertes} alertes actives — action immediate recommandee.")

        def envoyer_alertes_email(email, alertes_actives):
            try:
                import resend
                resend.api_key = st.secrets["RESEND_API_KEY"]
                contenu_alertes = ""
                for alerte in alertes_actives:
                    contenu_alertes += f"<li style='margin-bottom:8px;'>{alerte}</li>"
                html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #1e1e3c, #2d2d6b); padding: 2rem; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 1.5rem;">₿ CryptoTreasury</h1>
                        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0;">Alerte de risque detectee</p>
                    </div>
                    <div style="background: white; padding: 2rem; border: 1px solid #eee;">
                        <h2 style="color: #1e1e3c; font-size: 1.1rem;">Bonjour,</h2>
                        <p style="color: #444;">Les alertes suivantes ont ete detectees sur votre portefeuille crypto :</p>
                        <ul style="color: #444; background: #fff8f8; border-left: 4px solid #ef4444; padding: 1rem 1rem 1rem 2rem; border-radius: 4px;">
                            {contenu_alertes}
                        </ul>
                        <div style="background: #f8f9ff; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;">
                            <p style="color: #444; margin: 0; font-size: 0.9rem;"><strong>Portefeuille actuel :</strong></p>
                            <p style="color: #444; margin: 0.3rem 0; font-size: 0.9rem;">BTC : {montant_btc} ({valeur_btc:,.0f} EUR)</p>
                            <p style="color: #444; margin: 0.3rem 0; font-size: 0.9rem;">ETH : {montant_eth} ({valeur_eth:,.0f} EUR)</p>
                            <p style="color: #444; margin: 0.3rem 0; font-size: 0.9rem;">Valeur totale : {valeur_totale_crypto:,.0f} EUR</p>
                            <p style="color: #444; margin: 0.3rem 0; font-size: 0.9rem;">VaR 99% : -{var_99:,.0f} EUR</p>
                        </div>
                        <div style="text-align: center; margin-top: 1.5rem;">
                            <a href="https://crypto-treasury-uz62zhahjwgyypukzemdng.streamlit.app/"
                               style="background: #1e1e3c; color: white; padding: 0.8rem 2rem; border-radius: 8px; text-decoration: none; font-weight: 600;">
                                Voir mon tableau de bord
                            </a>
                        </div>
                    </div>
                    <div style="background: #f8f9ff; padding: 1rem; border-radius: 0 0 10px 10px; text-align: center;">
                        <p style="color: #888; font-size: 0.8rem; margin: 0;">
                            CryptoTreasury — Conforme IFRS 9 et MiCA<br>
                            Ce message est genere automatiquement — ne pas repondre
                        </p>
                    </div>
                </div>
                """
                resend.Emails.send({
                    "from": "CryptoTreasury <onboarding@resend.dev>",
                    "to": email,
                    "subject": f"[CryptoTreasury] {len(alertes_actives)} alerte(s) detectee(s) sur votre portefeuille",
                    "html": html
                })
                return True
            except Exception as e:
                st.error(f"Erreur envoi email : {str(e)}")
                return False

        if nb_alertes > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.warning(f"{nb_alertes} alerte(s) active(s) — voulez-vous recevoir un email ?")
            with col2:
                if st.button("Envoyer l'alerte par email"):
                    alertes_actives = []
                    if alerte1: alertes_actives.append(f"VaR journaliere ({var_99:,.0f} EUR) depasse votre seuil ({seuil_var:,.0f} EUR)")
                    if alerte2: alertes_actives.append(f"Poids crypto ({poids_crypto:.1f}%) depasse votre seuil maximum ({seuil_poids}%)")
                    if alerte3: alertes_actives.append(f"Perte en cas de crash -{seuil_crash}% depasse votre tolerance")
                    if alerte4: alertes_actives.append("Cash buffer insuffisant apres un crash de -50%")
                    if alerte5: alertes_actives.append(f"BTC a varie de {var_btc_24h:+.2f}% en 24h — seuil fixe : {seuil_variation_btc}%")
                    if alerte6: alertes_actives.append(f"CRASH DETECTE : BTC en baisse de {var_btc_24h:.2f}% en 24h")
                    if envoyer_alertes_email(email_alertes, alertes_actives):
                        st.success(f"Alerte envoyee avec succes a {email_alertes}")
    st.divider()

    # ── SECTION 10 : HEDGING ──
    st.subheader("10. Module hedging et couverture")
    st.markdown("Simulez l'impact d'une couverture partielle via futures sur votre risque.")
    col1, col2 = st.columns(2)
    with col1:
        pct_hedge = st.slider("Pourcentage de couverture (%)", 0, 100, 50)
        cout_hedge_annuel = st.slider("Cout annuel de la couverture (%)", 1, 10, 3)
    with col2:
        st.markdown("##### Impact de la couverture")
        valeur_couverte = valeur_totale_crypto * (pct_hedge / 100)
        valeur_non_couverte = valeur_totale_crypto * (1 - pct_hedge / 100)
        var_95_hedge = valeur_non_couverte * vol_journaliere * 1.645
        var_99_hedge = valeur_non_couverte * vol_journaliere * 2.326
        reduction_var = ((var_99 - var_99_hedge) / var_99) * 100
        cout_annuel_eur = valeur_couverte * (cout_hedge_annuel / 100)
        st.metric("VaR 99% apres couverture", f"-{var_99_hedge:,.0f} EUR", f"{-reduction_var:.0f}% vs sans couverture")
        st.metric("Cout annuel de la couverture", f"{cout_annuel_eur:,.0f} EUR")
        st.metric("Valeur couverte", f"{valeur_couverte:,.0f} EUR")

    fig_hedge = go.Figure()
    fig_hedge.add_trace(go.Bar(name="Sans couverture", x=["VaR 95%", "VaR 99%"], y=[var_95, var_99], marker_color="#ef4444"))
    fig_hedge.add_trace(go.Bar(name=f"Avec couverture {pct_hedge}%", x=["VaR 95%", "VaR 99%"], y=[var_95_hedge, var_99_hedge], marker_color="#22c55e"))
    fig_hedge.update_layout(title="Impact de la couverture sur le risque (EUR)", barmode="group", height=320, yaxis_title="Perte potentielle (EUR)")
    st.plotly_chart(fig_hedge, use_container_width=True)

    if reduction_var > 0:
        st.info(f"Une couverture a {pct_hedge}% reduit votre VaR de {reduction_var:.0f}% pour un cout de {cout_annuel_eur:,.0f} EUR/an.")

    st.divider()

    # ── SECTION 11 : RECOMMANDATION STRATEGIQUE ──
    st.subheader("11. Recommandation strategique IA")
    tresorerie_investissable = tresorerie_totale - cash_buffer

    if tolerance == "Faible":
        alloc_min, alloc_max = 1, 3
    elif tolerance == "Moderee":
        alloc_min, alloc_max = 3, 7
    else:
        alloc_min, alloc_max = 7, 15

    if horizon == "3 mois":
        alloc_max = min(alloc_max, 3)
    elif horizon == "6 mois":
        alloc_max = min(alloc_max, 5)

    if revenus_usd > 50:
        alloc_min += 1
        alloc_max += 2

    alloc_recommandee = (alloc_min + alloc_max) / 2
    montant_recommande = tresorerie_investissable * (alloc_recommandee / 100)
    btc_recommande = montant_recommande / prix_btc
    ecart_actuel = montant_recommande - valeur_totale_crypto

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1e3c, #2d2d6b);
         padding: 2rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
        <h3 style="color: white; margin-bottom: 1rem;">Recommandation personnalisee</h3>
        <p style="font-size: 1.1rem;">
            Pour un profil <strong>{tolerance}</strong> avec un horizon <strong>{horizon}</strong>,
            une allocation de <strong>{alloc_min}-{alloc_max}% en BTC</strong> est recommandee.
        </p>
        <p style="font-size: 1rem; opacity: 0.85;">
            Montant optimal : <strong>{montant_recommande:,.0f} EUR</strong>
            ({btc_recommande:.3f} BTC au prix actuel)
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Allocation recommandee", f"{alloc_recommandee:.1f}%")
    col2.metric("Montant optimal en BTC", f"{montant_recommande:,.0f} EUR")

    if ecart_actuel > 0:
        col3.metric("Action recommandee", f"Acheter {ecart_actuel:,.0f} EUR de BTC", f"+{(ecart_actuel/prix_btc):.4f} BTC")
        st.warning(f"Votre exposition actuelle ({valeur_totale_crypto:,.0f} EUR) est inferieure a l'optimal. Vous pourriez ajouter {ecart_actuel:,.0f} EUR de BTC.")
    elif ecart_actuel < 0:
        col3.metric("Action recommandee", f"Reduire de {abs(ecart_actuel):,.0f} EUR", f"-{(abs(ecart_actuel)/prix_btc):.4f} BTC")
        st.warning(f"Votre exposition actuelle ({valeur_totale_crypto:,.0f} EUR) depasse l'optimal. Envisagez de reduire de {abs(ecart_actuel):,.0f} EUR.")
    else:
        col3.metric("Action recommandee", "Position optimale")
        st.success("Votre allocation est parfaitement alignee avec votre profil de risque.")

    st.markdown("""
    <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px;
         border-left: 4px solid #0ea5e9; margin-top: 1rem;">
        <small style="color: #0369a1;">
        <strong>Avertissement :</strong> Ces recommandations sont generees automatiquement
        sur la base de votre profil de risque et des donnees de marche.
        Elles ne constituent pas un conseil en investissement au sens reglementaire.
        Consultez un conseiller financier avant toute decision.
        </small>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── SECTION 12 : ANALYSE IA CLAUDE ──
    st.subheader("12. Analyse IA — Powered by Claude")
    if bloc_pro("l'analyse IA", "professional"):
        if st.button("Generer l'analyse IA de votre tresorerie"):
            with st.spinner("Claude analyse votre portefeuille..."):
                try:
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                    prompt = f"""Tu es un expert en gestion de tresorerie d'entreprise et en crypto-actifs, specialise dans les normes IFRS 9 et MiCA.

Voici le profil complet d'une entreprise :

PROFIL ENTREPRISE :
- Nom : {nom_entreprise}
- Tresorerie totale : {tresorerie_totale:,.0f} EUR
- Cash buffer minimum : {cash_buffer:,.0f} EUR
- Revenus en USD : {revenus_usd}%
- Horizon d'investissement : {horizon}
- Tolerance au risque : {tolerance}

EXPOSITION CRYPTO ACTUELLE :
- Bitcoin : {montant_btc} BTC = {valeur_btc:,.0f} EUR
- Ethereum : {montant_eth} ETH = {valeur_eth:,.0f} EUR
- Valeur totale crypto : {valeur_totale_crypto:,.0f} EUR
- Poids dans la tresorerie : {poids_crypto:.1f}%

INDICATEURS DE RISQUE :
- Score de risque global : {score}/100 ({profil})
- VaR 95% journaliere : {var_95:,.0f} EUR
- VaR 99% journaliere : {var_99:,.0f} EUR
- Cash disponible apres crash -50% : {cash_apres_crash:,.0f} EUR
- Statut cash buffer : {"ALERTE" if cash_apres_crash < cash_buffer else "OK"}

PRIX MARCHE :
- Bitcoin : {prix_btc:,.0f} EUR ({var_btc_24h:+.2f}% / 24h)
- Ethereum : {prix_eth:,.0f} EUR ({var_eth_24h:+.2f}% / 24h)

Genere une analyse strategique complete en francais avec :
1. Une evaluation globale de la situation (2-3 phrases)
2. Les 3 points de vigilance principaux
3. Une recommandation d'allocation precise et chiffree
4. Les actions concretes a prendre dans les 30 prochains jours
5. Le verdict final en une phrase

Sois precis, professionnel, et parle comme un CFO s'adressant a son conseil d'administration."""

                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    analyse = message.content[0].text
                    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e3c, #2d2d6b);
             padding: 2rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h3 style="color: white; margin-bottom: 1rem;">Analyse IA — {nom_entreprise}</h3>
            <div style="line-height: 1.8; font-size: 0.95rem;">{analyse.replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)
                    st.success("Analyse generee avec succes — powered by Claude AI")
                except Exception as e:
                    st.error(f"Erreur API : {str(e)}")
    st.divider()

    # ── SECTION 13 : MODULE FX ──
    st.subheader("13. Module FX — Gestion du risque de change")
    if bloc_pro("le module FX multi-devises", "corporate"):
        @st.cache_data(ttl=3600)
        def get_fx_rates():
            try:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                r = requests.get(url, timeout=10)
                data = r.json()
                return data["rates"]
            except:
                return {"EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "CHF": 0.89, "CAD": 1.36, "AUD": 1.53}

        fx_rates = get_fx_rates()
        eur_usd = 1 / fx_rates.get("EUR", 0.92)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e3c, #2d2d6b);
             padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h4 style="color:white; margin-bottom:0.5rem;">Taux de change en temps reel</h4>
            <p style="opacity:0.85;">EUR/USD : <strong>{eur_usd:.4f}</strong> —
            GBP/USD : <strong>{1/fx_rates.get('GBP', 0.79):.4f}</strong> —
            USD/JPY : <strong>{fx_rates.get('JPY', 149.5):.2f}</strong> —
            USD/CHF : <strong>{fx_rates.get('CHF', 0.89):.4f}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Profil de revenus en devises etrangeres")
        col1, col2 = st.columns(2)
        with col1:
            revenus_annuels_usd = st.number_input("Revenus annuels en USD", min_value=0, value=500000, step=10000)
            revenus_annuels_gbp = st.number_input("Revenus annuels en GBP", min_value=0, value=0, step=10000)
            revenus_annuels_jpy = st.number_input("Revenus annuels en JPY", min_value=0, value=0, step=1000000)
        with col2:
            revenus_annuels_chf = st.number_input("Revenus annuels en CHF", min_value=0, value=0, step=10000)
            revenus_annuels_cad = st.number_input("Revenus annuels en CAD", min_value=0, value=0, step=10000)
            revenus_annuels_aud = st.number_input("Revenus annuels en AUD", min_value=0, value=0, step=10000)

        total_revenus_eur = (
            revenus_annuels_usd * fx_rates.get("EUR", 0.92) +
            revenus_annuels_gbp / fx_rates.get("GBP", 0.79) * fx_rates.get("EUR", 0.92) +
            revenus_annuels_jpy / fx_rates.get("JPY", 149.5) * fx_rates.get("EUR", 0.92) +
            revenus_annuels_chf / fx_rates.get("CHF", 0.89) * fx_rates.get("EUR", 0.92) +
            revenus_annuels_cad / fx_rates.get("CAD", 1.36) * fx_rates.get("EUR", 0.92) +
            revenus_annuels_aud / fx_rates.get("AUD", 1.53) * fx_rates.get("EUR", 0.92)
        )

        st.divider()
        st.markdown("#### Risque de change sur vos revenus")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total revenus en EUR", f"{total_revenus_eur:,.0f} EUR")
        col2.metric("Impact depreciation USD -10%", f"-{total_revenus_eur * 0.10:,.0f} EUR")
        col3.metric("Impact depreciation USD -20%", f"-{total_revenus_eur * 0.20:,.0f} EUR")

        vol_fx = 0.08
        var_fx_95 = total_revenus_eur * vol_fx * 1.645
        var_fx_99 = total_revenus_eur * vol_fx * 2.326

        col1, col2 = st.columns(2)
        col1.metric("VaR FX 95% (annuelle)", f"-{var_fx_95:,.0f} EUR")
        col2.metric("VaR FX 99% (annuelle)", f"-{var_fx_99:,.0f} EUR")

        if revenus_annuels_usd > 0:
            scenarios_fx = {
                "USD -20%": revenus_annuels_usd * (fx_rates.get("EUR", 0.92) * 0.80),
                "USD -10%": revenus_annuels_usd * (fx_rates.get("EUR", 0.92) * 0.90),
                "Actuel": revenus_annuels_usd * fx_rates.get("EUR", 0.92),
                "USD +10%": revenus_annuels_usd * (fx_rates.get("EUR", 0.92) * 1.10),
                "USD +20%": revenus_annuels_usd * (fx_rates.get("EUR", 0.92) * 1.20),
            }
            fig_fx = go.Figure()
            fig_fx.add_trace(go.Bar(
                x=list(scenarios_fx.keys()),
                y=list(scenarios_fx.values()),
                marker_color=["#ef4444", "#f59e0b", "#6366f1", "#22c55e", "#15803d"]
            ))
            fig_fx.update_layout(
                title="Impact des variations EUR/USD sur vos revenus USD (EUR)",
                yaxis_title="Revenus en EUR", height=350
            )
            st.plotly_chart(fig_fx, use_container_width=True)

        st.divider()
        st.markdown("#### Simulation de couverture FX")
        col1, col2 = st.columns(2)
        with col1:
            type_couverture = st.selectbox("Type de couverture", ["Forward (vente a terme)", "Options de change", "Couverture naturelle"])
            pct_couverture_fx = st.slider("Pourcentage a couvrir (%)", 0, 100, 50)
            duree_couverture = st.selectbox("Duree de la couverture", ["3 mois", "6 mois", "1 an"])
        with col2:
            cout_couverture_map = {"Forward (vente a terme)": 0.5, "Options de change": 1.5, "Couverture naturelle": 0.2}
            cout_pct = cout_couverture_map[type_couverture]
            montant_couvert = total_revenus_eur * (pct_couverture_fx / 100)
            montant_non_couvert = total_revenus_eur * (1 - pct_couverture_fx / 100)
            cout_couverture_eur = montant_couvert * (cout_pct / 100)
            var_residuelle = montant_non_couvert * vol_fx * 2.326
            st.metric("Montant couvert", f"{montant_couvert:,.0f} EUR")
            st.metric("Cout de la couverture", f"{cout_couverture_eur:,.0f} EUR/an")
            st.metric("VaR residuelle 99%", f"-{var_residuelle:,.0f} EUR")

        reduction_var_fx = ((var_fx_99 - var_residuelle) / var_fx_99 * 100) if var_fx_99 > 0 else 0

        fig_fx2 = go.Figure()
        fig_fx2.add_trace(go.Bar(name="Sans couverture", x=["VaR FX 95%", "VaR FX 99%"], y=[var_fx_95, var_fx_99], marker_color="#ef4444"))
        fig_fx2.add_trace(go.Bar(name=f"Avec couverture {pct_couverture_fx}%", x=["VaR FX 95%", "VaR FX 99%"], y=[montant_non_couvert * vol_fx * 1.645, var_residuelle], marker_color="#22c55e"))
        fig_fx2.update_layout(title="Impact de la couverture sur le risque FX", barmode="group", height=320)
        st.plotly_chart(fig_fx2, use_container_width=True)

        if reduction_var_fx > 0:
            st.info(f"Une couverture {type_couverture} a {pct_couverture_fx}% reduit votre risque FX de {reduction_var_fx:.0f}% pour un cout de {cout_couverture_eur:,.0f} EUR/an.")

        st.markdown("""
        <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px;
             border-left: 4px solid #0ea5e9; margin-top: 1rem;">
            <small style="color: #0369a1;">
            <strong>Note :</strong> Les taux de change sont fournis par ExchangeRate-API.
            Les couts de couverture sont indicatifs. Consultez votre banque ou un courtier specialise.
            </small>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # ── SECTION 14 : HISTORIQUE DES RAPPORTS ──
    st.subheader("14. Historique des rapports")
    if st.button("Charger mon historique"):
        try:
            historique = supabase.table("rapports")\
                .select("*")\
                .eq("user_id", st.session_state.user.id)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()

            if len(historique.data) == 0:
                st.info("Aucun rapport genere pour l'instant. Generez votre premier rapport dans la section 8.")
            else:
                st.success(f"{len(historique.data)} rapport(s) trouve(s)")
                for rapport in historique.data:
                    date = rapport["created_at"][:10]
                    heure = rapport["created_at"][11:16]
                    with st.expander(f"{rapport['entreprise']} — {date} a {heure}"):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Tresorerie", f"{rapport['tresorerie_totale']:,.0f} EUR")
                        col2.metric("Valeur crypto", f"{rapport['valeur_crypto']:,.0f} EUR")
                        col3.metric("Poids crypto", f"{rapport['poids_crypto']:.1f}%")
                        col4.metric("Score risque", f"{rapport['score_risque']}/100")
                        st.caption(f"Profil : {rapport['profil']} — VaR 99% : -{rapport['var_99']:,.0f} EUR")
        except Exception as e:
            st.error(f"Erreur chargement historique : {str(e)}")

    st.divider()
    st.caption("CryptoTreasury — Donnees : CoinGecko — Conforme IFRS 9 et MiCA — Usage professionnel")
