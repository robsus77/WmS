import streamlit as st
from supabase import create_client
import pandas as pd

# 1. Konfiguracja strony
st.set_page_config(page_title="Magazyn Supabase", layout="wide")

# 2. Inicjalizacja połączenia
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        st.error("Błąd: Sprawdź plik .streamlit/secrets.toml")
        st.stop()

supabase = init_connection()

st.title("📦 Zarządzanie Kategoriami i Produktami")

# Zakładki
tab1, tab2 = st.tabs(["📂 Kategorie", "🛒 Produkty"])

# --- ZAKŁADKA 1: KATEGORIE ---
with tab1:
    st.header("Dodaj nową kategorię")
    with st.form("form_kat", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            n_kat = st.text_input("Nazwa kategorii")
        with col2:
            l_kat = st.number_input("Liczba", min_value=0.0)
        with col3:
            k_kat = st.number_input("Kwota", min_value=0.0)
        
        btn_kat = st.form_submit_button("Dodaj Kategorię")

    if btn_kat and n_kat:
        try:
            # Używamy małej litery 'kategorie' zgodnie ze schematem
            supabase.table("kategorie").insert({
                "nazwa": n_kat, 
                "liczba": l_kat, 
                "kwota": k_kat
            }).execute()
            st.success(f"Dodano kategorię: {n_kat}")
            st.rerun()
        except Exception as e:
            st.error(f"Błąd: {e}")

    st.divider()
    st.subheader("Lista Kategorii")
    res_kat = supabase.table("kategorie").select("*").execute()
    if res_kat.data:
        st.dataframe(pd.DataFrame(res_kat.data), use_container_width=True)

# --- ZAKŁADKA 2: PRODUKTY ---
with tab2:
    st.header("Dodaj nowy produkt")
    
    # Pobranie kategorii do listy wyboru
    res_kat_list = supabase.table("kategorie").select("id, nazwa").execute()
    opcje_kat = {item['nazwa']: item['id'] for item in res_kat_list.data} if res_kat_list.data else {}

    if not opcje_kat:
        st.warning("Najpierw dodaj kategorię!")
    else:
        with st.form("form_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            c1, c2, c3 = st.columns(3)
            with c1:
                p_kat = st.selectbox("Kategoria", options=list(opcje_kat.keys()))
            with c2:
                p_liczba = st.number_input("Ilość", min_value=0.0)
            with c3:
                p_kwota = st.number_input("Cena (kwota)", min_value=0.0)
            
            btn_prod = st.form_submit_button("Dodaj Produkt")

        if btn_prod and p_nazwa:
            try:
                # WAŻNE: Używamy dużej litery 'Produkty' zgodnie z Twoim schematem
                supabase.table("Produkty").insert({
                    "nazwa": p_nazwa,
                    "liczba": p_liczba,
                    "kwota": p_kwota,
                    "kategoria_id": opcje_kat[p_kat]
                }).execute()
                st.success(f"Dodano produkt: {p_nazwa}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd: {e}")

    st.divider()
    st.subheader("Lista Produktów")
    # Pobieranie produktów wraz z nazwą kategorii (join)
    res_prod = supabase.table("Produkty").select("*, kategorie(nazwa)").execute()
    if res_prod.data:
        df_p = pd.DataFrame(res_prod.data)
        # Czyszczenie wyglądu tabeli
        if 'kategorie' in df_p.columns:
            df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else None)
        st.dataframe(df_p.drop(columns=['kategorie'], errors='ignore'), use_container_width=True)
