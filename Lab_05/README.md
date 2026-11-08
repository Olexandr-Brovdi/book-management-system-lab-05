# Імпорт та експорт системи обліку книг

Лабораторна робота №5 «Обробка помилок, файли та серіалізація».
**Бровді Олександр, ФеП-32, варіант 2.** Курс «Професійний Python».

## Встановлення Python 3.11+

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m book_io --config config.yaml
book-io --config config.yaml
python -m unittest discover -s tests -v
python -m book_io.experiments
```

Linux/macOS: `source .venv/bin/activate`. Команди виконуються з кореня
або автономної папки `Lab_05`. PyYAML встановлюється як залежність проєкту.

## Вхідні дані та перевірки

CSV: `isbn,title,author,year,pages`. Підтримуються UTF-8, BOM і quoted multiline
fields. ISBN-10/13 перевіряється за довжиною, символами та контрольною цифрою;
дефіси й пробіли нормалізуються, для ISBN-13 дозволено префікси 978/979.
Назва й автор непорожні. Рік — цілий у діапазоні `min_year..max_year` із YAML,
pages — додатне ціле. Float і bool замість цілих не приймаються.
Неповні/зайві поля запису вважаються помилкою; зіпсований заголовок або
структурно пошкоджений CSV завершує імпорт, бо межі рядків можуть бути втрачені.

`data/books.csv` містить 8 навчальних записів: 4 коректні та 4 некоректні.
ISBN і назви створено для навчального набору; бібліографічну відповідність
реальним виданням не заявлено. При типовому tolerant-запуску експортуються
4 книги, а причини відхилення записуються в log.

## Конфігурація та надійність

Усі відносні шляхи обчислюються від каталогу YAML-файла.
`schema_version: 1`; `skip_invalid` має бути YAML boolean, а не рядком.
Строгий режим (`false`) припиняє імпорт на першому неправильному записі.
Толерантний (`true`) рахує помилку, пише warning і продовжує обхід.
Рік поза дозволеним діапазоном вважається invalid, а не прихованим фільтром.

Неправильна конфігурація виявляється до імпорту. Відсутні вихідні каталоги
створюються; конфлікт шляхів input/output/log/summary/config відхиляється.
Очікувані помилки загортаються у конкретні application exceptions через
`raise ... from error`; CLI контрольовано завершується з кодом 1.

Atomic output використовує унікальний temporary file у каталозі призначення,
flush, fsync і os.replace. При помилці temp видаляється, старий output зберігається.
Запис books і summary атомарний для кожного файла окремо, це не спільна
транзакція кількох файлів і не гарантія від усіх видів втрати живлення.
Статистика exported оновлюється лише після успішного commit основного output.

## Структура

```text
config.yaml, pyproject.toml, README.md, .gitignore
data/books.csv, data/books_100000.csv
src/book_io/
  config.py, exceptions.py, models.py
  readers.py, validators.py, services.py
  exporters.py, resources.py, logging_config.py
  datasets.py, experiments.py, main.py, __init__.py, __main__.py
tests/test_reliability.py
tools/create_report_assets.py, build_report.py, validate_submission.py
docs/results/, docs/screenshots/, docs/Lab_05_Report_Variant_2.docx
output/ і logs/ — результати роботи, ігноруються Git
Lab_05/src/, data/, tests/, tools/, config.yaml, pyproject.toml, README.md
Lab_05/report/report.docx
```

CSV і JSON Lines реалізують спільний Importer Protocol. JSON array і JSON Lines
exporters реалізують Exporter Protocol. Звичайний JSON array підтримується
для output; для streaming input JSON використовується формат JSON Lines.
Формат обирається автоматично за extension або явно у YAML.

## Експерименти та результати

1. 1000 valid + 10 invalid: strict зупиняється після 1001 запису, commit не
   виконується; tolerant обробляє всі 1010 і експортує 1000.
2. 10 000, 100 000, 500 000: порівнюються eager та повністю спожитий streaming
   CSV reader. Генерація не входить у вимірювання, tracemalloc активний;
   peak — Python allocations, не повний RSS. Один запуск на режим, можливий кеш ОС.
3. Зафіксовано traceback ValueError → RecordValidationError.
4. Навмисний збій після першого запису підтверджує незмінність старого output
   та відсутність temporary files.
5. Missing/malformed config, відсутній input key, неправильний діапазон років,
   missing input file і автоматичне створення відсутнього output directory.
   Параметр minimum_grade із прикладу методички замінено діапазоном років варіанта 2.

Реальна доказова база — `docs/results/experiments.json`, `exception_chain.txt`,
`experiments.log`, `application.log`, `tests.txt`. Відтворювані великі файли
генеруються в ігнорованій `data/generated`. Готовий CSV на 100 000 записів
також додано до `data/books_100000.csv`.

## Додаткові можливості та звіт

Реалізовано Importer/Exporter Protocols, автоматичний format selection,
JSON Lines, nested configuration, schema version, configurable logging,
rotation, transaction-like context manager, atomic output і JSON summary.
У logs не записуються повні вихідні рядки чи секрети; лише номер, поле та причина.
`logger.exception` зберігає traceback очікуваних помилок.

```text
python -m pip install -e ".[report]"
python tools/create_report_assets.py
python tools/build_report.py
python tools/validate_submission.py
```

Звіт містить усі 70 відповідей на контрольні запитання. Відсутні звіти інших
лабораторних; локальна перевірка контролює Lab_05, варіант 2, автора і тему книг.
