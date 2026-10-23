import os

import numpy as np
import pandas as pd
from sqlalchemy import text

from core.database import get_engine
from core.logger import get_logger

logger = get_logger(__name__)

TABLE = "DKP_reestr"
REQUIRED_COLS = ["cadastral_number", "dkp_contract_number", "previous_lessee", "area"]

# Выставь True, чтобы реально записать в БД. False = только предпросмотр (dry-run).
APPLY = True


def clean_area(val):
    """'9,3823' -> 9.3823; порожнє -> NaN."""
    if pd.isna(val) or str(val).strip() in ["", "-", "None", "nan"]:
        return np.nan
    try:
        return float(str(val).replace(",", ".").replace(" ", "").strip())
    except (ValueError, TypeError):
        return np.nan


def clean_text(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("nan", "none") else None


def upload_dkp_registry(file_path):
    print(f"⏳ Читаємо файл: {file_path}...")
    if not os.path.exists(file_path):
        print("❌ Файл не знайдено!")
        return

    try:
        # dtype=str, щоб '9,3823' та номери на кшталт '17/03-3' не спотворювались
        df = pd.read_excel(file_path, dtype=str)
        df.columns = [str(c).strip().strip("[]") for c in df.columns]

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            print(f"❌ У файлі немає колонок: {missing}. Є: {list(df.columns)}")
            return

        df = df[REQUIRED_COLS].copy()
        df["cadastral_number"] = df["cadastral_number"].apply(clean_text)
        df["dkp_contract_number"] = df["dkp_contract_number"].apply(clean_text)
        df["previous_lessee"] = df["previous_lessee"].apply(clean_text)
        df["area"] = df["area"].apply(clean_area)

        # Рядки без кадастрового номера не мають сенсу
        before = len(df)
        df = df.dropna(subset=["cadastral_number"])
        if len(df) < before:
            print(f"⚠️ Пропущено рядків без кадастрового номера: {before - len(df)}")

        # Дублі всередині самого файлу
        dup_file = df.duplicated(subset=["cadastral_number", "dkp_contract_number"], keep=False)
        if dup_file.any():
            print(f"⚠️ Дублі в самому файлі ({dup_file.sum()} рядків):")
            print(df[dup_file].to_string(index=False))

        # Що вже є в таблиці (щоб повторний запуск не створив дублікати)
        engine = get_engine()
        with engine.connect() as conn:
            existing = pd.read_sql(
                text(f"SELECT cadastral_number, dkp_contract_number FROM {TABLE}"), conn
            )
        existing_keys = set(
            zip(existing["cadastral_number"].astype(str).str.strip(),
                existing["dkp_contract_number"].astype(str).str.strip(), strict=True)
        )
        is_new = [
            (str(c), str(d)) not in existing_keys
            for c, d in zip(df["cadastral_number"], df["dkp_contract_number"], strict=True)
        ]
        df_new = df[is_new]

        print(f"📊 У файлі: {len(df)} | вже є в БД: {len(df) - len(df_new)} | буде додано: {len(df_new)}")
        print("🔎 Перші 10 рядків до завантаження:")
        print(df_new.head(10).to_string(index=False))

        if not APPLY:
            print("ℹ️ Режим перегляду (APPLY = False). Нічого не записано.")
            return
        if df_new.empty:
            print("ℹ️ Нових рядків немає.")
            return

        with engine.begin() as conn:  # одна транзакція: або все, або нічого
            df_new.to_sql(TABLE, con=conn, if_exists="append", index=False, chunksize=1000)

        logger.info("DKP_reestr: завантажено %s рядків з %s", len(df_new), file_path)
        print(f"🎉 УСПІШНО! Завантажено {len(df_new)} записів.")

    except Exception as e:
        logger.exception("Помилка завантаження DKP_reestr")
        print(f"❌ Помилка: {e}")


if __name__ == "__main__":
    EXCEL_FILE = r"data\dkp.xlsx"  # вкажи точну назву свого файлу
    upload_dkp_registry(EXCEL_FILE)