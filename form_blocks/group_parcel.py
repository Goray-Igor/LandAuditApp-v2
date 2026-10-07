import streamlit as st

from core.utils import clean_numeric, format_area, get_db_val, get_saved_val


def render_group_parcel(cadastral_number, db_data, existing_audit, contract_type, counterparty_type):
    """
    Малює Групу 2 (Відомості про земельну ділянку).
    Поле "Інше" тепер доступне для всіх.
    Агрохім паспорт з'являється тільки для ОМС.
    """
    result = {}

    with st.expander("🌍 Група 2: Відомості про земельну ділянку", expanded=True):

        # ==========================================
        # 1. БАЗОВІ ВІДОМОСТІ (Кадастр, Площа, Розташування)
        # ==========================================
        c1, c2 = st.columns(2)
        c1.text_input("Кадастровий номер (Автоматично)", value=cadastral_number, disabled=True)
        area_input = c2.text_input(
            "Площа (га)",
            value=format_area(get_saved_val(existing_audit, "area", get_db_val(db_data, 'area_drrp', get_db_val(db_data, 'area_dzk'))))
        )
        result["area"] = clean_numeric(area_input) # Одразу чистимо число!

        result["location"] = st.text_input(
            "Місце розташування",
            value=str(get_saved_val(existing_audit, "location", f"{get_db_val(db_data, 'region')} обл., {get_db_val(db_data, 'district')} р-н, {get_db_val(db_data, 'village_council')} с/р"))
        )

        # ==========================================
        # 2. ПРИЗНАЧЕННЯ ТА УГІДДЯ
        # ==========================================
        c3, c4 = st.columns(2)
        result["purpose"] = c3.text_input(
            "Цільове призначення",
            value=str(get_saved_val(existing_audit, "purpose", get_db_val(db_data, 'purpose_normalized')))
        )

        land_opts = ["Рілля", "Сіножаті", "Пасовища", "Багаторічні насадження"]
        saved_land = str(get_saved_val(existing_audit, "land_type", "Рілля"))
        result["land_type"] = c4.selectbox(
            "Вид угідь",
            land_opts,
            index=land_opts.index(saved_land) if saved_land in land_opts else 0
        )

        # ==========================================
        # 3. ІНШЕ ТА СПЕЦИФІЧНІ ПОЛЯ
        # ==========================================
        c5, c6 = st.columns(2)
        result["parcel_other_notes"] = c5.text_input(
            "Інше (Ділянка)",
            value=str(get_saved_val(existing_audit, "parcel_other_notes", ""))
        )

        # Агрохім паспорт тільки для ОМС
        if counterparty_type == "ОМС":
            result["has_agrochemical_passport"] = c6.checkbox(
                "Наявність агрохім паспорту",
                value=bool(get_saved_val(existing_audit, "has_agrochemical_passport", False))
            )

    return result
