"""Pobiera dane o przyroście naturalnym na 1000 ludności za lata 2002-2025
i zapisuje je do katalogu data/ (jeden plik CSV na rok).

Uruchomienie:
    python main.py
"""

import sys

# Konsola Windows domyślnie używa cp1250 - bez tego znaki ✓/✗ i polskie ogonki
# wywalają skrypt UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.download_statistics import (
    DATA_DIR,
    YEAR_FIRST,
    YEAR_LAST,
    download_and_save,
)


def print_summary(data: dict) -> None:
    """Wypisuje podsumowanie pobranych danych."""
    years = sorted(data.keys())

    print(f"\n{'=' * 64}")
    print("  Podsumowanie")
    print(f"{'=' * 64}")
    print(f"  Katalog:  {DATA_DIR}")
    print(f"  Lata:     {years[0]}-{years[-1]} ({len(years)} plików CSV)")
    print(f"  Rekordów: {sum(len(df) for df in data.values())}")

    missing = sorted(set(range(YEAR_FIRST, YEAR_LAST + 1)) - set(years))
    if missing:
        print(f"  Brak danych dla lat: {missing}")

    print("\n  Przyrost naturalny dla Polski na 1000 ludności:")
    for year in years:
        df = data[year]
        polska = df.loc[df["jednostka"] == "POLSKA", "przyrost_naturalny_na_1000"]
        if polska.empty:
            print(f"   {year}   brak danych")
            continue
        val = polska.iloc[0]
        print(f"   {year}  {val:>6.2f}  {'#' * int(abs(val) * 4)}")


def main() -> None:
    try:
        data = download_and_save()
    except KeyboardInterrupt:
        print("\nPrzerwano.")
        sys.exit(130)

    if not data:
        sys.exit(1)

    print_summary(data)


if __name__ == "__main__":
    main()
