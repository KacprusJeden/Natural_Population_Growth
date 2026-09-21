"""Analiza danych o przyroście naturalnym z użyciem LangChain i ChatGPT.

Moduł wczytuje pliki CSV z katalogu ``data/``, wysyła je do modelu OpenAI
za pośrednictwem LangChain, zapisuje tekstowe podsumowanie do
``reports/report.txt`` oraz generuje wykresy liniowe do ``plots/``:

- ``polska_przyrost_naturalny.png`` – zbiorczy dla Polski,
- ``wojewodztwa_przyrost_naturalny.png`` – wszystkie województwa na jednym
  wykresie,
- ``{wojewodztwo}_przyrost_naturalny.png`` – osobny wykres dla każdego
  województwa.

Klucz API OpenAI jest czytany ze zmiennej środowiskowej ``OPENAI_API_KEY``
lub może być przekazany jako argument funkcji.
"""

import os
from pathlib import Path

# Nieinteraktywny backend matplotlib – konieczny w środowiskach bez GUI
# oraz przy uruchamianiu z poziomu skryptów/testów.
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

DATA_DIR = Path(__file__).parent.parent / "data"
PLOTS_DIR = Path(__file__).parent.parent / "plots"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORT_PATH = REPORTS_DIR / "report.txt"

DEFAULT_MODEL = "gpt-4o-mini"

# Prosta transliteracja polskich znaków dla nazw plików.
_POLISH_TO_ASCII = str.maketrans(
    "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "acelnoszzACELNOSZZ"
)


def load_all_data() -> pd.DataFrame:
    """Wczytuje wszystkie pliki ``przyrost_naturalny_pl_*.csv`` i łączy je.

    Returns:
        DataFrame z kolumnami ``rok``, ``kod_teryt``, ``jednostka``,
        ``przyrost_naturalny_na_1000``, posortowany po jednostce i roku.

    Raises:
        FileNotFoundError: gdy nie znaleziono żadnych pasujących plików CSV.
    """
    csv_files = sorted(DATA_DIR.glob("przyrost_naturalny_pl_*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono plików CSV w {DATA_DIR}")

    frames = [pd.read_csv(filepath) for filepath in csv_files]
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["jednostka", "rok"], ignore_index=True)
    return df


def format_data_for_llm(df: pd.DataFrame) -> str:
    """Zwraca dane jako tekst CSV gotowy do wysłania do modelu."""
    return df.to_csv(index=False, encoding="utf-8")


def create_llm(api_key: str | None = None, model: str = DEFAULT_MODEL) -> ChatOpenAI:
    """Tworzy instancję ``ChatOpenAI``.

    Args:
        api_key: Klucz API OpenAI. Jeśli ``None``, używa
            ``OPENAI_API_KEY`` ze zmiennych środowiskowych.
        model: Nazwa modelu OpenAI.

    Returns:
        Skonfigurowana instancja ``ChatOpenAI``.

    Raises:
        ValueError: gdy nie podano klucza API ani nie znaleziono go w env.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "Brak klucza API OpenAI. Ustaw zmienną środowiskową OPENAI_API_KEY "
            "lub przekaż argument api_key."
        )
    return ChatOpenAI(model=model, api_key=key, temperature=0.2)


def analyze_with_llm(df: pd.DataFrame, llm: ChatOpenAI) -> str:
    """Wysyła dane do modelu i zwraca tekstową analizę oraz podsumowanie.

    Args:
        df: Ramka danych do przeanalizowania.
        llm: Skonfigurowana instancja ``ChatOpenAI``.

    Returns:
        Treść odpowiedzi modelu (analiza po polsku).
    """
    data_csv = format_data_for_llm(df)

    system_prompt = (
        "Jesteś analitykiem demograficznym. Otrzymasz dane o przyroście "
        "naturalnym na 1000 ludności w Polsce i województwach za lata "
        "2002-2025. Wykonaj analizę trendów, porównaj województwa, wskaż "
        "lata o największych zmianach oraz kluczowe wnioski. Odpowiedź "
        "podaj po polsku w formie zwięzłego, strukturalnego raportu tekstowego."
    )
    human_prompt = (
        "Poniżej znajdują się dane w formacie CSV "
        "(kolumny: rok, kod_teryt, jednostka, przyrost_naturalny_na_1000):\n\n"
        f"{data_csv}\n\n"
        "Przygotuj analizę i podsumowanie."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    response = llm.invoke(messages)
    return str(response.content)


def save_report(summary: str) -> Path:
    """Zapisuje podsumowanie do ``reports/report.txt``.

    Returns:
        Ścieżka do zapisanego pliku.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(summary, encoding="utf-8")
    return REPORT_PATH


def _normalize_filename(name: str) -> str:
    """Zamienia nazwę jednostki na bezpieczną, ASCII nazwę pliku."""
    ascii_name = name.translate(_POLISH_TO_ASCII)
    safe = ascii_name.lower().replace(" ", "_").replace("-", "_")
    safe = "".join(char for char in safe if char.isalnum() or char == "_")
    safe = safe.strip("_")
    return safe


def _save_line_plot(
    x: pd.Series,
    y: pd.Series,
    title: str,
    ylabel: str,
    path: Path,
) -> Path:
    """Generuje i zapisuje pojedynczy wykres liniowy.

    Args:
        x: Wartości na oś X (rok).
        y: Wartości na oś Y (przyrost naturalny).
        title: Tytuł wykresu.
        ylabel: Etykieta osi Y.
        path: Ścieżka docelowa pliku PNG.

    Returns:
        Ścieżka do zapisanego pliku.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, marker="o", linewidth=1.5)
    ax.axhline(0, color="red", linestyle="--", linewidth=0.8)
    ax.set_title(title)
    ax.set_xlabel("Rok")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle=":", alpha=0.7)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_plots(df: pd.DataFrame) -> list[Path]:
    """Generuje wykresy do ``plots/``.

    Args:
        df: Połączona ramka danych z wszystkich lat.

    Returns:
        Lista ścieżek do zapisanych plików PNG.
    """
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    ylabel = "Przyrost naturalny na 1000 ludności"

    polska_df = df[df["jednostka"].str.upper() == "POLSKA"].copy()
    if not polska_df.empty:
        path = PLOTS_DIR / "polska_przyrost_naturalny.png"
        _save_line_plot(
            polska_df["rok"],
            polska_df["przyrost_naturalny_na_1000"],
            title="Przyrost naturalny na 1000 ludności – Polska (2002-2025)",
            ylabel=ylabel,
            path=path,
        )
        saved.append(path)

    woj_df = df[df["jednostka"].str.upper() != "POLSKA"].copy()
    if not woj_df.empty:
        # Wykres zbiorczy ze wszystkimi województwami.
        fig, ax = plt.subplots(figsize=(14, 8))
        for name, group in woj_df.groupby("jednostka", sort=True):
            ax.plot(
                group["rok"],
                group["przyrost_naturalny_na_1000"],
                marker="o",
                label=name,
                linewidth=1.2,
            )
        ax.axhline(0, color="red", linestyle="--", linewidth=0.8)
        ax.set_title("Przyrost naturalny na 1000 ludności – województwa (2002-2025)")
        ax.set_xlabel("Rok")
        ax.set_ylabel(ylabel)
        ax.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize="small",
        )
        ax.grid(True, linestyle=":", alpha=0.7)
        path = PLOTS_DIR / "wojewodztwa_przyrost_naturalny.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        saved.append(path)

        # Osobne wykresy dla każdego województwa.
        for name, group in woj_df.groupby("jednostka", sort=True):
            safe_name = _normalize_filename(name)
            path = PLOTS_DIR / f"{safe_name}_przyrost_naturalny.png"
            _save_line_plot(
                group["rok"],
                group["przyrost_naturalny_na_1000"],
                title=f"Przyrost naturalny – {name}",
                ylabel=ylabel,
                path=path,
            )
            saved.append(path)

    return saved


def run_analysis(
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> tuple[Path, list[Path]]:
    """Główna funkcja: analiza LLM, raport tekstowy i wykresy.

    Args:
        api_key: Klucz API OpenAI (opcjonalnie).
        model: Nazwa modelu OpenAI (domyślnie ``gpt-4o-mini``).

    Returns:
        Krotka ``(ścieżka_raportu, lista_ścieżek_wykresów)``.
    """
    df = load_all_data()
    llm = create_llm(api_key=api_key, model=model)
    summary = analyze_with_llm(df, llm)
    report_path = save_report(summary)
    plot_paths = generate_plots(df)
    return report_path, plot_paths

