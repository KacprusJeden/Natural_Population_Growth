\# Natural\_Population\_Growth



\## Cel projektu

Zadaniem projektu jest stworzenie mechanizmu do tego, aby pobrać wszystkie dane z rankingu "Przyrost naturalny na 1000 ludności według województw" ze strony https://bdl.stat.gov.pl/bdl/rankingi. Dane mają być zapisane do csv do folderu dane, każde CSV o nazwie przyrost\_naturalny\_pl\_\[ROK].csv, a wykresy jak to się zmienia w poszczególnych latach dla województw i w polsce - zapisane w folderze plots

Informacje a propos warunków używania API Banku Danych Lokalnych znajduje się na stronie: https://api.stat.gov.pl/Home/RegonApi



\## Struktura

\- src/ — moduły (scraping, zapis do CSV, rysowanie wykresów, etc.)

\- data/przyrost\_naturalny\_pl\_\[ROK].csv — jeden plik na rok

\- plots/ — wykresy per województwo + zbiorczy dla Polski

\- reports/ — podsumowania i wnioski; końcowy plik - report.txt

\- tests/ — testy jednostkowe (pytest)



\## Konwencje

\- Python 3.14, zależności w requirements.txt

\- Formatowanie: \[np. black/ruff — wpisz, jeśli używasz]

\- Uruchamianie testów: `pytest tests/ -v`

\- Nazwa CSV: przyrost\_naturalny\_pl\_{rok}.csv (dokładnie ten wzorzec)



\## Ważne

\- Nie commituj plików z data/ jeśli źródło się zmienia dynamicznie \[albo odwrotnie — Twoja decyzja]

\- Scraping ma być odporny na brak danych dla danego roku (nie failować całego batcha)

