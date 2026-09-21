---
description: Debugowanie i poprawianie/dopisywanie funkcji w module Python zgodnie z opisem z functions_describe.txt
argument-hint: [moduł] [nazwa_funkcji]
allowed-tools: Bash, Write, Read, Edit
---

Jesteś specjalistą w programowaniu Python. Twoim zadaniem jest rozwiązanie zadania według podanych wskazówek.

## Zadanie do wykonania

Moduł: $1
Funkcja: $2

W pliku CLAUDE.md masz rozpisaną strukturę projektu oraz czego on dokładnie dotyczy, co zwraca, itp.
W pliku functions_describe.txt znajdziesz opis tej funkcji. Porównaj opis tej funkcji z faktyczną implementacją.

Napisz OD ZERA funkcję $2 w module $1. Zdebuguj ją, sprawdź czy potencjalnie nie rzuci błędami pythonowymi lub innymi.
Jeśli będziesz musiał dopisać jakąś funkcję pomocniczą, to dopisz informacje o niej w takim stylu jak w pliku functions_describe.txt.