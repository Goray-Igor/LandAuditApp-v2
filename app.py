import streamlit as st

# Импортируем компоненты интерфейса
from ui.sidebar import render_sidebar
from ui.block_registry import render_block_registry
from core.database import get_parcel_data

# Импортируем наши формы аудита
from forms.form_ind import render_form_ind
from forms.form_legal import render_form_legal
from forms.form_oms import render_form_oms

def main():
    st.set_page_config(page_title="Земельний Аудит", layout="wide")
    
    cadastral_number = render_sidebar()
    
    if cadastral_number:
        st.header(f"Аудит ділянки: {cadastral_number}")
        
        db_data = get_parcel_data(cadastral_number)
        if db_data is None: db_data = {}
            
        render_block_registry(cadastral_number, db_data)
        
        st.markdown("---")
        st.subheader("📝 Класифікація договору")
        
        auditor_code = st.session_state.get('current_auditor', '').strip()
        if not auditor_code:
            st.error("⚠️ Помилка авторизації. Введіть Код аудитора в меню зліва.")
            return
            
        col1, col2 = st.columns(2)
        contract_type = col1.selectbox("Тип договору", ["Оренда", "Суборенда", "Постійне користування", "Емфітевзис", "Приватна власність", "Управління спадщиною"])
        counterparty_type = col2.selectbox("Тип контрагенту", ["Фізична", "Юридична", "ОМС"])
        
        # МАПА МАРШРУТІВ (Routing Dictionary)
        # Ключ: (Тип договору, Тип контрагенту) -> Значення: Функція, яка малює форму
        routes = {
            # --- ОРЕНДА ---
            ("Оренда", "Фізична"): render_form_ind,
            ("Оренда", "Юридична"): render_form_legal,
            ("Оренда", "ОМС"): render_form_oms,
            
            # --- СУБОРЕНДА ---
            ("Суборенда", "Фізична"): render_form_ind,
            ("Суборенда", "Юридична"): render_form_legal,
            # Для ОМС суборенди немає, тому не додаємо
            
            # --- ЕМФІТЕВЗИС ---
            ("Емфітевзис", "Фізична"): render_form_ind,
            ("Емфітевзис", "Юридична"): render_form_legal,
        }
        
        # Логіка запуску
        current_route = (contract_type, counterparty_type)
        
        if current_route in routes:
            # Запускаємо знайдену функцію і передаємо їй стандартний набір аргументів
            render_func = routes[current_route]
            render_func(cadastral_number, db_data, contract_type, counterparty_type)
        else:
            st.warning("⚠️ Форма для обраної комбінації ще знаходиться в розробці.")
            
    else:
        st.info("👈 Оберіть ділянку в меню зліва для початку роботи.")

if __name__ == "__main__":
    main()