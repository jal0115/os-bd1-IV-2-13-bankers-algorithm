# Banker's Algorithm – F.CSM302 Үйлдлийн систем, Бие даалт 1

**Хуваарилалтын код:** IV-2-13
**Төсөл:** Banker's Algorithm (Silberschatz, *Operating System Concepts*, 8-р бүлэг, Programming Projects)
**Үндсэн дүрслэл:** Resource graph (процесс–нөөцийн граф, Safe sequence алхамчилсан)
**Хичээл заасан багш:** Г.Ганбат /F.CS10/

## Зорилго

Banker's Algorithm-аар түгжрэлээс (deadlock) сэргийлэх алгоритмыг сурах бичгийн шаардлагын дагуу бүрэн хэрэгжүүлж,
Allocation / Max / Available өгөгдөл болон хүсэлтийг өөрчилж дахин турших, safe state ба safe sequence-ийг
Resource graph-аар алхам алхмаар харуулах.

![Resource graph: Safe sequence-ийн 3-р алхам](docs/screenshots/s02_graph_step3.png)

## Юу хийж чадах вэ

- **Цөм (`core.py`)**: Need, Safety algorithm, Resource-Request algorithm (rollback-тай), Release, Reset. UI-аас хараат бус.
- **CLI (`cli.py`)**: номын шаардлагын дагуу `RQ`, `RL`, `*`, `exit`; нийт нөөц аргументаар, Max файлаас.
- **Вэб UI**: Allocation / Max / Available-г хүснэгтэнд засах, +/− процесс, нөөц, хүсэлт ба чөлөөлөлт илгээх,
  Request бүрийн 3 шалгалтыг ✔/✘-ээр харах, Safety analysis, хүсэлтийн түүх, Reset, бэлэн сценари
  (Номын жишээ, Unsafe эхний төлөв, Том туршилт 10×5, Banker-гүй).
- **Resource graph (`graph.js`)**: цэнхэр сум = Allocation (нөөц → процесс), саарал тасархай сум = Need (процесс → нөөц);
  «▶ Эхлүүлэх» дарахад процесс дуусах бүрд сумнууд алга болж, нөөц чөлөөтэй болж, Work нэмэгдэнэ.

## Quick Start

Шаардлага: **Python 3.10+** (туршсан: 3.12.3), Chrome / Edge / Firefox. Веб UI, CLI-д гадны сан шаардлагагүй, интернет хэрэггүй.
`pytest` нь зөвхөн автомат тестэд хэрэгтэй.

```bash
git clone https://github.com/jal0115/os-bd1-IV-2-13-bankers-algorithm.git
cd os-bd1-IV-2-13-bankers-algorithm
```

**1. Вэб UI** (үндсэн)

```bash
python src/server.py            # Mac/Linux: python3 src/server.py
```

Терминалд `Banker's Algorithm UI: http://127.0.0.1:5000 (зогсоох: Ctrl+C)` гарна. Хөтчөөр **http://127.0.0.1:5000** нээнэ,
номын жишээ ачаалагдсан байна. «▶ Эхлүүлэх» дарж Safe sequence-ийг граф дээр алхам алхмаар хар.
Порт завгүй бол: `python src/server.py --port 5001`. UI хуучин харагдвал `Ctrl+Shift+R`.

**2. CLI** (сурах бичгийн төсөл)

```bash
python src/cli.py 10 5 7 --max examples/book_max.txt --allocation examples/book_allocation.txt < examples/book_commands.txt
```

Хүлээгдэх гаралт: эхний төлөв `SAFE <P1, P3, P0, P2, P4>`, дараа нь `granted` → `wait` → `unsafe`.
Гараар оруулах бол `< examples/book_commands.txt`-ийг орхиж `RQ 1 1 0 2`, `RL 1 1 0 0`, `*`, `exit` бичнэ.

**3. Автомат тест**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q              # хүлээгдэх үр дүн: 64 passed
```

Дэлгэрэнгүй заавар, жишээ, алдаа ба шийдэл: **[docs/IV-2-13_Manual.pdf](docs/IV-2-13_Manual.pdf)**.
Судалгаа, туршилтын үр дүн: **[docs/IV-2-13_BD1_Report.pdf](docs/IV-2-13_BD1_Report.pdf)**.

## Бүтэц

| Зам | Агуулга |
|---|---|
| `src/core.py` | Banker цөм: Safety, Resource-Request (rollback), Release, Reset, `to_json` |
| `src/cli.py` | Номын төслийн командын мөрийн хувилбар (`RQ`, `RL`, `*`) |
| `src/server.py` | HTTP сервер + JSON API (Python стандарт сан) |
| `src/ui/index.html` | UI: өгөгдлийн хүснэгт, хүсэлтийн форм, Safety analysis, түүх |
| `src/ui/graph.js` | Resource graph (inline SVG), тоглуулах удирдлага |
| `tests/` | 5 файл, 64 автомат тест (цөм 15, CLI 24, CLI төлөв 7, сервер 13, Banker унтраалттай 5) |
| `examples/` | Номын 8.6.3 жишээний Max, Allocation, командууд |
| `docs/` | Manual, Report, `screenshots/`, `data-format.md`, `requirements.md` |

## Баг

Хуваарилалтын 6 үүргийг тайлангийн Хавсралт A-тай нийцүүлэн бичив.

| Гишүүн | Хариуцсан ажил | Файл |
|---|---|---|
| Г.Лувсанжал /B242270016/ (GitHub: jal0115) | Цөм алгоритм ба CLI: Need, Safety, Resource-Request, rollback | `src/core.py`, `src/cli.py`, `tests/` |
| Г.Ганжаргал /B222270701/ | CLI команд, файл унших хэсгийн анхны бүтэц | `src/cli.py` |
| Б.Лхагвадорж /B231940136/ | Вэб UI-ийн хүснэгт, анхны загвар (дэмжлэг) | `src/ui/index.html` |
| У.Анужин /B241940071/ | UI, Resource graph, Safe sequence алхамчилсан төлөв, UI/UX сайжруулалт, нэмэлт тест | `src/ui/index.html`, `src/ui/graph.js` |
| Я.Төгөлдөр /B242270806/ | Safe sequence ба төлөвийн логикийг шалгахад хамтарсан (дэмжлэг) | `src/ui/` |
| Г.Ганхүү /B210930028/ | Docs, Manual, README | `docs/`, `README.md` |

## Бэлэн код, сан, AI ашигласан зүйл

- **Сан:** Python стандарт сан (`http.server`, `argparse`, `json`); тестэд `pytest`. UI-д гадны JS/CSS сан, CDN ашиглаагүй,
  граф нь inline SVG.
- **Алгоритм:** псевдокод нь сурах бичгийн 8-р бүлэгт тулгуурласан.
- **AI:** Claude (Anthropic), Gemini (Google) туслах хэрэгслээр ашигласан: core алгоритм ба автомат тестийн эхний бүтцийн санаа;
  UI-ийн layout, харагдах байдал, UX-ийн сайжруулалт; баримт бичгийн төсөл. AI-аас гарсан санаа, кодыг багийн гишүүд нэг бүрчлэн нягтлан шалгаж, өөрсдийн логикоор оновчлон, автомат тестүүдийг бүрэн ажиллуулж баталгаажуулсан. Дэлгэрэнгүй: Report 5.5.
- Нууц түлхүүр, нууц үг, хувийн өгөгдөл репод байхгүй.

## Мэдэгдэж буй хязгаарлалт

- Сервер нэг хэрэглэгчийн төлвийг санах ойд хадгална (олон таб нэг төлөв хуваалцана, дахин асаахад номын жишээ рүү буцна).
- Олон thread-тэй customer (mutex) загвар хэрэгжээгүй; хүсэлтүүд дарааллаар боловсруулагдана.
- 10×5 дээр граф дахь сумнууд давхцана; процесс эсвэл нөөц дээр дарж холбоотой сумыг тодруулна.
