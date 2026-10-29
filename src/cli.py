"""Banker's Algorithm CLI (сурах бичиг Ch. 8 Programming Project).

Ажиллуулах:
    python src/cli.py <нийт_нөөц...> --max <файл> [--allocation <файл>]

Жишээ (номын 8.6.3 жишээ, нийт нөөц 10 5 7):
    python src/cli.py 10 5 7 --max examples/book_max.txt \
        --allocation examples/book_allocation.txt

Командууд (0-ээс эхэлсэн процессын дугаар):
    RQ <customer> <r0> <r1> ...   нөөц хүсэх
    RL <customer> <r0> <r1> ...   нөөц чөлөөлөх
    *                             Available, Max, Allocation, Need хэвлэх
    exit                          гарах

Анхаар: номын шаардлагаар Available нь НИЙТ нөөцөөр эхэлж, Allocation 0 байна.
--allocation нь заавал биш нэмэлт сонголт; өгвөл
available = нийт − Σ allocation болно.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Banker, BankerError  # noqa: E402


class CliError(Exception):
    """Эхлүүлэх үеийн оролтын алдаа."""


def parse_int(text, what):
    try:
        return int(text)
    except ValueError:
        raise CliError(f"{what}: бүхэл тоо байх ёстой (олдсон: {text!r})")


def load_matrix(path, m, name):
    """Файлаас n x m матриц уншина. Мөр бүр нэг процесс, таслал эсвэл
    хоосон зайгаар тусгаарласан. Хоосон мөр болон # тайлбарыг алгасна."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as e:
        raise CliError(f"{name}: файл нээгдсэнгүй ({path}): {e.strerror}")
    rows = []
    for lineno, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p for p in line.replace(",", " ").split() if p]
        row = [parse_int(p, f"{name}, {lineno}-р мөр") for p in parts]
        if len(row) != m:
            raise CliError(f"{name}, {lineno}-р мөр: {m} утга байх ёстой, "
                           f"{len(row)} олдлоо")
        if any(x < 0 for x in row):
            raise CliError(f"{name}, {lineno}-р мөр: сөрөг тоо байж болохгүй")
        rows.append(row)
    if not rows:
        raise CliError(f"{name}: файл хоосон байна ({path})")
    return rows


def build_banker(total, max_path, alloc_path=None):
    """(Banker, анхааруулгууд). Нийт нөөцөөс available-ийг тооцно."""
    if not total:
        raise CliError("нийт нөөцийг аргументаар өгнө үү, жишээ нь: 10 5 7")
    if any(t < 0 for t in total):
        raise CliError("нийт нөөц сөрөг байж болохгүй")
    m = len(total)
    maximum = load_matrix(max_path, m, "Max")
    n = len(maximum)
    allocation = None
    if alloc_path:
        allocation = load_matrix(alloc_path, m, "Allocation")
        if len(allocation) != n:
            raise CliError(f"Allocation {len(allocation)} мөртэй, Max {n} "
                           f"мөртэй байна; ижил байх ёстой")
    held = [sum((allocation[i][j] if allocation else 0) for i in range(n))
            for j in range(m)]
    available = [total[j] - held[j] for j in range(m)]
    for j in range(m):
        if available[j] < 0:
            raise CliError(f"Allocation-ийн нийлбэр R{j}-ийн нийт нөөцөөс "
                           f"их байна ({held[j]} > {total[j]})")
    warnings = []
    for i in range(n):
        for j in range(m):
            if maximum[i][j] > total[j]:
                warnings.append(f"анхааруулга: P{i}-ийн Max[R{j}]="
                                f"{maximum[i][j]} нь нийт нөөц {total[j]}-аас "
                                f"их тул P{i} хэзээ ч дуусч чадахгүй")
    try:
        return Banker(available, maximum, allocation), warnings
    except BankerError as e:
        raise CliError(str(e))


def format_state(b):
    def mat(title, rows):
        out = [title]
        for i, r in enumerate(rows):
            out.append(f"  P{i}: " + " ".join(f"{x:>3}" for x in r))
        return out
    lines = ["Available: " + " ".join(str(x) for x in b.available)]
    lines += mat("Max:", b.maximum)
    lines += mat("Allocation:", b.allocation)
    lines += mat("Need:", b.need)
    safe, seq, _ = b.is_safe()
    lines.append("Төлөв: " + ("SAFE  <" + ", ".join(f"P{i}" for i in seq) + ">"
                              if safe else "UNSAFE"))
    return "\n".join(lines)


def execute(b, line):
    """Нэг командыг гүйцэтгэж хэвлэх текст буцаана. 'exit' үед None."""
    parts = line.split()
    if not parts:
        return ""
    cmd = parts[0].upper()
    if cmd in ("EXIT", "QUIT"):
        return None
    if cmd == "*":
        return format_state(b)
    if cmd in ("RQ", "RL"):
        if len(parts) != 2 + b.m:
            return (f"алдаа: {cmd} <customer> + {b.m} нөөцийн утга хэрэгтэй "
                    f"(жишээ: {cmd} 0 " + " ".join(["1"] * b.m) + ")")
        try:
            nums = [int(p) for p in parts[1:]]
        except ValueError:
            return f"алдаа: {cmd}-ийн бүх аргумент бүхэл тоо байх ёстой"
        i, vec = nums[0], nums[1:]
        status, msg = (b.request(i, vec) if cmd == "RQ" else b.release(i, vec))
        return f"{status}: {msg}"
    return f"алдаа: мэдэхгүй команд {parts[0]!r} (RQ, RL, *, exit)"


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="cli.py", description="Banker's Algorithm (сурах бичиг Ch. 8)")
    p.add_argument("resources", nargs="*", metavar="R",
                   help="нийт нөөц, жишээ нь: 10 5 7")
    p.add_argument("--max", dest="max_file", required=True,
                   help="Max матрицын файл (мөр = процесс, таслалаар)")
    p.add_argument("--allocation", dest="alloc_file", default=None,
                   help="(нэмэлт) эхний Allocation матрицын файл")
    return p.parse_args(argv)


def main(argv=None, stdin=None, out=None):
    stdin = stdin if stdin is not None else sys.stdin
    out = out if out is not None else sys.stdout
    try:
        args = parse_args(argv if argv is not None else sys.argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        total = [parse_int(r, "нөөц") for r in args.resources]
        b, warnings = build_banker(total, args.max_file, args.alloc_file)
    except CliError as e:
        print(f"алдаа: {e}", file=out)
        return 2
    for w in warnings:
        print(w, file=out)
    interactive = hasattr(stdin, "isatty") and stdin.isatty()
    while True:
        if interactive:
            out.write("command> ")
            out.flush()
        line = stdin.readline()
        if line == "":
            break
        res = execute(b, line.strip())
        if res is None:
            break
        if res:
            print(res, file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
