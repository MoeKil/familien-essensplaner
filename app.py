# -----------------------------
# Familien-Essensplaner Streamlit App
# -----------------------------
import streamlit as st
import pandas as pd
import random
import requests

# -----------------------------
# Google Sheet CSV
# -----------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1X9g21WLcgmcqsdrNSCCoUm4scz1-dLp2Uba13SVEZt4/export?format=csv"

# -----------------------------
# Gerichte laden
# -----------------------------
@st.cache_data
def lade_gerichte():
    try:
        df = pd.read_csv(SHEET_URL, encoding="utf-8-sig")
    except Exception as e:
        st.error(f"Fehler beim Laden des Sheets: {e}")
        return {}

    gerichte = {}

    # Prüfen, ob die notwendigen Spalten vorhanden sind
    required_columns = ["Gericht","Kategorie","Zutat","Menge","Einheit"]
    if not set(required_columns).issubset(df.columns):
        st.error(f"Google Sheet muss die Spalten enthalten: {required_columns}")
        return {}

    # Gerichte aus Sheet zusammenbauen
    for _, row in df.iterrows():
        name = row['Gericht']
        kategorie = row['Kategorie']
        wochenende = row.get('Wochenende', False)  # optional

        # Zutaten-Dict
        zutaten_dict = {row['Zutat']: (row['Menge'], row['Einheit'])}

        # Mehrere Zeilen pro Gericht zusammenführen
        if name in gerichte:
            gerichte[name]['zutaten'].update(zutaten_dict)
        else:
            gerichte[name] = {
                "kategorie": kategorie,
                "zutaten": zutaten_dict,
                "wochenende": wochenende
            }

    return gerichte

gerichte = lade_gerichte()

# -----------------------------
# Wochenplan generieren
# -----------------------------
def generiere_wochenplan(gerichte, tage=["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]):
    plan = {}
    letzte_kategorie = None
    letzte_gerichte = []

    for tag in tage:
        moegliche_gerichte = []
        for name, daten in gerichte.items():
            if name in letzte_gerichte:
                continue
            if daten["kategorie"] == letzte_kategorie:
                continue
            if daten.get("wochenende", False) and tag not in ["Samstag","Sonntag"]:
                continue
            moegliche_gerichte.append(name)

        if not moegliche_gerichte:
            moegliche_gerichte = list(gerichte.keys())

        auswahl = random.choice(moegliche_gerichte)
        plan[tag] = auswahl
        letzte_kategorie = gerichte[auswahl]["kategorie"]
        letzte_gerichte.append(auswahl)
        if len(letzte_gerichte) > 1:
            letzte_gerichte.pop(0)

    return plan

# -----------------------------
# Einkaufsliste erstellen
# -----------------------------
def erstelle_einkaufsliste(plan):
    einkauf = {}
    for gericht in plan.values():
        for zutat, (menge, einheit) in gerichte[gericht]["zutaten"].items():
            if zutat not in einkauf:
                einkauf[zutat] = [0, einheit]
            einkauf[zutat][0] += menge
    return einkauf

# -----------------------------
# Zufälliges vegetarisches Rezept
# -----------------------------
def zufall_vegetarisches_rezept():
    try:
        url = "https://www.themealdb.com/api/json/v1/1/filter.php?c=Vegetarian"
        res = requests.get(url).json()
        meals = res.get("meals", [])
        if not meals:
            return None

        meal = random.choice(meals)
        meal_id = meal["idMeal"]
        detail_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
        detail_res = requests.get(detail_url).json()
        meal_details = detail_res["meals"][0]

        zutaten = []
        for i in range(1, 21):
            zutat = meal_details.get(f"strIngredient{i}")
            menge = meal_details.get(f"strMeasure{i}")
            if zutat and zutat.strip() != "":
                zutaten.append(f"{zutat} – {menge}")

        name = meal_details["strMeal"]
        link = meal_details.get("strSource") or meal_details.get("strYoutube") or "Kein Link verfügbar"

        return {"name": name, "zutaten": zutaten, "link": link}
    except:
        return None

# -----------------------------
# Streamlit App
# -----------------------------
st.title("👨‍👩‍👧‍👦 Familien-Essensplaner")

if not gerichte:
    st.warning("Keine Gerichte geladen. Bitte Google Sheet prüfen.")
else:
    # Dropdown: immer mindestens "Zufall" + "Vegetarisch"
    options = ["Zufall", "Vegetarisch"] + list(gerichte.keys())
    option = st.selectbox("Gericht auswählen", options)

    # Verhalten je nach Auswahl
    if option == "Zufall":
        gericht = random.choice(list(gerichte.keys()))
        st.write(f"**Ausgewähltes Gericht:** {gericht}")
        st.write("**Zutaten:**")
        for z, (menge, einheit) in gerichte[gericht]['zutaten'].items():
            st.write(f"- {z}: {menge} {einheit}")

    elif option == "Vegetarisch":
        rezept = zufall_vegetarisches_rezept()
        if rezept:
            st.write(f"**{rezept['name']}**")
            st.write("**Zutaten:**")
            for z in rezept["zutaten"]:
                st.write(f"- {z}")
            st.markdown(f"[Zum Rezept]({rezept['link']})")
        else:
            st.write("Leider konnte kein vegetarisches Rezept gefunden werden.")

    else:
        st.write(f"**Ausgewähltes Gericht:** {option}")
        st.write("**Zutaten:**")
        for z, (menge, einheit) in gerichte[option]['zutaten'].items():
            st.write(f"- {z}: {menge} {einheit}")

    # Wochenplan Button
    if st.button("📅 Wochenplan erstellen"):
        plan = generiere_wochenplan(gerichte)
        st.subheader("Wochenplan")
        for tag, gericht in plan.items():
            st.write(f"**{tag}:** {gericht}")

        einkauf = erstelle_einkaufsliste(plan)
        st.subheader("🛒 Einkaufsliste")
        for zutat, (menge, einheit) in einkauf.items():
            st.write(f"- {zutat}: {menge} {einheit}")
