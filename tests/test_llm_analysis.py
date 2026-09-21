"""Testy jednostkowe modułu src.llm_analysis."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src import llm_analysis as llm


def test_load_all_data_reads_csv_files(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "DATA_DIR", tmp_path)

    (tmp_path / "przyrost_naturalny_pl_2024.csv").write_text(
        "rok,kod_teryt,jednostka,przyrost_naturalny_na_1000\n"
        "2024,PL,Polska,-0.8\n",
        encoding="utf-8",
    )
    (tmp_path / "przyrost_naturalny_pl_2025.csv").write_text(
        "rok,kod_teryt,jednostka,przyrost_naturalny_na_1000\n"
        "2025,PL,Polska,-0.5\n",
        encoding="utf-8",
    )

    result = llm.load_all_data()

    assert list(result.columns) == [
        "rok",
        "kod_teryt",
        "jednostka",
        "przyrost_naturalny_na_1000",
    ]
    assert len(result) == 2
    assert result.iloc[0]["rok"] == 2024
    assert result.iloc[1]["rok"] == 2025


def test_load_all_data_raises_when_no_csv_files(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "DATA_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        llm.load_all_data()


def test_format_data_for_llm_returns_csv_string():
    df = pd.DataFrame(
        {
            "rok": [2024, 2025],
            "jednostka": ["Polska", "Polska"],
            "przyrost_naturalny_na_1000": [-0.8, -0.5],
        }
    )

    csv_text = llm.format_data_for_llm(df)

    assert "rok,jednostka,przyrost_naturalny_na_1000" in csv_text
    assert "2024,Polska,-0.8" in csv_text


def test_create_llm_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Brak klucza API OpenAI"):
        llm.create_llm()


def test_create_llm_uses_api_key_argument(monkeypatch):
    """Sprawdza, że przy przekazanym kluczu funkcja nie rzuca wyjątku.

    Nie wywołujemy rzeczywistego API – wystarczy, że obiekt został utworzony.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    chat = llm.create_llm(api_key="fake-key-for-tests")

    assert chat is not None


def test_save_report_creates_report_file(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(llm, "REPORT_PATH", tmp_path / "report.txt")

    path = llm.save_report("Podsumowanie testowe")

    assert path.exists()
    assert path.read_text(encoding="utf-8") == "Podsumowanie testowe"


def test_normalize_filename_transliterates_polish_chars():
    assert llm._normalize_filename("DOLNOŚLĄSKIE") == "dolnoslaskie"
    assert llm._normalize_filename("świętokrzyskie") == "swietokrzyskie"
    assert llm._normalize_filename("KUJAWSKO-POMORSKIE") == "kujawsko_pomorskie"


def test_generate_plots_creates_expected_png_files(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "PLOTS_DIR", tmp_path)

    df = pd.DataFrame(
        {
            "rok": [2024, 2025, 2024, 2025],
            "kod_teryt": ["PL", "PL", "02", "02"],
            "jednostka": ["POLSKA", "POLSKA", "DOLNOŚLĄSKIE", "DOLNOŚLĄSKIE"],
            "przyrost_naturalny_na_1000": [-0.8, -0.5, -1.2, -1.0],
        }
    )

    paths = llm.generate_plots(df)

    assert len(paths) == 3
    assert tmp_path / "polska_przyrost_naturalny.png" in paths
    assert tmp_path / "wojewodztwa_przyrost_naturalny.png" in paths
    assert tmp_path / "dolnoslaskie_przyrost_naturalny.png" in paths
    for path in paths:
        assert path.exists()
        assert path.stat().st_size > 0


def test_analyze_with_llm_returns_model_response(monkeypatch):
    df = pd.DataFrame(
        {
            "rok": [2024],
            "kod_teryt": ["PL"],
            "jednostka": ["Polska"],
            "przyrost_naturalny_na_1000": [-0.8],
        }
    )

    fake_response = MagicMock()
    fake_response.content = "To jest testowe podsumowanie."
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_response

    result = llm.analyze_with_llm(df, fake_llm)

    assert result == "To jest testowe podsumowanie."
    fake_llm.invoke.assert_called_once()
    messages = fake_llm.invoke.call_args[0][0]
    assert any("analitykiem demograficznym" in msg.content for msg in messages)
    assert any("2024" in msg.content for msg in messages)
