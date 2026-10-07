import streamlit as st
from core.utils import parse_to_date, extract_years
from core.database import get_additional_agreements
import datetime
def render_group_agreements(cadastral_number, existing_audit, contract_type, counterparty_type):
    """
    Малює блок додаткових угод та повертає список угод для збереження.
    Відновлено динамічну логіку полів + додано вибір Форми (1-10).
    """
    MIN_DATE = datetime.date(1990, 1, 1)
    MAX_DATE = datetime.date(2100, 12, 31)
    agreements_key = f"agreements_{cadastral_number}"
    
    if agreements_key not in st.session_state:
        if existing_audit:
            st.session_state[agreements_key] = get_additional_agreements(cadastral_number, contract_type, counterparty_type)
        else:
            st.session_state[agreements_key] = []

    with st.expander(f"📝 Група 5: Додаткові угоди ({len(st.session_state[agreements_key])})", expanded=True):
        
        for i, agr in enumerate(st.session_state[agreements_key]):
            st.markdown(f"**📄 Додаткова угода #{i+1}**")
            
            # Ставимо Тип та Форму в один рядок для краси
            c_type, c_form = st.columns(2)
            
            # --- 1. ТИП УГОДИ ---
            agr_opts = ["Заміна сторони", "Продовження терміну ДОЗ", "Зміна умов", "Розірвання"]
            saved_agr_type = str(agr.get("agreement_type", "Заміна сторони"))
            a_idx = agr_opts.index(saved_agr_type) if saved_agr_type in agr_opts else 0
            
            agr_type = c_type.selectbox("Тип додаткової угоди", agr_opts, index=a_idx, key=f"agr_t_{cadastral_number}_{i}")
            agr["agreement_type"] = agr_type

            # --- 2. ФОРМА УГОДИ (Нове поле) ---
            form_opts = [f"Форма {j}" for j in range(1, 11)]
            saved_agr_form = str(agr.get("agreement_form", "Форма 1"))
            f_idx = form_opts.index(saved_agr_form) if saved_agr_form in form_opts else 0
            
            agr_form = c_form.selectbox("Форма додаткової угоди", form_opts, index=f_idx, key=f"agr_f_{cadastral_number}_{i}")
            agr["agreement_form"] = agr_form

            # --- ДИНАМІЧНІ ПОЛЯ ЗАЛЕЖНО ВІД ТИПУ ---
            if agr_type in ["Заміна сторони", "Продовження терміну ДОЗ"]:
                c1, c2 = st.columns(2)
                agr["sign_date"] = c1.date_input("Дата підписання", value=parse_to_date(agr.get("sign_date")),  min_value=MIN_DATE, max_value=MAX_DATE, format="DD.MM.YYYY", key=f"agr_sd_{cadastral_number}_{i}")
                agr["reg_date_property_right"] = c2.date_input("Дата реєстрації права", value=parse_to_date(agr.get("reg_date_property_right")), min_value=MIN_DATE, max_value=MAX_DATE, format="DD.MM.YYYY", key=f"agr_reg_{cadastral_number}_{i}")
                
                # --- ЛОГІКА ДЛЯ РІЗНИХ КОНТРАГЕНТІВ ---
                if counterparty_type == "Фізична":
                    agr["lessor_name"] = st.text_input("ПІБ", value=agr.get("lessor_name", ""), key=f"agr_n_{cadastral_number}_{i}")
                else:
                    col_n, col_edr = st.columns([3, 1])
                    agr["lessor_name"] = col_n.text_input("Назва компанії", value=agr.get("lessor_name", ""), key=f"agr_n_{cadastral_number}_{i}")
                    agr["edrpou_code"] = col_edr.text_input("ЄДРПОУ", value=agr.get("edrpou_code", ""), key=f"agr_edr_{cadastral_number}_{i}")
                
                c3, c4 = st.columns(2)
                agr["validity_term"] = extract_years(c3.text_input("Строк дії (роки)", value=str(agr.get("validity_term", "")), key=f"agr_vt_{cadastral_number}_{i}"))
                agr["end_date"] = c4.date_input("Дата закінчення", value=parse_to_date(agr.get("end_date")), min_value=MIN_DATE, max_value=MAX_DATE, format="DD.MM.YYYY", key=f"agr_ed_{cadastral_number}_{i}")
                
                agr["has_title_deed_copy"] = st.checkbox("Копія правостановчих документів", value=bool(agr.get("has_title_deed_copy", True)), key=f"agr_td_{cadastral_number}_{i}")
                agr["other_docs_notes"] = st.text_input("Інше (текст)", value=agr.get("other_docs_notes", ""), key=f"agr_o_{cadastral_number}_{i}")
                
                st.write("*Юридичні реквізити:*")
                agr["restriction_type"] = st.text_input("Тип обмеження", value=agr.get("restriction_type", "Відсутні"), key=f"agr_res_{cadastral_number}_{i}")
                c5, c6 = st.columns(2)
                
                # Адаптація назви для Емфітевзису
                sublease_label = "Передача в Оренду" if contract_type == "Емфітевзис" else "Передача в Суборенду"
                agr["sublease_allowed"] = c5.checkbox(sublease_label, value=bool(agr.get("sublease_allowed", True)), key=f"agr_sub_{cadastral_number}_{i}")
                
                agr["unilateral_termination_allowed"] = c6.checkbox("Розірвання в односторонньому порядку", value=bool(agr.get("unilateral_termination_allowed", False)), key=f"agr_uni_{cadastral_number}_{i}")
                agr["reorg_transfer_does_not_terminate"] = st.checkbox("Реорганізація не припиняє договір", value=bool(agr.get("reorg_transfer_does_not_terminate", True)), key=f"agr_reo_{cadastral_number}_{i}")
                
                c7, c8 = st.columns(2)
                agr["has_lessor_signature"] = c7.checkbox("Підпис Орендодавця", value=bool(agr.get("has_lessor_signature", True)), key=f"agr_sl_{cadastral_number}_{i}")
                agr["has_lessee_signature"] = c8.checkbox("Підпис Орендаря", value=bool(agr.get("has_lessee_signature", True)), key=f"agr_sles_{cadastral_number}_{i}")
                
                # --- ПЕЧАТКИ ДЛЯ РІЗНИХ КОНТРАГЕНТІВ ---
                if counterparty_type == "Фізична":
                    agr["has_stamps"] = st.checkbox("Печатки", value=bool(agr.get("has_stamps", True)), key=f"agr_st_{cadastral_number}_{i}")
                else:
                    c9, c10 = st.columns(2)
                    agr["has_lessor_stamps"] = c9.checkbox("Печатки Орендодавця", value=bool(agr.get("has_lessor_stamps", True)), key=f"agr_stl_{cadastral_number}_{i}")
                    agr["has_lessee_stamps"] = c10.checkbox("Печатки Орендаря", value=bool(agr.get("has_lessee_stamps", True)), key=f"agr_stle_{cadastral_number}_{i}")
                
                agr["auto_prolongation_date"] = st.date_input("Автопролонгація з", value=parse_to_date(agr.get("auto_prolongation_date")),min_value=MIN_DATE, max_value=MAX_DATE, format="DD.MM.YYYY", key=f"agr_ap_{cadastral_number}_{i}")
                agr["auditor_comments"] = st.text_area("Примітки", value=agr.get("auditor_comments", ""), key=f"agr_com_{cadastral_number}_{i}")

            elif agr_type == "Зміна умов":
                agr["sign_date"] = st.date_input("Дата підписання", value=parse_to_date(agr.get("sign_date")), format="DD.MM.YYYY", key=f"agr_sd2_{cadastral_number}_{i}")
                agr["has_signatures"] = st.checkbox("Наявність Підписів", value=bool(agr.get("has_signatures", True)), key=f"agr_sig_{cadastral_number}_{i}")
                agr["other_docs_notes"] = st.text_input("Інше (текст)", value=agr.get("other_docs_notes", ""), key=f"agr_oth2_{cadastral_number}_{i}")
                
            elif agr_type == "Розірвання":
                agr["termination_protocol_date"] = st.date_input("Дата протоколу", value=parse_to_date(agr.get("termination_protocol_date")), min_value=MIN_DATE, max_value=MAX_DATE, format="DD.MM.YYYY", key=f"agr_tp_{cadastral_number}_{i}")
                agr["other_docs_notes"] = st.text_input("Інше (текст)", value=agr.get("other_docs_notes", ""), key=f"agr_oth3_{cadastral_number}_{i}")

            if st.button(f"🗑️ Видалити угоду #{i+1}", key=f"del_agr_{cadastral_number}_{i}"):
                st.session_state[agreements_key].pop(i)
                st.rerun()
            
            st.write("---")

        if st.button("➕ ДОДАТИ ДОДАТКОВУ УГОДУ", width="stretch"):
            # За замовчуванням ставимо Форму 1 при створенні нової угоди
            st.session_state[agreements_key].append({"agreement_type": "Заміна сторони", "agreement_form": "Форма 1"})
            st.rerun()

    return st.session_state[agreements_key]