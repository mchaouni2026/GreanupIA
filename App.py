import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time
import anthropic

# ──────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Amendis Green Ops Hub",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

VEOLIA_GREEN  = "#1D9E75"
VEOLIA_DARK   = "#0F6E56"
VEOLIA_BLUE   = "#185FA5"
VEOLIA_LIGHT  = "#EAF3DE"
AMENDIS_GOLD  = "#EF9F27"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Mono&display=swap');
  html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
  .main-header {{
      background: linear-gradient(120deg, {VEOLIA_DARK} 0%, {VEOLIA_GREEN} 60%, {VEOLIA_BLUE} 100%);
      padding: 1.8rem 2rem;
      border-radius: 16px;
      margin-bottom: 1.5rem;
      color: white;
  }}
  .main-header h1 {{ color: white; font-size: 2rem; margin: 0; font-weight: 700; }}
  .main-header p  {{ color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 0.95rem; }}
  .kpi-card {{
      background: white;
      border-radius: 12px;
      padding: 1.2rem;
      border: 1px solid #e8f5f0;
      box-shadow: 0 2px 8px rgba(29,158,117,0.08);
      text-align: center;
  }}
  .kpi-number {{ font-size: 2rem; font-weight: 700; color: {VEOLIA_GREEN}; margin: 0; }}
  .kpi-label  {{ font-size: 0.8rem; color: #666; margin: 4px 0 0; }}
  .kpi-delta  {{ font-size: 0.75rem; color: {VEOLIA_GREEN}; font-weight: 500; }}
  .section-title {{ font-size: 1.1rem; font-weight: 600; color: {VEOLIA_DARK}; margin: 1.5rem 0 0.8rem; display: flex; align-items: center; gap: 8px; }}
  .alert-card {{
      border-radius: 10px;
      padding: 0.9rem 1rem;
      margin-bottom: 0.6rem;
      border-left: 4px solid;
  }}
  .alert-critical {{ background:#FFF0ED; border-color:#E24B4A; }}
  .alert-warning  {{ background:#FAEEDA; border-color:{AMENDIS_GOLD}; }}
  .alert-ok       {{ background:{VEOLIA_LIGHT}; border-color:{VEOLIA_GREEN}; }}
  .agent-bubble {{
      background: linear-gradient(135deg, {VEOLIA_LIGHT}, #E6F1FB);
      border-radius: 12px;
      padding: 1rem 1.2rem;
      border: 1px solid #C0DD97;
      margin-bottom: 0.8rem;
  }}
  .stButton>button {{
      background: {VEOLIA_GREEN} !important;
      color: white !important;
      border-radius: 8px !important;
      border: none !important;
      font-weight: 500 !important;
      padding: 0.5rem 1.5rem !important;
  }}
  .stButton>button:hover {{ background: {VEOLIA_DARK} !important; }}
  .green-score {{ font-size: 3rem; font-weight: 800; color: {VEOLIA_GREEN}; }}
  div[data-testid="stSidebar"] {{ background: #f8fffe; }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# FAKE DATA GENERATORS
# ──────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def gen_network_data():
    zones = ["Zone Nord", "Zone Sud", "Zone Centre", "Zone Est", "Zone Ouest"]
    rows = []
    for z in zones:
        for d in range(30):
            date = datetime.today() - timedelta(days=29-d)
            debit = random.gauss(120, 15)
            pression = random.gauss(3.5, 0.4)
            perte = max(0, random.gauss(12, 5))
            rows.append({"Zone": z, "Date": date, "Débit (m³/h)": round(debit,1),
                         "Pression (bar)": round(pression,2), "Perte (%)": round(perte,1)})
    return pd.DataFrame(rows)

@st.cache_data(ttl=60)
def gen_interventions():
    types = ["Fuite détectée", "Maintenance préventive", "Contrôle qualité", "Remplacement compteur", "Urgence réseau"]
    statuts = ["Planifié", "En cours", "Terminé", "En attente"]
    zones = ["Zone Nord", "Zone Sud", "Zone Centre", "Zone Est", "Zone Ouest"]
    equipes = ["Équipe A", "Équipe B", "Équipe C", "Équipe D"]
    rows = []
    for i in range(40):
        date = datetime.today() + timedelta(days=random.randint(-5, 10))
        rows.append({
            "ID": f"INT-{1000+i}",
            "Type": random.choice(types),
            "Zone": random.choice(zones),
            "Équipe": random.choice(equipes),
            "Date": date.strftime("%d/%m/%Y"),
            "Statut": random.choice(statuts),
            "Priorité": random.choice(["🔴 Haute", "🟡 Moyenne", "🟢 Faible"]),
            "CO₂ évité (kg)": round(random.uniform(5, 120), 1)
        })
    return pd.DataFrame(rows)

@st.cache_data(ttl=60)
def gen_alerts():
    return [
        {"niveau": "critical", "zone": "Zone Nord", "msg": "Débit anormal détecté — possible fuite majeure", "heure": "08:42", "co2": 45},
        {"niveau": "warning",  "zone": "Zone Est",  "msg": "Pression basse sur le réseau secondaire",         "heure": "09:15", "co2": 12},
        {"niveau": "warning",  "zone": "Zone Sud",  "msg": "Compteur #4421 — lecture suspecte",                "heure": "10:01", "co2": 8},
        {"niveau": "ok",       "zone": "Zone Centre","msg": "Maintenance planifiée terminée avec succès",      "heure": "11:30", "co2": 0},
        {"niveau": "ok",       "zone": "Zone Ouest", "msg": "Réseau nominal — tous indicateurs au vert",       "heure": "11:55", "co2": 0},
    ]

@st.cache_data(ttl=300)
def gen_green_metrics():
    return {
        "eau_economisee_m3": 18_420,
        "co2_evite_tonnes": 2.4,
        "fuites_detectees": 14,
        "score_green": 82,
        "interventions_auto": 73,
        "heures_gagnees": 124,
    }


# ──────────────────────────────────────────────────────────
# ANTHROPIC CLIENT
# ──────────────────────────────────────────────────────────
def get_client():
    return anthropic.Anthropic()


# ──────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding: 1rem 0;'>
      <div style='font-size:2.5rem;'>🌿</div>
      <div style='font-weight:700; color:{VEOLIA_DARK}; font-size:1.1rem;'>Green Ops Hub</div>
      <div style='font-size:0.75rem; color:#888;'>par Amendis · Veolia</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    page = st.selectbox("Navigation", [
        "🏠  Tableau de bord",
        "💧  Fuites & Réseau",
        "📅  Planification",
        "📋  Rapports IA",
        "🤖  Agent IA",
        "🌍  Impact Green UP",
    ])

    st.divider()
    st.markdown(f"<div style='font-size:0.75rem;color:#aaa;text-align:center;'>Veolia Agentic Challenge 2026<br>#MAKE_IT_HAPPEN</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class='main-header'>
  <h1>🌿 Amendis Green Ops Hub</h1>
  <p>Agent IA pour l'automatisation des opérations réseau &amp; l'impact environnemental · {datetime.now().strftime("%A %d %B %Y")}</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# PAGE: TABLEAU DE BORD
# ──────────────────────────────────────────────────────────
if "Tableau de bord" in page:
    m = gen_green_metrics()
    net = gen_network_data()
    alerts = gen_alerts()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class='kpi-card'>
          <div class='kpi-number'>{m['eau_economisee_m3']:,} m³</div>
          <div class='kpi-label'>💧 Eau économisée ce mois</div>
          <div class='kpi-delta'>▲ 18% vs mois dernier</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='kpi-card'>
          <div class='kpi-number'>{m['co2_evite_tonnes']} T</div>
          <div class='kpi-label'>🌍 CO₂ évité ce mois</div>
          <div class='kpi-delta'>▲ 12% vs mois dernier</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='kpi-card'>
          <div class='kpi-number'>{m['fuites_detectees']}</div>
          <div class='kpi-label'>⚡ Fuites détectées par IA</div>
          <div class='kpi-delta'>Avant détection: 3 jours → 2h</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='kpi-card'>
          <div class='kpi-number'>{m['score_green']}/100</div>
          <div class='kpi-label'>🏅 Green Score global</div>
          <div class='kpi-delta'>▲ 7 pts ce mois</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("<div class='section-title'>📈 Débit réseau — 30 derniers jours</div>", unsafe_allow_html=True)
        daily = net.groupby("Date")["Débit (m³/h)"].mean().reset_index()
        fig = px.line(daily, x="Date", y="Débit (m³/h)",
                      color_discrete_sequence=[VEOLIA_GREEN])
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("<div class='section-title'>🚨 Alertes temps réel</div>", unsafe_allow_html=True)
        css_map = {"critical": "alert-critical", "warning": "alert-warning", "ok": "alert-ok"}
        icon_map = {"critical": "🔴", "warning": "🟡", "ok": "🟢"}
        for a in alerts:
            st.markdown(f"""
            <div class='alert-card {css_map[a["niveau"]]}'>
              <strong>{icon_map[a["niveau"]]} {a["zone"]}</strong> · {a["heure"]}<br>
              <span style='font-size:0.85rem;'>{a["msg"]}</span>
            </div>
            """, unsafe_allow_html=True)

    # Répartition par zone
    st.markdown("<div class='section-title'>📊 Pertes par zone — 30 jours</div>", unsafe_allow_html=True)
    zone_loss = net.groupby("Zone")["Perte (%)"].mean().reset_index().sort_values("Perte (%)", ascending=True)
    fig2 = px.bar(zone_loss, x="Perte (%)", y="Zone", orientation="h",
                  color="Perte (%)", color_continuous_scale=["#1D9E75","#EF9F27","#E24B4A"])
    fig2.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=220,
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                       coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)


# ──────────────────────────────────────────────────────────
# PAGE: FUITES & RÉSEAU
# ──────────────────────────────────────────────────────────
elif "Fuites" in page:
    net = gen_network_data()
    alerts = gen_alerts()

    st.markdown("<div class='section-title'>🔍 Analyse réseau par zone</div>", unsafe_allow_html=True)

    zone_sel = st.selectbox("Sélectionner une zone", net["Zone"].unique())
    z_data = net[net["Zone"] == zone_sel]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(z_data, x="Date", y="Débit (m³/h)", title=f"Débit — {zone_sel}",
                      color_discrete_sequence=[VEOLIA_GREEN])
        fig.update_layout(height=260, margin=dict(l=0,r=0,t=30,b=0),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.line(z_data, x="Date", y="Pression (bar)", title=f"Pression — {zone_sel}",
                       color_discrete_sequence=[VEOLIA_BLUE])
        fig2.update_layout(height=260, margin=dict(l=0,r=0,t=30,b=0),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    # Anomalies auto-détectées
    st.markdown("<div class='section-title'>🤖 Anomalies détectées par l'agent IA</div>", unsafe_allow_html=True)

    anomalies = z_data[z_data["Perte (%)"] > 15].copy()
    anomalies["Sévérité"] = anomalies["Perte (%)"].apply(lambda x: "🔴 Critique" if x > 20 else "🟡 Modérée")
    anomalies["Eau perdue (m³)"] = (anomalies["Débit (m³/h)"] * anomalies["Perte (%)"] / 100 * 24).round(0)

    if len(anomalies) > 0:
        st.dataframe(anomalies[["Date","Débit (m³/h)","Perte (%)","Sévérité","Eau perdue (m³)"]].reset_index(drop=True),
                     use_container_width=True)
        total_eau = anomalies["Eau perdue (m³)"].sum()
        st.warning(f"⚠️ {len(anomalies)} anomalies détectées dans {zone_sel} · {total_eau:,.0f} m³ d'eau perdue estimée")
    else:
        st.success(f"✅ Aucune anomalie critique détectée dans {zone_sel}")

    if st.button("🤖 Analyser avec l'agent IA et recommander des actions"):
        with st.spinner("L'agent analyse le réseau..."):
            client = get_client()
            prompt = f"""Tu es un agent IA expert en gestion de réseau d'eau potable pour Amendis (Veolia Maroc).
            
Zone analysée: {zone_sel}
Données du réseau sur 30 jours:
- Débit moyen: {z_data['Débit (m³/h)'].mean():.1f} m³/h
- Pression moyenne: {z_data['Pression (bar)'].mean():.2f} bar
- Taux de perte moyen: {z_data['Perte (%)'].mean():.1f}%
- Nombre d'anomalies: {len(anomalies)}

Donne:
1. Un diagnostic précis du réseau
2. Les 3 actions prioritaires à mener
3. L'impact environnemental estimé si les fuites sont réparées (eau économisée, CO₂ évité)
4. Une recommandation de planification pour les équipes terrain

Sois concis, opérationnel et orienté impact green."""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                st.markdown("<div class='agent-bubble'>🤖 <strong>Agent IA — Diagnostic réseau</strong><br><br>", unsafe_allow_html=True)
                container = st.empty()
                full = ""
                for text in stream.text_stream:
                    full += text
                    container.markdown(full)
                st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# PAGE: PLANIFICATION
# ──────────────────────────────────────────────────────────
elif "Planification" in page:
    interventions = gen_interventions()

    st.markdown("<div class='section-title'>📅 Planification des interventions terrain</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        filtre_zone = st.multiselect("Zone", interventions["Zone"].unique(), default=list(interventions["Zone"].unique()))
    with c2:
        filtre_statut = st.multiselect("Statut", interventions["Statut"].unique(), default=list(interventions["Statut"].unique()))
    with c3:
        filtre_equipe = st.multiselect("Équipe", interventions["Équipe"].unique(), default=list(interventions["Équipe"].unique()))

    df_filtered = interventions[
        interventions["Zone"].isin(filtre_zone) &
        interventions["Statut"].isin(filtre_statut) &
        interventions["Équipe"].isin(filtre_equipe)
    ]

    st.dataframe(df_filtered, use_container_width=True, height=350)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    stat_map = {
        "En cours": ("🔄", VEOLIA_BLUE),
        "Planifié": ("📌", AMENDIS_GOLD),
        "Terminé": ("✅", VEOLIA_GREEN),
        "En attente": ("⏳", "#888"),
    }
    counts = df_filtered["Statut"].value_counts()
    for col, (statut, (icon, color)) in zip([c1,c2,c3,c4], stat_map.items()):
        with col:
            n = counts.get(statut, 0)
            st.markdown(f"""<div class='kpi-card'>
              <div class='kpi-number' style='color:{color};'>{icon} {n}</div>
              <div class='kpi-label'>{statut}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Optimisation automatique
    st.markdown("<div class='section-title'>🤖 Optimisation IA du planning</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        nb_equipes = st.slider("Nombre d'équipes disponibles", 1, 8, 4)
        priorite = st.selectbox("Prioriser par", ["Criticité environnementale", "Urgence technique", "Proximité géographique", "CO₂ évité"])
    with col_b:
        date_debut = st.date_input("Date début planning", datetime.today())
        contraintes = st.text_area("Contraintes particulières (optionnel)", placeholder="Ex: Équipe C indisponible lundi, Zone Nord prioritaire...")

    if st.button("🤖 Générer le planning optimisé par l'IA"):
        with st.spinner("L'agent optimise le planning..."):
            client = get_client()
            en_attente = df_filtered[df_filtered["Statut"].isin(["Planifié","En attente"])]
            prompt = f"""Tu es un agent IA expert en planification opérationnelle pour Amendis (Veolia Maroc).

Contexte:
- {nb_equipes} équipes terrain disponibles
- {len(en_attente)} interventions à planifier
- Critère de priorisation: {priorite}
- Date de début: {date_debut}
- Contraintes: {contraintes if contraintes else "Aucune"}

Répartition actuelle:
{en_attente.groupby('Zone')['Type'].count().to_string()}

Types d'interventions:
{en_attente['Type'].value_counts().to_string()}

Génère:
1. Un planning hebdomadaire optimisé pour chaque équipe (lundi à vendredi)
2. L'ordre des interventions par priorité et zone géographique
3. L'impact green estimé (eau économisée, CO₂ évité, km parcourus réduits)
4. Les gains d'efficacité vs planning manuel

Format clair et opérationnel pour un manager terrain."""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                container = st.empty()
                full = ""
                for text in stream.text_stream:
                    full += text
                    container.markdown(full)


# ──────────────────────────────────────────────────────────
# PAGE: RAPPORTS IA
# ──────────────────────────────────────────────────────────
elif "Rapports" in page:
    st.markdown("<div class='section-title'>📋 Génération de rapports par l'agent IA</div>", unsafe_allow_html=True)
    st.info("💡 Décrivez en langage naturel le rapport dont vous avez besoin. L'agent le génère instantanément.")

    exemples = [
        "Rapport hebdomadaire des pertes réseau par zone avec recommandations",
        "Bilan mensuel impact environnemental — eau économisée et CO₂ évité",
        "Rapport d'intervention équipe A — semaine dernière",
        "Analyse comparative des performances réseau Q1 vs Q2",
        "Rapport de conformité qualité eau — mois en cours",
    ]

    type_rapport = st.selectbox("Exemples de rapports", ["Personnalisé..."] + exemples)
    
    if type_rapport == "Personnalisé...":
        demande = st.text_area("Décrivez votre rapport :", height=100,
                               placeholder="Ex: Je veux un rapport sur les fuites détectées en Zone Nord ce mois...")
    else:
        demande = type_rapport

    c1, c2 = st.columns(2)
    with c1:
        periode = st.selectbox("Période", ["Cette semaine", "Ce mois", "Trimestre en cours", "Année en cours"])
    with c2:
        format_out = st.selectbox("Format de sortie", ["Rapport exécutif", "Rapport technique détaillé", "Présentation synthétique", "Tableau de bord"])

    m = gen_green_metrics()
    net = gen_network_data()

    if st.button("📋 Générer le rapport avec l'IA") and demande:
        with st.spinner("L'agent rédige votre rapport..."):
            client = get_client()
            context = f"""
Données Amendis — {periode}:
- Eau économisée: {m['eau_economisee_m3']:,} m³
- CO₂ évité: {m['co2_evite_tonnes']} tonnes
- Fuites détectées: {m['fuites_detectees']}
- Score Green: {m['score_green']}/100
- Interventions automatisées: {m['interventions_auto']}%
- Heures de travail économisées: {m['heures_gagnees']}h
- Taux de perte moyen réseau: {net['Perte (%)'].mean():.1f}%
- Zones les plus affectées: {net.groupby('Zone')['Perte (%)'].mean().idxmax()}
"""
            prompt = f"""Tu es un expert en gestion de réseau d'eau pour Amendis (Veolia Maroc) et rédiges un rapport professionnel.

Demande: {demande}
Période: {periode}
Format: {format_out}

Données disponibles:
{context}

Génère un rapport complet, structuré et professionnel incluant:
- Titre et résumé exécutif
- Analyse des données clés
- Points forts et points d'amélioration
- Impact environnemental (Green UP)
- Recommandations opérationnelles
- Conclusion

Utilise des emojis pertinents pour la lisibilité. Sois précis et orienté action."""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                st.markdown("<div class='agent-bubble'>", unsafe_allow_html=True)
                container = st.empty()
                full = ""
                for text in stream.text_stream:
                    full += text
                    container.markdown(full)
                st.markdown("</div>", unsafe_allow_html=True)

            st.download_button("⬇️ Télécharger le rapport (TXT)", full, "rapport_amendis.txt", "text/plain")


# ──────────────────────────────────────────────────────────
# PAGE: AGENT IA (Chat)
# ──────────────────────────────────────────────────────────
elif "Agent IA" in page:
    st.markdown("<div class='section-title'>🤖 Agent IA Amendis — Posez vos questions</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='agent-bubble'>
    🤖 Bonjour ! Je suis votre agent IA Amendis. Je peux vous aider à :
    <ul>
      <li>Analyser les données réseau et détecter les anomalies</li>
      <li>Planifier et optimiser les interventions terrain</li>
      <li>Générer des rapports et bilans automatiquement</li>
      <li>Calculer l'impact environnemental de vos actions</li>
      <li>Répondre à toute question opérationnelle</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggestions rapides
    suggestions = [
        "Quelle zone a le plus de pertes ce mois ?",
        "Comment réduire le CO₂ de nos interventions ?",
        "Explique-moi comment fonctionne la détection de fuites IA",
        "Quelles sont les meilleures pratiques Green UP pour un réseau d'eau ?",
    ]

    st.markdown("**Suggestions rapides :**")
    cols = st.columns(2)
    for i, sug in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(sug, key=f"sug_{i}"):
                st.session_state.messages.append({"role": "user", "content": sug})

    # Historique
    for msg in st.session_state.messages:
        role_label = "Vous" if msg["role"] == "user" else "🤖 Agent IA"
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Posez votre question à l'agent Amendis..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        m = gen_green_metrics()
        system = f"""Tu es l'agent IA de Amendis (filiale Veolia au Maroc, gestion eau et assainissement à Tanger-Tétouan).
Tu aides les managers et techniciens terrain à:
- Analyser et optimiser le réseau d'eau potable
- Planifier les interventions terrain
- Mesurer et améliorer l'impact environnemental (Green UP)
- Générer des rapports opérationnels

Contexte actuel du réseau:
- Score Green: {m['score_green']}/100
- Eau économisée ce mois: {m['eau_economisee_m3']:,} m³  
- CO₂ évité: {m['co2_evite_tonnes']} tonnes
- Fuites détectées par IA: {m['fuites_detectees']}

Réponds en français, de façon concise, pratique et orientée action. Utilise des emojis pour la lisibilité."""

        msgs_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        with st.chat_message("assistant"):
            with st.spinner("L'agent réfléchit..."):
                client = get_client()
                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=600,
                    system=system,
                    messages=msgs_api
                ) as stream:
                    container = st.empty()
                    full = ""
                    for text in stream.text_stream:
                        full += text
                        container.markdown(full)
                st.session_state.messages.append({"role": "assistant", "content": full})

    if st.button("🗑️ Effacer la conversation"):
        st.session_state.messages = []
        st.rerun()


# ──────────────────────────────────────────────────────────
# PAGE: IMPACT GREEN UP
# ──────────────────────────────────────────────────────────
elif "Green UP" in page:
    m = gen_green_metrics()
    net = gen_network_data()

    st.markdown("<div class='section-title'>🌍 Tableau de bord Impact Environnemental — Green UP</div>", unsafe_allow_html=True)

    # Score central
    col_score, col_kpis = st.columns([1, 2])
    with col_score:
        st.markdown(f"""
        <div style='text-align:center; background:linear-gradient(135deg,{VEOLIA_LIGHT},{VEOLIA_GREEN}22); 
             border-radius:16px; padding:2rem; border:2px solid {VEOLIA_GREEN};'>
          <div style='font-size:0.9rem; color:{VEOLIA_DARK}; font-weight:600;'>GREEN SCORE GLOBAL</div>
          <div class='green-score'>{m['score_green']}</div>
          <div style='font-size:0.8rem; color:{VEOLIA_DARK};'>/100 · Ce mois</div>
          <div style='margin-top:12px; font-size:0.85rem; color:{VEOLIA_GREEN}; font-weight:500;'>🏅 Très Bon</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpis:
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.markdown(f"""<div class='kpi-card'>
              <div class='kpi-number'>💧 {m['eau_economisee_m3']:,}</div>
              <div class='kpi-label'>m³ eau économisée</div>
              <div class='kpi-delta'>≈ {m['eau_economisee_m3']//2500} piscines olympiques</div>
            </div>""", unsafe_allow_html=True)
        with r1c2:
            st.markdown(f"""<div class='kpi-card'>
              <div class='kpi-number'>🌱 {m['co2_evite_tonnes']}</div>
              <div class='kpi-label'>tonnes CO₂ évitées</div>
              <div class='kpi-delta'>≈ {int(m['co2_evite_tonnes']*100)} arbres plantés</div>
            </div>""", unsafe_allow_html=True)
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.markdown(f"""<div class='kpi-card'>
              <div class='kpi-number'>⚡ {m['interventions_auto']}%</div>
              <div class='kpi-label'>Interventions automatisées</div>
              <div class='kpi-delta'>{m['heures_gagnees']}h de travail économisées</div>
            </div>""", unsafe_allow_html=True)
        with r2c2:
            st.markdown(f"""<div class='kpi-card'>
              <div class='kpi-number'>🔍 {m['fuites_detectees']}</div>
              <div class='kpi-label'>Fuites détectées par IA</div>
              <div class='kpi-delta'>Délai: 3j → 2h (-93%)</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Évolution mensuelle Green Score
    st.markdown("<div class='section-title'>📈 Évolution du Green Score — 12 mois</div>", unsafe_allow_html=True)
    mois = [datetime.today() - timedelta(days=30*i) for i in range(11, -1, -1)]
    scores = [random.randint(60, 95) for _ in range(11)] + [m['score_green']]
    fig = px.area(x=[d.strftime("%b %Y") for d in mois], y=scores,
                  color_discrete_sequence=[VEOLIA_GREEN])
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=10,b=0),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis_title="", yaxis_title="Green Score")
    fig.update_yaxes(range=[0,100])
    st.plotly_chart(fig, use_container_width=True)

    # Répartition impact
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='section-title'>🌍 Répartition économies d'eau par zone</div>", unsafe_allow_html=True)
        zones = net["Zone"].unique()
        vals = [random.randint(2000, 6000) for _ in zones]
        fig3 = px.pie(names=zones, values=vals,
                      color_discrete_sequence=[VEOLIA_GREEN, VEOLIA_BLUE, AMENDIS_GOLD, "#5DCAA5", "#185FA5"])
        fig3.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig3, use_container_width=True)
    with c2:
        st.markdown("<div class='section-title'>⚡ CO₂ évité par type d'action</div>", unsafe_allow_html=True)
        actions = ["Réparation fuites", "Optimisation trajets", "Automatisation rapports", "Planification optimisée", "Monitoring temps réel"]
        co2_vals = [1.2, 0.45, 0.18, 0.32, 0.25]
        fig4 = px.bar(x=co2_vals, y=actions, orientation="h",
                      color_discrete_sequence=[VEOLIA_GREEN])
        fig4.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           xaxis_title="tonnes CO₂")
        st.plotly_chart(fig4, use_container_width=True)

    # Recommandations IA Green
    st.markdown("<div class='section-title'>🤖 Recommandations IA pour améliorer le Green Score</div>", unsafe_allow_html=True)
    if st.button("🌿 Générer les recommandations Green UP"):
        with st.spinner("L'agent analyse votre impact environnemental..."):
            client = get_client()
            prompt = f"""Tu es un expert en développement durable et gestion environnementale pour Amendis (Veolia Maroc).

Données actuelles:
- Green Score: {m['score_green']}/100
- Eau économisée: {m['eau_economisee_m3']:,} m³/mois
- CO₂ évité: {m['co2_evite_tonnes']} T/mois
- Taux d'automatisation: {m['interventions_auto']}%
- Délai détection fuites: réduit de 93%

Génère 5 recommandations concrètes et chiffrées pour:
1. Améliorer le Green Score de +10 points
2. Réduire davantage les pertes en eau
3. Minimiser l'empreinte carbone des opérations
4. Maximiser l'impact de l'IA sur la durabilité
5. Valoriser ces actions dans le cadre du challenge Veolia Agentic

Pour chaque recommandation: action, impact estimé, délai de mise en œuvre."""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                container = st.empty()
                full = ""
                for text in stream.text_stream:
                    full += text
                    container.markdown(full)
