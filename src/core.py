"""Banker's Algorithm core (F.CSM302 BD1, topic 13).

UI-gui, zuvhun algoritm. Bусад гишүүд зөвхөн энэ интерфейсээр харьцана.

Нэр томьёо:
  available  -- ОДОО чөлөөтэй байгаа нөөц (Allocation-ийг аль хэдийн хассан).
                Номын CLI-д (./a.out 10 5 7) өгөх НИЙТ нөөцийг CLI давхарга
                available = total - sum(allocation) болгож хөрвүүлнэ.
  maximum    -- n x m, процесс бүрийн дээд хэрэгцээ
  allocation -- n x m, одоо эзэлж буй (өгөхгүй бол бүгд 0)
  need       -- maximum - allocation (тооцогдоно)
"""

GRANTED = "granted"
WAIT = "wait"
UNSAFE = "unsafe"
ERROR = "error"
RELEASED = "released"


class BankerError(ValueError):
    """Буруу оролт."""


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _check_vector(v, m, name):
    if not isinstance(v, (list, tuple)) or len(v) != m:
        raise BankerError(f"{name}: {m} урттай жагсаалт байх ёстой")
    for x in v:
        if not _is_int(x):
            raise BankerError(f"{name}: бүхэл тоо байх ёстой (олдсон: {x!r})")
        if x < 0:
            raise BankerError(f"{name}: сөрөг тоо байж болохгүй ({x})")
    return [int(x) for x in v]


def _check_matrix(mat, n, m, name):
    if not isinstance(mat, (list, tuple)) or len(mat) != n:
        raise BankerError(f"{name}: {n} мөртэй байх ёстой")
    return [_check_vector(row, m, f"{name}[P{i}]") for i, row in enumerate(mat)]


class Banker:
    def __init__(self, available, maximum, allocation=None):
        if not isinstance(maximum, (list, tuple)) or len(maximum) == 0:
            raise BankerError("maximum: хоосон байж болохгүй")
        if not isinstance(available, (list, tuple)) or len(available) == 0:
            raise BankerError("available: хоосон байж болохгүй")
        self.n = len(maximum)
        self.m = len(available)
        self.available = _check_vector(available, self.m, "available")
        self.maximum = _check_matrix(maximum, self.n, self.m, "maximum")
        if allocation is None:
            allocation = [[0] * self.m for _ in range(self.n)]
        self.allocation = _check_matrix(allocation, self.n, self.m, "allocation")
        for i in range(self.n):
            for j in range(self.m):
                if self.allocation[i][j] > self.maximum[i][j]:
                    raise BankerError(
                        f"allocation[P{i}][R{j}]={self.allocation[i][j]} нь "
                        f"maximum={self.maximum[i][j]}-аас их байна")
        self.enforce = True   # False бол request() safety шалгахгүй (Banker унтраалттай горим)
        self._initial = (list(self.available),
                         [r[:] for r in self.maximum],
                         [r[:] for r in self.allocation])

    # ---------- төлөв ----------
    @property
    def need(self):
        return [[self.maximum[i][j] - self.allocation[i][j]
                 for j in range(self.m)] for i in range(self.n)]

    def reset(self):
        a, mx, al = self._initial
        self.available = list(a)
        self.maximum = [r[:] for r in mx]
        self.allocation = [r[:] for r in al]

    # ---------- safety algorithm ----------
    def is_safe(self):
        """(safe, sequence, steps). sequence нь процессын индексүүд.
        steps: [{process, work_before, work_after}] (процессын индекс)."""
        need = self.need
        work = list(self.available)
        finish = [False] * self.n
        sequence, steps = [], []
        while True:
            found = None
            for i in range(self.n):
                if not finish[i] and all(need[i][j] <= work[j] for j in range(self.m)):
                    found = i
                    break
            if found is None:
                break
            before = list(work)
            work = [work[j] + self.allocation[found][j] for j in range(self.m)]
            finish[found] = True
            sequence.append(found)
            steps.append({"process": found, "work_before": before,
                          "work_after": list(work)})
        safe = all(finish)
        return safe, (sequence if safe else []), (steps if safe else steps)

    def valid_sequence(self, seq):
        """Өгсөн дараалал яг одоогийн төлөвт хүчинтэй эсэхийг шалгана."""
        if sorted(seq) != list(range(self.n)):
            return False
        need = self.need
        work = list(self.available)
        for i in seq:
            if any(need[i][j] > work[j] for j in range(self.m)):
                return False
            work = [work[j] + self.allocation[i][j] for j in range(self.m)]
        return True

    # ---------- resource-request algorithm ----------
    def _validate_call(self, i, vec, name):
        if not _is_int(i) or not (0 <= i < self.n):
            raise BankerError(f"Процесс P{i} байхгүй (0..{self.n - 1})")
        return _check_vector(vec, self.m, name)

    def request(self, i, req):
        """Буцаах: (status, message). Granted биш бол төлөв ӨӨРЧЛӨГДӨХГҮЙ."""
        try:
            req = self._validate_call(i, req, "request")
        except BankerError as e:
            return ERROR, str(e)
        need = self.need[i]
        for j in range(self.m):
            if req[j] > need[j]:
                return ERROR, (f"P{i}-ийн хүсэлт Need-ээс хэтэрсэн: "
                               f"R{j} хүсэлт={req[j]}, Need={need[j]}")
        for j in range(self.m):
            if req[j] > self.available[j]:
                return WAIT, (f"P{i} хүлээнэ: R{j} хүсэлт={req[j]}, "
                              f"Available={self.available[j]}")
        # түр олгох
        for j in range(self.m):
            self.available[j] -= req[j]
            self.allocation[i][j] += req[j]
        if not self.enforce:
            return GRANTED, f"P{i}-д олголоо (Banker унтраалттай: safety шалгаагүй)"
        safe, _, _ = self.is_safe()
        if safe:
            return GRANTED, f"P{i}-д олголоо; төлөв safe хэвээр"
        # rollback
        for j in range(self.m):
            self.available[j] += req[j]
            self.allocation[i][j] -= req[j]
        return UNSAFE, f"P{i}-ийн хүсэлтийг олговол unsafe болно; татгалзлаа"

    def release(self, i, rel):
        try:
            rel = self._validate_call(i, rel, "release")
        except BankerError as e:
            return ERROR, str(e)
        for j in range(self.m):
            if rel[j] > self.allocation[i][j]:
                return ERROR, (f"P{i} барьж буйгаасаа их чөлөөлөх гэж байна: "
                               f"R{j} чөлөөлөх={rel[j]}, Allocation="
                               f"{self.allocation[i][j]}")
        for j in range(self.m):
            self.available[j] += rel[j]
            self.allocation[i][j] -= rel[j]
        return RELEASED, f"P{i} чөлөөллөө"

    # ---------- UI-д зориулсан JSON ----------
    def to_json(self):
        safe, seq, steps = self.is_safe()
        name = lambda k: f"P{k}"
        return {
            "n": self.n, "m": self.m,
            "available": list(self.available),
            "max": [r[:] for r in self.maximum],
            "allocation": [r[:] for r in self.allocation],
            "need": self.need,
            "safe": safe,
            "sequence": [name(k) for k in seq],
            "steps": [{"process": name(s["process"]),
                       "work_before": s["work_before"],
                       "work_after": s["work_after"]} for s in steps],
        }
