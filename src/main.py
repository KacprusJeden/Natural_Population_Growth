"""Główny program łączący pobieranie danych z analizą LLM.

Pipeline:

1. Pobiera dane o przyroście naturalnym na 1000 ludności z API BDL
   i zapisuje je jako pliki CSV w ``data/``.
2. Wysyła połączone dane do ChatGPT przez LangChain, zapisuje
   raport tekstowy do ``reports/report.txt``.
3. Generuje wykresy liniowe do ``plots/``.

Uruchomienie:

    python src/main.py

Wymagane zmienne środowiskowe:

- ``OPENAI_API_KEY`` – klucz API OpenAI (analiza LLM).
- Opcjonalnie ``BDL_CLIENT_ID`` – klucz klienta BDL (wyższe limity zapytań).
"""

import sys

# Konsola Windows domyślnie używa cp1250 - bez tego znaki ✓/✗ i polskie ogonki
# wywalają skrypt UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.download_statistics import download_and_save
from src.llm_analysis import run_analysis


def main() -> None:
    """Uruchamia pełny pipeline: pobieranie -> analiza LLM -> wykresy."""
    print("=" * 64)
    print("  Natural Population Growth - pipeline")
    print("=" * 64)

    print("\n[1/3] Pobieranie danych z BDL...")
    data = download_and_save()
    if not data:
        print("✗ Nie udało się pobrać danych. Przerywam.")
        sys.exit(1)

    print("\n[2/3] Analiza danych przez ChatGPT (LangChain)...")
    try:
        report_path, plot_paths = run_analysis()
    except ValueError as exc:
        print(f"✗ Błąd analizy LLM: {exc}")
        sys.exit(1)

    print("\n[3/3] Podsumowanie")
    print(f"  Raport:   {report_path}")
    print(f"  Wykresy:  {len(plot_paths)}")
    for path in plot_paths:
        print(f"    - {path.name}")

    print("\n✓ Pipeline zakończony pomyślnie.")


if __name__ == "__main__":
    main()
