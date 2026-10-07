import os

import streamlit as st


def render_form_actions(cadastral_number, existing_audit, audit_data, agreements_to_save, save_func, update_func):
    """
    Універсальний блок кнопок збереження/оновлення.
    Приймає дані з будь-якої форми і відповідні функції для роботи з БД.
    """
    admin_password_correct = os.getenv("ADMIN_PASSWORD", "12345")

    edit_key = f"edit_mode_{cadastral_number}"
    confirm_save_key = f"confirm_save_{cadastral_number}"
    confirm_update_key = f"confirm_update_{cadastral_number}"

    if edit_key not in st.session_state: st.session_state[edit_key] = False
    if confirm_save_key not in st.session_state: st.session_state[confirm_save_key] = False
    if confirm_update_key not in st.session_state: st.session_state[confirm_update_key] = False

    if existing_audit:
        if not st.session_state[edit_key]:
            st.warning("🔒 Цей договір вже перевірено і заблоковано. Для внесення правок потрібен пароль.")
            col_pass, col_btn = st.columns([2, 1])
            edit_password = col_pass.text_input("🔑 Пароль адміністратора", type="password", key=f"pass_{cadastral_number}")
            col_btn.write(""); col_btn.write("")
            if col_btn.button("🔓 РОЗБЛОКУВАТИ", width="stretch"):
                if edit_password == admin_password_correct:
                    st.session_state[edit_key] = True
                    st.rerun()
                else:
                    st.error("❌ Невірний пароль! Зверніться до керівника.")
        else:
            st.info("🔓 Режим редагування увімкнено. Уважно перевірте зміни перед збереженням.")
            if not st.session_state[confirm_update_key]:
                if st.button("📝 ОНОВИТИ ДАНІ В БАЗІ", width="stretch", type="primary"):
                    st.session_state[confirm_update_key] = True
                    st.rerun()
            else:
                st.warning("❓ Ви впевнені, що хочете ПЕРЕЗАПИСАТИ ці дані в базі?")
                col_yes, col_no = st.columns(2)
                if col_yes.button("✅ ТАК, ОНОВИТИ", width="stretch", type="primary"):
                    with st.spinner("Оновлюємо дані..."):
                        # Викликаємо передану функцію оновлення
                        success = update_func(audit_data, agreements_to_save)
                    if success:
                        st.success(f"✅ Дані по ділянці {cadastral_number} успішно оновлено!")
                        st.session_state[edit_key] = False
                        st.session_state[confirm_update_key] = False
                        st.balloons()
                    else: st.error("❌ Помилка при оновленні.")
                if col_no.button("❌ СКАСУВАТИ", width="stretch"):
                    st.session_state[confirm_update_key] = False
                    st.rerun()
    else:
        if not st.session_state[confirm_save_key]:
            if st.button("💾 ЗБЕРЕГТИ ДАНІ АУДИТУ", width="stretch", type="primary"):
                st.session_state[confirm_save_key] = True
                st.rerun()
        else:
            st.warning("❓ Ви впевнені, що хочете ЗБЕРЕГТИ ці дані в базу?")
            col_yes, col_no = st.columns(2)
            if col_yes.button("✅ ТАК, ЗБЕРЕГТИ", width="stretch", type="primary"):
                with st.spinner("Зберігаємо дані в базу..."):
                    # Викликаємо передану функцію збереження
                    success = save_func(audit_data, agreements_to_save)
                if success:
                    st.success(f"✅ Дані по ділянці {cadastral_number} успішно збережено в SQL!")
                    st.session_state[confirm_save_key] = False
                    st.balloons()
                else: st.error("❌ Сталася помилка при збереженні.")
            if col_no.button("❌ СКАСУВАТИ", width="stretch"):
                st.session_state[confirm_save_key] = False
                st.rerun()
