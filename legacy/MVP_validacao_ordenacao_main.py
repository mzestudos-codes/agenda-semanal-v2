
import json
import logging
import re
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from tkinter import Tk, filedialog, messagebox

from openpyxl import load_workbook


# ============================================================
# CONFIGURAÇÕES
# ============================================================

SHEET_NAME = "Agenda"

DAY_BLOCKS = {
    "segunda": (4, 8),
    "terca": (12, 16),
    "quarta": (20, 24),
    "quinta": (28, 32),
    "sexta": (36, 40),
}

MARKERS = {
    "VejaMaisConferencias",
    "VejaMaisDivulgacoes",
    "VejaMaisInvestorDay",
}

PERIOD_PRIORITY = {
    "Antes Abert.": 1,
    "Após Fech.": 2,
}

# Colunas:
# Divulgação: empresa A | período normalizado J
# Conferência: empresa C | horário PT K | horário EN L
# Investor Day: empresa F | modalidade M | horário N


# ============================================================
# LOG
# ============================================================

def configure_logger(output_path):
    log_path = output_path.with_name(
        output_path.stem + "_ordenacao.log"
    )

    logger = logging.getLogger("agenda")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger, log_path


# ============================================================
# UTILITÁRIOS
# ============================================================

def cell_value(value):
    """Converte valores do Excel para valores serializáveis."""

    if value is None:
        return None

    if isinstance(value, (datetime, time)):
        return value.isoformat()

    if isinstance(value, timedelta):
        return str(value)

    return value


def is_empty(value):
    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def is_marker(company):
    return company in MARKERS


def normalize_company_key(company):
    """Comparação case-insensitive, preservando o nome original."""
    return str(company).casefold()


def parse_time(value):
    if is_empty(value):
        return None

    if isinstance(value, datetime):
        return (
            value.hour * 3600
            + value.minute * 60
            + value.second
        )

    if isinstance(value, time):
        return (
            value.hour * 3600
            + value.minute * 60
            + value.second
        )

    if isinstance(value, timedelta):
        return int(value.total_seconds()) % 86400

    if isinstance(value, (int, float)):
        if 0 <= value < 1:
            return round(value * 86400)

    text = str(value).strip()

    # Informações que não representam horários
    NON_TIME_VALUES = {
    "trad. simul.",
    "sem informação",
    "-"
}

    if text.casefold() in NON_TIME_VALUES:
        return None

    patterns = [
        "%H:%M",
        "%H:%M:%S",
        "%I:%M %p",
        "%I:%M:%S %p",
        "%I:%M%p",
        "%I:%M:%S%p",
    ]

    for pattern in patterns:
        try:
            parsed = datetime.strptime(text.upper(), pattern)
            return (
                parsed.hour * 3600
                + parsed.minute * 60
                + parsed.second
            )
        except ValueError:
            pass

    match = re.fullmatch(r"(\d{1,2})h(\d{2})", text, re.I)

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))

        if hour < 24 and minute < 60:
            return hour * 3600 + minute * 60

    raise ValueError(
        f"Não foi possível interpretar o horário: {value!r}"
    )


def time_label(seconds):
    """Transforma segundos em HH:MM para registro no JSON."""
    if seconds is None:
        return None

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return f"{hours:02d}:{minutes:02d}"


# ============================================================
# EXTRAÇÃO DOS DADOS
# ============================================================

def extract_day(ws, day, first_row, last_row, logger):

    data = {
        "divulgacoes": [],
        "conferencias": [],
        "investor_day": [],
    }

    for row in range(first_row, last_row + 1):

        # ----------------------------------------------------
        # DIVULGAÇÕES
        # ----------------------------------------------------

        company = ws[f"A{row}"].value
        period = ws[f"J{row}"].value

        if not is_empty(company):

            event = {
                "empresa": str(company),
                "periodo": cell_value(period),
                "linha_excel": row,
                "posicao_original": len(data["divulgacoes"]) + 1,
                "_marker": is_marker(company),
            }

            data["divulgacoes"].append(event)

        # ----------------------------------------------------
        # CONFERÊNCIAS
        # ----------------------------------------------------

        company = ws[f"C{row}"].value
        time_pt = ws[f"K{row}"].value
        time_en = ws[f"L{row}"].value

        if not is_empty(company):

            parsed_times = []

            for value in (time_pt, time_en):
                if not is_empty(value):
                    parsed = parse_time(value)

                    if parsed is not None:
                        parsed_times.append(parsed)

            event_time = min(parsed_times) if parsed_times else None

            event = {
                "empresa": str(company),
                "horario_pt": cell_value(time_pt),
                "horario_en": cell_value(time_en),
                "horario_ordenacao": time_label(event_time),
                "linha_excel": row,
                "posicao_original": len(data["conferencias"]) + 1,
                "_sort_time": event_time,
                "_marker": is_marker(company),
            }

            data["conferencias"].append(event)

        # ----------------------------------------------------
        # INVESTOR DAY
        # ----------------------------------------------------

        company = ws[f"F{row}"].value
        modality = ws[f"M{row}"].value
        event_time = ws[f"N{row}"].value

        if not is_empty(company):

            parsed_time = parse_time(event_time)

            event = {
                "empresa": str(company),
                "modalidade": cell_value(modality),
                "horario": cell_value(event_time),
                "horario_ordenacao": time_label(parsed_time),
                "linha_excel": row,
                "posicao_original": len(data["investor_day"]) + 1,
                "_sort_time": parsed_time,
                "_marker": is_marker(company),
            }

            data["investor_day"].append(event)

    logger.info(
        "%s | Extração concluída: %s divulgações, "
        "%s conferências, %s Investor Days",
        day,
        len(data["divulgacoes"]),
        len(data["conferencias"]),
        len(data["investor_day"]),
    )

    return data


# ============================================================
# VALIDAÇÕES
# ============================================================

def validate_duplicates(events, day, category):

    seen = {}

    for event in events:

        company = event["empresa"]

        if is_marker(company):
            continue

        key = normalize_company_key(company)

        if key in seen:
            raise ValueError(
                f"Empresa duplicada!\n\n"
                f"Dia: {day}\n"
                f"Categoria: {category}\n"
                f"Empresa: {company}\n"
                f"Linhas no Excel: "
                f"{seen[key]} e {event['linha_excel']}"
            )

        seen[key] = event["linha_excel"]


def validate_periods(events, day):

    for event in events:

        if is_marker(event["empresa"]):
            continue

        period = event["periodo"]

        if is_empty(period):
            raise ValueError(
                f"Período de divulgação ausente!\n\n"
                f"Dia: {day}\n"
                f"Empresa: {event['empresa']}\n"
                f"Linha no Excel: {event['linha_excel']}"
            )

        if period not in PERIOD_PRIORITY:
            raise ValueError(
                f"Período de divulgação inesperado!\n\n"
                f"Dia: {day}\n"
                f"Empresa: {event['empresa']}\n"
                f"Valor encontrado: {period!r}"
            )


def validate_day(day, data, logger):

    validate_duplicates(
        data["divulgacoes"], day, "Divulgação"
    )

    validate_duplicates(
        data["conferencias"], day, "Conferência"
    )

    validate_duplicates(
        data["investor_day"], day, "Investor Day"
    )

    validate_periods(data["divulgacoes"], day)

    logger.info("%s | Validações concluídas", day)


# ============================================================
# ORDENAÇÃO
# ============================================================

def sort_events(events, category, day, logger):

    original_order = list(events)

    markers = [
        event for event in events
        if event["_marker"]
    ]

    companies = [
        event for event in events
        if not event["_marker"]
    ]

    if category == "divulgacoes":

        companies.sort(
            key=lambda event: (
                PERIOD_PRIORITY[event["periodo"]],
                normalize_company_key(event["empresa"]),
            )
        )

    elif category in ("conferencias", "investor_day"):

        companies.sort(
            key=lambda event: (
                event["_sort_time"] is None,
                event["_sort_time"]
                if event["_sort_time"] is not None
                else float("inf"),
                normalize_company_key(event["empresa"]),
            )
        )

    ordered = companies + markers

    for new_position, event in enumerate(ordered, start=1):

        old_position = event["posicao_original"]

        logger.info(
            "%s | %s | %s | posição %s -> %s",
            day,
            category,
            event["empresa"],
            old_position,
            new_position,
        )

        event["posicao_ordenada"] = new_position

    return ordered


def sort_day(day, data, logger):

    for category in (
        "divulgacoes",
        "conferencias",
        "investor_day",
    ):

        data[category] = sort_events(
            data[category],
            category,
            day,
            logger,
        )

        # Remove campos internos utilizados somente na ordenação.
        for event in data[category]:
            event.pop("_marker", None)
            event.pop("_sort_time", None)

    return data


# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

def process_excel(excel_path):

    excel_path = Path(excel_path)

    output_path = excel_path.with_name(
        excel_path.stem + "_ordenado.json"
    )

    logger, log_path = configure_logger(output_path)

    logger.info("Iniciando processamento: %s", excel_path)

    workbook = load_workbook(
        excel_path,
        data_only=True
    )

    if SHEET_NAME not in workbook.sheetnames:
        raise ValueError(
            f"A aba '{SHEET_NAME}' não foi encontrada."
        )

    ws = workbook[SHEET_NAME]

    result = {}

    for day, (first_row, last_row) in DAY_BLOCKS.items():

        logger.info("Iniciando processamento de %s", day)

        day_data = extract_day(
            ws,
            day,
            first_row,
            last_row,
            logger,
        )

        validate_day(day, day_data, logger)

        result[day] = sort_day(
            day,
            day_data,
            logger,
        )

    # Metadados do processamento
    output = {
        "arquivo_origem": excel_path.name,
        "data_processamento": datetime.now().isoformat(
            timespec="seconds"
        ),
        "dias": result,
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=4,
        )

    logger.info("JSON gerado: %s", output_path)
    logger.info("Processamento concluído.")

    return output_path, log_path


# ============================================================
# INTERFACE
# ============================================================

def main():

    root = Tk()
    root.withdraw()

    root.attributes("-topmost", True)

    excel_path = filedialog.askopenfilename(
        title="Selecione a planilha de agenda",
        filetypes=[
            ("Arquivos Excel", "*.xlsx *.xlsm"),
            ("Todos os arquivos", "*.*"),
        ],
    )

    if not excel_path:
        root.destroy()
        return

    try:

        output_path, log_path = process_excel(excel_path)

        messagebox.showinfo(
            "Processamento concluído",
            f"Ordenação realizada com sucesso!\n\n"
            f"JSON:\n{output_path}\n\n"
            f"Log:\n{log_path}",
            parent=root,
        )

    except Exception as error:

        messagebox.showerror(
            "Erro no processamento",
            str(error),
            parent=root,
        )

        # Abre o Excel para correção quando houver falha.
        try:
            import os
            os.startfile(excel_path)
        except Exception:
            pass

    finally:
        root.destroy()


if __name__ == "__main__":
    main()