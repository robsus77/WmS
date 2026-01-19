import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Konfiguracja strony
st.set_page_config(page_title="Menedżer Produktów Supabase", layout="centered")

# 2. Połączenie z Supabase
# Używamy st.cache_resource, aby nie łączyć się przy każdym kliknięciu
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

st.title("📦 System Zarządzania Produktami")

# Tworzymy zakładki dla lepszej organizacji
tab1, tab2 = st.tabs(["📂 Zarządzaj Kategoriami", "🛒 Zarządzaj Produktami"])

# --- ZAKŁADKA 1: KATEGORIE ---
with tab1:
    st.header("Dodaj nową kategorię")
    
    with st.form("category_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cat_nazwa = st.text_input("Nazwa kategorii")
            cat_liczba = st.number_input("Liczba (np. stan magazynowy)", min_value=0.0, step=1.0)
        with col2:
            cat_kwota = st.number_input("Kwota (limit/budżet)", min_value=0.0, step=0.01, format="%.2f")
            
        submitted_cat = st.form_submit_button("Zapisz Kategorię")
        
        if submitted_cat:
            if cat_nazwa:
                try:
                    data = {
                        "nazwa": cat_nazwa,
                        "liczba": cat_liczba,
                        "kwota": cat_kwota
                    }
                    response = supabase.table("kategorie").insert(data).execute()
                    st.success(f"Dodano kategorię: {cat_nazwa}")
                except Exception as e:
                    st.error(f"Błąd podczas dodawania: {e}")
            else:
                st.warning("Nazwa kategorii jest wymagana.")

    st.divider()
    st.subheader("Istniejące kategorie")
    
    # Pobieranie danych do podglądu
    try:
        response = supabase.table("kategorie").select("*").execute()
        df_cat = pd.DataFrame(response.data)
        if not df_cat.empty:
            st.dataframe(df_cat, use_container_width=True)
        else:
            st.info("Brak kategorii w bazie.")
    except Exception as e:
        st.error("Nie udało się pobrać kategorii.")

# --- ZAKŁADKA 2: PRODUKTY ---
with tab2:
    st.header("Dodaj nowy produkt")
    
    # Najpierw musimy pobrać kategorie, aby użytkownik mógł wybrać z listy (relacja Foreign Key)
    try:
        categories_response = supabase.table("kategorie").select("id, nazwa").execute()
        categories_data = categories_response.data
        
        if not categories_data:
            st.warning("Najpierw dodaj przynajmniej jedną kategorię w zakładce obok!")
        else:
            # Tworzymy słownik: Nazwa -> ID
            cat_options = {item['nazwa']: item['id'] for item in categories_data}
            
            with st.form("product_form", clear_on_submit=True):
                prod_nazwa = st.text_input("Nazwa produktu")
                
                col1, col2 = st.columns(2)
                with col1:
                    prod_liczba = st.number_input("Ilość", min_value=0.0, step=1.0)
                    # Wybór kategorii z listy
                    selected_cat_name = st.selectbox("Wybierz kategorię", options=list(cat_options.keys()))
                
                with col2:
                    prod_kwota = st.number_input("Cena / Kwota", min_value=0.0, step=0.01, format="%.2f")
                
                submitted_prod = st.form_submit_button("Zapisz Produkt")
                
                if submitted_prod:
                    if prod_nazwa and selected_cat_name:
                        try:
                            # Pobieramy ID na podstawie wybranej nazwy
                            cat_id = cat_options[selected_cat_name]
                            
                            data = {
                                "nazwa": prod_nazwa,
                                "liczba": prod_liczba,
                                "kwota": prod_kwota,
                                "kategoria_id": cat_id  # Klucz obcy
                            }
                            supabase.table("produkty").insert(data).execute()
                            st.success(f"Dodano produkt: {prod_nazwa}")
                        except Exception as e:
                            st.error(f"Błąd zapisu: {e}")
                    else:
                        st.warning("Uzupełnij nazwę produktu.")

            st.divider()
            st.subheader("Lista produktów")
            
            # Pobieranie produktów
            try:
                # Pobieramy też nazwę kategorii (join) dla czytelności
                response = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
                
                if response.data:
                    # Spłaszczanie JSONa, żeby nazwa kategorii była czytelna w tabeli
                    flat_data = []
                    for item in response.data:
                        row = item.copy()
                        if item.get('kategorie'):
                            row['kategoria_nazwa'] = item['kategorie']['nazwa']
                        else:
                            row['kategoria_nazwa'] = "Brak"
                        del row['kategorie'] # usuwamy zagnieżdżony obiekt
                        flat_data.append(row)
                        
                    df_prod = pd.DataFrame(flat_data)
                    
                    # Uporządkowanie kolumn
                    column_order = ['id', 'nazwa', 'liczba', 'kwota', 'kategoria_nazwa']
                    # Filtrujemy tylko te kolumny, które faktycznie istnieją w df
                    existing_cols = [c for c in column_order if c in df_prod.columns]
                    
                    st.dataframe(df_prod[existing_cols], use_container_width=True)
                else:
                    st.info("Brak produktów.")
            except Exception as e:
                st.error(f"Błąd pobierania produktów: {e}")

    except Exception as e:
        st.error(f"Błąd połączenia z bazą: {e}")
