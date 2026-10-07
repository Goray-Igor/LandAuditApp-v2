import streamlit as st

from core.utils import clean_numeric, get_db_val, get_saved_val


def render_group_rent(db_data, existing_audit, contract_type, counterparty_type):
    """
    Малює Групу 3 (Орендна плата).
    Логіка залежить виключно від контрагента (ОМС чи інші),
    оскільки для всіх типів договорів (Оренда/Суборенда/Емфітевзис) реквізити ідентичні.
    """
    result = {}

    with st.expander("💰 Група 3: Орендна плата", expanded=True):

        # ==========================================
        # 1. СПЕЦИФІКА ОМС
        # ==========================================
        if counterparty_type == "ОМС":
            result["rent_form"] = st.selectbox("Форма оплати", ["Грошова"], index=0)

            c1, c2, c3 = st.columns(3)
            rent_uah = c1.number_input("Розмір (грн)", value=float(get_saved_val(existing_audit, "rent_amount_uah", get_db_val(db_data, 'rent_amount_uah', 0))), step=100.0)
            rent_perc = c2.number_input("% від НГО", value=float(get_saved_val(existing_audit, "rent_percent_ngo", get_db_val(db_data, 'rent_percent_ngo', 0))), step=0.1)
            ngo_signing = c3.number_input("НГО на момент підписання грн", value=float(get_saved_val(existing_audit, "ngo_at_signing_uah", 0.0)), step=100.0)

            result["rent_amount_uah"] = clean_numeric(rent_uah)
            result["rent_percent_ngo"] = clean_numeric(rent_perc)
            result["ngo_at_signing_uah"] = clean_numeric(ngo_signing)

        # ==========================================
        # 2. ФІЗИЧНІ ТА ЮРИДИЧНІ ОСОБИ (Всі типи договорів)
        # ==========================================
        else:
            rent_opts = ["Грошова", "Натуральна", "Змішана"]
            saved_rent_form = str(get_saved_val(existing_audit, "rent_form", "Грошова"))
            result["rent_form"] = st.selectbox("Форма оплати", rent_opts, index=rent_opts.index(saved_rent_form) if saved_rent_form in rent_opts else 0)

            c1, c2, c3 = st.columns(3)
            rent_uah, rent_perc, grain_amt = 0.0, 0.0, 0.0

            if result["rent_form"] in ["Грошова", "Змішана"]:
                rent_uah = c1.number_input("Розмір (грн)", value=float(get_saved_val(existing_audit, "rent_amount_uah", get_db_val(db_data, 'rent_amount_uah', 0))), step=100.0)
                rent_perc = c2.number_input("% від НГО", value=float(get_saved_val(existing_audit, "rent_percent_ngo", get_db_val(db_data, 'rent_percent_ngo', 0))), step=0.1)

            if result["rent_form"] in ["Натуральна", "Змішана"]:
                grain_amt = c3.number_input("Кількість зерна (тонн)", value=float(get_saved_val(existing_audit, "grain_amount_tons", 0.0)), step=0.1)

            result["rent_amount_uah"] = clean_numeric(rent_uah)
            result["rent_percent_ngo"] = clean_numeric(rent_perc)
            result["grain_amount_tons"] = clean_numeric(grain_amt)

        # ==========================================
        # 3. СПІЛЬНІ ПОЛЯ ДЛЯ ВСІХ
        # ==========================================
        c4, c5 = st.columns(2)
        result["ngo_indexation"] = c4.checkbox("Індексація НГО", value=bool(get_saved_val(existing_audit, "ngo_indexation", False)))
        result["inflation_index_applied"] = c5.checkbox("Застосування індексів інфляції", value=bool(get_saved_val(existing_audit, "inflation_index_applied", False)))

        result["additional_payments_notes"] = st.text_input("Наявність додаткових виплат", value=str(get_saved_val(existing_audit, "additional_payments_notes", "")))

    return result
