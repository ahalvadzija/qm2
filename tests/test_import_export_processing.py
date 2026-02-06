""" 
Tests for CSV processing logic in import_export.py (focus: csv_to_json flattened processing).
"""

import json
import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from qm2.core.import_export import csv_to_json, json_to_csv


class _FakeDictReader:
    def __init__(self, rows, fieldnames):
        self._rows = rows
        self.fieldnames = fieldnames

    def __iter__(self):
        return iter(self._rows)


class TestImportExportProcessing:
    def test_csv_to_json_flattened_basic(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "flat.csv"
        json_file = tmp_path / "out.json"

        csv_file.write_text(
            "type,question,correct,wrong_answers/0,wrong_answers/1,pairs/left/0,pairs/right/0,pairs/answers/0\n"
            "match,Glavni grad?,Sarajevo,Mostar,Banja Luka,A,B,0:0\n",
            encoding="utf-8",
        )

        csv_to_json(csv_file, json_file)

        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        row = data[0]
        assert row["type"] == "match"
        assert row["question"] == "Glavni grad?"
        assert row["correct"] == "Sarajevo"
        assert row["wrong_answers"] == ["Mostar", "Banja Luka"]
        assert row["pairs"] == {"left": ["A"], "right": ["B"], "answers": {"0": "0:0"}}

    def test_csv_to_json_flattened_list_values_via_patched_dictreader(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "ignored.csv"
        json_file = tmp_path / "out.json"
        csv_file.write_text("dummy\n", encoding="utf-8")

        rows = [
            {
                "wrong_answers/0": "x",
                "wrong_answers/1": "y",
                "pairs/left/0": "L1",
                "pairs/left/1": "L2",
                "pairs/right/0": "R1",
                "pairs/answers/0": "1",
                "type": "match",
                "question": "Q?",
                "correct": "C",
            }
        ]
        fieldnames = list(rows[0].keys())

        def _fake_reader(_fileobj, *args, **kwargs):
            return _FakeDictReader(rows=rows, fieldnames=fieldnames)

        with patch("csv.DictReader", side_effect=_fake_reader):
            csv_to_json(csv_file, json_file)

        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data[0]["wrong_answers"] == ["x", "y"]
        assert data[0]["pairs"] == {"left": ["L1", "L2"], "right": ["R1"], "answers": {"0": "1"}}
        assert isinstance(data[0]["type"], str)

    def test_csv_to_json_utf8_preserved(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "utf.csv"
        json_file = tmp_path / "utf.json"

        question = "čćžšđ"
        csv_file.write_text(f"type,question,correct\nmultiple,{question},tačno\n", encoding="utf-8")

        csv_to_json(csv_file, json_file)

        raw = json_file.read_text(encoding="utf-8")
        assert question in raw

    def test_json_to_csv_empty_raises(self, tmp_path: Path) -> None:
        json_file = tmp_path / "empty.json"
        csv_file = tmp_path / "out.csv"

        json_file.write_text("[]", encoding="utf-8")

        with pytest.raises(ValueError, match="JSON is empty"):
            json_to_csv(json_file, csv_file)

    def test_csv_to_json_normal_wrong_answers_literal_eval(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "normal.csv"
        json_file = tmp_path / "out.json"

        csv_file.write_text(
            "type,question,correct,wrong_answers\n"
            "multiple,2+2?,4,\"['3','5']\"\n",
            encoding="utf-8",
        )

        csv_to_json(csv_file, json_file)
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data[0]["wrong_answers"] == ["3", "5"]
        assert "pairs" not in data[0]

    def test_csv_to_json_normal_wrong_answers_fallback_strips_quotes(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "fallback.csv"
        json_file = tmp_path / "out.json"

        csv_file.write_text(
            "type,question,correct,wrong_answers\n"
            "multiple,Q?,A,\"\"x, y\"\"\n",
            encoding="utf-8",
        )

        csv_to_json(csv_file, json_file)
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data[0]["wrong_answers"] == ["x", "y"]

    def test_csv_to_json_match_left_right_answers_reconstructs_pairs(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "match.csv"
        json_file = tmp_path / "out.json"

        csv_file.write_text(
            "type,question,correct,left,right,answers\n"
            "match,Match?,ignored,L1|L2,R1|R2,a:1,b:0\n",
            encoding="utf-8",
        )

        csv_to_json(csv_file, json_file)
        data = json.loads(json_file.read_text(encoding="utf-8"))
        row = data[0]
        assert row["pairs"] == {"left": ["L1", "L2"], "right": ["R1", "R2"], "answers": {"a": "1", "b": "0"}}
        assert "left" not in row
        assert "right" not in row
        assert "answers" not in row

    def test_csv_to_json_non_match_removes_left_right_answers_and_empties_pairs(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "nonmatch.csv"
        json_file = tmp_path / "out.json"

        csv_file.write_text(
            "type,question,correct,left,right,answers\n"
            "multiple,Q?,A,L1|L2,R1|R2,a:1\n",
            encoding="utf-8",
        )

        csv_to_json(csv_file, json_file)
        data = json.loads(json_file.read_text(encoding="utf-8"))
        row = data[0]
        assert "pairs" not in row
        assert "left" not in row
        assert "right" not in row
        assert "answers" not in row

    def test_json_to_csv_serializes_pairs_dict(self, tmp_path: Path) -> None:
        json_file = tmp_path / "in.json"
        csv_file = tmp_path / "out.csv"

        pairs = {"left": ["A"], "right": ["B"], "answers": {"0": "0"}}
        json_file.write_text(
            json.dumps([{"type": "match", "question": "Q", "correct": "C", "pairs": pairs}], ensure_ascii=False),
            encoding="utf-8",
        )

        json_to_csv(json_file, csv_file)
        rows = list(csv.DictReader(open(csv_file, encoding="utf-8")))
        pairs_str = rows[0]["pairs"]
        assert isinstance(pairs_str, str)
        assert json.loads(pairs_str) == pairs
