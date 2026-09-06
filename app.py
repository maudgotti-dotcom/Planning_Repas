import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

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

# Plats peu adaptés au micro-ondes
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

# Liste complète triée pour le menu déroulant
tous_les_plats = sorted(list(set(df['plat_clean'].tolist() + SUGGESTIONS_EXTERIEURES)))

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", 
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

if "plannings" not in st.session_state:
    st.session_state.plannings = {}
if "verrouilles" not in st.session_state:
    st.session_state.verrouilles = {}

today = datetime.now().date()
lundi_courant = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.week_offset)

JOURS_DATES = []
nom_jours = ["Lundi", "Mardi", "Mercredi", "Jeudi"]
for i in range(4):
    d = lundi_courant + timedelta(days=i)
    mois_str = MOIS[d.month - 1]
    JOURS_DATES.append((f"{nom_jours[i]} {d.day} {mois_str}", d.isoformat()))

week_key = lundi_courant.isoformat()

if week_key not in st.session_state.plannings:
    st.session_state.plannings[week_key] = {date_iso: "" for _, date_iso in JOURS_DATES}
if week_key not in st.session_state.verrouilles:
    st.session_state.verrouilles[week_key] = {date_iso: False for _, date_iso in JOURS_DATES}

st.sidebar.header("⚙️ Configuration")
frequence_externe = st.sidebar.slider("Fréquence des idées extérieures (%)", 0, 50, 15) / 100.0

def tirer_un_plat(deja_selectionnes):
    if random.random() < frequence_externe:
        options = [p for p in SUGGESTIONS_EXTERIEURES if p not in deja_selectionnes]
        if options:
            return f"{random.choice(options)} (Nouveauté extérieure)"
    
    if random.random() < 0.60 and plats_complets:
        options = [p for p in plats_complets if p not in deja_selectionnes]
        if options:
            return random.choice(options)
    
    v_opt = [v for v in viandes if v not in deja_selectionnes]
    l_opt = legumes
    if v_opt and l_opt:
        return f"{random.choice(v_opt)} + {random.choice(l_opt)}"
    
    return random.choice(plats_complets)

def generer_planning_semaine(wk):
    deja_choisis = [plat.split(" (")[0] for date_iso, plat in st.session_state.plannings[wk].items() if st.session_state.verrouilles[wk][date_iso]]
    for _, date_iso in JOURS_DATES:
        if not st.session_state.verrouilles[wk][date_iso]:
            nouveau_plat = tirer_un_plat(deja_choisis)
            st.session_state.plannings[wk][date_iso] = nouveau_plat
            deja_choisis.append(nouveau_plat.split(" (")[0])

if all(v == "" for v in st.session_state.plannings[week_key].values()):
    generer_planning_semaine(week_key)

col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
with col_nav1:
    if st.button("⬅️ Semaine précédente"):
        st.session_state.week_offset -= 1
        st.rerun()

with col_nav2:
    if st.button("📅 Semaine actuelle"):
        st.session_state.week_offset = 0
        st.rerun()

with col_nav3:
    if st.button("Semaine suivante ➡️"):
        st.session_state.week_offset += 1
        st.rerun()

jeudi_d = lundi_courant + timedelta(days=3)
st.subheader(f"📅 Semaine du {lundi_courant.day} {MOIS[lundi_courant.month-1]} au {jeudi_d.day} {MOIS[jeudi_d.month-1]} {lundi_courant.year}")

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    if st.button("🔄 Régénérer les plats non verrouillés", type="primary"):
        generer_planning_semaine(week_key)
with col_btn2:
    if st.button("🗑️ Réinitialiser la semaine"):
        st.session_state.verrouilles[week_key] = {date_iso: False for _, date_iso in JOURS_DATES}
        st.session_state.plannings[week_key] = {date_iso: "" for _, date_iso in JOURS_DATES}
        generer_planning_semaine(week_key)
        st.rerun()

st.write("---")

for label_jour, date_iso in JOURS_DATES:
    col_lock, col_text, col_change = st.columns([1, 3.5, 1.5])
    
    with col_lock:
        is_locked = st.checkbox("🔒 Valider", value=st.session_state.verrouilles[week_key][date_iso], key=f"lock_{week_key}_{date_iso}")
        st.session_state.verrouilles[week_key][date_iso] = is_locked
    
    with col_text:
        plat_actuel = st.session_state.plannings[week_key][date_iso]
        if is_locked:
            st.markdown(f"**{label_jour}** : {plat_actuel} ✅")
        else:
            st.markdown(f"**{label_jour}** : {plat_actuel}")
    
    with col_change:
        if not is_locked:
            if st.button("🎲 Tirer au sort", key=f"btn_{week_key}_{date_iso}"):
                deja_choisis = [p.split(" (")[0] for p in st.session_state.plannings[week_key].values()]
                st.session_state.plannings[week_key][date_iso] = tirer_un_plat(deja_choisis)
                st.rerun()
    
    # Choix manuel
    if not is_locked:
        with st.expander(f"✏️ Choisir manuellement pour {label_jour}"):
            col_sel, col_inp = st.columns(2)
            with col_sel:
                choix_liste = st.selectbox(
                    "Depuis la liste :",
                    options=["-- Choisir un plat --"] + tous_les_plats,
                    key=f"select_{week_key}_{date_iso}"
                )
                if choix_liste != "-- Choisir un plat --":
                    if st.button("Appliquer la sélection", key=f"btn_apply_sel_{week_key}_{date_iso}"):
                        st.session_state.plannings[week_key][date_iso] = choix_liste
                        st.session_state.verrouilles[week_key][date_iso] = True
                        st.rerun()
            
            with col_inp:
                saisie_libre = st.text_input("Ou saisie libre :", key=f"input_{week_key}_{date_iso}")
                if saisie_libre.strip() != "":
                    if st.button("Valider la saisie", key=f"btn_apply_inp_{week_key}_{date_iso}"):
                        st.session_state.plannings[week_key][date_iso] = saisie_libre.strip()
                        st.session_state.verrouilles[week_key][date_iso] = True
                        st.rerun()

    st.write("")
