# Natural Population Growth

Projekt pobiera, analizuje i wizualizuje dane o przyroście naturalnym na 1000 ludności w Polsce oraz w poszczególnych województwach za lata 2002–2025.

Dane pochodzą z publicznego API **Banku Danych Lokalnych GUS** (zmienna *przyrost naturalny na 1000 ludności – ogółem*, temat P3992). Analiza trendów oraz generowanie raportu tekstowego odbywa się z wykorzystaniem modelu **ChatGPT** przez bibliotekę **LangChain**, a wykresy tworzone są lokalnie za pomocą **matplotlib**.

---

## Funkcjonalności

- **Pobieranie danych** z BDL dla całej Polski oraz 16 województw (lata 2002–2025).
- **Zapis danych** do katalogu `data/` jako osobne pliki CSV dla każdego roku.
- **Analiza LLM** – wysyłanie zebranych danych do ChatGPT i zapisywanie raportu tekstowego do `reports/report.txt`.
- **Wizualizacja**:
  - wykres dla całej Polski,
  - zbiorczy wykres wszystkich województw,
  - osobne wykresy dla każdego województwa w katalogu `plots/`.

---

## Wymagania

- Python 3.10+
- Klucz API OpenAI (do analizy LLM)
- Opcjonalnie klucz klienta BDL `BDL_CLIENT_ID` (wyższe limity zapytań)

Zależności Pythona znajdują się w pliku `requirements.txt`:

- `requests`
- `pandas`
- `truststore`
- `pytest`
- `langchain`, `langchain-openai`, `openai`
- `matplotlib`

---

## Instalacja

```bash
# Sklonuj lub przejdź do katalogu projektu
cd Natural_Population_Growth

# Utwórz i aktywuj wirtualne środowisko
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt
```

---

## Konfiguracja

Ustaw zmienną środowiskową z kluczem OpenAI:

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "twój-klucz-api"

# Windows (cmd)
set OPENAI_API_KEY=twój-klucz-api

# Linux/macOS
export OPENAI_API_KEY=twój-klucz-api
```

Opcjonalnie możesz ustawić klucz klienta BDL, aby uzyskać wyższe limity zapytań:

```bash
export BDL_CLIENT_ID=twój-klucz-bdl
```

---

## Użycie

### Pełny pipeline (pobieranie + analiza LLM + wykresy)

```bash
python src/main.py
```

Wykonuje trzy kroki:

1. Pobiera dane z BDL i zapisuje je w `data/`.
2. Wysyła dane do ChatGPT i zapisuje raport w `reports/report.txt`.
3. Generuje wykresy w katalogu `plots/`.


## Struktura projektu

```
Natural_Population_Growth/
├── data/                        # Pliki CSV z danymi rocznymi
├── plots/                       # Wygenerowane wykresy PNG
├── reports/                     # Raport tekstowy z analizy LLM
├── src/
│   ├── download_statistics.py   # Pobieranie danych z API BDL
│   ├── llm_analysis.py          # Analiza LLM + generowanie wykresów
│   └── main.py                  # Pełny pipeline
├── tests/
│   ├── test_download_statistics.py
│   └── test_llm_analysis.py
├── main.py                      # Skrypt do samodzielnego pobierania danych
├── requirements.txt             # Zależności projektu
└── README.md                    # Ten plik
```

---

## Testy

```bash
pytest
```

---

## Źródło danych i licencja

- Dane: [Bank Danych Lokalnych GUS](https://bdl.stat.gov.pl/)
- API: [https://bdl.stat.gov.pl/api/v1/](https://bdl.stat.gov.pl/api/v1/)
- Licencja danych: Creative Commons BY 4.0

---

## Uwagi

- API BDL ma limity zapytań: anonimowo 5 zapytań/s, z kluczem `X-ClientId` 10 zapytań/s. Projekt domyślnie czeka 0,25 s między kolejnymi stronami.
- Moduł `llm_analysis.py` używa nieinteraktywnego backendu matplotlib (`Agg`), więc wykresy generują się również na serwerach bez GUI.
- W przypadku problemów z certyfikatami HTTPS (np. antywirus/proxy firmowy) używana jest opcjonalna biblioteka `truststore`, która korzysta z systemowego magazynu certyfikatów.
