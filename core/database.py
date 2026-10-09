import os
from functools import lru_cache

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from core.logger import get_logger

logger = get_logger(__name__)

# Завантажуємо змінні з файлу .env
load_dotenv()

# Отримуємо дані для підключення
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
EXTRA_CHECKS_TABLE = "Audit_Extra_Checks"
EXTRA_CHECK_FIELDS = (
    "area_discrepancy_title_vs_contract",
    "state_act_area_rounded_2dp",
    "lessee_alienation_with_notary_consent",
    "lessee_bears_destruction_risk",
)

@lru_cache(maxsize=1)
def get_engine():
    """Повертає єдиний на процес SQLAlchemy engine (з пулом підключень)."""
    required = {
        "DB_SERVER": DB_SERVER,
        "DB_DATABASE": DB_DATABASE,
        "DB_USERNAME": DB_USERNAME,
        "DB_PASSWORD": DB_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Не задано змінні оточення в .env: {', '.join(missing)}")

    # URL.create сам екранує спецсимволи в логіні/паролі
    url = URL.create(
        "mssql+pyodbc",
        username=DB_USERNAME,
        password=DB_PASSWORD,
        host=DB_SERVER,
        database=DB_DATABASE,
        query={"driver": "ODBC Driver 17 for SQL Server"},
    )
    return create_engine(
        url,
        fast_executemany=True,
        pool_pre_ping=True,   # перевіряє "мертві" підключення перед використанням
        pool_recycle=1800,    # оновлює підключення старше 30 хв
    )

def test_connection():
    """Тестує підключення до бази даних."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Виконуємо простий тестовий запит
            result = conn.execute(text("SELECT @@VERSION")).fetchone()
            print("✅ Підключення успішне!")
            print(f"🖥 Версія SQL Server: {result[0][:50]}...")
            return True
    except Exception as e:
        print("❌ Помилка підключення до бази даних:")
        print(e)
        logger.exception("Помилка підключення до БД")
        return False



def search_parcels(search_term):
    """Шукає ділянки за частиною кадастрового номера (наприклад, останні 4 цифри)."""
    engine = get_engine()

    # Використовуємо параметризований запит SQLAlchemy для безпеки
    query = text("""
    SELECT cadastral_number, district, village_council
    FROM Parcel_reestr
    WHERE cadastral_number LIKE :search
    """)

    try:
        # Додаємо % з обох боків, щоб шукати входження в будь-якому місці рядка
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"search": f"%{search_term}%"})
        return df
    except Exception as e:
        print(f"Помилка при пошуку ділянок: {e}")
        logger.exception("Помилка пошуку ділянок: term=%s", search_term)
        return pd.DataFrame()

def get_parcel_data(cadastral_number):
    """Отримує всі дані з реєстру для одного кадастрового номера."""
    engine = get_engine()
    query = text("SELECT * FROM Parcel_reestr WHERE cadastral_number = :cad_num")

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"cad_num": cadastral_number})

        # Якщо знайшли, повертаємо перший рядок як словник (dictionary)
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"Помилка при отриманні даних ділянки: {e}")
        logger.exception("Помилка отримання даних ділянки: %s", cadastral_number)
        return None

def get_sublease_data(cadastral_number):
    """Отримує дані ВИКЛЮЧНО про суборенду з таблиці Usage_Rights_reestr."""
    engine = get_engine()

    # Додали умову AND usage_right_type LIKE '%суборенди%'
    # Вона відфільтрує всі інші записи (наприклад, звичайну оренду), якщо вони потрапили в цю таблицю
    query = text("""
        SELECT * FROM Usage_Rights_reestr
        WHERE cadastral_number = :cad_num
        AND LOWER(usage_right_type) LIKE '%суборенди%'
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"cad_num": cadastral_number})

        # Якщо запис про суборенду знайдено, повертаємо його
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"Помилка при отриманні даних суборенди: {e}")
        logger.exception("Помилка отримання суборенди: %s", cadastral_number)
        return None

# ==========================================
# НОВІ ФУНКЦІЇ: ПЕРЕВІРКА ДУБЛІВ ТА ОНОВЛЕННЯ
# ==========================================

def get_target_table(contract_type, counterparty_type):
    """Повертає назву таблиці для основного договору."""
    tables = {
        ("Оренда", "Фізична"): "Audit_Lease_Individual",
        ("Оренда", "Юридична"): "Audit_Lease_Legal",
        ("Оренда", "ОМС"): "Audit_Lease_OMS",
        # ("Суборенда", "Фізична"): "Audit_Sublease_Individual", # Заготовка на майбутнє
    }
    return tables.get((contract_type, counterparty_type))

def get_agreements_table(contract_type, counterparty_type):
    """Повертає назву таблиці для ДОДАТКОВИХ УГОД."""
    tables = {
        ("Оренда", "Фізична"): "Audit_Additional_Agreements",
        ("Оренда", "Юридична"): "Audit_Additional_Agreements_Legal",
        ("Оренда", "ОМС"): "Audit_Additional_Agreements_OMS",
    }
    return tables.get((contract_type, counterparty_type))

def check_existing_audit(cadastral_number, contract_type, counterparty_type):
    table_name = get_target_table(contract_type, counterparty_type)
    if not table_name: return None

    engine = get_engine()
    query = text(f"SELECT * FROM {table_name} WHERE cadastral_number = :cad_num AND contract_type = :ct AND counterparty_type = :cpt")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"cad_num": cadastral_number, "ct": contract_type, "cpt": counterparty_type})
        if not df.empty:
            audit = df.iloc[0].to_dict()
            audit.update(get_extra_checks(cadastral_number, contract_type, counterparty_type))
            return audit
        return None
    except Exception as e:
        print(f"Помилка при перевірці дублів: {e}")
        logger.exception("Помилка перевірки дублів: %s/%s/%s", cadastral_number, contract_type, counterparty_type)
        return None

def get_extra_checks(cadastral_number, contract_type, counterparty_type):
    """Читає додаткові чекбокси (групи 2 і 4) з Audit_Extra_Checks."""
    engine = get_engine()
    query = text(
        f"SELECT {', '.join(EXTRA_CHECK_FIELDS)} FROM {EXTRA_CHECKS_TABLE} "
        "WHERE cadastral_number = :cad_num AND contract_type = :ct AND counterparty_type = :cpt"
    )
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"cad_num": cadastral_number, "ct": contract_type, "cpt": counterparty_type})
        return df.iloc[0].to_dict() if not df.empty else {}
    except Exception:
        logger.exception("Помилка читання додаткових чекбоксів: %s", cadastral_number)
        return {}

def get_additional_agreements(cadastral_number, contract_type, counterparty_type):
    table_name = get_agreements_table(contract_type, counterparty_type)
    if not table_name: return []

    engine = get_engine()
    query = text(f"SELECT * FROM {table_name} WHERE cadastral_number = :cad_num")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"cad_num": cadastral_number})
        return df.to_dict(orient='records') if not df.empty else []
    except Exception:
        logger.exception("Помилка читання додаткових угод: %s", cadastral_number)
        return []

def _insert_audit(conn, audit_data, agreements_list=None):
    """Вставляє основний договір і додаткові угоди через переданий connection (без власного commit)."""
    table_name = get_target_table(audit_data['contract_type'], audit_data['counterparty_type'])
    agr_table_name = get_agreements_table(audit_data['contract_type'], audit_data['counterparty_type'])
    if not table_name:
        raise ValueError(
            f"Не знайдено таблицю для {audit_data['contract_type']}/{audit_data['counterparty_type']}"
        )

    main_data = {k: v for k, v in audit_data.items() if k not in EXTRA_CHECK_FIELDS}
    df_main = pd.DataFrame([main_data])
    df_main['updated_at'] = pd.Timestamp.now()
    df_main = df_main.drop(columns=['id'], errors='ignore')
    df_main.to_sql(table_name, con=conn, if_exists='append', index=False)

    extra_row = {
        "cadastral_number": audit_data['cadastral_number'],
        "contract_type": audit_data['contract_type'],
        "counterparty_type": audit_data['counterparty_type'],
        "auditor_code": audit_data.get('auditor_code'),
        "updated_at": pd.Timestamp.now(),
        **{f: bool(audit_data.get(f, False)) for f in EXTRA_CHECK_FIELDS},
    }
    pd.DataFrame([extra_row]).to_sql(EXTRA_CHECKS_TABLE, con=conn, if_exists='append', index=False)

    if agreements_list and agr_table_name:
        df_agr = pd.DataFrame(agreements_list)
        df_agr['cadastral_number'] = audit_data['cadastral_number']
        df_agr['auditor_code'] = audit_data['auditor_code']
        df_agr['updated_at'] = pd.Timestamp.now()
        df_agr = df_agr.drop(columns=['id'], errors='ignore')
        df_agr.to_sql(agr_table_name, con=conn, if_exists='append', index=False)


def update_audit_lease(audit_data, agreements_list=None):
    table_name = get_target_table(audit_data['contract_type'], audit_data['counterparty_type'])
    agr_table_name = get_agreements_table(audit_data['contract_type'], audit_data['counterparty_type'])

    engine = get_engine()
    try:
        with engine.begin() as conn:  # DELETE + INSERT в одній транзакції
            conn.execute(
                text(f"DELETE FROM {table_name} WHERE cadastral_number = :cad_num AND contract_type = :ct AND counterparty_type = :cpt"),
                {"cad_num": audit_data['cadastral_number'], "ct": audit_data['contract_type'], "cpt": audit_data['counterparty_type']},
            )
            conn.execute(
                text(f"DELETE FROM {EXTRA_CHECKS_TABLE} WHERE cadastral_number = :cad_num AND contract_type = :ct AND counterparty_type = :cpt"),
                {"cad_num": audit_data['cadastral_number'], "ct": audit_data['contract_type'], "cpt": audit_data['counterparty_type']},
            )
            if agr_table_name:
                conn.execute(
                    text(f"DELETE FROM {agr_table_name} WHERE cadastral_number = :cad_num"),
                    {"cad_num": audit_data['cadastral_number']},
                )
            _insert_audit(conn, audit_data, agreements_list)

        # Лог пишемо тільки після успішного commit
        logger.info("Аудит оновлено: %s | %s/%s | аудитор=%s",
                    audit_data['cadastral_number'], audit_data['contract_type'],
                    audit_data['counterparty_type'], audit_data.get('auditor_code'))
        return True
    except Exception as e:
        print(f"Помилка при оновленні: {e}")
        logger.exception("Помилка оновлення аудиту: %s", audit_data.get('cadastral_number'))
        return False


def save_audit_lease(audit_data, agreements_list=None):
    engine = get_engine()
    try:
        with engine.begin() as conn:  # основний договір і допугоди: або все, або нічого
            _insert_audit(conn, audit_data, agreements_list)

        logger.info("Аудит збережено: %s | %s/%s | аудитор=%s",
                    audit_data['cadastral_number'], audit_data['contract_type'],
                    audit_data['counterparty_type'], audit_data.get('auditor_code'))
        return True
    except Exception as e:
        print(f"Помилка при збереженні: {e}")
        logger.exception("Помилка збереження аудиту: %s", audit_data.get('cadastral_number'))
        return False

def get_ipn_by_cadastral(cadastral_number):
    """Шукає всі ІПН в таблиці-довіднику IPN_reestr та з'єднує їх через '/' """
    engine = get_engine()
    # Убрали TOP 1, теперь ищем все совпадения
    query = text("SELECT ipn_code FROM IPN_reestr WHERE cadastral_number = :cad_num AND ipn_code IS NOT NULL")

    try:
        with engine.connect() as conn:
            # fetchall() возвращает список всех найденных строк
            results = conn.execute(query, {"cad_num": cadastral_number}).fetchall()

            if results:
                # Извлекаем ИНН из каждой строки и очищаем от пробелов
                ipns = [str(row[0]).strip() for row in results if row[0]]

                # Удаляем возможные дубликаты (оставляя уникальные ИНН), сохраняя порядок
                unique_ipns = list(dict.fromkeys(ipns))

                # Склеиваем список в одну строку через разделитель " / "
                return " / ".join(unique_ipns)

            return ""
    except Exception as e:
        print(f"Помилка пошуку ІПН: {e}")
        logger.exception("Помилка пошуку ІПН: %s", cadastral_number)
        return ""

def get_dkp_number_by_cadastral(cadastral_number):
    """Шукає номер договору ДКП в таблиці DKP_reestr та з'єднує їх через '/' """
    engine = get_engine()
    # Шукаємо всі записи ДКП для цього кадастрового
    query = text("SELECT dkp_contract_number FROM DKP_reestr WHERE cadastral_number = :cad_num AND dkp_contract_number IS NOT NULL")

    try:
        with engine.connect() as conn:
            results = conn.execute(query, {"cad_num": cadastral_number}).fetchall()

            if results:
                # Витягуємо номери, очищаємо від пробілів
                dkps = [str(row[0]).strip() for row in results if row[0]]
                # Видаляємо дублікати, зберігаючи порядок
                unique_dkps = list(dict.fromkeys(dkps))
                # Склеюємо через " / "
                return " / ".join(unique_dkps)

            return ""
    except Exception as e:
        print(f"Помилка пошуку ДКП: {e}")
        logger.exception("Помилка пошуку ДКП: %s", cadastral_number)
        return ""

def get_previous_lessees_by_cadastral(cadastral_number):
    """Повертає список унікальних 'Попередніх орендарів' з DKP_reestr для ділянки."""
    engine = get_engine()
    query = text("SELECT previous_lessee FROM DKP_reestr WHERE cadastral_number = :cad_num AND previous_lessee IS NOT NULL")
    try:
        with engine.connect() as conn:
            results = conn.execute(query, {"cad_num": cadastral_number}).fetchall()
        values = [str(row[0]).strip() for row in results if row[0] and str(row[0]).strip()]
        return list(dict.fromkeys(values))
    except Exception:
        logger.exception("Помилка пошуку попереднього орендаря: %s", cadastral_number)
        return []

# Цей блок виконається тільки якщо запустити саме цей файл (для перевірки)
if __name__ == "__main__":
    print("Тестуємо підключення...")
    if test_connection():
        print("База працює відмінно!")
