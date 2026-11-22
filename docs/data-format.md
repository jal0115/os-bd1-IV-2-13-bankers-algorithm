# Core ↔ UI өгөгдлийн формат ба интерфейс

Хуваарилалтын код: IV-2-13 · Сэдэв 13 · Banker's Algorithm

Цөм: `src/core.py`. Тест: `tests/test_core.py`.

## 1. Нэр томьёо

| Нэр | Утга |
|---|---|
| `available` | ОДОО чөлөөтэй нөөц (Allocation-ийг хассан) |
| `max` | n × m, процесс бүрийн дээд хэрэгцээ |
| `allocation` | n × m, одоо эзэлж буй нөөц |
| `need` | `max − allocation` (цөм тооцно, гараар өгөхгүй) |
| Процесс | `P0 … P(n-1)`, индекс нь 0-ээс эхэлнэ |
| Нөөц | `R0 … R(m-1)` |

**CLI-ийн оролт:** номын CLI `./a.out 10 5 7` гэж НИЙТ нөөц өгдөг.
Цөм харин одоо чөлөөтэй нөөцийг авдаг тул CLI дээр:

```
available = total − Σ allocation   (багана бүрээр)
```

Allocation эхэндээ 0 бол `available = total`.

## 2. Python интерфейс

```python
from core import Banker, BankerError, GRANTED, WAIT, UNSAFE, ERROR, RELEASED

b = Banker(available, maximum, allocation=None)   # буруу оролтод BankerError
```

| Дуудлага | Буцаах утга |
|---|---|
| `b.need` | `list[list[int]]` |
| `b.is_safe()` | `(safe: bool, sequence: list[int], steps: list[dict])`, индексээр |
| `b.valid_sequence(seq)` | `bool`, дарааллыг шалгана |
| `b.request(i, req)` | `(status, message)` |
| `b.release(i, rel)` | `(status, message)` |
| `b.reset()` | Анх ачаалсан төлөвт буцаана |
| `b.to_json()` | `dict` (доорх §3), процессууд `"P1"` нэртэй |

### Статусууд

| `request()` | Утга | Төлөв өөрчлөгдөх үү |
|---|---|---|
| `granted` | Олгосон. Banker асаалттай бол төлөв SAFE хэвээр | Тийм |
| `wait` | Request > Available, хүлээнэ | Үгүй |
| `unsafe` | Олговол unsafe болно, татгалзсан (rollback) | Үгүй |
| `error` | Буруу оролт, эсвэл Request > Need | Үгүй |

| `release()` | Утга |
|---|---|
| `released` | Амжилттай |
| `error` | Буруу оролт, эсвэл барьж буйгаасаа их чөлөөлөх гэсэн |

`message` нь хэрэглэгчид шууд харуулах боломжтой ойлгомжтой текст (жишээ нь
`P1-ийн хүсэлт Need-ээс хэтэрсэн: R0 хүсэлт=2, Need=1`).

Анхаарах:
- `Banker(...)` үүсгэхэд буруу оролт бол **exception** шиднэ. `request`/`release` нь exception шидэхгүй, `error` статус буцаана.
- Алдаа, `wait`, `unsafe` үед төлөв ЯГ өмнөх хэвээр үлдэнэ.

## 3. `to_json()`-ы формат

Номын жишээ (Available = 3,3,2):

```json
{
  "n": 5,
  "m": 3,
  "available": [3, 3, 2],
  "max":        [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]],
  "allocation": [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]],
  "need":       [[7,4,3],[1,2,2],[6,0,0],[0,1,1],[4,3,1]],
  "safe": true,
  "sequence": ["P1", "P3", "P0", "P2", "P4"],
  "steps": [
    {"process": "P1", "work_before": [3,3,2],   "work_after": [5,3,2]},
    {"process": "P3", "work_before": [5,3,2],   "work_after": [7,4,3]},
    {"process": "P0", "work_before": [7,4,3],   "work_after": [7,5,3]},
    {"process": "P2", "work_before": [7,5,3],   "work_after": [10,5,5]},
    {"process": "P4", "work_before": [10,5,5],  "work_after": [10,5,7]}
  ]
}
```

- `work_after = work_before + allocation[process]`.
- Дараалал номын `<P1,P3,P4,P2,P0>`-аас өөр боловч **хүчинтэй**. Цөм P0-оос эхлэн хайдаг. UI-д яг тэр нэг дарааллыг хүлээж болохгүй.
- **Unsafe үед:** `"safe": false`, `"sequence": []`. `steps` нь дуусч чадсан процессуудын хэсэгчилсэн жагсаалт (огт байхгүй бол `[]`). Unsafe яагаад гэдгийг UI дээр харуулахдаа `steps`-д ороогүй процессуудыг "дуусч чадаагүй" гэж тайлбарлаж болно.

## 4. Вэб API-ийн хариу

`POST /api/request` болон `POST /api/release` хоёр талбар буцаана.

| Талбар | Агуулга |
|---|---|
| `request_result` | Үйлдлийн `status` болон хэрэглэгчид харуулах `message` |
| `state` | Үйлдлийн дараах батлагдсан төлөв. §3-ын талбарууд дээр Banker горимын `enforce` нэмэгдэнэ. |

Жишээлбэл, P0-ийн хүсэлтэд `request_result.status` нь `unsafe` байхад
`state.safe` нь `true` байж болно. Эхнийх нь түр олголтыг яагаад
буцаасныг, хоёр дахь нь буцаасны дараах системийн төлвийг заана.

## 5. Бэлэн жишээний өгөгдөл

Вэб интерфейс болон `tests/test_ui_scenarios.py` нь 3×2, 10×5 жишээг
`src/ui/scenarios.json` файлаас уншина. Жишээний тоог өөрчилсөн бол
`python -m pytest -q tests/test_ui_scenarios.py` командаар шалгана.

## 6. Ажиллуулах

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q          # БД2-ын нийт 75 тест
```

Хурдан туршилт:

```bash
PYTHONPATH=src python3 -c "
from core import Banker
b = Banker([3,3,2],
           [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]],
           [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]])
print(b.is_safe()[1])
print(b.request(1,[1,0,2]))
print(b.request(4,[3,3,0]))
print(b.request(0,[0,2,0]))
"
```

Хүлээгдэх үр дүн: дараалал (хүчинтэй), дараа нь `granted`, `wait`, `unsafe`.
(Эдгээр нь **дараалсан** хүсэлт: P1 олгогдсоны дараа Available = 2,3,0 болно.)

## 7. Мэдэгдэж буй шийдвэрүүд (номд тодорхой биш)

- Барьж буйгаасаа их чөлөөлөх (`RL`) нь `error`.
- Номын `request_resources()` нь `wait`, `unsafe` хоёуланд `-1` буцаадаг. Бид UI-д шалтгааныг ялгахын тулд статусыг тусад нь буцаана.
- Allocation нь Max-аас их байж болохгүй (`Banker(...)` дээр `BankerError`).

## 8. AI ашигласан тухай

Core алгоритмын эхний хувилбарыг AI-ийн тусламжтайгаар бичсэн. Баг хянаж,
тестээр баталгаажуулсан.
