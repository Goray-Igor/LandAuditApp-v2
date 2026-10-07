# LandAuditApp

Веб-застосунок для аудиту договорів земельної оренди (Україна).
Аудитор знаходить ділянку за кадастровим номером, звіряє дані з реєстрів
(ДЗК / ДРРП) із паперовим договором і зберігає результат перевірки в MS SQL Server.

## Можливості

- Пошук ділянки за кадастровим номером (від 3 символів), вхід за кодом аудитора (ПІБ).
- Блок «Дані з реєстрів»: параметри ділянки, власність, користування,
  обмеження/обтяження/іпотека/суди, суборенда.
- Форма аудиту за типом договору (Оренда / Суборенда / Емфітевзис) та
  типом контрагента (Фізична / Юридична / ОМС), що складається з груп:
  0 — наявність документів, 1 — реквізити, 2 — ділянка, 3 — орендна плата,
  4 — юридичний блок, 5 — додаткові угоди.
- Автопідстановка з реєстрів, ІПН з `IPN_reestr`, номерів ДКП з `DKP_reestr`.
- Захист від дублів: збережений договір блокується, редагування — за паролем адміністратора.

## Стек

Python 3.11/3.12 · Streamlit · pandas · SQLAlchemy + pyodbc (MS SQL Server,
ODBC Driver 17) · python-dotenv · openpyxl · PyInstaller (збірка exe).

## Структура

```text
LandAuditApp/
├── app.py              # Точка входу, маршрутизація форм
├── run_app.py          # Запуск Streamlit (для PyInstaller)
├── run_app.spec        # Конфіг збірки PyInstaller
├── core/               # database.py (запити до SQL Server), utils.py (дати, числа, вибір ДРРП/ДЗК)
├── ui/                 # sidebar.py, block_registry.py, form_actions.py
├── forms/              # form_ind.py, form_legal.py, form_oms.py (оркестратори форм)
├── form_blocks/        # group_*.py (повторно використовувані групи форми)
└── scripts/            # Разове завантаження Excel у БД (upload_registry, upload_ipn)
```

## Запуск (Windows, PowerShell)

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # заповнити значення
streamlit run app.py
```

Потрібен встановлений ODBC Driver 17 for SQL Server.
Перевірка підключення до БД: `python -m core.database`.

## Змінні оточення (.env)

| Змінна | Призначення |
|---|---|
| DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD | Підключення до SQL Server |
| ADMIN_PASSWORD | Пароль розблокування редагування збережених договорів |

## Завантаження реєстрів

```powershell
python -m scripts.upload_registry   # Parcel_reestr
python -m scripts.upload_ipn        # IPN_reestr
```

Скрипти додають рядки (`if_exists='append'`), повторний запуск створить дублікати.

## Збірка exe

```powershell
pip install -r requirements-dev.txt
pyinstaller run_app.spec
```

## Заметки по доработке (чернетка)

- Оранка (так/ні)
- Номер договору
- Зміна власника (так/ні), новий власник
- Набуття чинності з дати підписання та державної реєстрації договору
- Номер реєстрації оренди
- ДКП: номер договору, дата ДКП права оренди, розмір оплати, наявність акту
  приймання-передачі, наявність додатка (реєстр ділянок), сума платіжної
  інструкції, примітка