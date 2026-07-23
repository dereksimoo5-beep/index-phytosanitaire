"""
Lecteur de l'export ONSSA de l'index phytosanitaire.

L'ONSSA exporte un fichier « .xls » qui n'en est pas un : c'est une page HTML
dont le tableau est enfermé dans un commentaire conditionnel Microsoft Office.
Les lecteurs Excel classiques (openpyxl, xlrd, pandas.read_html) échouent tous
dessus. Ce module l'extrait de façon robuste.

Utilisation en ligne de commande :
    python parser_onssa.py export.xls.gz data/index_phyto.csv.gz
"""

from __future__ import annotations

import gzip
import html as ihtml
import io
import re
import sys

import pandas as pd

# Colonnes françaises de l'export, dans l'ordre. Les colonnes arabes qui
# suivent sont ignorées : elles sont vides dans tous les exports observés.
COLONNES = {
    "Organisme nuisible": "Organisme nuisible",
    "Produits": "Produit",
    "Détenteur": "Détenteur",
    "Fournisseur": "Fournisseur",
    "Numéro homologation": "N° homologation",
    "Valable jusqu'au": "Valable jusqu'au",
    "Tableau toxicologique": "Tox",
    "Catégorie": "Catégorie",
    "Formulation": "Formulation",
    "Matière active": "Matière active",
    "Teneur": "Teneur",
    "Usage": "Usage",
    "Dose": "Dose",
    "Culture": "Culture",
    "DAR": "DAR",
    "Nbr d'application": "Nb applications",
}

_TAG = re.compile(r"<[^>]+>")
_BR = re.compile(r"<br\s*/?>", re.I)
_TR = re.compile(r"<tr\b.*?>(.*?)</tr>", re.S | re.I)
_TD = re.compile(r"<t[dh]\b.*?>(.*?)</t[dh]>", re.S | re.I)
_WS = re.compile(r"\s+")


def _lire_octets(source) -> str:
    """Accepte un chemin, des octets ou un objet fichier. Gère le gzip."""
    if hasattr(source, "read"):
        brut = source.read()
    elif isinstance(source, (bytes, bytearray)):
        brut = bytes(source)
    else:
        with open(source, "rb") as fh:
            brut = fh.read()

    if brut[:2] == b"\x1f\x8b":  # signature gzip
        brut = gzip.decompress(brut)

    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return brut.decode(enc)
        except UnicodeDecodeError:
            continue
    return brut.decode("utf-8", errors="replace")


def _cellules(ligne_html: str) -> list[str]:
    sorties = []
    for cellule in _TD.findall(ligne_html):
        texte = _BR.sub(" ", cellule)
        texte = _TAG.sub("", texte)
        texte = ihtml.unescape(texte)
        sorties.append(_WS.sub(" ", texte).strip())
    return sorties


def _normaliser_entete(entete: list[str]) -> list[str]:
    """« Produits (4851) » varie à chaque export : on retire le compteur."""
    return [re.sub(r"\s*\(\d+\)\s*$", "", c).strip() for c in entete]


def lire_export(source) -> pd.DataFrame:
    """Renvoie l'index phytosanitaire sous forme de DataFrame nettoyé."""
    contenu = _lire_octets(source)
    # Les commentaires conditionnels masquent le tableau aux parseurs HTML.
    contenu = contenu.replace("<!--", "").replace("-->", "")

    lignes = _TR.findall(contenu)
    if not lignes:
        raise ValueError("Aucun tableau trouvé : le fichier n'est pas un export ONSSA.")

    donnees = [_cellules(l) for l in lignes]
    entete = _normaliser_entete(donnees[0])
    largeur = len(entete)
    corps = [l for l in donnees[1:] if len(l) == largeur]

    if not corps:
        raise ValueError("Tableau vide ou colonnes incohérentes.")

    # Doublons de noms (« DAR » existe en français et en arabe) : on suffixe.
    uniques, vus = [], {}
    for nom in entete:
        vus[nom] = vus.get(nom, 0) + 1
        uniques.append(nom if vus[nom] == 1 else f"{nom}__{vus[nom]}")

    brut = pd.DataFrame(corps, columns=uniques)

    manquantes = [c for c in COLONNES if c not in brut.columns]
    if manquantes:
        raise ValueError(f"Colonnes absentes de l'export : {', '.join(manquantes)}")

    df = brut[list(COLONNES)].rename(columns=COLONNES).copy()
    return _enrichir(df)


def _dar_numerique(valeur: str):
    """« 7 » → 7 · « 15 j » → 15 · « Non requis » → 0 · reste → None."""
    v = str(valeur).strip().lower()
    if not v or v in {"-", "na", "n/a"}:
        return None
    if v.startswith(("nr", "non requis", "n.r")):
        return 0
    trouve = re.search(r"\d+", v)
    return int(trouve.group()) if trouve else None


def _enrichir(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    df["Expiration"] = pd.to_datetime(
        df["Valable jusqu'au"], format="%d/%m/%Y", errors="coerce"
    )
    df["DAR (j)"] = df["DAR"].map(_dar_numerique)

    # « Abamectine(18 g/l) » → « Abamectine » : indispensable pour regrouper
    # les produits qui partagent la même substance active.
    df["Substance"] = (
        df["Matière active"]
        .str.replace(r"\([^)]*\)", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    df["Recherche"] = (
        df["Produit"] + " | " + df["Matière active"] + " | "
        + df["Détenteur"] + " | " + df["Fournisseur"] + " | "
        + df["Catégorie"] + " | " + df["Culture"] + " | " + df["Organisme nuisible"]
    ).str.lower()

    return df.reset_index(drop=True)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage : python parser_onssa.py <export.xls[.gz]> <sortie.csv.gz>")
        raise SystemExit(1)

    df = lire_export(sys.argv[1])
    df.to_csv(sys.argv[2], index=False, compression="gzip")
    print(f"OK — {len(df)} lignes, {df['Produit'].nunique()} produits → {sys.argv[2]}")


if __name__ == "__main__":
    main()
