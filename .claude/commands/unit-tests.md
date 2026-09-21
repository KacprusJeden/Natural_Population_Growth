---
description: Debugowanie i poprawianie/dopisywanie funkcji w module Python zgodnie z opisem z functions_describe.txt
argument-hint: [moduł] [nazwa_funkcji]
allowed-tools: Bash, Write, Read, Edit
---

Jesteś specjalistą w programowaniu Python. Twoim zadaniem jest rozwiązanie zadania według podanych wskazówek.

## Zadanie do wykonania

Moduł: $1

W pliku CLAUDE.md masz rozpisaną strukturę projektu oraz czego on dokładnie dotyczy, co zwraca, itp.
W pliku functions_describe.txt znajdziesz opis tej funkcji. Porównaj opis tej funkcji z faktyczną implementacją.

Dla wszystkich metod modułu $1 napisz testy jednostkowe z wykorzystaniem pytest. Tworzysz nowy plik lub nadpisujesz go tam gdzie trzeba stworzyć nowy test lub który poprawiasz. Poprawnie napisanych testów nie musisz ruszać.