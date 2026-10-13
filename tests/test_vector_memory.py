"""Regression tests for exact cosine retrieval, local persistence and CSV parsing."""
import json
import math
import pytest

from episodic_vector_store.store import VectorStore
from cli import main, parse_csv_bool


def test_similarity_order_filter_and_dimensions():
    store = VectorStore()
    store.put("same", [1.0, 0], "same direction")
    store.put("orthogonal", [0, 1], "right angle")
    store.put("opposite", [-1, 0])
    assert [r["id"] for r in store.search([1, 0], top_k=2)] == ["same", "orthogonal"]
    assert store.search([1, 0], min_similarity=0.5)[0]["similarity"] == pytest.approx(1)
    assert [r["id"] for r in store.search([1, 0], min_similarity=0.5)] == ["same"]
    with pytest.raises(ValueError, match="Expected 2"):
        store.search([1, 0, 0])
    with pytest.raises(ValueError, match="Expected 2"):
        store.put("wrong", [1, 2, 3])


@pytest.mark.parametrize("vector", [
    [], [0, 0], [float("nan")], [float("inf")], [True, 0], ["x"], [0] * 4097,
])
def test_invalid_vectors_rejected(vector):
    with pytest.raises(ValueError):
        VectorStore().put("bad", vector)


def test_json_persistence_upsert_delete_and_dimension_reset(tmp_path):
    db = tmp_path / "vectors.json"
    memory = VectorStore(db)
    memory.put("abc", [3, 4], "demo", {"origin": "test"})
    assert db.exists()
    assert memory.dimension == 2
    reopened = VectorStore(db)
    assert len(reopened.list_episodes()) == 1
    assert reopened.search([3, 4])[0]["similarity"] == pytest.approx(1)
    reopened.put("abc", [1, 0], "replaced")
    assert len(reopened.list_episodes()) == 1
    assert reopened.list_episodes()[0]["text"] == "replaced"
    assert reopened.delete("abc")
    assert not reopened.delete("abc")
    assert reopened.dimension is None
    assert VectorStore(db).list_episodes() == []
    reopened.put("other", [1, 0, 0])
    assert reopened.dimension == 3


def test_malformed_files_rejected(tmp_path):
    db = tmp_path / "vectors.json"
    db.write_text('{"version":1,"dimension":3,"episodes":[]}')
    with pytest.raises(ValueError, match="dimension"):
        VectorStore(db)


def test_cli_commands(tmp_path, capsys):
    db = str(tmp_path / "episodes.json")
    assert main(["memory-put", "--db", db, "--id", "A", "--vector", "[1,0]",
                 "--text", "example"]) == 0
    assert main(["memory-search", "--db", db, "--vector", "[1,0]"]) == 0
    output = capsys.readouterr().out
    assert '"similarity": 1.0' in output
    assert main(["memory-list", "--db", db]) == 0
    assert main(["memory-delete", "--db", db, "--id", "A"]) == 0
    assert VectorStore(db).list_episodes() == []


@pytest.mark.parametrize(("value", "expected"), [
    ("False", False), ("0", False), ("no", False), ("", False),
    ("True", True), ("1", True), ("YES", True), (False, False),
])
def test_csv_boolean_parser(value, expected):
    assert parse_csv_bool(value) is expected


def test_csv_boolean_invalid():
    with pytest.raises(ValueError, match="Invalid boolean"):
        parse_csv_bool("maybe")


def test_batch_csv_false_remains_noncritical(tmp_path):
    input_file = tmp_path / "in.csv"
    output_file = tmp_path / "out.csv"
    input_file.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n"
        "T1,KEY-1,1,1,NOMINAL,False\n"
    )
    assert main(["batch", "-i", str(input_file), "-o", str(output_file)]) == 0
    assert "ROUTINE" in output_file.read_text()
