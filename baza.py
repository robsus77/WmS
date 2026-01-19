import streamlit as st
from supabase import create_client
import pandas as pd

# 1. Połączenie z bazą (Pobiera dane z .streamlit/secrets.toml)
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        st.error("❌ Błąd: Nie znaleziono kluczy API. Dodaj je do .streamlit/secrets.toml")
        st.stop()

supabase = init_connection()

st.title("📦 System Zarządzania Baza Danych")

# Menu w zakładkach
tab1, tab2 = st.tabs(["📂 Kategorie", "🛒 Produkty"])

# --- SEKCJA: KATEGORIE ---
with tab1:
    st.header("Dodaj nową kategorię")
    with st.form("form_kat", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            n_kat = st.text_input("Nazwa kategorii")
        with col2:
            l_kat = st.number_input("Liczba (kategorie)", min_value=0.0)
        with col3:
            k_kat = st.number_input("Kwota (kategorie)", min_value=0.0)
        
        submit_kat = st.form_submit_button("Zapisz Kategorię")

    if submit_kat and n_kat:
        try:
            # Wstawianie do tabeli 'kategorie'
            supabase.table("kategorie").insert({
                "nazwa": n_kat, 
                "liczba": l_kat, 
                "kwota": k_kat
            }).execute()
            st.success(f"Dodano kategorię: {n_kat}")
            st.rerun()
        except Exception as e:
            st.error(f"Błąd bazy: {e}")

    st.divider()
    st.subheader("Aktualne kategorie")
    res_kat = supabase.table("kategorie").select("*").execute()
    if res_kat.data:
        st.dataframe(pd.DataFrame(res_kat.data), use_container_width=True)

# --- SEKCJA: PRODUKTY ---
with tab2:
    st.header("Dodaj nowy produkt")
    
    # Pobieramy listę kategorii, żeby móc przypisać produkt do kategorii
    res_kat_list = supabase.table("kategorie").select("id, nazwa").execute()
    lista_kategorii = {item['nazwa']: item['id'] for item in res_kat_list.data} if res_kat_list.data else {}

    if not lista_kategorii:
        st.warning("⚠️ Najpierw musisz dodać chociaż jedną kategorię!")
    else:
        with st.form("form_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            c1, c2, c3 = st.columns(3)
            with c1:
                p_kat_select = st.selectbox("Wybierz kategorię", options=list(lista_kategorii.keys()))
            with c2:
                p_liczba = st.number_input("Ilość produktu", min_value=0.0)
            with c3:
                p_kwota = st.number_input("Cena produktu", min_value=0.0)
            
            submit_prod = st.form_submit_button("Zapisz Produkt")

        if submit_prod and p_nazwa:
            try:
                # Wstawianie do tabeli 'Produkty' (Z dużej litery P!)
                supabase.table("Produkty").insert({
                    "nazwa": p_nazwa,
                    "liczba": p_liczba,
                    "kwota": p_kwota,
                    "kategoria_id": lista_kategorii[p_kat_select]
                }).execute()
                st.success(f"Dodano produkt: {p_nazwa}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd bazy: {e}")

    st.divider()
    st.subheader("Aktualne produkty")
    # Pobieramy produkty i dołączamy nazwę kategorii
    res_prod = supabase.table("Produkty").select("*, kategorie(nazwa)").execute()
    if res_prod.data:
        df_p = pd.DataFrame(res_prod.data)
        # Uproszczenie wyświetlania nazwy kategorii
        if 'kategorie' in df_p.columns:
            df_p['nazwa_kategorii'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
            df_p = df_p.drop(columns=['kategorie'])
        st.dataframe(df_p, use_container_width=True)
