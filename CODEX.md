# CODEX

## Cel projektu

Projekt: pobrać dane z rankingu "Przyrost naturalny na 1000 ludności według województw" ze strony BDL (bdl.stat.gov.pl/bdl/rankingi/raport), zapisać je do CSV w `data/` oraz wygenerować wykresy do `plots/`.

## Struktura (skrót)


- `src/` — moduły (scraping, zapis do CSV, wykresy)
- `data/` — `przyrost_naturalny_pl_{rok}.csv`
- `plots/` — wykresy per województwo + zbiorczy
- `reports/` — podsumowania; finalnie `report.txt`
- `tests/` — `pytest`

## Zasady pracy

- Najpierw diagnoza i plan, potem zmiany w kodzie.
- Zmiany małe i minimalne; nie przepisuj modułów bez potrzeby.
- Sekrety/klucze trzymać poza repo (env), nie commitować.
- Informacje a propos warunków używania API Banku Danych Lokalnych znajduje się na stronie: https://api.stat.gov.pl/Home/RegonApi

## Uruchamianie

- Testy: `pytest tests/ -v`
- Wersja Pythona: 3.14.x (jeśli faktycznie używasz; inaczej popraw)
