import datetime

import streamlit as st

from core.utils import get_saved_val, parse_to_date


def render_group_legal(existing_audit, contract_type, counterparty_type, data_group_0):
    """
    Малює Групу 4 (Юридичний блок).
    Приймає data_group_0 для перевірки наявності паспорта.
    Динамічно ховає поля "Відповідність", якщо немає підпису або паспорта.
    """
    MIN_DATE = datetime.date(1990, 1, 1)
    MAX_DATE = datetime.date(2100, 12, 31)
    result = {}

    # Дістаємо інформацію про паспорт з Групи 0 (якщо ключа немає, за замовчуванням False)
    has_passport = data_group_0.get("has_passport_copy", False)

    with st.expander("⚖️ Група 4: Юридичний блок", expanded=True):

        result["restriction_type"] = st.text_input("Тип обмеження", value=str(get_saved_val(existing_audit, "restriction_type", "Відсутні")))

        c1, c2, c3 = st.columns(3)
        sublease_label = "Передача в Оренду" if contract_type == "Емфітевзис" else "Передача в Суборенду"
        result["sublease_allowed"] = c1.checkbox(sublease_label, value=bool(get_saved_val(existing_audit, "sublease_allowed", True)))
        result["reorg_transfer_does_not_terminate"] = c2.checkbox("Реорганізація не припиняє договір", value=bool(get_saved_val(existing_audit, "reorg_transfer_does_not_terminate", True)))
        result["unilateral_termination_allowed"] = c3.checkbox("Розірвання в односторонньому порядку", value=bool(get_saved_val(existing_audit, "unilateral_termination_allowed", False)))

        st.write("---")
        st.write("**Підписи та Печатки на документі:**")

        c_sig_1, c_sig_2 = st.columns(2)
        result["has_lessor_signature"] = c_sig_1.checkbox("Наявність підпису Орендодавця (Власника)", value=bool(get_saved_val(existing_audit, "has_lessor_signature", True)))
        result["has_lessee_signature"] = c_sig_2.checkbox("Наявність підпису Орендаря (Користувача)", value=bool(get_saved_val(existing_audit, "has_lessee_signature", True)))

        if counterparty_type == "Фізична":
            st.write("---")
            c_match_1, c_match_2 = st.columns(2)

            # --- ЛОГІЧНІ ЕЛЕМЕНТИ (Відновлено!) ---

            # 1. Відповідність Орендодавця (Потрібен ПАСПОРТ + ПІДПИС)
            if has_passport and result["has_lessor_signature"]:
                result["signature_matches_lessor"] = c_match_1.checkbox("Відповідність підпису (Орендодавець/Власник)", value=bool(get_saved_val(existing_audit, "signature_matches_lessor", True)))
            else:
                result["signature_matches_lessor"] = False # Якщо умов немає, жорстко пишемо False в базу

            # 2. Відповідність Орендаря (Потрібен лише ПІДПИС)
            if result["has_lessee_signature"]:
                result["signature_matches_lessee"] = c_match_2.checkbox("Відповідність підпису (Орендар/Користувач)", value=bool(get_saved_val(existing_audit, "signature_matches_lessee", True)))
            else:
                result["signature_matches_lessee"] = False

            # Печатка
            result["has_stamps"] = st.checkbox("Наявність печаток", value=bool(get_saved_val(existing_audit, "has_stamps", True)))

        else:
            st.write("---")
            c_stamp_1, c_stamp_2 = st.columns(2)
            result["has_lessor_stamps"] = c_stamp_1.checkbox("Наявність печаток Орендодавця", value=bool(get_saved_val(existing_audit, "has_lessor_stamps", True)))
            result["has_lessee_stamps"] = c_stamp_2.checkbox("Наявність печаток Орендаря", value=bool(get_saved_val(existing_audit, "has_lessee_stamps", True)))

        st.write("---")
        result["auto_prolongation_date"] = st.date_input("Автопролонгація з", value=parse_to_date(get_saved_val(existing_audit, "auto_prolongation_date", None)),min_value=MIN_DATE, max_value=MAX_DATE , format="DD.MM.YYYY")
        result["auditor_comments"] = st.text_area("Примітки аудитора", value=str(get_saved_val(existing_audit, "auditor_comments", "")))

    return result
