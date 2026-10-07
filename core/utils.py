import datetime
import re

import pandas as pd
from sqlalchemy import text

from core.database import get_engine
from core.logger import get_logger

logger = get_logger(__name__)


def clean_numeric(val):
    """Очищення чисел: заміна коми на крапку та видалення пробілів."""
    if val is None or str(val).strip() in ["", "-", "None"]: return 0.0
    try: return float(str(val).replace(',', '.').replace(' ', '').strip())
    except (ValueError, TypeError):
        return 0.0

def extract_years(text_val):
    """Витягує лише цифри з тексту (наприклад, '15 років' -> '15')."""
    if not text_val: return "0"
    match = re.search(r'\d+', str(text_val))
    return match.group() if match else "0"

def parse_to_date(date_str):
    """Гнучкий парсинг дат з різних форматів."""
    if pd.isna(date_str) or not date_str or str(date_str).strip() in ["", "None", "nan", "-"]: return None
    if isinstance(date_str, (datetime.date, datetime.datetime, pd.Timestamp)):
        return date_str.date() if isinstance(date_str, datetime.datetime) else date_str
    s = str(date_str).strip().split(" ")[0]
    try:
        if "." in s: return datetime.datetime.strptime(s, "%d.%m.%Y").date()
        elif "-" in s: return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None
    return None

def format_area(val):
    """Примусове форматування площі до 4 знаків після коми."""
    if val is None or pd.isna(val) or str(val).strip() in ["", "None", "nan", "-"]: return ""
    try:
        return f"{float(str(val).replace(',', '.').replace(' ', '')):.4f}"
    except (ValueError, TypeError):
        return str(val).strip()

def get_calculated_reg_date(cadastral_number, db_data):
    """Вираховує дату реєстрації права з реєстрів."""
    engine = get_engine()
    query = text("SELECT usage_right_type, usage_reg_date_drrp, usage_reg_date_dzk FROM Usage_Rights_reestr WHERE cadastral_number = :cad_num")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"cad_num": cadastral_number})
        if len(df) > 1:
            mask = ~df['usage_right_type'].astype(str).str.lower().str.contains('суборенди', na=False)
            main_rights = df[mask]
            if not main_rights.empty:
                row = main_rights.iloc[0]
                drrp = row.get('usage_reg_date_drrp'); dzk = row.get('usage_reg_date_dzk')
                if pd.notna(drrp) and str(drrp).strip() not in ["", "None", "nan", "-"]: return parse_to_date(drrp)
                return parse_to_date(dzk)
        drrp = db_data.get('usage_reg_date_drrp'); dzk = db_data.get('usage_reg_date_dzk')
        if pd.notna(drrp) and str(drrp).strip() not in ["", "None", "nan", "-"]: return parse_to_date(drrp)
        return parse_to_date(dzk)
    except Exception:
        logger.exception("Помилка розрахунку дати реєстрації права: %s", cadastral_number)
        return None

def get_saved_val(existing_audit, audit_key, default_val):
    """Безпечно дістає збережене значення з бази аудиту, якщо воно є."""
    if existing_audit and audit_key in existing_audit:
        val = existing_audit[audit_key]
        if pd.notna(val):
            return val
    return default_val

def get_db_val(db_data, key, default=""):
    """Безпечно дістає значення з реєстрів (блакитний блок)."""
    if not db_data:
        return default
    val = db_data.get(key)
    return str(val).strip() if pd.notna(val) and str(val).strip() not in ["None", "nan", ""] else default

def get_owner_name(db_data):
    """
    Выбирает имя владельца: приоритет owner_drrp, если пусто — owner_dzk.
    """
    if not db_data:
        return ""

    # Сначала пробуем РРП
    owner = db_data.get('owner_drrp')

    # Если в РРП пусто или написано 'Інформація відсутня', берем ДЗК
    if not owner or str(owner).strip().lower() in ["nan", "none", "", "інформація відсутня"]:
        owner = db_data.get('owner_dzk')

    return str(owner).strip() if owner else ""
