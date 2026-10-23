"""Разовая выгрузка всех таблиц БД в один Excel (лист = таблица) или в набор CSV.

Только чтение. Результат по умолчанию кладётся в data/ (игнорируется git).
Запуск: python -m scripts.export_db_dump --help
"""
import argparse
import hashlib
import hmac
import re
import secrets
from pathlib import Path

import pandas as pd
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from sqlalchemy import inspect, text

from core.database import get_engine
from core.logger import get_logger

logger = get_logger(__name__)

EXCEL_MAX_ROWS = 1_048_575  # 1 048 576 минус строка заголовка
SHEET_NAME_MAX = 31
SCHEMA_SHEET = "_schema"
AUDIT_PREFIX = "Audit_"
DEFAULT_OUT = Path("data") / "db_dump.xlsx"

# Колонки с персональными данными (по именам из проекта). Дополни при необходимости.
PII_COLUMNS = {
    "full_name", "ipn_code", "new_owner_ipn", "lessor_name", "lessee_name", "new_owner_name",
    "owner_dzk", "owner_drrp", "owner_code_dzk", "owner_code_drrp",
    "user_dzk", "user_drrp", "user_code_dzk", "user_code_drrp",
    "subject_details",
}


def _q(name):
    """Квотирование идентификатора T-SQL (имена берём из inspector, не от пользователя)."""
    return "[" + name.replace("]", "]]") + "]"


def safe_sheet_name(name, used):
    """Имя листа Excel: ≤31 символа, без запрещённых символов, уникальное."""
    base = re.sub(r"[\[\]:*?/\\]", "_", name)[:SHEET_NAME_MAX]
    candidate, n = base, 1
    while candidate.lower() in used:
        suffix = f"_{n}"
        candidate = base[: SHEET_NAME_MAX - len(suffix)] + suffix
        n += 1
    used.add(candidate.lower())
    return candidate


def mask_value(val, salt):
    """Стабильная (в рамках запуска) анонимизация: одинаковые значения -> одинаковый токен."""
    if pd.isna(val) or not str(val).strip():
        return val
    digest = hmac.new(salt, str(val).strip().encode("utf-8"), hashlib.sha256).hexdigest()[:8]
    return f"ANON_{digest}"


def mask_pii(df, salt):
    for col in df.columns:
        if col in PII_COLUMNS:
            df[col] = df[col].map(lambda v: mask_value(v, salt))
    return df


def strip_illegal_chars(df):
    """openpyxl падает на управляющих символах — вычищаем их из строк."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda v: ILLEGAL_CHARACTERS_RE.sub("", v) if isinstance(v, str) else v)
    return df


def export_db(out_path, fmt, schema, include, exclude, audit_limit, registry_limit, mask):
    engine = get_engine()
    insp = inspect(engine)
    tables = sorted(insp.get_table_names(schema=schema))
    if include:
        tables = [t for t in tables if t in include]
    tables = [t for t in tables if t not in exclude]
    if not tables:
        print("❌ Не знайдено таблиць для вигрузки.")
        return

    salt = secrets.token_bytes(16)
    used_sheets = set()
    summary_rows, column_rows = [], []
    frames = {}  # sheet/file name -> DataFrame

    with engine.connect() as conn:
        for table in tables:
            full = f"{_q(schema)}.{_q(table)}"
            total = conn.execute(text(f"SELECT COUNT(*) FROM {full}")).scalar()

            limit = audit_limit if table.startswith(AUDIT_PREFIX) else registry_limit
            if fmt == "xlsx":
                limit = min(limit, EXCEL_MAX_ROWS) if limit else EXCEL_MAX_ROWS
            top = f"TOP {int(limit)} " if limit else ""

            print(f"⏳ {table}: {total} рядків...")
            df = pd.read_sql(text(f"SELECT {top}* FROM {full}"), conn)
            if mask:
                df = mask_pii(df, salt)

            sheet = safe_sheet_name(table, used_sheets)
            frames[sheet] = df
            summary_rows.append({
                "table": table, "sheet_or_file": sheet,
                "rows_total": total, "rows_exported": len(df), "columns": len(df.columns),
                "truncated": len(df) < total,
            })
            for c in insp.get_columns(table, schema=schema):
                column_rows.append({
                    "table": table, "column": c["name"], "type": str(c["type"]),
                    "nullable": c["nullable"], "masked": bool(mask and c["name"] in PII_COLUMNS),
                })
            pk = insp.get_pk_constraint(table, schema=schema).get("constrained_columns") or []
            summary_rows[-1]["primary_key"] = ", ".join(pk)

    df_summary = pd.DataFrame(summary_rows)
    df_columns = pd.DataFrame(column_rows)

    if fmt == "xlsx":
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for sheet, df in frames.items():
                strip_illegal_chars(df).to_excel(writer, sheet_name=sheet, index=False)
            # Єдиний лист-схема: зведення, нижче — колонки
            df_summary.to_excel(writer, sheet_name=SCHEMA_SHEET, index=False)
            df_columns.to_excel(writer, sheet_name=SCHEMA_SHEET, index=False, startrow=len(df_summary) + 3)
            book = writer.book
            book.move_sheet(SCHEMA_SHEET, offset=-(len(book.sheetnames) - 1))
        print(f"🎉 Готово: {out_path} (листів: {len(frames) + 1})")
    else:
        out_dir = out_path.with_suffix("")  # data/db_dump/
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, df in frames.items():
            df.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8-sig")
        df_summary.to_csv(out_dir / "_schema_tables.csv", index=False, encoding="utf-8-sig")
        df_columns.to_csv(out_dir / "_schema_columns.csv", index=False, encoding="utf-8-sig")
        print(f"🎉 Готово: {out_dir} (файлів: {len(frames) + 2})")

    logger.info("Вигрузка БД: %s таблиць -> %s (mask=%s)", len(tables), out_path, mask)


def main():
    p = argparse.ArgumentParser(description="Вигрузка всіх таблиць БД у Excel/CSV (лише читання).")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Шлях до .xlsx (для csv — назва папки без розширення)")
    p.add_argument("--format", choices=["xlsx", "csv"], default="xlsx")
    p.add_argument("--schema", default="dbo")
    p.add_argument("--tables", nargs="*", default=[], help="Лише ці таблиці")
    p.add_argument("--exclude", nargs="*", default=[], help="Пропустити ці таблиці")
    p.add_argument("--audit-limit", type=int, default=0, help="Макс. рядків для Audit_* (0 = всі)")
    p.add_argument("--registry-limit", type=int, default=0, help="Макс. рядків для реєстрів, не Audit_* (0 = всі)")
    p.add_argument("--mask", action="store_true", help="Анонімізувати ПІБ/ІПН/коди власників (стабільні токени)")
    a = p.parse_args()

    export_db(a.out, a.format, a.schema, set(a.tables), set(a.exclude),
              a.audit_limit, a.registry_limit, a.mask)


if __name__ == "__main__":
    main()
