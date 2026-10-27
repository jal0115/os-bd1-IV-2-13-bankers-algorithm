import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cli  # noqa: E402

EX = os.path.join(os.path.dirname(__file__), "..", "examples")
MAX = os.path.join(EX, "book_max.txt")
ALLOC = os.path.join(EX, "book_allocation.txt")


def run(argv, text=""):
    out = io.StringIO()
    code = cli.main(argv, stdin=io.StringIO(text), out=out)
    return code, out.getvalue()


def write_tmp(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                    encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


BOOK = ["10", "5", "7", "--max", MAX, "--allocation", ALLOC]


def test_book_sequence_via_cli():
    code, out = run(BOOK, "RQ 1 1 0 2\nRQ 4 3 3 0\nRQ 0 0 2 0\nexit\n")
    assert code == 0
    lines = out.strip().splitlines()
    assert lines[0].startswith("granted")
    assert lines[1].startswith("wait")
    assert lines[2].startswith("unsafe")


def test_star_prints_matrices():
    code, out = run(BOOK, "*\n")
    assert "Available: 3 3 2" in out
    for word in ("Max:", "Allocation:", "Need:", "SAFE"):
        assert word in out


def test_book_default_allocation_zero():
    # Номын шаардлага: Allocation өгөхгүй бол 0, Available = нийт нөөц
    code, out = run(["10", "5", "7", "--max", MAX], "*\n")
    assert code == 0 and "Available: 10 5 7" in out
    assert "Төлөв: SAFE" in out


def test_available_from_total_minus_allocation():
    b, _ = cli.build_banker([10, 5, 7], MAX, ALLOC)
    assert b.available == [3, 3, 2]


def test_release_command():
    code, out = run(BOOK, "RQ 1 1 0 2\nRL 1 1 0 2\n*\n")
    assert "granted" in out and "released" in out
    assert "Available: 3 3 2" in out


def test_release_more_than_held_is_error():
    code, out = run(BOOK, "RL 1 5 0 0\n")
    assert out.startswith("error:")


def test_request_exceeds_need():
    code, out = run(BOOK, "RQ 1 2 0 0\n")
    assert out.startswith("error:") and "Need" in out


def test_command_syntax_errors():
    for line in ["RQ", "RQ 1 1 0", "RQ 1 a 0 2", "RQ x 1 0 2", "FOO 1 2 3",
                 "RQ 1 1 0 2 9", "RQ 99 0 0 0", "RQ 1 -1 0 2"]:
        code, out = run(BOOK, line + "\n")
        assert code == 0
        assert out.strip().startswith(("алдаа", "error")), (line, out)


def test_lowercase_and_blank_lines():
    code, out = run(BOOK, "\nrq 1 1 0 2\n\n")
    assert out.strip().startswith("granted")


def test_exit_stops_processing():
    code, out = run(BOOK, "exit\nRQ 1 1 0 2\n")
    assert out == ""


def test_eof_ends_cleanly():
    code, out = run(BOOK, "")
    assert code == 0


def test_no_resources_given():
    code, out = run(["--max", MAX])
    assert code == 2 and "нийт нөөц" in out


def test_non_integer_resource():
    code, out = run(["10", "x", "7", "--max", MAX])
    assert code == 2 and "бүхэл тоо" in out


def test_negative_resource():
    code, out = run(["10", "-5", "7", "--max", MAX])
    assert code == 2


def test_missing_file():
    code, out = run(["10", "5", "7", "--max", "/no/such/file.txt"])
    assert code == 2 and "файл нээгдсэнгүй" in out


def test_max_file_wrong_columns():
    p = write_tmp("7,5,3\n3,2\n")
    code, out = run(["10", "5", "7", "--max", p])
    os.unlink(p)
    assert code == 2 and "2-р мөр" in out


def test_max_file_bad_number_and_negative():
    p = write_tmp("7,5,x\n")
    code, out = run(["10", "5", "7", "--max", p])
    os.unlink(p)
    assert code == 2 and "бүхэл тоо" in out
    p = write_tmp("7,-5,3\n")
    code, out = run(["10", "5", "7", "--max", p])
    os.unlink(p)
    assert code == 2 and "сөрөг" in out


def test_empty_max_file():
    p = write_tmp("# зөвхөн тайлбар\n\n")
    code, out = run(["10", "5", "7", "--max", p])
    os.unlink(p)
    assert code == 2 and "хоосон" in out


def test_allocation_exceeds_total():
    p = write_tmp("9,0,0\n9,0,0\n9,0,0\n9,0,0\n9,0,0\n")
    code, out = run(["10", "5", "7", "--max", MAX, "--allocation", p])
    os.unlink(p)
    assert code == 2 and "нийт нөөцөөс" in out


def test_allocation_exceeds_max():
    p = write_tmp("8,0,0\n0,0,0\n0,0,0\n0,0,0\n0,0,0\n")
    code, out = run(["10", "5", "7", "--max", MAX, "--allocation", p])
    os.unlink(p)
    assert code == 2 and "maximum" in out


def test_allocation_row_count_mismatch():
    p = write_tmp("0,0,0\n0,0,0\n")
    code, out = run(["10", "5", "7", "--max", MAX, "--allocation", p])
    os.unlink(p)
    assert code == 2 and "ижил байх" in out


def test_max_greater_than_total_warns():
    p = write_tmp("20,0,0\n")
    code, out = run(["10", "5", "7", "--max", p], "*\n")
    os.unlink(p)
    assert code == 0 and "анхааруулга" in out


def test_comments_and_spaces_in_files():
    p = write_tmp("# тайлбар\n 7 5 3 # мөрийн тайлбар\n\n3,2,2\n")
    code, out = run(["10", "5", "7", "--max", p], "*\n")
    os.unlink(p)
    assert code == 0 and "P1:" in out


def test_four_resource_types():
    # 4 төрлийн нөөц (номын төслийн формат: ./a.out 10 5 7 8). Өгөгдөл өөрсдийнх.
    p = write_tmp("6,4,7,3\n4,2,3,2\n2,5,3,3\n6,3,3,2\n5,5,7,5\n")
    code, out = run(["10", "5", "7", "8", "--max", p], "RQ 0 3 1 2 1\n*\n")
    os.unlink(p)
    assert code == 0 and out.startswith("granted")
    assert "Available: 7 4 5 7" in out
