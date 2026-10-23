# Product Analytics — Synthetic Data Generator

## Требования
- Python 3.10+
- NumPy
- Pandas

## Установка

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
```

## Запуск

Из каталога проекта:

```bash
python product_analytics_generator.py --output data
```

Будут созданы `users.csv`, `products.csv`, `orders.csv`, `order_items.csv`, `events.csv` и `generation_report.json` в каталоге `data/`.

Параметры:

```bash
python product_analytics_generator.py --output data --seed 42 --users 10000 --products 150
```

Один и тот же seed и одинаковые версии зависимостей обеспечивают воспроизводимую структуру генерации. Для независимого набора используйте другой `--seed`.

См. `DATA_DICTIONARY.md` для описания полей, связей, бизнес-правил и ограничений.
