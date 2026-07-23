"""
Index phytosanitaire ONSSA — application de recherche.

Lancement :  streamlit run app.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st
import re

from parser_onssa import lire_export

FICHIER_DONNEES = Path(__file__).parent / "data" / "index_phyto.csv.gz"

TOX_LIBELLES = {
    "A": "A — très toxique / toxique",
    "B": "B — nocif",
    "C": "C — peu ou pas toxique",
    "N": "N — non classé",
}

st.set_page_config(
    page_title="Index phytosanitaire ONSSA",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Design system — CSS personnalisé
# --------------------------------------------------------------------------
_CSS = """
<style>
/* ===== Google Fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ===== Variables ===== */
:root {
    --purple-50: #f5f3ff;
    --purple-100: #ede9fe;
    --purple-200: #ddd6fe;
    --purple-300: #c4b5fd;
    --purple-400: #a78bfa;
    --purple-500: #8b5cf6;
    --purple-600: #7c3aed;
    --purple-700: #6d28d9;
    --purple-800: #5b21b6;
    --purple-900: #4c1d95;
    --amber-400: #fbbf24;
    --amber-500: #f59e0b;
    --surface-0: #ffffff;
    --surface-1: #f8fafc;
    --surface-2: #f1f5f9;
    --surface-3: #e2e8f0;
    --surface-4: #cbd5e1;
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --border-subtle: rgba(124, 58, 237, 0.15);
    --border-accent: rgba(124, 58, 237, 0.4);
    --glow-purple: 0 4px 14px rgba(124, 58, 237, 0.15);
    --glass-bg: rgba(255, 255, 255, 0.8);
    --glass-border: rgba(124, 58, 237, 0.1);
    --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Base ===== */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: var(--surface-0) !important;
}

/* ===== Animations ===== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 8px rgba(124, 58, 237, 0.1); }
    50% { box-shadow: 0 0 20px rgba(124, 58, 237, 0.25); }
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--surface-4);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--purple-600); }

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--surface-1) 0%, var(--surface-2) 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    background: linear-gradient(135deg, var(--purple-400), var(--amber-400));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* ===== Main header ===== */
.main-header {
    text-align: center;
    padding: 1.5rem 0 1rem;
    animation: fadeInUp 0.6s ease-out;
}
.main-header .logo {
    font-size: 3rem;
    display: block;
    margin-bottom: 0.25rem;
    filter: drop-shadow(0 0 12px rgba(124, 58, 237, 0.4));
}
.main-header h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, var(--purple-300) 0%, var(--purple-500) 40%, var(--amber-400) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2;
}
.main-header .subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-weight: 400;
    margin-top: 0.3rem;
    letter-spacing: 0.02em;
}
.header-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--purple-600), var(--amber-500), transparent);
    border: none;
    margin: 0.75rem auto 1.5rem;
    max-width: 500px;
    border-radius: 1px;
}

/* ===== Metric cards ===== */
div[data-testid="stMetric"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border) !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
    transition: var(--transition-smooth);
    animation: fadeInUp 0.5s ease-out both;
    position: relative;
    overflow: hidden;
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--purple-600), var(--purple-400));
    border-radius: 14px 14px 0 0;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    border-color: var(--border-accent) !important;
    box-shadow: var(--glow-purple);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 1.8rem !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-weight: 500 !important;
}

/* Stagger animation for metrics */
div[data-testid="column"]:nth-child(1) div[data-testid="stMetric"] { animation-delay: 0s; }
div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] { animation-delay: 0.1s; }
div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] { animation-delay: 0.2s; }
div[data-testid="column"]:nth-child(4) div[data-testid="stMetric"] { animation-delay: 0.3s; }

/* ===== Tabs ===== */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface-2) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--glass-border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    color: var(--text-secondary) !important;
    transition: var(--transition-smooth);
    border: none !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background: var(--surface-3) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--purple-700), var(--purple-600)) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ===== Buttons ===== */
.stDownloadButton button,
button[kind="primary"],
.stButton > button {
    background: linear-gradient(135deg, var(--purple-700), var(--purple-600)) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: var(--transition-smooth);
    letter-spacing: 0.01em;
}
.stDownloadButton button:hover,
button[kind="primary"]:hover,
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.35) !important;
    background: linear-gradient(135deg, var(--purple-600), var(--purple-500)) !important;
}

/* ===== Expander ===== */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    color: var(--text-primary) !important;
}
details[data-testid="stExpander"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--glass-border) !important;
    border-left: 3px solid var(--purple-600) !important;
    border-radius: 10px !important;
    transition: var(--transition-smooth);
}
details[data-testid="stExpander"]:hover {
    border-left-color: var(--purple-400) !important;
    box-shadow: var(--glow-purple);
}

/* ===== DataFrame ===== */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid var(--glass-border) !important;
}

/* ===== Selectbox & Multiselect ===== */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    border-radius: 10px !important;
    border-color: var(--surface-4) !important;
    transition: var(--transition-smooth);
}
.stSelectbox > div > div:focus-within,
.stMultiSelect > div > div:focus-within {
    border-color: var(--purple-500) !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
}

/* ===== Text input ===== */
.stTextInput > div > div {
    border-radius: 10px !important;
    border-color: var(--surface-4) !important;
    transition: var(--transition-smooth);
}
.stTextInput > div > div:focus-within {
    border-color: var(--purple-500) !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
}

/* ===== Slider ===== */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--purple-600) !important;
}

/* ===== Alerts ===== */
.stAlert [data-testid="stNotification"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* ===== File uploader ===== */
section[data-testid="stFileUploader"] {
    border-radius: 12px !important;
}
section[data-testid="stFileUploader"] > div {
    border-radius: 12px !important;
    border: 2px dashed var(--surface-4) !important;
    transition: var(--transition-smooth);
}
section[data-testid="stFileUploader"] > div:hover {
    border-color: var(--purple-500) !important;
}

/* ===== Divider ===== */
hr {
    border-color: var(--border-subtle) !important;
}

/* ===== Source badge ===== */
.source-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--surface-3);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 0.5rem;
}
.source-badge .dot {
    width: 6px; height: 6px;
    background: #22c55e;
    border-radius: 50%;
    display: inline-block;
    animation: pulseGlow 2s infinite;
}

/* ===== Footer ===== */
.pro-footer {
    text-align: center;
    padding: 1.5rem 0 1rem;
    color: var(--text-muted);
    font-size: 0.8rem;
    line-height: 1.6;
}
.pro-footer a {
    color: var(--purple-400);
    text-decoration: none;
    transition: var(--transition-smooth);
}
.pro-footer a:hover {
    color: var(--purple-300);
}
.footer-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--purple-800), transparent);
    border: none;
    margin: 2rem auto 1rem;
    max-width: 300px;
}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Données
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Chargement de l'index…")
def charger(chemin: str) -> pd.DataFrame:
    df = pd.read_csv(chemin, dtype=str, keep_default_na=False)
    df["Expiration"] = pd.to_datetime(df["Expiration"], errors="coerce")
    df["DAR (j)"] = pd.to_numeric(df["DAR (j)"], errors="coerce")
    return df


@st.cache_data(show_spinner="Lecture de l'export ONSSA…")
def charger_televerse(octets: bytes) -> pd.DataFrame:
    return lire_export(octets)


def source_donnees() -> tuple[pd.DataFrame, str]:
    televerse = st.session_state.get("export_onssa")
    if televerse is not None:
        return charger_televerse(televerse.getvalue()), f"import : {televerse.name}"
    if FICHIER_DONNEES.exists():
        return charger(str(FICHIER_DONNEES)), "index fourni"
    st.error(
        "Aucune donnée. Déposez un export ONSSA dans la barre latérale, "
        "ou placez le fichier index_phyto.csv.gz dans le dossier data/."
    )
    st.stop()


def reinitialiser() -> None:
    for cle in list(st.session_state):
        if cle.startswith("f_"):
            del st.session_state[cle]


# --------------------------------------------------------------------------
# Barre latérale
# --------------------------------------------------------------------------
df, origine = source_donnees()

with st.sidebar:
    st.markdown("### 🌿 Index phytosanitaire")
    _n = f"{len(df):,}".replace(",", " ")
    st.markdown(
        f'<div class="source-badge"><span class="dot"></span> {origine} · {_n} usages</div>',
        unsafe_allow_html=True,
    )

    st.text_input(
        "Recherche libre",
        key="f_texte",
        placeholder="produit, matière active, détenteur…",
        help="Cherche dans le nom du produit, la matière active, le détenteur, "
             "le fournisseur, la culture et l'organisme nuisible.",
    )

    st.multiselect("Culture", sorted(df["Culture"].unique()), key="f_culture")
    st.multiselect(
        "Organisme nuisible", sorted(df["Organisme nuisible"].unique()), key="f_organisme"
    )
    st.multiselect("Catégorie", sorted(df["Catégorie"].unique()), key="f_categorie")

    with st.expander("Filtres avancés"):
        st.multiselect("Substance active", sorted(df["Substance"].unique()), key="f_substance")
        st.multiselect("Formulation", sorted(df["Formulation"].unique()), key="f_formulation")
        st.multiselect("Détenteur", sorted(df["Détenteur"].unique()), key="f_detenteur")

        st.markdown("**Classe toxicologique**")
        tox_dispo = [t for t in ["A", "B", "C", "N"] if t in set(df["Tox"])]
        tox_choisies = [
            t for t in tox_dispo
            if st.checkbox(TOX_LIBELLES.get(t, t), value=True, key=f"f_tox_{t}")
        ]

        st.markdown("**Délai avant récolte**")
        dar_max = st.slider("DAR maximum (jours)", 0, 120, 120, key="f_dar")
        dar_seul = st.checkbox(
            "Masquer les usages sans DAR renseigné", key="f_dar_seul"
        )

        st.markdown("**Homologation**")
        mois_min = st.slider(
            "Valable encore au moins (mois)", 0, 36, 0, key="f_mois",
            help="Écarte les homologations qui expirent trop tôt.",
        )

    st.button("Réinitialiser les filtres", on_click=reinitialiser, width="stretch")

    st.divider()
    st.file_uploader(
        "Mettre à jour l'index",
        type=["xls", "gz", "html", "htm", "xlsx"],
        key="export_onssa",
        help="Déposez ici un export frais depuis eservice.onssa.gov.ma "
             "pour travailler sur des données à jour.",
    )
    st.markdown(
        '<div class="source-badge" style="margin-top:0.75rem">'
        '<span class="dot"></span> '
        '<a href="https://eservice.onssa.gov.ma/IndPesticide.aspx" '
        'target="_blank" style="color:inherit;text-decoration:none">'
        'eservice.onssa.gov.ma</a></div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Filtrage
# --------------------------------------------------------------------------
def filtrer(df: pd.DataFrame) -> pd.DataFrame:
    m = pd.Series(True, index=df.index)
    s = st.session_state

    texte = (s.get("f_texte") or "").strip().lower()
    if texte:
        for mot in texte.split():
            m &= df["Recherche"].str.contains(mot, regex=False, na=False)

    for cle, colonne in [
        ("f_culture", "Culture"),
        ("f_organisme", "Organisme nuisible"),
        ("f_categorie", "Catégorie"),
        ("f_substance", "Substance"),
        ("f_formulation", "Formulation"),
        ("f_detenteur", "Détenteur"),
    ]:
        choix = s.get(cle)
        if choix:
            m &= df[colonne].isin(choix)

    if tox_choisies and len(tox_choisies) < len(tox_dispo):
        m &= df["Tox"].isin(tox_choisies)

    if dar_max < 120:
        m &= df["DAR (j)"].le(dar_max) | df["DAR (j)"].isna()
    if s.get("f_dar_seul"):
        m &= df["DAR (j)"].notna()

    if mois_min > 0:
        limite = pd.Timestamp.today() + pd.DateOffset(months=mois_min)
        m &= df["Expiration"].ge(limite)

    return df[m]


res = filtrer(df)

COLONNES_TABLE = [
    "Produit", "Matière active", "Catégorie", "Culture", "Organisme nuisible",
    "Dose", "DAR", "Nb applications", "Tox", "Formulation", "Détenteur",
    "N° homologation", "Valable jusqu'au",
]


def table(donnees: pd.DataFrame, hauteur: int = 460) -> None:
    st.dataframe(
        donnees[COLONNES_TABLE],
        width="stretch",
        hide_index=True,
        height=hauteur,
        column_config={
            "Produit": st.column_config.TextColumn(width="medium"),
            "Dose": st.column_config.TextColumn(width="small"),
            "DAR": st.column_config.TextColumn("DAR", width="small"),
            "Tox": st.column_config.TextColumn(width="small"),
        },
    )


def bouton_export(donnees: pd.DataFrame, nom: str) -> None:
    st.download_button(
        "⬇️  Exporter la sélection (CSV)",
        donnees[COLONNES_TABLE].to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{nom}_{dt.date.today():%Y-%m-%d}.csv",
        mime="text/csv",
        width="stretch",
    )


# --------------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">'
    '<span class="logo">🌿</span>'
    '<h1>Index phytosanitaire ONSSA</h1>'
    '<div class="subtitle">Recherche et analyse des usages homologués au Maroc</div>'
    '</div>'
    '<div class="header-divider"></div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Usages", f"{len(res):,}".replace(",", " "), f"{len(res) - len(df):+,}".replace(",", " ") if len(res) != len(df) else None)
c2.metric("Produits", res["Produit"].nunique())
c3.metric("Substances actives", res["Substance"].nunique())
c4.metric("Détenteurs", res["Détenteur"].nunique())

onglets = st.tabs(
    ["🔍  Recherche", "🎯  Que traiter ?", "🧪  Fiche produit", "📊  Analyse", "⏳  Expirations", "🚫  Retirés / Expirés", "🏢  Par société", "☣️  Par toxicité", "🧮  Calculateur"]
)

# ---- Recherche ----
with onglets[0]:
    if res.empty:
        st.warning("Aucun résultat. Élargissez les filtres.")
    else:
        table(res)
        bouton_export(res, "index_phyto")

# ---- Que traiter ? ----
with onglets[1]:
    st.caption(
        "Choisissez une culture et un ennemi : les solutions homologuées "
        "apparaissent regroupées par substance active, pour construire une alternance."
    )
    g1, g2 = st.columns(2)
    culture = g1.selectbox("Culture", sorted(df["Culture"].unique()), key="q_culture")
    ennemis = sorted(df.loc[df["Culture"] == culture, "Organisme nuisible"].unique())
    ennemi = g2.selectbox("Organisme nuisible", ennemis, key="q_organisme")

    sel = df[(df["Culture"] == culture) & (df["Organisme nuisible"] == ennemi)]

    if sel.empty:
        st.warning("Aucun produit homologué pour cette combinaison.")
    else:
        st.success(
            f"**{sel['Produit'].nunique()} produits** homologués contre *{ennemi}* "
            f"sur *{culture}*, répartis sur **{sel['Substance'].nunique()} substances actives**."
        )
        dar_dispo = sel["DAR (j)"].dropna()
        if not dar_dispo.empty:
            st.caption(
                f"DAR de {int(dar_dispo.min())} à {int(dar_dispo.max())} jours — "
                "le plus court est souvent décisif en pleine récolte."
            )

        for substance, bloc in sorted(sel.groupby("Substance"), key=lambda x: -len(x[1])):
            with st.expander(f"**{substance}**  ·  {bloc['Produit'].nunique()} produit(s)"):
                st.dataframe(
                    bloc[["Produit", "Teneur", "Formulation", "Dose", "DAR",
                          "Nb applications", "Tox", "Détenteur"]],
                    width="stretch", hide_index=True,
                )
        bouton_export(sel, f"{culture}_{ennemi}".replace(" ", "_"))
        st.info(
            "Deux produits partageant la même substance active n'alternent rien. "
            "Pour une vraie rotation, changez de substance — et vérifiez le mode "
            "d'action sur irac-online.org, frac.info ou hracglobal.com.",
            icon="💡",
        )

# ---- Fiche produit ----
with onglets[2]:
    produits = sorted(res["Produit"].unique()) if not res.empty else sorted(df["Produit"].unique())
    produit = st.selectbox("Produit", produits, key="p_produit")
    fiche = df[df["Produit"] == produit]
    tete = fiche.iloc[0]

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(f"### {produit}")
        st.markdown(f"**Matière active** · {tete['Matière active']}")
        st.markdown(f"**Catégorie** · {tete['Catégorie']}")
        st.markdown(f"**Formulation** · {tete['Formulation']}")
    with f2:
        st.markdown("### &nbsp;")
        st.markdown(f"**Détenteur** · {tete['Détenteur']}")
        st.markdown(f"**Fournisseur** · {tete['Fournisseur']}")
        st.markdown(f"**Classe toxicologique** · {TOX_LIBELLES.get(tete['Tox'], tete['Tox'])}")
    with f3:
        st.metric("N° homologation", tete["N° homologation"])
        if pd.notna(tete["Expiration"]):
            reste = (tete["Expiration"] - pd.Timestamp.today()).days
            st.metric("Valable jusqu'au", tete["Valable jusqu'au"], f"{reste} jours")

    st.markdown(f"#### Usages homologués ({len(fiche)})")
    st.dataframe(
        fiche[["Culture", "Organisme nuisible", "Dose", "DAR", "Nb applications"]],
        width="stretch", hide_index=True,
    )
    bouton_export(fiche, f"fiche_{produit}".replace(" ", "_"))

# ---- Analyse ----
with onglets[3]:
    base = res if not res.empty else df
    a1, a2 = st.columns(2)
    with a1:
        st.markdown("**Répartition par catégorie**")
        st.bar_chart(base["Catégorie"].value_counts().head(12), horizontal=True)
        st.markdown("**Cultures les plus couvertes**")
        st.bar_chart(base["Culture"].value_counts().head(12), horizontal=True)
    with a2:
        st.markdown("**Substances actives les plus représentées**")
        st.bar_chart(base["Substance"].value_counts().head(12), horizontal=True)
        st.markdown("**Ennemis les plus ciblés**")
        st.bar_chart(base["Organisme nuisible"].value_counts().head(12), horizontal=True)

    st.markdown("**Concentration du marché — parts par détenteur**")
    parts = (
        base.groupby("Détenteur")["Produit"].nunique()
        .sort_values(ascending=False).head(15).rename("Produits")
    )
    st.bar_chart(parts, horizontal=True)

# ---- Expirations ----
with onglets[4]:
    st.caption(
        "Homologations arrivant à échéance : utile pour anticiper un retrait "
        "de gamme ou proposer une alternative à un client."
    )
    horizon = st.slider("Horizon (mois)", 3, 48, 12, key="e_horizon")
    limite = pd.Timestamp.today() + pd.DateOffset(months=horizon)
    bientot = (
        df[df["Expiration"].le(limite)]
        .drop_duplicates("N° homologation")
        .sort_values("Expiration")
    )

    if bientot.empty:
        st.success(f"Aucune homologation n'expire dans les {horizon} prochains mois.")
    else:
        st.warning(f"**{len(bientot)} homologations** expirent d'ici {horizon} mois.")
        vue = bientot[["Produit", "Matière active", "Catégorie", "Détenteur",
                       "N° homologation", "Valable jusqu'au"]].copy()
        vue["Jours restants"] = (bientot["Expiration"] - pd.Timestamp.today()).dt.days
        st.dataframe(vue, width="stretch", hide_index=True, height=440)
        st.download_button(
            "⬇️  Exporter la liste (CSV)",
            vue.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"expirations_{horizon}mois_{dt.date.today():%Y-%m-%d}.csv",
            mime="text/csv",
        )

# ---- Retirés / Expirés ----
with onglets[5]:
    st.caption(
        "Produits dont l'homologation a expiré ou qui ont été retirés du marché."
    )
    retires = (
        df[df["Expiration"].lt(pd.Timestamp.today())]
        .drop_duplicates("N° homologation")
        .sort_values("Expiration", ascending=False)
    )

    if retires.empty:
        st.success("Aucun produit retiré ou expiré trouvé dans la base.")
    else:
        st.warning(f"**{len(retires)} produits** sont retirés ou ont une homologation expirée.")
        vue_ret = retires[["Produit", "Matière active", "Catégorie", "Détenteur",
                           "N° homologation", "Valable jusqu'au"]].copy()
        vue_ret["Jours depuis expiration"] = (pd.Timestamp.today() - retires["Expiration"]).dt.days
        st.dataframe(vue_ret, width="stretch", hide_index=True, height=440)
        st.download_button(
            "⬇️  Exporter la liste (CSV)",
            vue_ret.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"retires_expires_{dt.date.today():%Y-%m-%d}.csv",
            mime="text/csv",
        )

# ---- Par société ----
with onglets[6]:
    st.caption("Consultez le portefeuille de produits d'une société (détenteur de l'homologation).")
    societes = sorted(df["Détenteur"].unique())
    societe = st.selectbox("Sélectionnez une société (Détenteur)", societes, key="s_societe")
    
    if societe:
        prod_soc = df[df["Détenteur"] == societe].drop_duplicates("N° homologation")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Produits homologués", len(prod_soc))
        c2.metric("Substances actives uniques", prod_soc["Substance"].nunique())
        
        # Trouver les catégories principales de la société
        cats = prod_soc["Catégorie"].value_counts()
        top_cat = cats.index[0] if not cats.empty else "N/A"
        c3.metric("Catégorie principale", top_cat)
        
        st.markdown(f"#### Portefeuille de {societe}")
        vue_soc = prod_soc[["Produit", "Matière active", "Catégorie", "N° homologation", "Valable jusqu'au"]].sort_values("Produit")
        st.dataframe(vue_soc, width="stretch", hide_index=True)
        
        st.download_button(
            f"⬇️  Exporter le portefeuille de {societe} (CSV)",
            vue_soc.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"portefeuille_{societe.replace(' ', '_')}_{dt.date.today():%Y-%m-%d}.csv",
            mime="text/csv",
        )

# ---- Par toxicité ----
with onglets[7]:
    st.caption("Consultez la liste des produits classés selon leur niveau de toxicité.")
    
    tox_dispo = [t for t in ["A", "B", "C", "N", "-"] if t in set(df["Tox"])]
    labels_tox = [TOX_LIBELLES.get(t, t) for t in tox_dispo]
    
    choix_tox_label = st.selectbox("Sélectionnez une classe toxicologique", labels_tox, key="s_tox")
    
    if choix_tox_label:
        # Retrouver la clé d'origine (A, B, C...) à partir du label
        choix_tox = tox_dispo[labels_tox.index(choix_tox_label)]
        
        prod_tox = df[df["Tox"] == choix_tox].drop_duplicates("N° homologation")
        
        t1, t2 = st.columns(2)
        t1.metric("Produits dans cette classe", len(prod_tox))
        t2.metric("Proportion de l'index", f"{(len(prod_tox) / df['Produit'].nunique() * 100):.1f}%")
        
        st.markdown(f"#### Produits classés : {choix_tox_label}")
        vue_tox = prod_tox[["Produit", "Matière active", "Catégorie", "Formulation", "Détenteur"]].sort_values("Produit")
        st.dataframe(vue_tox, width="stretch", hide_index=True)
        
        st.download_button(
            f"⬇️  Exporter la liste {choix_tox_label.replace(' ', '_')} (CSV)",
            vue_tox.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"toxicite_{choix_tox}_{dt.date.today():%Y-%m-%d}.csv",
            mime="text/csv",
        )

# ---- Calculateur de dose ----
def parse_dose(dose_str: str):
    """Retourne (valeur, unite_standardisee, est_fourchette)."""
    if not isinstance(dose_str, str) or not dose_str.strip():
        return None, "", False
    
    dose_str = str(dose_str).lower().replace(",", ".").replace(" ", "")
    est_fourchette = "-" in dose_str
    
    # Extraire le premier nombre (borne basse si fourchette)
    match_num = re.search(r"(\d+(?:\.\d+)?)", dose_str)
    if not match_num:
        return None, "", False
    
    val = float(match_num.group(1))
    
    if "%" in dose_str:
        return val * 1000, "cc/hl", est_fourchette  # 0.05% = 500 cc/hl? Non, 1% = 1L/100L = 1000cc/100L. 0.05% = 50 cc/hl.
    
    if "l/ha" in dose_str:
        return val, "L/ha", est_fourchette
    elif "cc/hl" in dose_str or "ml/hl" in dose_str:
        return val, "cc/hL", est_fourchette
    elif "l/hl" in dose_str:
        return val * 1000, "cc/hL", est_fourchette
    elif "kg/ha" in dose_str:
        return val, "kg/ha", est_fourchette
    elif "g/ha" in dose_str:
        return val / 1000.0, "kg/ha", est_fourchette
    elif "g/hl" in dose_str:
        return val, "g/hL", est_fourchette
    elif "kg/hl" in dose_str:
        return val * 1000, "g/hL", est_fourchette
        
    return None, "", False

with onglets[8]:
    st.caption("Calculateur intelligent des doses par cuve et par hectare, avec vérification des garde-fous de l'ONSSA.")
    
    calc_col1, calc_col2 = st.columns([1, 1])
    
    with calc_col1:
        st.markdown("### 1. Données produit (ONSSA)")
        calc_produit = st.selectbox("Produit", sorted(df["Produit"].unique()), key="calc_prod")
        
        # Filtre les cultures pour ce produit
        cultures_prod = sorted(df[df["Produit"] == calc_produit]["Culture"].unique())
        calc_culture = st.selectbox("Culture", cultures_prod, key="calc_cult")
        
        # Filtre les ennemis pour ce produit et cette culture
        ennemis_prod = sorted(df[(df["Produit"] == calc_produit) & (df["Culture"] == calc_culture)]["Organisme nuisible"].unique())
        calc_ennemi = st.selectbox("Organisme nuisible", ennemis_prod, key="calc_ennemi")
        
        usage_df = df[(df["Produit"] == calc_produit) & (df["Culture"] == calc_culture) & (df["Organisme nuisible"] == calc_ennemi)]
        
        if not usage_df.empty:
            usage = usage_df.iloc[0]
            st.info(f"**Dose homologuée:** {usage['Dose']}\n\n**DAR:** {usage['DAR']} jours\n\n**Nb max applications:** {usage['Nb applications']}", icon="📋")
            dose_val, dose_unite, is_fourchette = parse_dose(usage["Dose"])
        else:
            usage = None
            dose_val = None
    
    with calc_col2:
        st.markdown("### 2. Contexte d'application")
        surf_ha = st.number_input("Surface à traiter (ha)", min_value=0.1, value=1.0, step=0.1, key="calc_surf")
        vol_bouillie = st.number_input("Volume de bouillie visé (L/ha)", min_value=50, value=300, step=50, key="calc_vol")
        cap_cuve = st.number_input("Capacité de la cuve (L)", min_value=10, value=1000, step=100, key="calc_cuve")
        
    st.divider()
    
    # --- LOGIQUE DE CALCUL ET GARDE-FOUS ---
    if usage is not None and dose_val is not None:
        st.markdown("### 3. Vérifications & Calculs")
        
        erreurs = []
        alertes = []
        
        # Garde-fou : Expiration
        if pd.notna(usage["Expiration"]) and usage["Expiration"] < pd.Timestamp.today():
            erreurs.append(f"L'homologation de ce produit a expiré le {usage['Expiration'].strftime('%d/%m/%Y')}.")
            
        if is_fourchette:
            alertes.append("La dose est donnée sous forme de fourchette. Le calcul utilise la borne basse pour sécurité.")
            
        # Calculs fondamentaux
        vol_hl_ha = vol_bouillie / 100.0
        
        if dose_unite in ["L/ha", "kg/ha"]:
            dose_surf = dose_val
            concentration = dose_val / vol_hl_ha if vol_hl_ha > 0 else 0
            unite_surf = dose_unite
            unite_conc = "L/hL" if dose_unite == "L/ha" else "kg/hL"
            
            # Conversion pour affichage pratique
            if unite_conc == "L/hL":
                concentration_display = concentration * 1000
                unite_conc_display = "cc/hL"
            else:
                concentration_display = concentration * 1000
                unite_conc_display = "g/hL"
                
        elif dose_unite in ["cc/hL", "g/hL"]:
            concentration_display = dose_val
            unite_conc_display = dose_unite
            
            # Dose surfacique induite
            if dose_unite == "cc/hL":
                dose_surf = (dose_val * vol_hl_ha) / 1000.0
                unite_surf = "L/ha"
            else:
                dose_surf = (dose_val * vol_hl_ha) / 1000.0
                unite_surf = "kg/ha"
                
            # Pas de dose max connue stricte de l'ONSSA si exprimée en cc/hl, mais on pourrait alerter si dose surfacique est absurde
        else:
            erreurs.append("Format de dose non reconnu. Calcul impossible.")
            dose_surf = 0
            unite_surf = ""
            concentration_display = 0
            unite_conc_display = ""
            
        if erreurs:
            for err in erreurs:
                st.error(err, icon="🛑")
        else:
            for alt in alertes:
                st.warning(alt, icon="⚠️")
                
            # Quantités de travail
            qt_totale = dose_surf * surf_ha
            unite_totale = "L" if "L" in unite_surf else "kg"
            
            surf_par_cuve = cap_cuve / vol_bouillie if vol_bouillie > 0 else 0
            prod_par_cuve = dose_surf * surf_par_cuve
            nb_cuves = surf_ha / surf_par_cuve if surf_par_cuve > 0 else 0
            
            # Contrôle croisé
            controle_prod = (concentration_display * cap_cuve) / 100.0
            if "cc" in unite_conc_display or "g" in unite_conc_display:
                prod_par_cuve_affichage = prod_par_cuve * 1000.0 # Convertir L/kg en cc/g
            else:
                prod_par_cuve_affichage = prod_par_cuve
                
            unite_cuve = "cc" if "cc" in unite_conc_display else "g" if "g" in unite_conc_display else unite_totale
            
            # Affichage
            c_res1, c_res2, c_res3, c_res4 = st.columns(4)
            c_res1.metric(f"Dose surfacique", f"{dose_surf:.2f} {unite_surf}")
            c_res2.metric(f"Concentration", f"{concentration_display:.1f} {unite_conc_display}")
            c_res3.metric("Quantité totale", f"{qt_totale:.2f} {unite_totale}")
            c_res4.metric("Nombre de cuves", f"{nb_cuves:.1f} cuves")
            
            st.success(f"🧪 **Préparation par cuve ({cap_cuve} L) :** Il faut verser **{prod_par_cuve_affichage:.0f} {unite_cuve}** de produit pour traiter **{surf_par_cuve:.2f} ha** par cuve.")
            
            with st.expander("Voir le détail des calculs (Contrôle croisé)"):
                st.write(f"- Volume de bouillie = {vol_bouillie} L/ha = {vol_hl_ha} hL/ha")
                if dose_unite in ["L/ha", "kg/ha"]:
                    st.write(f"- Concentration = {dose_val} {dose_unite} ÷ {vol_hl_ha} hL/ha = {concentration:.3f} {unite_conc} = {concentration_display:.1f} {unite_conc_display}")
                else:
                    st.write(f"- Dose surfacique = {dose_val} {dose_unite} × {vol_hl_ha} hL/ha = {dose_surf:.2f} {unite_surf}")
                st.write(f"- Produit par cuve (Méthode Surface) = {dose_surf:.2f} {unite_surf} × {surf_par_cuve:.2f} ha/cuve = {prod_par_cuve:.3f} {unite_totale}")
                st.write(f"- Produit par cuve (Méthode Concentration) = {concentration_display:.1f} {unite_conc_display} × ({cap_cuve} L ÷ 100) = {controle_prod:.1f} {unite_cuve}")
                
    elif usage is not None and dose_val is None:
        st.error(f"Impossible de lire la dose automatiquement : `{usage['Dose']}`. Veuillez vérifier l'étiquette.")

st.markdown('<div class="footer-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pro-footer">'
    'Données issues de l\'index phytosanitaire officiel de l\'ONSSA.<br>'
    'Seules les attestations d\'homologation font foi. '
    'Vérifiez la version en cours sur '
    '<a href="https://eservice.onssa.gov.ma" target="_blank">eservice.onssa.gov.ma</a> '
    'avant toute recommandation.'
    '</div>',
    unsafe_allow_html=True,
)
