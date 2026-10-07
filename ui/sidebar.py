import streamlit as st

from core.database import search_parcels


def render_sidebar():
    st.sidebar.title("Меню аудитора")
    
    # --- ПОЛЕ ДЛЯ ЛОГІНУ ---
    if 'current_auditor' not in st.session_state:
        st.session_state.current_auditor = ""
        
    # ВАЖЛИВА ПРАВКА ТУТ: використовуємо key="current_auditor" замість value та переприсвоєння
    auditor_code = st.sidebar.text_input(
        "👤 Ваш Код аудитора (ПІБ):", 
        key="current_auditor",
        placeholder="Наприклад: Іванов І.І."
    )
    
    st.sidebar.divider()

    # Якщо код не введено - блокуємо подальшу роботу
    if not str(auditor_code).strip():
        st.sidebar.warning("⚠️ Будь ласка, введіть свій ПІБ для початку роботи.")
        return None

    # --- ПОШУК ДІЛЯНКИ (Показується тільки якщо введено логін) ---
    st.sidebar.subheader("Пошук ділянки")
    st.sidebar.write("Введіть кадастровий номер або його частину:")
    
    search_query = st.sidebar.text_input("🔍 Кадастровий номер", placeholder="Наприклад: 0199")
    
    if search_query:
        if len(search_query) >= 3:
            df_results = search_parcels(search_query)
            
            if df_results.empty:
                st.sidebar.warning("За вашим запитом нічого не знайдено.")
            else:
                st.sidebar.success(f"Знайдено збігів: {len(df_results)}")
                
                cadastral_list = df_results['cadastral_number'].tolist()
                options = ["-- Оберіть потрібну ділянку --"] + cadastral_list
                
                selected_option = st.sidebar.selectbox("Результати пошуку:", options)
                
                if selected_option != "-- Оберіть потрібну ділянку --":
                    return selected_option
        else:
            st.sidebar.info("Введіть мінімум 3 символи для пошуку.")
    else:
        st.sidebar.info("Чекаю на ввід...")

    return None