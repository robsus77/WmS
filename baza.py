import streamlit as st
from supabase import create_client
import pandas as pd

# 1. Połączenie z bazą
@st.cache_resource
def init_connection():
    try:
        # Streamlit automatycznie szuka tych danych w Secrets
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        st.error("❌ Błąd: Nie znaleziono kluczy API w Secrets!")
        st.stop()

supabase = init_connection()

st.title("📦 System Zarządzania Magazynem")

# Zakładki dla czytelności
tab1, tab2 = st.tabs(["📂 Zarządzaj Kategoriami", "🛒 Zarządzaj Produktami"])

# --- SEKCJA KATEGORII ---
with tab1:
    st.header("Dodaj nową kategorię")
    with st.form("form_kat", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            n_kat = st.text_input("Nazwa kategorii")
        with col2:
            l_kat = st.number_input("Liczba (kategorie)", min_value=0.0, format="%.2f")
        with col3:
            k_kat = st.number_input("Kwota (kategorie)", min_value=0.0, format="%.2f")
        
        btn_kat = st.form_submit_button("Zapisz Kategorię")

    if btn_kat and n_kat:
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
            st.error(f"Błąd podczas dodawania kategorii: {e}")

    st.divider()
    st.subheader("Istniejące kategorie")
    res_kat = supabase.table("kategorie").select("*").execute()
    if res_kat.data:
        st.dataframe(pd.DataFrame(res_kat.data), use_container_width=True)

# --- SEKCJA PRODUKTÓW ---
with tab2:
    st.header("Dodaj nowy produkt")
    
    # Pobranie kategorii, aby przypisać produkt do ID
    res_kat_list = supabase.table("kategorie").select("id, nazwa").execute()
    mapa_kategorii = {item['nazwa']: item['id'] for item in res_kat_list.data} if res_kat_list.data else {}

    if not mapa_kategorii:
        st.info("Najpierw dodaj kategorię w pierwszej zakładce.")
    else:
        with st.form("form_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            c1, c2, c3 = st.columns(3)
            with c1:
                p_kat_name = st.selectbox("Wybierz kategorię", options=list(mapa_kategorii.keys()))
            with c2:
                p_liczba = st.number_input("Ilość produktu", min_value=0.0, format="%.2f")
            with c3:
                p_kwota = st.number_input("Kwota produktu", min_value=0.0, format="%.2f")
            
            btn_prod = st.form_submit_button("Zapisz Produkt")

        if btn_prod and p_nazwa:
            try:
                # Wstawianie do tabeli 'Produkty' (duża litera P)
                supabase.table("Produkty").insert({
                    "nazwa": p_nazwa,
                    "liczba": p_liczba,
                    "kwota": p_kwota,
                    "kategoria_id": mapa_kategorii[p_kat_name]
                }).execute()
                st.success(f"Dodano produkt: {p_nazwa}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd podczas dodawania produktu: {e}")

    st.divider()
    st.subheader("Lista produktów")
    # Pobieranie produktów wraz z danymi kategorii (Join)
    res_prod = supabase.table("Produkty").select("*, kategorie(nazwa)").execute()
    if res_prod.data:
        df_p = pd.DataFrame(res_prod.data)
        # Uproszczenie kolumny kategorii dla tabeli
        if 'kategorie' in df_p.columns:
            df_p['kategoria_nazwa'] = df_p['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else None)
            df_p = df_p.drop(columns=['kategorie'])
        st.dataframe(df_p, use_container_width=True)
