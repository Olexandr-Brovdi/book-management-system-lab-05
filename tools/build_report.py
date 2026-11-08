"""Build the variant 2 reliability report from real code and measurements."""
from pathlib import Path
import json
import shutil
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm,Pt,RGBColor

ROOT = Path(__file__).resolve().parents[1]
QA = [('Що таке exception?', 'Виняток — об’єкт, який сигналізує про помилку та перериває звичайний потік виконання до відповідного обробника.'), ('Для чого використовується try?', 'try позначає блок операцій, помилки якого потрібно контрольовано обробити.'), ('Для чого except?', 'except перехоплює винятки визначеного типу та виконує обробник.'), ('Коли виконується else після try?', 'else виконується, якщо блок try завершився без винятку.'), ('Коли виконується finally?', 'finally виконується під час виходу з try за нормального завершення, винятку або return; примусове завершення процесу може завадити цьому.'), ('Для чого використовується raise?', 'raise піднімає виняток і передає керування механізму обробки помилок.'), ('Що означає raise без аргументів?', 'Порожній raise повторно піднімає поточний оброблюваний виняток зі збереженням traceback.'), ('Чому не рекомендується except: pass?', 'Такий обробник приховує помилку, втрачає діагностику та може залишити програму в некоректному стані.'), ('Чому потрібно перехоплювати конкретні exception types?', 'Конкретні типи дозволяють обробити очікувані ситуації, не маскуючи сторонні програмні помилки.'), ('Що таке exception hierarchy?', 'Це дерево успадкування класів винятків; обробник базового класу також ловить його підкласи.'), ('Для чого створювати custom exceptions?', 'Власні винятки надають помилкам предметний зміст і дозволяють клієнту розрізняти configuration, import, validation та export failures.'), ('Що таке exception chaining?', 'Exception chaining пов’язує новий виняток з початковою причиною.'), ('Що означає raise ... from ...?', 'raise NewError(...) from error явно встановлює error як __cause__ нового винятку.'), ('Яку перевагу дає chaining для debugging?', 'Traceback показує низькорівневу причину разом із предметним контекстом; наприклад ValueError і RecordValidationError з номером рядка.'), ('Що означає EAFP?', 'EAFP означає Easier to Ask Forgiveness than Permission: спочатку виконати операцію та перехопити очікуваний виняток.'), ('Що означає LBYL?', 'LBYL означає Look Before You Leap: перевірити умови перед виконанням операції. Для файлових операцій перевірка не усуває гонку з подальшим доступом.'), ('Що таке fail-fast?', 'Fail-fast — негайне припинення роботи при порушенні обов’язкової передумови.'), ('Де доцільно застосовувати fail-fast?', 'На межі системи: перевірка конфігурації, схеми, шляхів і strict validation до публікації нового результату.'), ('Що таке context manager?', 'Context manager керує входом у контекст і гарантованим виходом із нього, зокрема звільненням ресурсів.'), ('Для чого використовується with?', 'with організовує життєвий цикл ресурсу й викликає його завершення навіть при винятку всередині блоку.'), ('Які methods утворюють context manager protocol?', 'Синхронний протокол складається з __enter__ та __exit__.'), ('Що робить __enter__()?', '__enter__ готує ресурс і повертає значення для змінної після as.'), ('Що робить __exit__()?', '__exit__(exc_type, exc_value, traceback) звільняє ресурси; істинний результат пригнічує виняток, хибний дозволяє його поширення.'), ('Чи закриває with файл при exception?', 'Так, файловий context manager закриває відкритий файл при виході з with, у тому числі через виняток.'), ('Для чого contextlib.contextmanager?', 'Декоратор contextlib.contextmanager дозволяє описати context manager генератором із try/finally замість окремого класу.'), ('Яку роль має yield у generator-based context manager?', 'Єдиний yield передає ресурс у with; код до нього виконує підготовку, після нього — завершення. Виняток із with надходить у точку yield.'), ('Що таке pathlib.Path?', 'pathlib.Path — об’єктне представлення файлового шляху з методами читання, запису, перевірки й створення каталогів.'), ('Чому pathlib кращий за ручну конкатенацію шляхів?', 'Path поєднує компоненти оператором /, враховує платформу й зменшує помилки з роздільниками та відносними шляхами.'), ('Для чого задається encoding="utf-8"?', 'Явний UTF-8 забезпечує передбачуване збереження українського тексту незалежно від системного кодування.'), ('Що таке CSV?', 'CSV — текстовий табличний формат із розділеними полями, лапками та правилами екранування.'), ('Для чого csv.reader?', 'csv.reader читає CSV рядок за рядком і повертає списки полів з урахуванням лапок та роздільників.'), ('Для чого csv.DictReader?', 'csv.DictReader зіставляє значення рядка з назвами колонок і повертає словники.'), ('Чим DictReader зручний для structured data?', 'Доступ за іменами isbn чи pages зрозуміліший за числові індекси; також зручно перевіряти схему.'), ('Для чого csv.DictWriter?', 'csv.DictWriter записує словники в CSV за заданим порядком fieldnames та підтримує заголовок writeheader().'), ('Що таке JSON?', 'JSON — текстовий формат обміну даними з об’єктами, масивами, рядками, числами, boolean та null.'), ('Що таке serialization?', 'Серіалізація перетворює об’єкти програми на формат, придатний для зберігання або передавання.'), ('Що таке deserialization?', 'Десеріалізація відновлює структури даних із такого представлення; предметні об’єкти потребують додаткової перевірки.'), ('Чим json.dump() відрізняється від json.dumps()?', 'json.dump записує JSON у файловий об’єкт, json.dumps повертає рядок.'), ('Чим json.load() відрізняється від json.loads()?', 'json.load читає JSON із файлового об’єкта, json.loads розбирає рядок або bytes.'), ('Що таке JSONDecodeError?', 'JSONDecodeError — підклас ValueError, який містить опис і позицію синтаксичної помилки JSON.'), ('Для чого використовується YAML?', 'YAML використовують для зручного людині опису конфігурації, вкладених структур і списків.'), ('Чому рекомендується yaml.safe_load()?', 'safe_load обмежує конструювання звичайними типами даних і не дозволяє довільне створення Python-об’єктів; схему все одно потрібно перевірити.'), ('Які типові сценарії використання JSON?', 'API, обмін структурованими даними, експорт результатів та збереження документів.'), ('Які типові сценарії використання YAML?', 'Конфігурація застосунків, параметри середовища й опис завдань автоматизації.'), ('Що таке configuration file?', 'Файл конфігурації містить зовнішні параметри запуску: шляхи, режими перевірки, допустимі роки й налаштування журналу.'), ('Чому configuration краще не hard-code у Python?', 'Винесені параметри можна змінити без редагування коду, перевіряти окремо й використовувати для різних середовищ.'), ('Що потрібно перевіряти у configuration?', 'Наявність ключів, типи й діапазони значень, версію схеми, підтримувані формати, доступність input та відсутність колізій шляхів.'), ('Що таке logging?', 'Logging — кероване записування подій програми з часом, рівнем, джерелом і контекстом.'), ('Чим logging відрізняється від print()?', 'Logging має рівні, handlers, форматування, файловий запис і ротацію; print зазвичай лише виводить текст у потік.'), ('Які існують logging levels?', 'Стандартні рівні: DEBUG, INFO, WARNING, ERROR, CRITICAL; NOTSET означає відсутність власного порога.'), ('Для чого logger.info()?', 'logger.info повідомляє про нормальні важливі події, наприклад початок операції або кількість експортованих книг.'), ('Для чого logger.warning()?', 'logger.warning фіксує проблему, після якої робота може тривати: наприклад пропуск некоректного запису в tolerant mode.'), ('Для чого logger.error()?', 'logger.error повідомляє про помилку операції без автоматичного додавання поточного traceback.'), ('Для чого logger.exception()?', 'logger.exception викликають у except: він записує повідомлення рівня ERROR разом із поточним traceback.'), ('Що містить traceback?', 'Traceback містить послідовність викликів, файли й номери рядків, тип і повідомлення винятку; для chaining також його причину.'), ('Чому secrets не можна записувати в logs?', 'Журнали часто мають ширший доступ і тривале зберігання; паролі й токени в них можуть спричинити витік та несанкціонований доступ.'), ('Що таке streaming I/O?', 'Streaming I/O обробляє дані послідовно невеликими частинами, не накопичуючи весь файл.'), ('Яка перевага streaming для великих files?', 'Пам’ять залежить переважно від поточного запису й буферів, тому можна обробляти файли, більші за доступну RAM.'), ('Що таке eager file loading?', 'Eager loading завчасно матеріалізує весь вміст або всі записи в пам’яті.'), ('Чому list(reader) може бути небажаним?', 'list(reader) створює об’єкти для всіх рядків; на великих файлах це збільшує час виділення пам’яті та ризик її вичерпання.'), ('Що таке strict validation mode?', 'Strict mode припиняє обробку на першому неправильному записі й не публікує частковий основний output.'), ('Що таке tolerant mode?', 'Tolerant mode журналює неправильний запис, збільшує invalid counter та продовжує роботу з рештою.'), ('Коли доцільно використовувати strict mode?', 'Коли кожний запис є обов’язковим для цілісності результату або помилка означає ненадійність всього набору.'), ('Коли tolerant mode?', 'Коли допустимий корисний частковий результат, а кожне відхилення має бути явно враховане й доступне для аналізу.'), ('Що таке atomic write?', 'Atomic write записує новий вміст у temporary file й замінює ціль однією операцією після успіху; до заміни старий результат зберігається.'), ('Для чого використовується temporary file?', 'Temporary file ізолює незавершений результат від основного файла; створення в тому самому каталозі дозволяє заміну в межах файлової системи.'), ('Що може статися при звичайному output write та аварійному завершенні?', 'Після відкриття з режимом w старий вміст уже втрачений, а аварія може залишити порожній або частковий JSON.'), ('Навіщо видаляти temporary file після error?', 'Щоб не накопичувати сміття, не займати диск та не залишати неповні дані, які можна помилково прийняти за результат.'), ('Що таке JSON Lines?', 'JSON Lines — UTF-8 формат, у якому кожний непорожній рядок є окремим JSON-значенням; у цьому проєкті — об’єктом книги.'), ('Чому JSON Lines зручний для streaming?', 'Кожний запис розбирається незалежно, тому можна читати й писати по одному рядку без повного JSON-масиву в пам’яті.')]


def build() -> None:
    doc = Document()
    s = doc.sections[0]
    s.page_width,s.page_height = Cm(21),Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(2)
    s.left_margin,s.right_margin = Cm(2.5),Cm(1.5)
    for name in ('Normal','Title','Heading 1','Heading 2'):
        style = doc.styles[name]
        style.font.name = 'Times New Roman'
        style.font.size = Pt(12 if name == 'Normal' else 14)
        style.font.color.rgb = RGBColor(0,0,0)
    for border in doc.styles.element.xpath('.//w:pBdr'):
        border.getparent().remove(border)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.08
    doc.styles['Normal'].paragraph_format.space_after = Pt(6)

    def p(text):
        return doc.add_paragraph(text)
    def h(text):
        doc.add_heading(text,level=1)
    def page(text):
        doc.add_page_break()
        h(text)
    def code(text,size=8.5):
        para = p('')
        para.paragraph_format.line_spacing = 1
        run = para.add_run(text.strip())
        run.font.name,run.font.size = 'Consolas',Pt(size)
    def src(name):
        return (ROOT/'src/book_io'/name).read_text(encoding='utf-8')
    def picture(name,caption,width=16.5):
        doc.add_picture(str(ROOT/'docs/screenshots'/(name+'.png')),width=Cm(width))
        p(caption)
    def table(headers,rows):
        t = doc.add_table(rows=1,cols=len(headers))
        t.style = 'Table Grid'
        for cell,value in zip(t.rows[0].cells,headers):
            cell.text = value
            cell.paragraphs[0].runs[0].bold = True
        for row in rows:
            for cell,value in zip(t.add_row().cells,row):
                cell.text = str(value)

    cover = [
        ('ЛЬВІВСЬКИЙ НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ\nІМЕНІ ІВАНА ФРАНКА',14,65),
        ('ЗВІТ ДО ЛАБОРАТОРНОЇ РОБОТИ №5',16,20),
        ('«Обробка помилок, файли та серіалізація»',14,18),
        ('з курсу «Професійний Python»\nВаріант №2 — «Імпорт та експорт системи обліку книг»',14,45),
        ('Виконав: Бровді Олександр\nГрупа: ФеП-32\nПеревірив(ла): Свелеба Сергій Андрійович\nДата: 08.11.2026',12,70),
        ('Львів — 2026',14,0),
    ]
    for i,(text,size,after) in enumerate(cover):
        para = doc.add_paragraph(text,'Title' if i == 1 else None)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(after)
        for run in para.runs:
            run.font.size = Pt(size)

    page('Мета та постановка задачі')
    p('Мета — створити надійний модуль роботи з помилками, файлами й серіалізацією, опанувати custom exceptions та exception chaining, context managers, logging, pathlib, CSV/JSON/YAML, конфігурацію, streaming I/O та atomic output.')
    p('Варіант 2 — імпорт та експорт системи обліку книг. Схема: isbn, title, author, year, pages. Потрібно перевіряти ISBN, непорожні назву й автора, коректний рік та pages > 0. Реалізовано CSV import, JSON export, YAML configuration з допустимим діапазоном років, strict/tolerant processing та logging invalid records.')
    h('Вхідні дані та приклад CSV')
    code('\n'.join((ROOT/'data/books.csv').read_text(encoding='utf-8').splitlines()[:6]))
    p('Навчальний CSV містить 8 записів: 4 правильні та 4 неправильні. Для коректних ISBN-13 згенеровано контрольну цифру; назви й ISBN є навчальним набором без твердження про реальні видання. Підтримано ISBN-10, дефіси й пробіли в номері. Порожні поля, неправильні цілі числа та рік поза YAML-діапазоном відхиляються.')
    h('Структура проєкту')
    code('''book-management-system-lab-05/
├── config.yaml, pyproject.toml, README.md, .gitignore
├── data/books.csv, data/books_100000.csv
├── src/book_io/
│   ├── config.py, exceptions.py, models.py, readers.py
│   ├── validators.py, services.py, exporters.py, resources.py
│   └── logging_config.py, datasets.py, experiments.py, main.py
├── tests/, tools/, docs/results/, docs/screenshots/
├── output/, logs/, docs/Lab_05_Report_Variant_2.docx
└── Lab_05/ (автономна копія)
    └── report/report.docx''')

    page('Exception hierarchy та custom exceptions')
    code(src('exceptions.py'))
    p('ApplicationError є базовим контрактом очікуваних помилок. ConfigurationError відокремлює startup failures, DataImportError — проблеми читання й структури файла, RecordValidationError — окремий некоректний запис, DataExportError — збій серіалізації чи commit. Номер рядка й поле передаються як контекст без збереження повного вихідного рядка.')
    p('Перехоплюються конкретні exceptions. Немає except: pass. EAFP застосовано до читання конфігурації та перетворення чисел, fail-fast — до важливих параметрів і шляхів до початку імпорту.')

    page('Exception chaining та diagnostics')
    validators = src('validators.py')
    code(validators[validators.index('    numbers:'):validators.index('    if not config.min_year')],8.5)
    picture('chain','Рисунок 1. Фактичний traceback ValueError → RecordValidationError.')
    p('Значення pages="wrong" спричиняє ValueError під час int(). Конструкція raise RecordValidationError(...) from error зберігає __cause__ та показує обидва рівні traceback. Ланцюжок допомагає відрізнити неправильне зовнішнє значення від проблеми експорту чи конфігурації.')

    page('YAML configuration та правила валідації')
    code((ROOT/'config.yaml').read_text(encoding='utf-8'),10)
    p('yaml.safe_load читає лише безпечні базові структури. schema_version повинен бути цілим 1; skip_invalid — YAML boolean, а не текст "false". Роки — цілі значення, 1 <= min_year <= max_year <= поточний рік. Невідомий формат або logging level відхиляється.')
    p('Відносні шляхи обчислюються від каталогу config.yaml. Input, output, log, summary і config мають різні шляхи. Вхідний файл перевіряється до обробки. Відсутні вихідні каталоги створюються під час роботи. Значення true/false змінює політику без редагування Python-коду.')

    page('Configuration loader та fail fast')
    config = src('config.py')
    p('Нижче наведено повний load_config у двох послідовних фрагментах. Імпорти: pathlib.Path, datetime.date, yaml, ConfigurationError та dataclass-моделі з book_io.models.')
    split = config.index('        input_path, output_path')
    code(config[config.index('def load_config'):split],8)
    page('Configuration loader продовження')
    code(config[split:config.index('def validate_config')],8)
    page('Перевірка шляхів конфігурації')
    code(config[config.index('def validate_config'):],8.5)
    p('Структура nested configuration перетворюється на frozen AppConfig, ProcessingConfig і LoggingConfig. KeyError, TypeError та ValueError перетворюються на ConfigurationError зі збереженням причини. Запуск із missing або malformed YAML завершується контрольовано до зміни основного output.')

    page('Streaming reader та importer interface')
    readers = src('readers.py')
    code(readers[readers.index('class Importer'):],8)
    p('CSV читається по одному запису, без list(reader), з encoding="utf-8-sig" і newline="". csv.DictReader підтримує quoted multiline. line_num показує фізичний рядок завершення запису. Пошкоджений CSV чи заголовок зупиняє імпорт; неправильні значення полів обробляються окремо за policy.')
    p('Додатковий JsonLinesImporter реалізує той самий Protocol. Кожна JSON Lines-помилка локалізована одним рядком і може бути зареєстрована та пропущена в tolerant mode. Звичайний JSON array використано для output, а не заявлено як streaming input.')

    page('Валідація ISBN та domain conversion')
    code(validators[validators.index('def valid_isbn'):validators.index('def parse_book')],8.5)
    p('ISBN-13 має 13 ASCII-цифр, префікс 978/979 та суму з вагами 1 і 3, кратну 10. ISBN-10 має дев’ять цифр і цифру або X в кінці; сума з вагами 10..1 кратна 11. Перед перевіркою прибираються дефіси й пробіли. Номер зберігається текстом.')
    p('parse_book перевіряє точний набір колонок, непорожній текст, int для року й сторінок, допустимий YAML-діапазон років і pages > 0. bool та float замість цілих не приймаються. Після цього створюється frozen dataclass Book; to_dict формує структуру для серіалізації.')
    code('''SourceRow(line, mapping)
    -> parse_book(source, processing_config)
    -> Book(isbn, title, author, year, pages)
    -> book.to_dict()
    -> JSON / JSON Lines''',10)

    page('Повна валідація запису книги')
    code(validators[validators.index('def parse_book'):],8)
    p('FIELDS = ("isbn", "title", "author", "year", "pages"). Функція повертає Book лише після проходження всіх перевірок; перша помилка містить номер рядка та поле.')

    page('Strict tolerant та import statistics')
    service = src('services.py')
    code(service[service.index('def import_books'):service.index('def process')],8.5)
    p('total збільшується для кожного отриманого запису. invalid рахує RecordValidationError, valid — успішні domain conversions. У strict mode bare raise повторно піднімає той самий виняток. У tolerant mode виконується warning, counter і continue. exported задається лише після успішного атомарного commit.')
    p('Генератор імпорту відкривається через closing; при припиненні експорту або першій строгій помилці файл закривається. Для великих наборів усі правильні книги не накопичуються у списку.')

    page('Atomic output та власний context manager')
    resources = src('resources.py')
    code(resources[resources.index('@contextmanager'):resources.index('@contextmanager\ndef logged_operation')],8)
    p('Temporary file створюється в тому самому каталозі з унікальною назвою. Після успішного запису виконуються flush, fsync, закриття та os.replace. При помилці finally прибирає temporary file; попередній output не відкривається для часткового перезапису. OSError перетворюється на DataExportError через chaining.')
    p('Це atomic replacement одного файла, а не спільна транзакція output і summary. Воно не заявляється як абсолютна гарантія від втрати живлення чи будь-яких filesystem failures. Тести перевіряють помилку всередині export і невдалий replace.')

    page('JSON serialization та application service')
    exports = src('exporters.py')
    code(exports[exports.index('class JsonExporter'):exports.index('class JsonLinesExporter')],8.5)
    code(service[service.index('def process'):],8)
    p('JSON array записується по одному object із роздільниками, тому не потрібний list усіх книг. ensure_ascii=False зберігає український текст; allow_nan=False відхиляє нестандартні числа. Окремий atomic JSON summary містить total, valid, invalid, exported.')

    page('Logging та lifecycle операції')
    code(resources[resources.index('@contextmanager\ndef logged_operation'):],8.5)
    logging_code = src('logging_config.py')
    code(logging_code[logging_code.index('def configure_logging'):],8)
    p('try/except/else/finally відокремлюють failure, success та завершення вимірювання. logger.exception додає traceback очікуваної ApplicationError; bare raise не приховує проблему. Rotation обмежує обсяг журналу, рівень і шлях задаються YAML. Повні CSV-рядки, passwords і tokens не журналюються.')

    page('Результат запуску та журнал')
    picture('application','Рисунок 2. Фактичний запуск CSV → JSON у tolerant mode.')
    picture('log','Рисунок 3. Реальний фрагмент application.log.')
    p('Для вхідних 8 записів: total=8, valid=4, invalid=4, exported=4. У log показано поле й причину кожної помилки. Успішний output містить лише коректні книги. Зображення сформовано з фактичного виводу; повні тексти збережено у docs/results.')

    evidence = json.loads((ROOT/'docs/results/experiments.json').read_text(encoding='utf-8'))
    page('Експерименти strict tolerant та atomic failure')
    table(['Режим','Total','Valid','Invalid','Exported'],[
        [row['mode'],row['total'],row['valid'],row['invalid'],row['exported']]
        for row in evidence['policies']])
    p('Вхід сформовано з 1000 valid records, після яких розташовано 10 invalid. Strict доходить до першої помилки після 1000 правильних: total=1001, invalid=1, exported=0. Попередній valid output зберігається. Tolerant читає всі 1010 та комітить 1000 книг. Необроблені дев’ять помилок у strict не включаються до counters.')
    p('Strict доцільний для узгодженого набору, де частковий результат неприпустимий. Tolerant — для очищення зовнішніх даних, коли правильні записи корисні окремо, а відхилення потрібно явно зареєструвати.')
    h('Навмисна помилка всередині export')
    table(['Перевірка','Результат'],[
        ['Тип помилки',evidence['atomic']['exception']],
        ['Контрольовано перехоплено',evidence['atomic']['controlled']],
        ['Попередній output незмінний',evidence['atomic']['previous_preserved']],
        ['Залишені temporary files',evidence['atomic']['temporary_files']],
    ])
    p('Generator видає першу книгу, після чого піднімає DataExportError. Частковий JSON залишається тільки у temporary file, який видаляється. logger.exception фіксує failure. Додатково test інжектує PermissionError у os.replace і перевіряє cleanup та original cause.')

    page('Експеримент streaming vs eager')
    table(['Записів','Eager c','Stream c','Eager MiB','Stream MiB'],[
        [f"{r['records']:,}".replace(',',' '),f"{r['eager']['seconds']:.4f}",
         f"{r['streaming']['seconds']:.4f}",f"{r['eager']['peak_bytes']/1048576:.3f}",
         f"{r['streaming']['peak_bytes']/1048576:.3f}"] for r in evidence['benchmark']])
    picture('benchmark','Рисунок 4. Реальні результати повного читання CSV.')
    p('Обидва варіанти читають ті самі файли й завершують повний обхід. Eager виконує list(csv.DictReader), streaming підраховує записи без повної матеріалізації. Кількість прочитаних записів дорівнює 10 000, 100 000 та 500 000. Генерація не вимірюється.')
    p('tracemalloc активний під час вимірювання, тому elapsed time включає його накладні витрати; peak є Python allocations, не повний RSS. Це один запуск на режим із можливим впливом кешу ОС. Streaming значно зменшив пам’ять; швидший час саме цього досліду не означає, що він завжди швидший.')

    page('Експеримент помилок конфігурації та перевірка')
    names = {'missing_config':'Немає config.yaml','malformed_yaml':'Неправильний YAML',
             'missing_input_key':'Немає ключа input','invalid_year_range':'Недопустимий діапазон років',
             'missing_input_file':'Немає input file','missing_output_directory':'Немає output directory'}
    table(['Сценарій','Exit code','Output існує'],[
        [names[r['case']],r['exit_code'],r['output_exists']] for r in evidence['configuration']])
    p('Кожний сценарій перевірено окремим subprocess реальної CLI. Перші п’ять завершилися з кодом 1 без нового output. Відсутній output directory створено автоматично, код 0. Параметр minimum_grade з прикладу варіанта студентів замінено перевіркою діапазону років, який вимагає варіант 2.')
    p('Усі 21 автоматизований тест пройдено, перевірка стилю Ruff також пройшла. Додатково перевірено multiline CSV, missing/extra columns, ISBN-10/13, JSON Lines roundtrip, bool/float замість int, рядок "false" замість YAML boolean, path collisions, lazy open та закриття ресурсу після early termination.')
    p('Додаткові можливості: Importer/Exporter Protocols, format selection, JSON Lines, nested configuration, schema version, configurable logging, log rotation, власні context managers, atomic export і JSON summary. Це більше ніж три додаткові можливості з методички.')

    for start in range(0,70,10):
        page(f'Відповіді на контрольні запитання {start+1}–{start+10}')
        for i,(question,answer) in enumerate(QA[start:start+10],start+1):
            para = p('')
            para.paragraph_format.keep_with_next = True
            para.add_run(f'{i}. {question}').bold = True
            p(answer)

    page('Висновок')
    p('Реалізовано надійний імпорт та експорт системи обліку книг за варіантом 2. Зовнішні CSV/JSON Lines-записи перевіряються до domain conversion, а помилки мають конкретний тип, контекст і збережену причину. YAML configuration керує роками, політикою валідації та журналюванням. Strict і tolerant режими мають різні контрольовані результати.')
    p('Context managers закривають ресурси та прибирають temporary output. Streaming input/output дозволяють обробляти великі файли без накопичення всіх записів. Atomic replacement зберігає попередній output при навмисній помилці експорту. П’ять експериментів і автоматизовані тести підтверджують поведінку за нормальних та помилкових умов.')
    h('Використані матеріали')
    p('Методичка Lab_05_узгоджено_з_Lab_01.docx: розділи 1–96; варіант 2 з розділу 58; експерименти з розділів 77–83; вимоги до звіту з розділу 91.')
    p('Репозиторій: https://github.com/Olexandr-Brovdi/book-management-system-lab-05')
    doc.core_properties.author = 'Бровді Олександр'
    doc.core_properties.title = 'Лабораторна робота 5 Імпорт та експорт системи обліку книг Варіант 2'
    output = ROOT/'docs/Lab_05_Report_Variant_2.docx'
    doc.save(output)
    target = ROOT/'Lab_05/report/report.docx'
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(output,target)
    print(output)


if __name__ == '__main__':
    build()
