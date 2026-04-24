import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time

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
# MOTEUR IA LOCAL — remplace les appels API
# ──────────────────────────────────────────────────────────

def ia_diagnostic_reseau(zone, debit_moy, pression_moy, perte_moy, nb_anomalies):
    """Génère un diagnostic réseau intelligent basé sur les données."""
    
    # Niveau de criticité
    if perte_moy > 20:
        niveau = "🔴 CRITIQUE"
        statut_msg = "Le réseau présente des pertes très élevées nécessitant une intervention immédiate."
    elif perte_moy > 15:
        niveau = "🟡 MODÉRÉ"
        statut_msg = "Des pertes significatives sont détectées. Une intervention rapide est recommandée."
    else:
        niveau = "🟢 NOMINAL"
        statut_msg = "Le réseau fonctionne dans des paramètres acceptables."

    eau_economisable = round(debit_moy * perte_moy / 100 * 24 * 30 * 0.7)
    co2_estime = round(eau_economisable * 0.0003, 2)

    rapport = f"""## 🤖 Diagnostic Agent IA — {zone}

**Niveau d'alerte : {niveau}**

{statut_msg}

---

### 📊 Analyse des indicateurs

| Indicateur | Valeur | Évaluation |
|---|---|---|
| Débit moyen | {debit_moy:.1f} m³/h | {'✅ Normal' if 100 < debit_moy < 140 else '⚠️ Atypique'} |
| Pression moyenne | {pression_moy:.2f} bar | {'✅ Normale' if 3.0 < pression_moy < 4.0 else '⚠️ Hors plage'} |
| Taux de perte | {perte_moy:.1f}% | {'🔴 Élevé' if perte_moy > 15 else '✅ Acceptable'} |
| Anomalies détectées | {nb_anomalies} | {'🔴 Élevé' if nb_anomalies > 5 else '🟡 Modéré' if nb_anomalies > 2 else '✅ Faible'} |

---

### ⚡ 3 Actions prioritaires

**1. {'🚨 Inspection d'urgence sur points de fuite' if perte_moy > 15 else '🔍 Contrôle préventif des jonctions'}**
   - Zone ciblée : {zone}
   - Équipe recommandée : Équipe A (spécialisée fuites)
   - Délai : {'Immédiat (< 24h)' if perte_moy > 20 else 'Sous 48h'}

**2. 📉 Régulation de pression sur le réseau secondaire**
   - {'Augmenter la pression' if pression_moy < 3.2 else 'Réduire la pression' if pression_moy > 3.8 else 'Maintenir la pression actuelle'}
   - Impact estimé : réduction des pertes de 8 à 12%
   - Délai : 2 à 3 jours ouvrés

**3. 🔧 Remplacement des compteurs suspects**
   - {nb_anomalies} compteurs à vérifier prioritairement
   - Planifier avec Équipe B sur la semaine prochaine
   - Réduction estimée des erreurs de mesure : 15%

---

### 🌍 Impact environnemental estimé (si fuites réparées)

- 💧 **Eau économisée** : ~{eau_economisable:,} m³/mois
- 🌱 **CO₂ évité** : ~{co2_estime} tonnes/mois
- ⏱️ **Délai de retour sur investissement** : 3 à 5 semaines

---

### 📅 Recommandation planning

Mobiliser **2 équipes** sur {zone} en priorité cette semaine.
Commencer par les secteurs à plus fort débit (point de fuite probable), puis intervention systématique sur compteurs signalés.
"""
    return rapport


def ia_planning_optimise(nb_equipes, priorite, date_debut, contraintes, nb_interventions, repartition_zones, types_interventions):
    """Génère un planning optimisé basé sur les paramètres."""
    
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    zones = list(repartition_zones.index) if len(repartition_zones) > 0 else ["Zone Nord", "Zone Sud", "Zone Centre"]
    equipes = [f"Équipe {chr(65+i)}" for i in range(nb_equipes)]
    
    planning_lines = f"""## 🗓️ Planning Optimisé — Semaine du {date_debut.strftime('%d/%m/%Y')}

**Critère de priorisation :** {priorite}  
**Équipes mobilisées :** {nb_equipes}  
**Interventions à planifier :** {nb_interventions}  
{'**Contraintes :** ' + contraintes if contraintes else ''}

---

### 📋 Planning hebdomadaire par équipe

"""
    
    for i, equipe in enumerate(equipes):
        planning_lines += f"**{equipe}**\n"
        zone_assignee = zones[i % len(zones)]
        for j, jour in enumerate(jours):
            type_inter = list(types_interventions.index)[(i + j) % len(types_interventions)] if len(types_interventions) > 0 else "Maintenance"
            planning_lines += f"- {jour} : {type_inter} — {zone_assignee} (8h00–12h00) + rapport terrain (14h00–16h00)\n"
        planning_lines += "\n"
    
    planning_lines += f"""---

### 🌍 Impact Green estimé

| Indicateur | Valeur estimée |
|---|---|
| 💧 Eau économisée | ~{nb_interventions * 320:,} m³ |
| 🌱 CO₂ évité | ~{round(nb_interventions * 0.12, 1)} tonnes |
| 🚗 Km parcourus réduits | ~{nb_equipes * 45} km (optimisation trajets) |
| ⏱️ Heures économisées vs manuel | ~{nb_equipes * 6}h |

---

### 📈 Gains d'efficacité vs planning manuel

- **Réduction des déplacements** : -23% grâce au regroupement géographique
- **Taux de complétion estimé** : 94% (vs 78% en planification classique)
- **Détection précoce** : 3× plus rapide grâce à la priorisation IA
- **Satisfaction équipes** : planning équilibré, charge de travail homogène
"""
    return planning_lines


def ia_rapport(demande, periode, format_out, m, net):
    """Génère un rapport professionnel basé sur les données."""
    
    zone_plus_affectee = net.groupby('Zone')['Perte (%)'].mean().idxmax()
    perte_moy = net['Perte (%)'].mean()
    
    rapport = f"""# 📋 {demande}
*Période : {periode} | Format : {format_out} | Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*

---

## 🔎 Résumé Exécutif

Ce rapport présente une analyse complète des performances opérationnelles et environnementales du réseau Amendis pour la période **{periode}**. Les résultats démontrent une amélioration significative de l'efficacité grâce à l'intégration de l'agent IA Green Ops Hub.

---

## 📊 Analyse des données clés

### Performances réseau
- **Taux de perte moyen** : {perte_moy:.1f}% (objectif : < 10%)
- **Zone la plus affectée** : {zone_plus_affectee}
- **Fuites détectées automatiquement** : {m['fuites_detectees']} cas
- **Délai de détection** : réduit de 3 jours à 2 heures (-93%)

### Automatisation opérationnelle
- **Interventions automatisées** : {m['interventions_auto']}%
- **Heures de travail économisées** : {m['heures_gagnees']}h
- **Rapports générés automatiquement** : 100%

---

## ✅ Points forts

1. 🤖 **Détection IA performante** — {m['fuites_detectees']} fuites identifiées avant escalade critique
2. 💧 **Économies d'eau record** — {m['eau_economisee_m3']:,} m³ économisés ce mois (+18% vs mois précédent)
3. ⚡ **Automatisation élevée** — {m['interventions_auto']}% des interventions planifiées automatiquement
4. 🌱 **Impact CO₂ positif** — {m['co2_evite_tonnes']} tonnes évitées grâce aux optimisations

## ⚠️ Points d'amélioration

1. 📉 **Zone {zone_plus_affectee}** — taux de perte encore élevé, nécessite investissement infrastructure
2. 🔧 **Vieillissement réseau** — 12% des compteurs ont plus de 10 ans, remplacement à planifier
3. 📡 **Couverture capteurs** — 3 secteurs sans monitoring temps réel à équiper

---

## 🌍 Impact environnemental — Green UP

| Indicateur | Valeur | Équivalence |
|---|---|---|
| 💧 Eau économisée | {m['eau_economisee_m3']:,} m³ | {m['eau_economisee_m3']//2500} piscines olympiques |
| 🌱 CO₂ évité | {m['co2_evite_tonnes']} tonnes | {int(m['co2_evite_tonnes']*100)} arbres plantés |
| ⚡ Interventions auto | {m['interventions_auto']}% | {m['heures_gagnees']}h travail économisées |
| 🏅 Green Score | {m['score_green']}/100 | +7 pts ce mois |

---

## 🎯 Recommandations opérationnelles

1. **Priorité immédiate** : Déployer 2 équipes sur {zone_plus_affectee} pour réduire le taux de perte sous 10%
2. **Court terme (1 mois)** : Remplacer les 15 compteurs les plus anciens pour améliorer la précision
3. **Moyen terme (3 mois)** : Installer 6 nouveaux capteurs IoT dans les zones non couvertes
4. **Long terme (6 mois)** : Viser un Green Score de 90/100 via le programme d'optimisation continue

---

## ✍️ Conclusion

Les performances d'Amendis sur la période {periode} confirment la valeur ajoutée de l'agent IA Green Ops Hub. La réduction de 93% du délai de détection des fuites et les {m['eau_economisee_m3']:,} m³ d'eau économisés illustrent concrètement l'impact positif de la digitalisation opérationnelle. 

L'objectif pour la prochaine période est d'atteindre un **Green Score de 90/100** et de réduire le taux de perte moyen à **moins de 8%** sur l'ensemble du réseau.

*— Rapport généré par Agent IA Green Ops Hub · Amendis · Veolia*
"""
    return rapport


def ia_chat_reponse(question, m):
    """Génère une réponse intelligente aux questions courantes."""
    
    q = question.lower()
    
    if any(w in q for w in ["perte", "fuite", "zone", "plus"]):
        return f"""📊 **Analyse des pertes réseau**

D'après les données temps réel du réseau Amendis :

- 🔴 La zone avec le plus de pertes ce mois est **Zone Nord** avec ~14,2% de perte moyenne
- 🟡 **Zone Est** suit avec ~13,8% de perte
- 🟢 **Zone Ouest** est la plus performante avec ~10,1% de perte

💡 **Recommandation** : Déployer Équipe A sur Zone Nord cette semaine pour inspection des jonctions principales. Impact estimé : économie de **~2 400 m³/mois**.

Souhaitez-vous un diagnostic détaillé d'une zone spécifique ?"""

    elif any(w in q for w in ["co2", "carbone", "empreinte", "réduire"]):
        return f"""🌱 **Réduction CO₂ des interventions — Stratégie Green UP**

Voici les 4 leviers principaux pour réduire l'empreinte carbone des opérations :

**1. 🚗 Optimisation des trajets (-35% km)**
   Regrouper les interventions par zone géographique → économie de ~45 km/équipe/semaine

**2. 💧 Réparation rapide des fuites (-40% pertes)**
   Chaque m³ d'eau non perdu = 0,0003 tonne CO₂ évitée
   Objectif : économiser **{m['eau_economisee_m3']:,} m³/mois**

**3. 📱 Rapports numériques (-100% papier)**
   Élimination des impressions et déplacements administratifs

**4. ⏰ Interventions préventives (-60% urgences)**
   Moins d'urgences = moins de déplacements non planifiés

**Impact actuel** : {m['co2_evite_tonnes']} tonnes CO₂ évitées ce mois ✅"""

    elif any(w in q for w in ["fonctionne", "détection", "ia", "intelligence", "comment"]):
        return f"""🤖 **Fonctionnement de la détection de fuites par IA**

L'agent IA Amendis utilise une approche multi-capteurs :

**📡 Étape 1 — Collecte des données**
Capteurs IoT sur le réseau → débit, pression, qualité eau (toutes les 15 min)

**🔍 Étape 2 — Détection d'anomalies**
Algorithme de détection statistique :
- Écart > 2σ sur le débit → alerte potentielle
- Chute de pression soudaine → suspicion de fuite
- Compteurs incohérents → vérification terrain

**⚡ Étape 3 — Qualification et priorité**
- 🔴 Critique : intervention sous 2h
- 🟡 Modérée : planification sous 48h
- 🟢 Faible : maintenance préventive prochaine

**📈 Résultats**
- Délai de détection : **3 jours → 2 heures** (-93%)
- Fuites détectées ce mois : **{m['fuites_detectees']}**
- Précision : ~87%"""

    elif any(w in q for w in ["green", "pratique", "améliorer", "score"]):
        return f"""🌍 **Meilleures pratiques Green UP — Réseau d'eau**

**Votre Green Score actuel : {m['score_green']}/100** 🏅

Top 5 des pratiques à fort impact :

**1. 💧 Zéro fuite tolérée** (impact : +8 pts)
Inspection mensuelle systématique de toutes les jonctions

**2. 📊 Monitoring continu** (impact : +6 pts)
Capteurs IoT sur 100% du réseau → détection en temps réel

**3. 🔄 Maintenance prédictive** (impact : +5 pts)
Remplacer les équipements avant la panne, pas après

**4. 🚗 Tournées optimisées** (impact : +4 pts)
Algorithme de routage → -30% km parcourus

**5. 📱 Digitalisation 100%** (impact : +3 pts)
Rapports, planning, alertes : tout en numérique

**Objectif atteignable** : Green Score **90/100** d'ici 3 mois ✅"""

    elif any(w in q for w in ["planning", "planif", "équipe", "intervention"]):
        return f"""📅 **Optimisation du planning des interventions**

Sur la base des {m['fuites_detectees']} interventions actives :

**Cette semaine — Priorités :**
| Équipe | Zone | Mission |
|---|---|---|
| Équipe A | Zone Nord 🔴 | Réparation fuite urgente |
| Équipe B | Zone Est 🟡 | Contrôle pression + compteurs |
| Équipe C | Zone Sud | Maintenance préventive |
| Équipe D | Zone Centre | Remplacement compteurs |

**📊 Charge de travail :**
- Interventions urgentes : 3
- Maintenance planifiée : 8
- Contrôles qualité : 5

💡 **Conseil** : Regrouper Équipes A et C sur Zone Nord lundi pour maximiser l'impact et réduire les déplacements."""

    else:
        return f"""🤖 **Agent IA Amendis — Réponse opérationnelle**

Merci pour votre question. Voici ce que je peux vous dire sur la situation actuelle du réseau :

**📊 État du réseau en temps réel :**
- 🏅 Green Score : **{m['score_green']}/100**
- 💧 Eau économisée ce mois : **{m['eau_economisee_m3']:,} m³**
- 🌱 CO₂ évité : **{m['co2_evite_tonnes']} tonnes**
- ⚡ Fuites détectées par IA : **{m['fuites_detectees']}**

Pour une réponse plus précise, essayez de poser une question sur :
- Les **pertes réseau** par zone
- La **réduction du CO₂** des interventions  
- Le **fonctionnement** de la détection IA
- Les **meilleures pratiques** Green UP
- Le **planning** des équipes terrain"""


def ia_recommandations_green(m):
    """Génère des recommandations Green UP chiffrées."""
    return f"""## 🌿 Recommandations Green UP — Plan d'action

*Green Score actuel : **{m['score_green']}/100** | Objectif : **90/100** en 3 mois*

---

### 1. 💧 Réduction des pertes réseau (-3% sur taux actuel)
**Action** : Déployer 4 capteurs IoT supplémentaires sur Zone Nord et Zone Est  
**Impact estimé** : +4 200 m³ économisés/mois (+22%)  
**CO₂ évité additionnel** : +1,3 tonne/mois  
**Délai** : 3 à 4 semaines | **Coût** : ~15 000 MAD  
**Score impact** : **+5 pts Green Score**

---

### 2. 🚗 Optimisation des tournées terrain (-30% km)
**Action** : Implémenter algorithme de routage géographique pour toutes les équipes  
**Impact estimé** : -180 km/semaine × 4 équipes = -720 km/mois  
**CO₂ évité** : ~0.17 tonne/mois (véhicules thermiques)  
**Délai** : Immédiat (outil digital) | **Coût** : 0 MAD  
**Score impact** : **+3 pts Green Score**

---

### 3. ⚡ Augmenter le taux d'automatisation (73% → 90%)
**Action** : Automatiser les rapports hebdomadaires et alertes équipes  
**Impact estimé** : +{m['heures_gagnees'] + 40}h économisées/mois  
**Bénéfice** : Réduction des erreurs humaines de 35%  
**Délai** : 2 semaines | **Coût** : 0 MAD (agent IA existant)  
**Score impact** : **+4 pts Green Score**

---

### 4. 🔧 Programme remplacement compteurs vieillissants
**Action** : Remplacer les 18 compteurs de plus de 10 ans (priorité Zone Sud)  
**Impact estimé** : Réduction pertes apparentes de 8%, meilleure facturation  
**Eau récupérée** : ~1 200 m³/mois  
**Délai** : 6 semaines | **Coût** : ~45 000 MAD  
**Score impact** : **+3 pts Green Score**

---

### 5. 🏆 Valorisation Veolia Agentic Challenge
**Action** : Documenter et partager les métriques Green Ops Hub  
**KPIs à mettre en avant** :
- Délai détection fuites : 3j → 2h (**-93%**)
- Eau économisée : **{m['eau_economisee_m3']:,} m³/mois**
- CO₂ évité : **{m['co2_evite_tonnes']} T/mois**
- Automatisation : **{m['interventions_auto']}%**  
**Impact** : Reconnaissance benchmark Veolia Group  
**Délai** : Avant fin du challenge #MAKE_IT_HAPPEN  
**Score impact** : **+5 pts Green Score (critère innovation)**

---

### 📈 Synthèse du plan

| Action | Impact Green Score | Délai | Investissement |
|---|---|---|---|
| Capteurs IoT | +5 pts | 4 semaines | 15 000 MAD |
| Tournées optimisées | +3 pts | Immédiat | 0 MAD |
| Automatisation | +4 pts | 2 semaines | 0 MAD |
| Remplacement compteurs | +3 pts | 6 semaines | 45 000 MAD |
| Valorisation challenge | +5 pts | En cours | 0 MAD |
| **TOTAL** | **+20 pts** | **6 semaines** | **60 000 MAD** |

✅ **Résultat projeté : Green Score {m['score_green'] + 8}/100 → objectif 90 atteint !**
"""


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
            time.sleep(0.8)  # simulation traitement
            rapport = ia_diagnostic_reseau(
                zone=zone_sel,
                debit_moy=z_data['Débit (m³/h)'].mean(),
                pression_moy=z_data['Pression (bar)'].mean(),
                perte_moy=z_data['Perte (%)'].mean(),
                nb_anomalies=len(anomalies)
            )
        st.markdown(f"<div class='agent-bubble'>{rapport}</div>", unsafe_allow_html=True)


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
            time.sleep(0.8)
            en_attente = df_filtered[df_filtered["Statut"].isin(["Planifié","En attente"])]
            planning = ia_planning_optimise(
                nb_equipes=nb_equipes,
                priorite=priorite,
                date_debut=date_debut,
                contraintes=contraintes,
                nb_interventions=len(en_attente),
                repartition_zones=en_attente.groupby('Zone')['Type'].count(),
                types_interventions=en_attente['Type'].value_counts()
            )
        st.markdown(planning)


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
            time.sleep(0.8)
            full = ia_rapport(demande, periode, format_out, m, net)

        st.markdown(f"<div class='agent-bubble'>{full}</div>", unsafe_allow_html=True)
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
                m = gen_green_metrics()
                reponse = ia_chat_reponse(sug, m)
                st.session_state.messages.append({"role": "assistant", "content": reponse})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Posez votre question à l'agent Amendis..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        m = gen_green_metrics()
        with st.chat_message("assistant"):
            with st.spinner("L'agent réfléchit..."):
                time.sleep(0.5)
                reponse = ia_chat_reponse(prompt, m)
            st.markdown(reponse)
        st.session_state.messages.append({"role": "assistant", "content": reponse})

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

    st.markdown("<div class='section-title'>🤖 Recommandations IA pour améliorer le Green Score</div>", unsafe_allow_html=True)
    if st.button("🌿 Générer les recommandations Green UP"):
        with st.spinner("L'agent analyse votre impact environnemental..."):
            time.sleep(0.8)
            recommandations = ia_recommandations_green(m)
        st.markdown(recommandations)
