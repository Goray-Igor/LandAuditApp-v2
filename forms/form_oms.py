import streamlit as st

# Імпортуємо функції для роботи з БД
from core.database import check_existing_audit, save_audit_lease, update_audit_lease
from form_blocks.group_agreements import render_group_agreements

# Імпортуємо наші універсальні "цеглинки" (групи)
from form_blocks.group_documents import render_group_documents
from form_blocks.group_legal import render_group_legal
from form_blocks.group_parcel import render_group_parcel
from form_blocks.group_rent import render_group_rent
from form_blocks.group_requisites import render_group_requisites

# Імпортуємо універсальний блок кнопок
from ui.form_actions import render_form_actions


def render_form_oms(cadastral_number, db_data, contract_type, counterparty_type):

    # ПЕРЕВІРКА ДУБЛІВ
    existing_audit = check_existing_audit(cadastral_number, contract_type, counterparty_type)
    if existing_audit:
        st.error("⛔ **УВАГА! Цей договір вже внесено в базу!** Зверніться до Адміністратора. Нижче відображено вже занесені дані.")
    else:
        st.success(f"🏛️ Завантажено шаблон: {contract_type} ({counterparty_type})")

    # ==========================================
    # ВИКЛИК УНІВЕРСАЛЬНИХ БЛОКІВ (ГРУП)
    # ==========================================
    data_group_0 = render_group_documents(existing_audit, contract_type, counterparty_type)
    data_group_1 = render_group_requisites(cadastral_number, db_data, existing_audit, contract_type, counterparty_type)
    data_group_2 = render_group_parcel(cadastral_number, db_data, existing_audit, contract_type, counterparty_type)
    data_group_3 = render_group_rent(db_data, existing_audit, contract_type, counterparty_type)
    data_group_4 = render_group_legal(existing_audit, contract_type, counterparty_type, data_group_0) # Передаємо data_group_0!

    # Група 5 (Додаткові угоди)
    agreements_to_save = render_group_agreements(cadastral_number, existing_audit, contract_type, counterparty_type)

    # ==========================================
    # ЗБІР ДАНИХ ТА КНОПКИ ЗБЕРЕЖЕННЯ
    # ==========================================
    st.write("---")

    audit_data = {
        "cadastral_number": cadastral_number,
        "contract_type": contract_type,
        "counterparty_type": counterparty_type,
        "auditor_code": st.session_state.get('current_auditor', '').strip(),

        **data_group_0,
        **data_group_1,
        **data_group_2,
        **data_group_3,
        **data_group_4
    }

    # ВИКЛИК УНІВЕРСАЛЬНОГО БЛОКУ КНОПОК
    render_form_actions(
        cadastral_number=cadastral_number,
        existing_audit=existing_audit,
        audit_data=audit_data,
        agreements_to_save=agreements_to_save,
        save_func=save_audit_lease,
        update_func=update_audit_lease
    )
