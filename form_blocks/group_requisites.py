import datetime

import streamlit as st

from core.database import (
    get_dkp_number_by_cadastral,
    get_ipn_by_cadastral,
    get_previous_lessees_by_cadastral,
)
from core.utils import (
    extract_years,
    get_calculated_reg_date,
    get_db_val,
    get_owner_name,
    get_saved_val,
    parse_to_date,
)

PREVIOUS_LESSEE_OPTIONS = ["ПСП ПЕРЕМОГА", "ПСП МИР", "ПСП ім. ВАТУТІНА", "ПСП ім. АРТЕМОНОВА"]
PREV_LESSEE_EMPTY = "— не вказано —"
PREV_LESSEE_CUSTOM = "Інший (вказати вручну)"


def render_previous_lessee(cadastral_number, current_value):
    """Випадаючий список 'Попередній орендар' + ручне введення. Повертає рядок ('' якщо не вказано)."""
    options = [PREV_LESSEE_EMPTY, *PREVIOUS_LESSEE_OPTIONS, PREV_LESSEE_CUSTOM]
    current = str(current_value or "").strip()

    custom_text = ""
    if not current:
        idx = 0
    else:
        # порівнюємо без урахування регістру, щоб 'псп мир' з бази збігся зі списком
        match = next((o for o in PREVIOUS_LESSEE_OPTIONS if o.casefold() == current.casefold()), None)
        if match:
            idx = options.index(match)
        else:
            idx = len(options) - 1
            custom_text = current

    choice = st.selectbox("Попередній орендар", options, index=idx, key=f"prev_lessee_sel_{cadastral_number}")
    if choice == PREV_LESSEE_CUSTOM:
        return st.text_input(
            "Назва попереднього орендаря", value=custom_text, key=f"prev_lessee_txt_{cadastral_number}"
        ).strip()
    if choice == PREV_LESSEE_EMPTY:
        return ""
    return choice

def clean_float_string(val):
    if not val or str(val).strip().lower() in ["nan", "none", "", "інформація відсутня"]:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        return val_str[:-2]
    return val_str

def get_db_code(db_data):
    if not db_data: return ""
    code = db_data.get('owner_code_drrp')
    if not code or str(code).strip().lower() in ["nan", "none", "", "інформація відсутня"]:
        code = db_data.get('owner_code_dzk')
    return clean_float_string(code)

def get_lease_reg_num(db_data):
    if not db_data: return ""
    reg_num = db_data.get('usage_reg_number_drrp')
    if not reg_num or str(reg_num).strip().lower() in ["nan", "none", "", "інформація відсутня"]:
        reg_num = db_data.get('usage_reg_number_dzk')
    return clean_float_string(reg_num)

def safe_date(val):
    if not val or str(val).strip().lower() in ["nan", "none", "nat", ""]:
        return None
    return parse_to_date(val)


def render_group_requisites(cadastral_number, db_data, existing_audit, contract_type, counterparty_type):
    result = {}
    is_edit_mode = bool(existing_audit)

    # Розширюємо дозволений діапазон дат: з 1990 до 2100 року
    MIN_DATE = datetime.date(1990, 1, 1)
    MAX_DATE = datetime.date(2100, 12, 31)

    def get_val(key, db_fallback=""):
        if is_edit_mode:
            val = existing_audit.get(key)
            return val if val is not None else ""
        return db_fallback

    def manage_date_state(field_name, default_value):
        """Повертає (значення за замовчуванням, ключ віджета).
        Стан віджета зберігає сам Streamlit за key — вручну в session_state не пишемо,
        інакше з'являється попередження 'created with a default value but also had its value set via Session State API'.
        """
        key = f"date_{field_name}_{cadastral_number}"
        return safe_date(default_value), key

    with st.expander("📋 Група 1: Реквізити договору", expanded=True):

        db_owner = get_owner_name(db_data)
        db_doc_num = clean_float_string(get_db_val(db_data, 'usage_doc_number'))
        db_lease_reg_num = get_lease_reg_num(db_data)
        db_dkp_num = get_dkp_number_by_cadastral(cadastral_number)
        db_prev_lessees = get_previous_lessees_by_cadastral(cadastral_number)
        db_prev_lessee = db_prev_lessees[0] if len(db_prev_lessees) == 1 else ""
        if len(db_prev_lessees) > 1 and not is_edit_mode:
            st.warning(f"⚠️ У DKP_reestr для цієї ділянки кілька різних орендарів: {' / '.join(db_prev_lessees)}. Оберіть вручну.")

        if counterparty_type == "Фізична":
            db_code = get_ipn_by_cadastral(cadastral_number)
            if not db_code: db_code = get_db_code(db_data)
        else:
            db_code = get_db_code(db_data)

        # 1. БАЗОВІ НОМЕРИ
        c_num1, c_num2, c_num3 = st.columns(3)
        result["contract_number"] = c_num1.text_input("Номер договору", value=str(get_val("contract_number", db_doc_num)))
        result["lease_reg_number"] = c_num2.text_input("Номер реєстрації оренди (з реєстру)", value=str(get_val("lease_reg_number", db_lease_reg_num)))
        result["dkp_contract_number"] = c_num3.text_input("Номер договору ДКП", value=str(get_val("dkp_contract_number", db_dkp_num)))
        result["previous_lessee"] = render_previous_lessee(cadastral_number, get_val("previous_lessee", db_prev_lessee))

        st.write("---")

        # 2. СТОРОНИ ДОГОВОРУ
        if contract_type == "Суборенда" and counterparty_type == "Фізична":
            c1, c2, c3 = st.columns([2, 2, 1])
            result["lessor_name"] = c1.text_input("ПІБ Суборендаря", value=str(get_val("lessor_name", "")))
            result["lessee_name"] = c2.text_input("ПІБ Орендаря", value=str(get_val("lessee_name", db_owner)))
            result["ipn_code"] = c3.text_input("ІПН", value=str(get_val("ipn_code", db_code)))
        elif counterparty_type == "Фізична":
            c1, c2 = st.columns([3, 1])
            label = "ПІБ Орендодавця" if contract_type == "Оренда" else "ПІБ Власника"
            result["lessor_name"] = c1.text_input(label, value=str(get_val("lessor_name", db_owner)))
            result["ipn_code"] = c2.text_input("ІПН", value=str(get_val("ipn_code", db_code)))
        else:
            c1, c2 = st.columns([3, 1])
            label = "Назва ОМС" if counterparty_type == "ОМС" else "Назва Юридичної особи"
            result["lessor_name"] = c1.text_input(label, value=str(get_val("lessor_name", db_owner)))
            result["edrpou_code"] = c2.text_input("Код ЄДРПОУ", value=str(get_val("edrpou_code", db_code)))

        # 3. ЗМІНА ВЛАСНИКА
        st.write("---")
        saved_owner_changed = existing_audit.get("owner_changed", False) if is_edit_mode else False
        result["owner_changed"] = st.checkbox("Зміна власника", value=bool(saved_owner_changed))

        is_ind = counterparty_type == "Фізична"
        if result["owner_changed"]:
            result["new_owner_name"] = st.text_input("Новий власник (ПІБ / Назва)", value=str(get_val("new_owner_name", "")))
            if is_ind:
                result["new_owner_ipn"] = st.text_input("ІПН нового власника", value=str(get_saved_val(existing_audit, "new_owner_ipn", "")))
                n1, n2, n3 = st.columns(3)
                result["new_owner_has_passport_copy"] = n1.checkbox("Копія паспорта нового власника", value=bool(get_saved_val(existing_audit, "new_owner_has_passport_copy", True)))
                result["new_owner_has_inn_copy"] = n2.checkbox("Копія ІПН нового власника", value=bool(get_saved_val(existing_audit, "new_owner_has_inn_copy", True)))
                result["new_owner_has_title_deed_copy"] = n3.checkbox("Копія правовстановлюючого документа нового власника", value=bool(get_saved_val(existing_audit, "new_owner_has_title_deed_copy", True)))
        else:
            result["new_owner_name"] = ""
            if is_ind:
                result["new_owner_ipn"] = ""
                result["new_owner_has_passport_copy"] = False
                result["new_owner_has_inn_copy"] = False
                result["new_owner_has_title_deed_copy"] = False

        st.write("---")

        # 4. ДАТИ ТА СТРОКИ
        c3, c4, c5 = st.columns(3)

        val_sign_date = existing_audit.get("sign_date") if is_edit_mode else get_db_val(db_data, 'usage_doc_date')
        v_sign, k_sign = manage_date_state("sign", val_sign_date)
        result["sign_date"] = c3.date_input("Дата підписання", value=v_sign, min_value=MIN_DATE, max_value=MAX_DATE, key=k_sign, format="DD.MM.YYYY")

        val_reg_date = existing_audit.get("reg_date_property_right") if is_edit_mode else get_calculated_reg_date(cadastral_number, db_data)
        v_reg, k_reg = manage_date_state("reg", val_reg_date)
        result["reg_date_property_right"] = c4.date_input("Дата реєстрації права", value=v_reg, min_value=MIN_DATE, max_value=MAX_DATE, key=k_reg, format="DD.MM.YYYY")

        entry_opts = [
            "З моменту підписання",
            "З моменту реєстрації права",
            "З моменту реєстрації договору",
            "з дати підписання та державної реєстрації договору"
        ]
        saved_entry = str(get_val("entry_into_force_type", "З моменту підписання"))
        result["entry_into_force_type"] = c5.selectbox("Тип набуття чинності", entry_opts, index=entry_opts.index(saved_entry) if saved_entry in entry_opts else 0)

        c6, c7, c8 = st.columns(3)
        validity_term = c6.text_input("Строк дії (роки)", value=str(get_val("validity_term", get_db_val(db_data, 'usage_term'))))
        result["validity_term"] = extract_years(validity_term)

        val_end_date = existing_audit.get("end_date") if is_edit_mode else get_db_val(db_data, 'usage_end_date_calculated')
        v_end, k_end = manage_date_state("end", val_end_date)
        result["end_date"] = c7.date_input("Дата закінчення", value=v_end, min_value=MIN_DATE, max_value=MAX_DATE, key=k_end, format="DD.MM.YYYY")

        val_auditor_end = existing_audit.get("auditor_end_date") if is_edit_mode else None
        v_aend, k_aend = manage_date_state("aud_end", val_auditor_end)
        result["auditor_end_date"] = c8.date_input("Дата закінчення (Аудитор)", value=v_aend, min_value=MIN_DATE, max_value=MAX_DATE, key=k_aend, format="DD.MM.YYYY")

    return result
