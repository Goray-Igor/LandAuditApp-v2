from datetime import date, datetime

import pandas as pd
import streamlit as st

# Додали імпорт нової функції get_sublease_data
from core.database import get_sublease_data


def render_block_registry(cadastral_number , data):
    st.subheader("📘 Дані з Реєстрів (ДЗК / ДРРП)")
    
    # Отримуємо дані з бази для основної ділянки та для суборенди
    sublease_data = get_sublease_data(cadastral_number)
    
    if not data:
        st.error("Дані для цієї ділянки не знайдені в базі.")
        return

    # Функція для красивого виводу: замінює None, порожні рядки або NaN на прочерк "-"
    def clean(val):
        # 1. Перевірка на порожні значення
        if pd.isna(val) or val is None or str(val).strip() in ["", "None", "nan"]:
            return "-"
        
        # 2. Якщо це справжній об'єкт дати (Pandas Timestamp або стандартна дата Python)
        if isinstance(val, (pd.Timestamp, datetime, date)):
            return val.strftime('%d.%m.%Y') # Робимо звичний формат: 01.05.2022
            
        # 3. Якщо база віддала це як текст, але з "хвостом" часу (наприклад, "2022-05-01 00:00:00")
        val_str = str(val).strip()
        if val_str.endswith(" 00:00:00"):
            val_str = val_str.replace(" 00:00:00", "")
            
        return val_str

    # Підблок 1: Параметри ділянки
    with st.expander("📍 Місце розташування та параметри"):
        col1, col2, col3, col4 = st.columns(4)
        col1.write(f"**Область / Район:**<br>{clean(data.get('region'))} / {clean(data.get('district'))}", unsafe_allow_html=True)
        col2.write(f"**Сільрада / КОАТУУ:**<br>{clean(data.get('village_council'))} / {clean(data.get('koatuu'))}", unsafe_allow_html=True)
        col3.write(f"**Площа (ДЗК / ДРРП):**<br>{clean(data.get('area_dzk'))} / {clean(data.get('area_drrp'))} га", unsafe_allow_html=True)
        col4.write(f"**НГО (Всього / За га):**<br>{clean(data.get('ngo_total_uah'))} / {clean(data.get('ngo_per_hectare_uah'))} грн", unsafe_allow_html=True)
        
        st.write("---")
        col1, col2 = st.columns(2)
        col1.write(f"**Категорія / Вид угідь:** {clean(data.get('land_category'))} / {clean(data.get('land_type'))}")
        col2.write(f"**Дата НГО:** {clean(data.get('ngo_date'))}")
        st.write(f"**Цільове призначення (ДЗК / ДРРП):** {clean(data.get('purpose_dzk'))} **/** {clean(data.get('purpose_drrp'))}")
        st.write(f"**Нормалізоване призначення:** {clean(data.get('purpose_normalized'))}")

    # Підблок 2: Власність
    with st.expander("👤 Інформація про Власність"):
        col1, col2 = st.columns(2)
        col1.write(f"**Власник (ДЗК / ДРРП):**<br>{clean(data.get('owner_dzk'))} **/** {clean(data.get('owner_drrp'))}", unsafe_allow_html=True)
        col1.write(f"**ІПН (ДЗК / ДРРП):** {clean(data.get('owner_code_dzk'))} / {clean(data.get('owner_code_drrp'))}")
        col1.write(f"**Форма власності (ДЗК / ДРРП):** {clean(data.get('ownership_form_dzk'))} / {clean(data.get('ownership_form_drrp'))}")
        col1.write(f"**Частка / Площа володіння:** {clean(data.get('ownership_percent_dzk'))} / {clean(data.get('ownership_area_dzk'))} га")
        
        col2.write(f"**Кількість власників:** {clean(data.get('owners_count'))}")
        col2.write(f"**Дата реєстрації (ДЗК / ДРРП):** {clean(data.get('ownership_reg_date_dzk'))} / {clean(data.get('ownership_reg_date_drrp'))}")
        col2.write(f"**Реєстратор:** {clean(data.get('ownership_registrar'))}")
        col2.write(f"**Документ:** {clean(data.get('ownership_doc_type'))} №{clean(data.get('ownership_doc_number'))} від {clean(data.get('ownership_doc_date'))}")
        col2.write(f"**Видавник документу:** {clean(data.get('ownership_doc_issuer'))}")

    # Підблок 3: Користування (Оренда)
    with st.expander("📄 Користування (Оренда / ДРРП)"):
        col1, col2 = st.columns(2)
        col1.write(f"**Орендар (ДЗК / ДРРП):**<br>{clean(data.get('user_dzk'))} **/** {clean(data.get('user_drrp'))}", unsafe_allow_html=True)
        col1.write(f"**Код Орендаря (ДЗК / ДРРП):** {clean(data.get('user_code_dzk'))} / {clean(data.get('user_code_drrp'))}")
        col1.write(f"**Кількість користувачів:** {clean(data.get('users_count'))}")
        col1.write(f"**Тип права:** {clean(data.get('usage_right_type'))}")
        col1.write(f"**Переважне право (Надра / Орендар):** {clean(data.get('priority_right_subsoil'))} / {clean(data.get('priority_right_tenant'))}")
        
        col2.write(f"**Дата реєстрації (ДЗК / ДРРП):** {clean(data.get('usage_reg_date_dzk'))} / {clean(data.get('usage_reg_date_drrp'))}")
        col2.write(f"**Номер реєстрації (ДЗК / ДРРП):** {clean(data.get('usage_reg_number_dzk'))} / {clean(data.get('usage_reg_number_drrp'))}")
        col2.write(f"**Реєстратор:** {clean(data.get('usage_registrar'))}")
        col2.write(f"**Строк дії / Дата завершення:** {clean(data.get('usage_term'))} / {clean(data.get('usage_end_date'))}")
        col2.write(f"**Розрахована дата завершення:** {clean(data.get('usage_end_date_calculated'))}")
        col2.write(f"**Орендна плата:** {clean(data.get('rent_amount_uah'))} грн ({clean(data.get('rent_percent_ngo'))} % від НГО)")
        
        st.write("---")
        st.write(f"**Документ користування:** {clean(data.get('usage_doc_type'))} №{clean(data.get('usage_doc_number'))} від {clean(data.get('usage_doc_date'))}")
        st.write(f"**Видавник документу:** {clean(data.get('usage_doc_issuer'))}")

    # Підблок 4: Обмеження, Обтяження, Суди
    with st.expander("⚖️ Обмеження, Обтяження, Іпотека, Суди"):
        col1, col2 = st.columns(2)
        col1.write(f"**Тип обмеження:** {clean(data.get('restriction_type'))}")
        col1.write(f"**Тип обтяження:** {clean(data.get('encumbrance_type'))}")
        col1.write(f"**Обтяжувач:** {clean(data.get('encumbrance_holder'))}")
        col1.write(f"**Дата / Номер обтяження:** {clean(data.get('encumbrance_date'))} / {clean(data.get('encumbrance_number'))}")
        col1.write(f"**Реєстратор обтяження:** {clean(data.get('encumbrance_registrar'))}")
        
        col2.write(f"**Іпотекодержатель / Іпотекодавець:** {clean(data.get('mortgage_holder'))} / {clean(data.get('mortgage_giver'))}")
        col2.write(f"**Сума іпотеки / Строк:** {clean(data.get('mortgage_amount'))} / {clean(data.get('mortgage_term'))}")
        col2.write(f"**Кількість судових документів:** {clean(data.get('court_docs_count'))}")
        col2.write(f"**ОНМ (Об'єкт нерухомості):** {clean(data.get('onm'))}")

    # Підблок 5: Суборенда (Динамічний - з'являється тільки якщо є дані)
    if sublease_data:
        with st.expander("🤝 Дані суборенди", expanded=True):
            st.success("Для цієї ділянки знайдено інформацію про суборенду в базі.")
            col1, col2 = st.columns(2)
            col1.write(f"**Суборендар (ДЗК / ДРРП):**<br>{clean(sublease_data.get('user_dzk'))} **/** {clean(sublease_data.get('user_drrp'))}", unsafe_allow_html=True)
            col1.write(f"**Код Суборендаря (ДЗК / ДРРП):** {clean(sublease_data.get('user_code_dzk'))} / {clean(sublease_data.get('user_code_drrp'))}")
            col1.write(f"**Тип права:** {clean(sublease_data.get('usage_right_type'))}")
            col1.write(f"**Дата реєстрації (ДЗК / ДРРП):** {clean(sublease_data.get('usage_reg_date_dzk'))} / {clean(sublease_data.get('usage_reg_date_drrp'))}")
            col1.write(f"**Реєстратор:** {clean(sublease_data.get('usage_registrar'))}")
            
            col2.write(f"**Строк дії / Дата завершення:** {clean(sublease_data.get('usage_term'))} / {clean(sublease_data.get('usage_end_date'))}")
            col2.write(f"**Орендна плата:** {clean(sublease_data.get('rent_amount_uah'))} грн ({clean(sublease_data.get('rent_percent_ngo'))} % від НГО)")
            col2.write(f"**З правом пролонгації:** {clean(sublease_data.get('has_prolongation_right'))}")
            col2.write(f"**З правом передачі в суборенду:** {clean(sublease_data.get('has_sublease_right'))}")
            col2.write(f"**Автоматична пролонгація:** {clean(sublease_data.get('auto_prolongation'))}")
            
            st.write("---")
            st.write(f"**Підстава (документ):** {clean(sublease_data.get('registration_basis'))}")
            st.write(f"**Опис предмета:** {clean(sublease_data.get('property_description'))}")
            st.write(f"**Відомості про суб’єктів:** {clean(sublease_data.get('subject_details'))}")