import pandas as pd

from core.database import get_engine


def clean_ipn(val):
    """Очищає ІПН від порожнечі та випадкових .0"""
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str if val_str else None

def upload_ipn_registry(file_path):
    print(f"⏳ Читаємо файл: {file_path}...")
    try:
        df = pd.read_excel(file_path)

        # 1. Перейменовуємо колонки (підстав свої точні назви з Excel, якщо вони відрізняються)
        # Формат: {"Назва в Excel": "назва_в_sql"}
        df = df.rename(columns={
            "ФИО": "full_name",
            "ИНН": "ipn_code",
            "Кадастровый номер": "cadastral_number"
        })

        # 2. Очищення даних
        if 'ipn_code' in df.columns:
            df['ipn_code'] = df['ipn_code'].apply(clean_ipn)
        if 'cadastral_number' in df.columns:
            df['cadastral_number'] = df['cadastral_number'].astype(str).str.strip()

        # Залишаємо тільки потрібні колонки (на випадок, якщо в Excel є зайві)
        df = df[['full_name', 'ipn_code', 'cadastral_number']]

        # 3. Завантаження в БД
        engine = get_engine()
        print("⏳ Завантажуємо в таблицю IPN_reestr...")
        df.to_sql('IPN_reestr', con=engine, if_exists='append', index=False, chunksize=1000)
        print(f"🎉 УСПІШНО! Завантажено {len(df)} записів.")

    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    # Вкажи точну назву свого файлу
    EXCEL_FILE = r"data\inn.xlsx"
    upload_ipn_registry(EXCEL_FILE)
