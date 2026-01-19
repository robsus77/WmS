import streamlit as st
from supabase import create_client
import pandas as pd

# 1. Połączenie
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    except Exception:
        st.error("❌ Błąd kluczy w Secrets!")
        st.stop()

supabase = init_connection()

st.title("📦 System Zarządzania")

t1, t2 = st.tabs(["📂 Kategorie", "🛒 Produkty"])

# --- KATEGORIE ---
with t1:
    st.header("Nowa Kategoria")
    with st.form("f_kat", clear_on_submit=True):
        nazwa = st.text_input("Nazwa")
        col1, col2 = st.columns(2)
        liczba = col1.number_input("Liczba", min_value=0.0)
        kwota = col2.number_input("Kwota", min_value=0.0)
        
        if st.form_submit_button("Zapisz"):
            if nazwa:
                # Wysyłamy TYLKO te trzy pola. Baza SAMA doda ID (bo jest Identity)
                res = supabase.table("kategorie").insert({
                    "nazwa": nazwa, 
                    "liczba": liczba, 
                    "kwota": kwota
                }).execute()
                st.success(f"Dodano: {nazwa}")
                st.rerun()

    st.divider()
    # Wyświetlanie listy kategorii
    data_k = supabase.table("kategorie").select("*").order("id").execute()
    if data_k.data:
        st.table(pd.DataFrame(data_k.data)[['id', 'nazwa', 'liczba', 'kwota']])

# --- PRODUKTY ---
with t2:
    st.header("Nowy Produkt")
    
    # Pobranie kategorii do wyboru
    kat_data = supabase.table("kategorie").select("id, nazwa").execute()
    opcje = {k['nazwa']: k['id'] for k in kat_data.data} if kat_data.data else {}

    if not opcje:
        st.warning("Dodaj najpierw kategorię!")
    else:
        with st.form("f_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_kat = st.selectbox("Kategoria", options=list(opcje.keys()))
            c1, c2 = st.columns(2)
            p_liczba = c1.number_input("Ilość", min_value=0.0)
            p_kwota = c2.number_input("Cena", min_value=0.0)
            
            if st.form_submit_button("Zapisz Produkt"):
                if p_nazwa:
                    # Tabela Produkty z DUŻEJ litery zgodnie ze schematem
                    supabase.table("Produkty").insert({
                        "nazwa": p_nazwa,
                        "liczba": p_liczba,
                        "kwota": p_kwota,
                        "kategoria_id": opcje[p_kat]
                    }).execute()
                    st.success(f"Dodano produkt: {p_nazwa}")
                    st.rerun()

    st.divider()
    # Wyświetlanie produktów
    data_p = supabase.table("Produkty").select("*, kategorie(nazwa)").order("id").execute()
    if data_p.data:
        df = pd.DataFrame(data_p.data)
        if 'kategorie' in df.columns:
            df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else "")
            st.dataframe(df[['id', 'nazwa', 'liczba', 'kwota', 'kategoria_nazwa']], use_container_width=True)
