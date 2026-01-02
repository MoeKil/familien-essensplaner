import streamlit as st
import pandas as pd
import random

# --------------------------------
# Grundeinstellungen
# --------------------------------
st.set_page_config(page_title="Familien-Essensplaner", layout="centered")
st.title("🍽 Familien-Essensplaner")
st.caption("Ein Klick zum Wochenplan inkl. Einkaufsliste")

# --------------------------------
# Google Sheet
# --------------------------------
SHEET_ID = "1X9g21WLcgmcqsdrNSCCoUm4scz1-dLp2Uba13SVEZt4"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# --------------------------------
# Daten laden
# --------------------------------
@st.cache_data
def lade_gerichte():
    df = pd.read_csv(CSV_URL)
    gerichte = {}

    for _, row in df.iterrows():
        name = row["Gericht"]
        if name not in gerichte:
            gerichte[name] = {
                "kategorie": row["Kategorie"],
                "zutaten": {}
            }
        gerichte[name]["zutaten"][row["Zutat"]] = (
            int(row["Menge"]),
            row["Einheit"]
        )
    return gerichte

try:
    gerichte = lade_gerichte()
except Exception as e:
    st.error("Fehler beim Laden der Gerichte")
    st.stop()

gericht_namen = sorted(gerichte.keys())

# --------------------------------
# Wochentage
# --------------------------------
wochentage = [
    "Montag", "Dienstag", "Mittwoch",
    "Donnerstag", "Freitag", "Samstag", "Sonntag"
]

# --------------------------------
# UI – Vorgaben
# --------------------------------
st.subheader("📌 Feste Tage (optional)")
st.write("Leer lassen = Zufall")

vorgaben = {}
for tag in wochentage:
    auswahl = st.selectbox(
        tag,
        options=["(Zufall)"] + gericht_namen,
        key=tag
    )
    if auswahl != "(Zufall)":
        vorgaben[tag] = auswahl

# --------------------------------
# Logik: Wochenplan
# --------------------------------
def erstelle_wochenplan(gerichte, vorgaben):
    plan = {}
    freie_gerichte = [
        g for g in gerichte if g not in vorgaben.values()
    ]
    random.shuffle(freie_gerichte)

    for i, tag in enumerate(wochentage):
        if tag in vorgaben:
            plan[tag] = vorgaben[tag]
            continue

        for gericht in freie_gerichte:
            kategorie = gerichte[gericht]["kategorie"]

            if i > 0:
                vorher = plan[wochentage[i - 1]]
                if vorher == gericht:
                    continue
                if gerichte[vorher]["kategorie"] == kategorie:
                    continue

            if kategorie == "Wochenende" and tag not in ["Samstag", "Sonntag"]:
                continue

            plan[tag] = gericht
            freie_gerichte.remove(gericht)
            break
        else:
            raise RuntimeError("Zu viele Einschränkungen – kein gültiger Plan möglich.")

    return plan

# --------------------------------
# Einkaufsliste
# --------------------------------
def erstelle_einkaufsliste(plan):
    einkauf = {}
    for gericht in plan.values():
        for zutat, (menge, einheit) in gerichte[gericht]["zutaten"].items():
            if zutat not in einkauf:
                einkauf[zutat] = [0, einheit]
            einkauf[zutat][0] += menge
    return einkauf

# --------------------------------
# Button
# --------------------------------
st.divider()

if st.button("🧠 Wochenplan erstellen", use_container_width=True):
    try:
        plan = erstelle_wochenplan(gerichte, vorgaben)
        einkauf = erstelle_einkaufsliste(plan)

        st.subheader("📅 Wochenplan")
        for tag in wochentage:
            g = plan[tag]
            st.write(f"**{tag}:** {g} ({gerichte[g]['kategorie']})")

        st.subheader("🛒 Einkaufsliste")
        for zutat, (menge, einheit) in einkauf.items():
            st.write(f"- {zutat}: {menge} {einheit}")

    except Exception as e:
        st.error(str(e))