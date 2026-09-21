"""Pobieranie danych o przyroście naturalnym na 1000 ludności z API Banku Danych Lokalnych.

API BDL: https://bdl.stat.gov.pl/api/v1/ (dokumentacja: https://api.stat.gov.pl/Home/BdlApi)
Dane na licencji Creative Commons BY 4.0.

Limity zapytań (anonimowo / z kluczem X-ClientId):
    1 s        5 / 10
    15 min   100 / 500
    12 h    1000 / 5000
    7 dni  10000 / 50000
"""

import os
import time
from pathlib import Path

import pandas as pd
import requests

try:
    # Korzystaj z systemowego magazynu certyfikatów zamiast bundla certifi.
    # Potrzebne, gdy ruch HTTPS jest przechwytywany przez antywirusa lub proxy
    # firmowe - ich certyfikat root jest w magazynie systemowym, ale nie w certifi.
    import truststore

    truststore.inject_into_ssl()
except ImportError:  # pragma: no cover - opcjonalna zależność
    pass


BDL_API_BASE = "https://bdl.stat.gov.pl/api/v1"
DATA_DIR = Path(__file__).parent.parent / "data"

# Zmienna "przyrost naturalny na 1000 ludności - ogółem" (temat P3992).
# API udostępnia lata 1999-2025, projekt obejmuje zakres 2002-2025.
VAR_NATURAL_GROWTH_PER_1000 = 1616456
YEAR_FIRST = 2002
YEAR_LAST = 2025

# Poziomy agregacji terytorialnej w BDL
UNIT_LEVEL_POLAND = 0
UNIT_LEVEL_VOIVODESHIP = 2

COLUMNS = ["rok", "kod_teryt", "jednostka", "przyrost_naturalny_na_1000"]

# Odstęp między zapytaniami, żeby nie przekroczyć limitu 5 zapytań/s
REQUEST_DELAY_S = 0.25


def _headers() -> dict[str, str]:
    """Nagłówki zapytania; klucz API czytany ze zmiennej środowiskowej BDL_CLIENT_ID."""
    headers = {"Accept": "application/json"}
    client_id = os.environ.get("BDL_CLIENT_ID")
    if client_id:
        headers["X-ClientId"] = client_id
    return headers


def get_variable_data(unit_level: int, page_size: int = 100) -> list[dict]:
    """
    Pobiera wszystkie dostępne dane zmiennej dla danego poziomu agregacji.

    Args:
        unit_level: poziom agregacji (0 = Polska, 2 = województwa)
        page_size: liczba jednostek na stronę (maks. 100)

    Returns:
        Lista rekordów: {"id": kod TERYT, "name": nazwa, "values": [{"year", "val", ...}]}

    Raises:
        requests.RequestException: gdy zapytanie do API się nie powiedzie
    """
    url = f"{BDL_API_BASE}/data/by-variable/{VAR_NATURAL_GROWTH_PER_1000}"
    params = {
        "format": "json",
        "unit-level": unit_level,
        "page-size": page_size,
    }

    results: list[dict] = []
    page = 0
    while True:
        response = requests.get(
            url,
            params={**params, "page": page},
            headers=_headers(),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        results.extend(payload.get("results", []))

        if not payload.get("links", {}).get("next"):
            break
        page += 1
        time.sleep(REQUEST_DELAY_S)

    return results


def to_dataframe(records: list[dict]) -> pd.DataFrame:
    """
    Zamienia odpowiedź API na "długą" ramkę danych, ograniczoną do lat YEAR_FIRST-YEAR_LAST.

    Returns:
        DataFrame z kolumnami: rok, kod_teryt, jednostka, przyrost_naturalny_na_1000
    """
    rows = []
    for record in records:
        for value in record.get("values", []):
            if value.get("val") is None:
                continue
            year = int(value["year"])
            if not YEAR_FIRST <= year <= YEAR_LAST:
                continue
            rows.append(
                {
                    "rok": year,
                    "kod_teryt": record.get("id"),
                    "jednostka": record.get("name"),
                    "przyrost_naturalny_na_1000": float(value["val"]),
                }
            )

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    return pd.DataFrame(rows).sort_values(["rok", "jednostka"], ignore_index=True)


def fetch_natural_growth_stats() -> dict[int, pd.DataFrame]:
    """
    Pobiera przyrost naturalny na 1000 ludności dla 16 województw i całej Polski
    za lata YEAR_FIRST-YEAR_LAST.

    Jedno zapytanie zwraca wszystkie lata dla wszystkich jednostek danego poziomu,
    więc nie odpytujemy API rok po roku. Błąd jednego poziomu nie przerywa całości.

    Returns:
        Słownik {rok: DataFrame}
    """
    frames = []

    for label, unit_level in (
        ("województwa", UNIT_LEVEL_VOIVODESHIP),
        ("Polska", UNIT_LEVEL_POLAND),
    ):
        try:
            print(f"Pobieranie danych ({label})...")
            df = to_dataframe(get_variable_data(unit_level))
            if df.empty:
                print(f"✗ Brak danych dla poziomu: {label}")
                continue
            frames.append(df)
            print(f"✓ {label}: {len(df)} rekordów, lata {df['rok'].min()}-{df['rok'].max()}")
        except requests.RequestException as e:
            print(f"✗ Błąd zapytania do API ({label}): {e}")
        except (ValueError, KeyError, TypeError) as e:
            print(f"✗ Błąd przetwarzania danych ({label}): {e}")

    if not frames:
        return {}

    combined = pd.concat(frames, ignore_index=True)
    return {
        int(year): group.reset_index(drop=True)
        for year, group in combined.groupby("rok", sort=True)
    }


def save_to_csv(data: dict[int, pd.DataFrame]) -> list[Path]:
    """
    Zapisuje dane do katalogu data/ jako przyrost_naturalny_pl_{rok}.csv

    Returns:
        Lista ścieżek zapisanych plików
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for year, df in sorted(data.items()):
        filepath = DATA_DIR / f"przyrost_naturalny_pl_{year}.csv"
        try:
            df.to_csv(filepath, index=False, encoding="utf-8")
            saved.append(filepath)
            print(f"✓ Zapisano {filepath.name}")
        except OSError as e:
            print(f"✗ Nie udało się zapisać {filepath.name}: {e}")

    return saved


def download_and_save() -> dict[int, pd.DataFrame]:
    """
    Pobiera dane za lata YEAR_FIRST-YEAR_LAST i zapisuje je do CSV (jeden plik na rok).

    Returns:
        Słownik {rok: DataFrame} z pobranymi danymi
    """
    print(f"Pobieranie przyrostu naturalnego za lata {YEAR_FIRST}-{YEAR_LAST}...")

    data = fetch_natural_growth_stats()

    if not data:
        print("✗ Nie pobrano żadnych danych")
        return {}

    save_to_csv(data)
    print(f"✓ Zapisano dane dla {len(data)} lat")
    return data
