import os

import numpy as np
import pandas as pd

from core.database import get_engine


def clean_area_value(val):
    """Очищает значение площади: меняет запятую на точку и переводит в число."""
    if pd.isna(val) or str(val).strip() in ["", "-", "None", "nan"]:
        return np.nan
    try:
        # Меняем запятую на точку, убираем пробелы и переводим во float
        return float(str(val).replace(',', '.').replace(' ', '').strip())
    except Exception:
        return np.nan

def upload_excel_to_parcel_reestr(file_path):
    print(f"⏳ Чтение файла: {file_path}...")

    if not os.path.exists(file_path):
        print("❌ Ошибка: Файл не найден!")
        return

    try:
        # 1. Читаем Excel файл
        df = pd.read_excel(file_path)
        print(f"✅ Файл прочитан. Найдено строк: {len(df)}")

        # 2. Очистка данных (подготовка FLOAT для площадей)
        if 'area_dzk' in df.columns:
            df['area_dzk'] = df['area_dzk'].apply(clean_area_value)
        if 'area_drrp' in df.columns:
            df['area_drrp'] = df['area_drrp'].apply(clean_area_value)

        # Здесь можно добавить очистку других колонок, если нужно
        # Например, привести кадастровые номера к строке и убрать лишние пробелы:
        if 'cadastral_number' in df.columns:
            df['cadastral_number'] = df['cadastral_number'].astype(str).str.strip()

        # 3. Подключение к базе и загрузка
        engine = get_engine()
        print("⏳ Загрузка данных в таблицу Parcel_reestr (это может занять пару минут)...")

        # chunksize=1000 разбивает загрузку на пакеты по 1000 строк
        # (чтобы не перегрузить оперативную память, если файл огромный)
        df.to_sql('Parcel_reestr', con=engine, if_exists='append', index=False, chunksize=1000)

        print("🎉 УСПЕШНО! Все данные загружены в базу.")

    except Exception as e:
        print(f"❌ Ошибка во время обработки или загрузки: {e}")

if __name__ == "__main__":
    # --- НАСТРОЙКА ---
    # Укажи здесь точный путь к твоему Excel-файлу
    EXCEL_FILE_PATH = r"C:\Users\IV.Horai\Desktop\UPI\PROJECT\LandAuditApp\data\Download_reestr.xlsx"

    upload_excel_to_parcel_reestr(EXCEL_FILE_PATH)
