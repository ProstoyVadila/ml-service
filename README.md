# Распознование фотки ТО

## Схема работы

```txt
photo -> OCR -> text -> LLM -> JSON -> Database

photo -> Database (S3/MinIO ?)
```

## OCR

Все ocr handlers связаны в цепочку с помощью `OCRChainFactory` и должны реализовывать `BaseOCRHandler`, а именно, как минимум, абстрактный метод `_process_image`.
Каждый ocr хэндлер имеет, по сути, 3 ключвых метода: `process`, `should_skip`, `can_accept`.
`Process` запускает `_process_image` в отдельном потоке, но перед этим с помощью `should_skip` проверяет имеет ли смысл вообще запускать данный OCR или лучше сразу переключится на следующий (например, размер изображения превышает лимит OCR Space API), уже после успешного получения текста он запускает `can_accept`. Это метод должен убедится в качестве рекогнишена, насколько текст ок (confidence выше какого-то значения). Если `can_accept` не проходит, то фотка передается следующему ocr по цепочке и всё начинается сначала.

На данный момент добавлены такие ocr handler'ы:

- OCR Space (внешнее API, 25k запросов в месяц)
- EasyOCR модель подгружается локально при запуске
- Tesseract (надо убедиться, что модель подгружается локально)

## TODO

- добавить экстракторы с локальной phi-2
- добавить таймеры на запросы к моделям
- добавить временное или lru кэширование результатов на всякий
- добавить установку tesseract и всех нужных зависимостей в Dockerfile
- улучшить расчёт confidence для llm (сейчас либо всё, либо ничего)

## LLM Clients

Содержит интерфейсы работы с llm моделями. По сути скрывают реализацию общение с внешним API это или локально запущенная модель. На данный момент содержит API DeepSeek. Планирую добавить компактную локальную модель phi-2.

Каждый LLM клиент должен реализовывать метод `chat`.

## Extractors

Содержат два базовых типа экстракторов — `BaseFieldExtractor`, `BaseMultiFieldExctractor`. Первый расчитан на получение только одного поля (это имеет смысл для использования с глупыми моделями или для даже просто regex), второй — на сбор сразу всех полей. Для перевода списка `BaseFieldExtractor` в один `BaseMultiFieldExtractor` используется адаптер `FieldToMultiAdapter`.

Реализованы несколько стратегий выбора моделей (только локальные, только внешние, внешние как бэкап, оба вида). На их основе оркестратор запускает конкретные экстракторы.

## Контракт с ботом

По сути им является `VehicleMaintenanceMLService`, который содержит пока что единственный метод `extract_maintenance_data`.

```python
@dataclass
class MaintenanceExtractionRequest:
    image: bytes


@dataclass
class MaintenanceData:
    date: str
    mileage: str
    price: str
    works: list[str]
    materials: list[str]


@dataclass
class MaintenanceExtractionResponse:
    success: bool
    error_message: str | None
    data: MaintenanceData | None
    raw_fields: list[ExtractionField]
    raw_text: str
    ocr_source: str
    ocr_confidence: float
    extractor_source: str
    extractor_confidence: float

class VehicleMaintenanceMLService:
    def extract_maintenance_data(self, request: MaintenanceExtractionRequest) -> MaintenanceExtractionResponse:
        ...

```

## Возможные доработки

- добавить для deepseek time based стратегию (у них скидки в 50%-75% в определенные часы)
- Разрешить пользователю подтвердить или отредактировать данные;
- использовать llm для валидации текста из ocr и его корректировки
- использовать другую llm (напримел, локальную) для валидации ответа llm
- добавить валидацию фото;
- добавить троттлинг отправки фоток ТО на уровне бота;
- обогащать JSON данными из других источников.
