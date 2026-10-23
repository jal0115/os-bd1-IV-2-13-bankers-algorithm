import itertools
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from core import (Banker, BankerError, GRANTED, WAIT, UNSAFE, ERROR,  # noqa: E402
                  RELEASED)

BOOK_MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
BOOK_ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]


def book():
    return Banker([3, 3, 2], BOOK_MAX, BOOK_ALLOC)


def brute_safe(b):
    """Бие даасан шалгагч: бүх permutation туршина (жижиг n)."""
    return any(b.valid_sequence(list(p))
               for p in itertools.permutations(range(b.n)))


def test_book_need():
    assert book().need == [[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]]


def test_book_initial_safe():
    b = book()
    safe, seq, steps = b.is_safe()
    assert safe and b.valid_sequence(seq)
    assert b.valid_sequence([1, 3, 4, 2, 0])      # номын <P1,P3,P4,P2,P0>
    assert b.valid_sequence([1, 3, 4, 0, 2])
    assert steps[0] == {"process": 1, "work_before": [3, 3, 2],
                        "work_after": [5, 3, 2]}
    assert steps[-1]["work_after"] == [10, 5, 7]   # нийт нөөц


def test_book_sequential_requests():
    b = book()
    assert b.request(1, [1, 0, 2])[0] == GRANTED
    assert b.available == [2, 3, 0]
    assert b.request(4, [3, 3, 0])[0] == WAIT
    assert b.available == [2, 3, 0]
    snap = (list(b.available), [r[:] for r in b.allocation])
    assert b.request(0, [0, 2, 0])[0] == UNSAFE
    assert (b.available, b.allocation) == snap     # rollback


def test_p4_on_fresh_state_is_not_wait():
    # Эхний төлөв дээр P4 (3,3,0) Available (3,3,2)-д багтана -> WAIT биш
    assert book().request(4, [3, 3, 0])[0] != WAIT


def test_t1_request_exceeds_need():
    b = book()
    st, msg = b.request(1, [2, 0, 0])
    assert st == ERROR and "Need" in msg
    assert b.available == [3, 3, 2]


def test_t2_negative_and_bad_input():
    b = book()
    for i, req in [(1, [-1, 0, 2]), (1, [1, 0]), (1, ["a", 0, 0]),
                   (9, [0, 0, 0]), (-1, [0, 0, 0]), (1, [1.5, 0, 0]),
                   (1, [True, 0, 0])]:
        assert b.request(i, req)[0] == ERROR
    assert b.available == [3, 3, 2] and b.allocation == BOOK_ALLOC


def unsafe_state():
    alloc = [[0, 3, 0], [3, 0, 2], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
    return Banker([2, 1, 0], BOOK_MAX, alloc)


def test_t3_unsafe_initial():
    b = unsafe_state()
    safe, seq, _ = b.is_safe()
    assert not safe and seq == []
    assert not brute_safe(b)


def test_t4_release_makes_safe():
    b = unsafe_state()
    assert b.release(4, [0, 0, 2])[0] == RELEASED
    assert b.available == [2, 1, 2]
    safe, seq, _ = b.is_safe()
    assert safe and b.valid_sequence(seq)


def test_release_errors():
    b = book()
    assert b.release(1, [3, 0, 0])[0] == ERROR     # барьж буйгаасаа их
    assert b.release(1, [-1, 0, 0])[0] == ERROR
    assert b.available == [3, 3, 2]


def test_t5_large_10x5():
    rnd = random.Random(2026)
    n, m = 10, 5
    for _ in range(50):
        mx = [[rnd.randint(0, 8) for _ in range(m)] for _ in range(n)]
        al = [[rnd.randint(0, mx[i][j]) for j in range(m)] for i in range(n)]
        av = [rnd.randint(0, 6) for _ in range(m)]
        b = Banker(av, mx, al)
        safe, seq, _ = b.is_safe()
        if safe:
            assert b.valid_sequence(seq)
            # Work эцэст нь available + sum(allocation)
            assert b.to_json()["steps"][-1]["work_after"] == [
                av[j] + sum(al[i][j] for i in range(n)) for j in range(m)]


def test_cross_check_with_bruteforce_small():
    rnd = random.Random(7)
    n, m = 5, 3
    for _ in range(200):
        mx = [[rnd.randint(0, 6) for _ in range(m)] for _ in range(n)]
        al = [[rnd.randint(0, mx[i][j]) for j in range(m)] for i in range(n)]
        av = [rnd.randint(0, 4) for _ in range(m)]
        b = Banker(av, mx, al)
        assert b.is_safe()[0] == brute_safe(b)


def test_t6_reset():
    b = book()
    b.request(1, [1, 0, 2])
    b.release(3, [1, 0, 0])
    b.reset()
    assert b.available == [3, 3, 2] and b.allocation == BOOK_ALLOC


def test_constructor_validation():
    with pytest.raises(BankerError):
        Banker([1, 2], [[1, 1, 1]])                       # хэмжээс зөрүү
    with pytest.raises(BankerError):
        Banker([-1, 0, 0], [[1, 1, 1]])                   # сөрөг
    with pytest.raises(BankerError):
        Banker([1, 1, 1], [[1, 1, 1]], [[2, 0, 0]])       # alloc > max
    with pytest.raises(BankerError):
        Banker([], [[1]])


def test_empty_allocation_default_is_safe():
    b = Banker([10, 5, 7], BOOK_MAX)       # номын CLI: allocation=0
    assert b.allocation == [[0] * 3 for _ in range(5)]
    assert b.is_safe()[0]


def test_to_json_shape():
    j = book().to_json()
    assert set(j) >= {"available", "max", "allocation", "need", "safe",
                      "sequence", "steps"}
    assert j["safe"] and all(s.startswith("P") for s in j["sequence"])
