import streamlit as st
import pandas as pd
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Analiza Dzienniczka Głodów",
    page_icon="📊",
    layout="wide"
)

# --- Data Loading ---
DATA_FILE = 'cravings.csv'

@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(DATA_FILE)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['intensity'] = pd.to_numeric(df['intensity'], errors='coerce')
        # Split comma-separated symptoms into a list
        df['triggers_list'] = df['triggers'].str.split(', ')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

df = load_data()

# --- Main Dashboard ---
st.title("📊 Analiza Dzienniczka Głodów Alkoholowych")

if df.empty:
    st.warning("Brak danych w dzienniczku. Dodaj wpisy w głównej aplikacji, aby zobaczyć analizę.")
else:
    st.header("Historia Wpisów")
    st.dataframe(df.drop(columns=['triggers_list']))

    st.divider()

    # --- Charts and Analysis ---
    st.header("Wizualizacje i Statystyki")

    col1, col2 = st.columns(2)

    with col1:
        # Intensity over time
        st.subheader("Intensywność Głodów w Czasie")
        st.line_chart(df.set_index('timestamp')['intensity'])

    with col2:
        # Average intensity
        avg_intensity = df['intensity'].mean()
        st.metric("Średnia Intensywność", f"{avg_intensity:.2f}")

        # Total entries
        total_entries = len(df)
        st.metric("Całkowita Liczba Wpisów", total_entries)

        # Days since first entry
        days_since_start = (df['timestamp'].max() - df['timestamp'].min()).days
        st.metric("Dni od Pierwszego Wpisu", days_since_start)

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        # Most common symptoms
        st.subheader("Najczęstsze Objawy/Wyzwalacze")
        symptoms_flat_list = [symptom for sublist in df['triggers_list'].dropna() for symptom in sublist]
        symptom_counts = pd.Series(symptoms_flat_list).value_counts()
        st.bar_chart(symptom_counts)

    with col4:
        # Most common coping mechanisms
        st.subheader("Najskuteczniejsze Sposoby Radzenia Sobie")
        coping_counts = df['coping_mechanism'].value_counts()
        st.bar_chart(coping_counts)

    st.info("Ta interaktywna deska rozdzielcza pozwala na głębszą analizę Twoich danych. Używaj jej regularnie, aby śledzić swoje postępy.")