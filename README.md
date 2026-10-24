# Banker's Algorithm – F.CSM302 БД1

**Хуваарилалтын код:** IV-2-13
**Сэдэв:** 13 – Banker's Algorithm (Silberschatz, Operating System Concepts, Ch. 8)
**Үндсэн дүрслэл:** Resource graph

## Зорилго
Banker's Algorithm-аар deadlock-аас сэргийлэх алгоритмыг хэрэгжүүлж,
Allocation/Max/Available өгөгдлийг өөрчлөн хүсэлт илгээж, safe state болон
safe sequence-ийг resource graph-аар харуулна.

## Quick Start
(8-р долоо хоногт бөглөнө)

Цөмийг туршиж үзэх:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python -m pytest -q

Цөмийн интерфейс, JSON формат: docs/data-format.md

## Баг
| Гишүүн | Үүрэг |
|---|---|
| jal0115 | Team lead / Core algorithm |
| (нэр) | Input / CLI / Validation |
| (нэр) | UI хүснэгт ба удирдлага |
| (нэр) | Resource graph |
| (нэр) | Safe sequence ба state view |
| (нэр) | Test / Docs / GitHub |

## Бэлэн код, сан, AI ашигласан зүйл
- Core алгоритмын (src/core.py) эхний хувилбар болон тестийг AI (Claude)-ийн
  тусламжтайгаар бичсэн. Баг хянаж, тестээр баталгаажуулсан.
- Сан: pytest (тест).# os-bd1-4-2-13-bankers-algorithm
