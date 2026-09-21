from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import requests

from src import download_statistics as ds


def test_headers_without_client_id(monkeypatch):
    monkeypatch.delenv("BDL_CLIENT_ID", raising=False)

    headers = ds._headers()

    assert headers == {"Accept": "application/json"}


def test_headers_with_client_id(monkeypatch):
    monkeypatch.setenv("BDL_CLIENT_ID", "secret-client")

    headers = ds._headers()

    assert headers == {
        "Accept": "application/json",
        "X-ClientId": "secret-client",
    }


def test_get_variable_data_reads_all_pages(monkeypatch):
    response_page_0 = MagicMock()
    response_page_0.json.return_value = {
        "results": [{"id": "PL", "name": "Polska", "values": []}],
        "links": {"next": "next-page"},
    }
    response_page_1 = MagicMock()
    response_page_1.json.return_value = {
        "results": [{"id": "02", "name": "Dolnoslaskie", "values": []}],
        "links": {},
    }

    get_mock = MagicMock(side_effect=[response_page_0, response_page_1])
    sleep_mock = MagicMock()
    monkeypatch.setattr(ds.requests, "get", get_mock)
    monkeypatch.setattr(ds.time, "sleep", sleep_mock)
    monkeypatch.setattr(ds, "_headers", lambda: {"Accept": "application/json"})

    results = ds.get_variable_data(ds.UNIT_LEVEL_POLAND, page_size=50)

    assert results == [
        {"id": "PL", "name": "Polska", "values": []},
        {"id": "02", "name": "Dolnoslaskie", "values": []},
    ]
    assert get_mock.call_count == 2
    assert get_mock.call_args_list[0].kwargs["params"]["page"] == 0
    assert get_mock.call_args_list[1].kwargs["params"]["page"] == 1
    sleep_mock.assert_called_once_with(ds.REQUEST_DELAY_S)


def test_to_dataframe_filters_and_sorts_records():
    records = [
        {
            "id": "10",
            "name": "Lodzkie",
            "values": [
                {"year": str(ds.YEAR_FIRST - 1), "val": 1.5},
                {"year": str(ds.YEAR_FIRST), "val": 0.2},
                {"year": str(ds.YEAR_LAST), "val": "1.7"},
                {"year": str(ds.YEAR_LAST), "val": None},
            ],
        },
        {
            "id": "PL",
            "name": "Polska",
            "values": [{"year": str(ds.YEAR_FIRST), "val": -0.3}],
        },
    ]

    result = ds.to_dataframe(records)

    assert list(result.columns) == ds.COLUMNS
    assert result.to_dict("records") == [
        {
            "rok": ds.YEAR_FIRST,
            "kod_teryt": "10",
            "jednostka": "Lodzkie",
            "przyrost_naturalny_na_1000": 0.2,
        },
        {
            "rok": ds.YEAR_FIRST,
            "kod_teryt": "PL",
            "jednostka": "Polska",
            "przyrost_naturalny_na_1000": -0.3,
        },
        {
            "rok": ds.YEAR_LAST,
            "kod_teryt": "10",
            "jednostka": "Lodzkie",
            "przyrost_naturalny_na_1000": 1.7,
        },
    ]


def test_to_dataframe_returns_empty_frame_for_empty_input():
    result = ds.to_dataframe([])

    assert result.empty
    assert list(result.columns) == ds.COLUMNS


def test_fetch_natural_growth_stats_groups_by_year(monkeypatch, capsys):
    voivodeship_records = [{"id": "02", "name": "Dolnoslaskie", "values": []}]
    poland_records = [{"id": "PL", "name": "Polska", "values": []}]
    voivodeship_df = pd.DataFrame(
        [
            {
                "rok": 2024,
                "kod_teryt": "02",
                "jednostka": "Dolnoslaskie",
                "przyrost_naturalny_na_1000": -1.2,
            },
            {
                "rok": 2025,
                "kod_teryt": "02",
                "jednostka": "Dolnoslaskie",
                "przyrost_naturalny_na_1000": -1.0,
            },
        ]
    )
    poland_df = pd.DataFrame(
        [
            {
                "rok": 2024,
                "kod_teryt": "PL",
                "jednostka": "Polska",
                "przyrost_naturalny_na_1000": -0.8,
            }
        ]
    )

    get_mock = MagicMock(side_effect=[voivodeship_records, poland_records])
    to_df_mock = MagicMock(side_effect=[voivodeship_df, poland_df])
    monkeypatch.setattr(ds, "get_variable_data", get_mock)
    monkeypatch.setattr(ds, "to_dataframe", to_df_mock)

    result = ds.fetch_natural_growth_stats()

    assert sorted(result) == [2024, 2025]
    assert result[2024].to_dict("records") == [
        {
            "rok": 2024,
            "kod_teryt": "02",
            "jednostka": "Dolnoslaskie",
            "przyrost_naturalny_na_1000": -1.2,
        },
        {
            "rok": 2024,
            "kod_teryt": "PL",
            "jednostka": "Polska",
            "przyrost_naturalny_na_1000": -0.8,
        },
    ]
    assert result[2025].to_dict("records") == [
        {
            "rok": 2025,
            "kod_teryt": "02",
            "jednostka": "Dolnoslaskie",
            "przyrost_naturalny_na_1000": -1.0,
        }
    ]
    output = capsys.readouterr().out
    assert "Pobieranie danych (województwa)..." in output
    assert "Pobieranie danych (Polska)..." in output


def test_fetch_natural_growth_stats_skips_request_errors(monkeypatch, capsys):
    get_mock = MagicMock(
        side_effect=[
            requests.RequestException("woj error"),
            [{"id": "PL", "name": "Polska", "values": []}],
        ]
    )
    poland_df = pd.DataFrame(
        [
            {
                "rok": 2024,
                "kod_teryt": "PL",
                "jednostka": "Polska",
                "przyrost_naturalny_na_1000": -0.8,
            }
        ]
    )
    to_df_mock = MagicMock(side_effect=[poland_df])
    monkeypatch.setattr(ds, "get_variable_data", get_mock)
    monkeypatch.setattr(ds, "to_dataframe", to_df_mock)

    result = ds.fetch_natural_growth_stats()

    assert list(result) == [2024]
    assert result[2024].iloc[0]["jednostka"] == "Polska"
    assert "Błąd zapytania do API (województwa)" in capsys.readouterr().out


def test_save_to_csv_creates_files_and_returns_saved_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(ds, "DATA_DIR", tmp_path)
    data = {
        2024: pd.DataFrame(
            [
                {
                    "rok": 2024,
                    "kod_teryt": "PL",
                    "jednostka": "Polska",
                    "przyrost_naturalny_na_1000": -0.8,
                }
            ]
        )
    }

    saved = ds.save_to_csv(data)

    expected_path = tmp_path / "przyrost_naturalny_pl_2024.csv"
    assert saved == [expected_path]
    assert expected_path.exists()
    content = expected_path.read_text(encoding="utf-8")
    assert "Polska" in content


def test_save_to_csv_continues_after_os_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ds, "DATA_DIR", tmp_path)
    df_ok = pd.DataFrame(
        [
            {
                "rok": 2025,
                "kod_teryt": "PL",
                "jednostka": "Polska",
                "przyrost_naturalny_na_1000": 0.1,
            }
        ]
    )
    df_fail = pd.DataFrame(
        [
            {
                "rok": 2024,
                "kod_teryt": "PL",
                "jednostka": "Polska",
                "przyrost_naturalny_na_1000": -0.1,
            }
        ]
    )

    original_to_csv = pd.DataFrame.to_csv

    def fake_to_csv(self, path, *args, **kwargs):
        if Path(path).name == "przyrost_naturalny_pl_2024.csv":
            raise OSError("disk full")
        return original_to_csv(self, path, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_csv", fake_to_csv)

    saved = ds.save_to_csv({2024: df_fail, 2025: df_ok})

    assert saved == [tmp_path / "przyrost_naturalny_pl_2025.csv"]
    assert "Nie udało się zapisać przyrost_naturalny_pl_2024.csv" in capsys.readouterr().out


def test_download_and_save_returns_empty_when_fetch_fails(monkeypatch, capsys):
    save_mock = MagicMock()
    monkeypatch.setattr(ds, "fetch_natural_growth_stats", lambda: {})
    monkeypatch.setattr(ds, "save_to_csv", save_mock)

    result = ds.download_and_save()

    assert result == {}
    save_mock.assert_not_called()
    assert "Nie pobrano żadnych danych" in capsys.readouterr().out


def test_download_and_save_saves_and_returns_data(monkeypatch, capsys):
    data = {
        2024: pd.DataFrame(
            [
                {
                    "rok": 2024,
                    "kod_teryt": "PL",
                    "jednostka": "Polska",
                    "przyrost_naturalny_na_1000": -0.8,
                }
            ]
        )
    }
    save_mock = MagicMock(return_value=[Path("data/przyrost_naturalny_pl_2024.csv")])
    monkeypatch.setattr(ds, "fetch_natural_growth_stats", lambda: data)
    monkeypatch.setattr(ds, "save_to_csv", save_mock)

    result = ds.download_and_save()

    assert result == data
    save_mock.assert_called_once_with(data)
    assert "Zapisano dane dla 1 lat" in capsys.readouterr().out
