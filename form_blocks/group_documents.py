import streamlit as st

from core.utils import get_saved_val


def render_group_documents(existing_audit, contract_type, counterparty_type):
    """
    Малює Групу 0 (Наявність документів).
    Адаптується під тип договору та контрагента.
    Додано: Форма документа (1-10).
    """
    result = {}
    
    with st.expander("📁 Група 0: Наявність документів", expanded=True):
        
        # ==========================================
        # 0. ФОРМА ДОКУМЕНТА
        # ==========================================
        form_opts = [f"Форма {i}" for i in range(1, 11)]
        saved_form = str(get_saved_val(existing_audit, "document_form", "Форма 1"))
        result["document_form"] = st.selectbox("Форма договору", form_opts, index=form_opts.index(saved_form) if saved_form in form_opts else 0)
        
        st.write("---")
        
        # ==========================================
        # 1. БАЗОВІ ПОЛЯ (Залежать від контрагента)
        # ==========================================
        if counterparty_type == "Фізична":
            c1, c2, c3, c4 = st.columns(4)
            result["has_original_contract"] = c1.checkbox("Оригінал договору", value=bool(get_saved_val(existing_audit, "has_original_contract", True)))
            result["has_passport_copy"] = c2.checkbox("Копія Паспорта", value=bool(get_saved_val(existing_audit, "has_passport_copy", True)))
            result["has_inn_copy"] = c3.checkbox("Копія ІПН", value=bool(get_saved_val(existing_audit, "has_inn_copy", True)))
            result["has_title_deed_copy"] = c4.checkbox("Копія правоустановчих док.", value=bool(get_saved_val(existing_audit, "has_title_deed_copy", True)))
            
            result["other_docs_notes"] = st.text_input("Інше (перерахуйте через кому, якщо є)", value=str(get_saved_val(existing_audit, "other_docs_notes", "")))
            
        elif counterparty_type == "Юридична":
            c1, c2, c3 = st.columns(3)
            result["has_original_contract"] = c1.checkbox("Оригінал договору", value=bool(get_saved_val(existing_audit, "has_original_contract", True)))
            result["has_title_deed_copy"] = c2.checkbox("Копія правоустановчих док.", value=bool(get_saved_val(existing_audit, "has_title_deed_copy", True)))
            result["has_edr_extract"] = c3.checkbox("Витяг(Виписка) з ЄДР", value=bool(get_saved_val(existing_audit, "has_edr_extract", True)))
            
        elif counterparty_type == "ОМС":
            c_check, c_select = st.columns([1, 3])
            result["has_original_contract"] = c_check.checkbox("Оригінал договору", value=bool(get_saved_val(existing_audit, "has_original_contract", True)))
            
            doc_opts = ["Рішення сесії", "Протокол", "Розпорядження РДА", "Наказ головного Управління Держгеокадастру", "Документ відсутній"]
            saved_doc = str(get_saved_val(existing_audit, "document_type", doc_opts[0]))
            result["document_type"] = c_select.selectbox("Документ", doc_opts, index=doc_opts.index(saved_doc) if saved_doc in doc_opts else 0)
            
            result["other_docs_notes"] = st.text_input("Інше (текстове поле)", value=str(get_saved_val(existing_audit, "other_docs_notes", "")))

        # ==========================================
        # 2. ДОДАТКОВІ ПОЛЯ (Залежать від типу договору)
        # ==========================================
        if contract_type == "Суборенда":
            st.write("---") 
            c_sub1, c_sub2 = st.columns(2)
            
            sub_opts = ["Віддана", "Прийнята"]
            saved_sub = str(get_saved_val(existing_audit, "sublease_type", sub_opts[0]))
            result["sublease_type"] = c_sub1.selectbox("Тип суборенди", sub_opts, index=sub_opts.index(saved_sub) if saved_sub in sub_opts else 0)
            
            result["sublease_permission"] = c_sub2.checkbox("Дозвіл для суборенди", value=bool(get_saved_val(existing_audit, "sublease_permission", True)))

        elif contract_type == "Емфітевзис":
            st.write("---")
            c_emf1, c_emf2 = st.columns(2)
            result["is_notarized"] = c_emf1.checkbox("Нотаріально посвідчений", value=bool(get_saved_val(existing_audit, "is_notarized", False)))
            result["has_power_of_attorney"] = c_emf2.checkbox("Наявність довіреності/Заповіт", value=bool(get_saved_val(existing_audit, "has_power_of_attorney", False)))

    return result