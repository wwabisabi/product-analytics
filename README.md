# Анализ пользовательского поведения в E-commerce (Product Analytics)

Учебный проект по анализу синтетического датасета интернет-магазина за первое полугодие 2026 года.

## Цели проекта
1. Оценить базовые метрики бизнеса.
2. Построить воронку конверсии на уровнях пользователей и сессий.
3. Проанализировать эффективность товаров (конверсия View → Purchase).
4. Провести когортный анализ Retention.

## Стек технологий
*   **База данных:** PostgreSQL
*   **Язык запросов:** SQL (сложные агрегации, CTE)
*   **Анализ и визуализация:** Python (pandas, plotly, sqlalchemy)
*   **Среда:** Jupyter Notebook, DBeaver


## Структура репозитория
*   **`generator/`** — Модуль генерации данных
    *   `product_analytics_generator.py` — Скрипт для создания синтетического датасета
*   **`sql_scripts/`** — SQL-запросы для аналитики
    *   `basis_metrics.sql` — Базовые метрики (выручка, заказы)
    *   `funnel_by_users.sql` — Воронка конверсии по пользователям
    *   `funnel_by_sessions.sql` — Воронка конверсии по сессиям
    *   `funnel_by_products.sql` — Анализ конверсии по товарам
    *   `retention.sql` — Когортный анализ удержания
*   **`.env`** — Локальные переменные окружения с паролем *(игнорируется Git)*
*   **`.env.example`** — Шаблон для настройки переменных окружения
*   **`.gitignore`** — Список файлов, исключенных из Git
*   **`DATA_DICTIONARY.md`** — Описание полей и бизнес-правил датасета
*   **`Product_Analytics_Report.ipynb`** — Главный Jupyter-ноутбук с визуализациями и выводами
*   **`README.md`** — Описание проекта
*   **`requirements.txt`** — Список зависимостей Python

## Как запустить проект

Все команды выполняются из корневой папки проекта.

1. Клонируйте репозиторий.
2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

3. Установите зависимости: 
```bash
pip install -r requirements.txt
```
4. Скопируйте `.env.example` в `.env` и укажите свой пароль от PostgreSQL.
5. Сгенерируйте данные:
```bash
python product_analytics_generator.py --output data
```
6. Запустите Jupyter Notebook:
```bash
jupyter notebook
```
и откройте файл `Product_Analytics_Report.ipynb`.

7. В ноутбуке выполните все ячейки (Run All Cells), чтобы загрузить данные из базы и построить графики.
