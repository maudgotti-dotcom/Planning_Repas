import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Planning Repas Étudiant", layout="centered", page_icon="🍲")

st.title("🍲 Planificateur de repas - Semaine étudiante")

@st.cache_data
def load_repas():
    df = pd.read_csv("Repas.csv")
    df['type_clean'] = df['type'].astype(str).str.strip().str.lower()
    df['plat_clean'] = df['plat'].astype(str).str.strip()
    return df

try:
    df = load_repas()
except Exception as e:
    st.error(f"Impossible de charger Repas.csv : {e}")
    st.stop()

# Exclusions des plats peu adaptés au micro-ondes
EXCLUSIONS = ['œufs au plat', 'poke bowl', 'pizzas', 'pinsa', 'croque monsieur', 'quesadillas']

plats_complets = df[(df['type_clean'] == 'plat') & (~df['plat_clean'].isin(EXCLUSIONS))]['plat_clean'].tolist()
viandes = df[(df['type_clean'] == 'viande/poisson') & (~df['plat_clean'].isin(EXCLUSIONS))]['plat_clean'].tolist()
legumes = df[df['type_clean'] == 'légumes']['plat_clean'].tolist()

SUGGESTIONS_EXTERIEURES = [
    "Dahl de lentilles corail au lait de coco et riz",
    "Curry de pois chiches et patates douces",
    "Chili sin carne aux haricots rouges et maïs",
    "Pâtes au pesto maison et poulet effiloché",
    "Sauté de porc au caramel et riz basmati",
    "Wok de nouilles au poulet et légumes",
    "Sauté de dinde aux poivrons et semoule"
]

st.sidebar.header("⚙️ Configuration")
frequence_externe = st.sidebar.slider("Fréquence des idées extérieures (%)", 0, 50, 15) / 100.0

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi"]

# Initialisation des états
if "planning" not in st.session_state:
    st.session_state.planning = {jour: "" for jour in JOURS}
if "verrouille" not in st.session_state:
    st.session_state.verrouille = {jour: False for jour in JOURS}

def tirer_un_plat(deja_selectionnes):
    # 1. Idée extérieure selon la probabilité choisie
    if random.random() < frequence_externe:
        options = [p for p in SUGGESTIONS_EXTERIEURES if p not in deja_selectionnes]
        if options:
            return f"{random.choice(options)} (Nouveauté extérieure)"
    
    # 2. Alternance équilibrée :
    # 60 % de chance : Plats complets réchauffables (lasagnes, blanquette, potée, etc.)
    # 40 % de chance : Viandes cuites le dimanche (rôti de porc, gigot, etc.) + Accompagnement
    if random.random() < 0.60 and plats_complets:
        options = [p for p in plats_complets if p not in deja_selectionnes]
        if options:
            return random.choice(options)
    
    # Assemblage : Viande cuite le dimanche + Légumes / Gratin / Purée
    v_opt = [v for v in viandes if v not in deja_selectionnes]
    l_opt = legumes
    if v_opt and l_opt:
        v_choisi = random.choice(v_opt)
        l_choisi = random.choice(l_opt)
        return f"{v_choisi} + {l_choisi}"
    
    return random.choice(plats_complets)

def generer_planning():
    deja_choisis = [plat.split(" (")[0] for jour, plat in st.session_state.planning.items() if st.session_state.verrouille[jour]]
    for jour in JOURS:
        if not st.session_state.verrouille[jour]:
            nouveau_plat = tirer_un_plat(deja_choisis)
            st.session_state.planning[jour] = nouveau_plat
            deja_choisis.append(nouveau_plat.split(" (")[0])

# Premier tirage au chargement
if all(v == "" for v in st.session_state.planning.values()):
    generer_planning()

# Actions globales
col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    if st.button("🔄 Régénérer les plats non verrouillés", type="primary"):
        generer_planning()
with col_btn2:
    if st.button("🗑️ Tout réinitialiser"):
        st.session_state.verrouille = {jour: False for jour in JOURS}
        st.session_state.planning = {jour: "" for jour in JOURS}
        generer_planning()
        st.rerun()

st.subheader("📋 Planning du lundi au jeudi")

for jour in JOURS:
    col_lock, col_text, col_change = st.columns([1, 4, 1.2])
    
    with col_lock:
        is_locked = st.checkbox("🔒 Valider", value=st.session_state.verrouille[jour], key=f"lock_{jour}")
        st.session_state.verrouille[jour] = is_locked
    
    with col_text:
        plat_actuel = st.session_state.planning[jour]
        if is_locked:
            st.markdown(f"**{jour}** : {plat_actuel} ✅")
        else:
            st.markdown(f"**{jour}** : {plat_actuel}")
    
    with col_change:
        if not is_locked:
            if st.button("🎲 Changer", key=f"btn_{jour}"):
                deja_choisis = [p.split(" (")[0] for p in st.session_state.planning.values()]
                st.session_state.planning[jour] = tirer_un_plat(deja_choisis)
                st.rerun()
