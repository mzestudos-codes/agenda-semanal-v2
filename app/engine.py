"""Fluxo de geração, logs, temporários e atualização segura das saídas."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
from zipfile import ZipFile
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

from openpyxl import load_workbook

from .assets import obtain_assets
from .excel_write import make_excel_candidate
from .render import render_day
from .validation import DAYS, AgendaError, name_of_day, read_week_dates, validate_and_sort

TMP_PREFIX = 'agenda-semanal-'
LOG_REGEX = re.compile(r'agenda_\d{8}_\d{6}_\d{6}\.log\Z')
MONTHS = '(?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)'
PNG_REGEX = re.compile(rf'Agenda_\d{{2}}{MONTHS}\.png\Z')


def cleanup_stale_temp():
    """Limpa restos de execuções encerradas, sem apagar outra execução ativa."""
    root = Path(gettempdir())
    for directory in root.glob(TMP_PREFIX + '*'):
        if not directory.is_dir() or directory.is_symlink() or not (directory / '.agenda-owned').is_file():
            continue
        match = re.fullmatch(r'agenda-semanal-(\d+)-[\w-]+', directory.name)
        if match:
            pid = int(match[1])
            if pid == os.getpid():
                continue
            try:
                import psutil
                if psutil.pid_exists(pid):
                    continue
            except ImportError:
                # Se não soubermos conferir o processo, só limpar após uma hora.
                if datetime.now().timestamp() - directory.stat().st_mtime < 3600:
                    continue
        elif datetime.now().timestamp() - directory.stat().st_mtime < 3600:
            continue
        try:
            shutil.rmtree(directory)
        except OSError:
            pass


def logger_for(excel):
    directory = excel.parent / 'Logs'
    directory.mkdir(exist_ok=True)
    for old in directory.iterdir():
        if not old.is_file() or not LOG_REGEX.fullmatch(old.name):
            continue
        try:
            if datetime.now() - datetime.fromtimestamp(old.stat().st_mtime) > timedelta(days=30):
                old.unlink()
        except OSError:
            pass
    name = datetime.now().strftime('agenda_%Y%m%d_%H%M%S_%f.log')
    logger = logging.getLogger('AgendaSemanal.' + name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = logging.FileHandler(directory / name, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(handler)
    return logger


def assert_excel_access(excel):
    if not excel.is_file() or excel.suffix.lower() != '.xlsx':
        raise AgendaError('Selecione um arquivo Excel .xlsx existente.')
    if excel.name.startswith('~$'):
        raise AgendaError('Selecione o arquivo Excel original, não um arquivo temporário de bloqueio.')
    try:
        with excel.open('r+b'):
            pass
        # A substituição atômica requer permissão também na pasta, não só no arquivo.
        with NamedTemporaryFile(dir=excel.parent, prefix='.agenda-write-test-', delete=True):
            pass
    except OSError as exc:
        raise AgendaError('Feche o arquivo no Excel e verifique a permissão de gravação antes de executar.') from exc


def open_result(path):
    if sys.platform == 'win32':
        os.startfile(str(path))
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', str(path)])
    else:
        subprocess.Popen(['xdg-open', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _stage_copy(source, target_dir, suffix):
    with NamedTemporaryFile(dir=target_dir, prefix='.agenda-stage-', suffix=suffix, delete=False) as tmp:
        destination = Path(tmp.name)
    try:
        shutil.copy2(source, destination)
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def _publish(excel, candidate, png_files, folder, year, logger, temp_root):
    """Tenta publicar Excel e PNGs como conjunto, com rollback em falhas comuns.

    Cada substituição é atômica dentro do volume. Não prometemos transação ACID
    entre múltiplos arquivos em caso de queda de energia ou desligamento abrupto.
    """
    old_folder = folder.exists()
    folder.mkdir(exist_ok=True)
    metadata = folder / '.agenda-year'
    old_metadata = metadata.read_bytes() if metadata.exists() else None
    previous = [p for p in folder.iterdir() if p.is_file() and PNG_REGEX.fullmatch(p.name)]
    backup_png = temp_root / 'png-backup'
    backup_png.mkdir()
    for old in previous:
        shutil.copy2(old, backup_png / old.name)
    backup = excel.with_name('.agenda-backup-' + uuid.uuid4().hex + '.xlsx')
    staged = []
    committed = False
    try:
        shutil.copy2(excel, backup)
        staged_excel = _stage_copy(candidate, excel.parent, '.xlsx')
        staged.append(staged_excel)
        for name, source in png_files.items():
            item = _stage_copy(source, folder, '.png')
            staged.append(item)
        with ZipFile(staged_excel) as archive:
            if archive.testzip():
                raise AgendaError('A cópia gerada do Excel não passou na validação de integridade.')
        try:
            os.replace(staged_excel, excel)
        except PermissionError as exc:
            raise AgendaError('O Excel está aberto ou bloqueado. Feche a planilha e tente novamente.') from exc
        for name, staged_png in zip(png_files, staged[1:]):
            os.replace(staged_png, folder / name)
        for old in previous:
            if old.name not in png_files:
                old.unlink()
        metadata.write_text(str(year), encoding='utf-8')
        committed = True
        logger.info('Publicação concluída: %d imagens PNG', len(png_files))
    except Exception:
        logger.exception('Falha na publicação; iniciando rollback')
        try:
            if backup.exists():
                os.replace(backup, excel)
            for current in folder.iterdir():
                if current.is_file() and PNG_REGEX.fullmatch(current.name) and current.name not in {p.name for p in previous}:
                    current.unlink()
            for previous_file in backup_png.iterdir():
                shutil.copy2(previous_file, folder / previous_file.name)
            if old_metadata is None:
                metadata.unlink(missing_ok=True)
            else:
                metadata.write_bytes(old_metadata)
            if not old_folder and not any(folder.iterdir()):
                folder.rmdir()
        except Exception:
            logger.exception('Rollback incompleto. Backup de emergência: %s', backup)
            raise AgendaError(f'Falha ao restaurar todas as saídas. Backup do Excel em {backup}.')
        raise
    finally:
        for file in staged:
            file.unlink(missing_ok=True)
        if committed:
            backup.unlink(missing_ok=True)
        # Caso o rollback tenha falhado, preservar o backup de emergência.
        elif not backup.exists():
            pass


def run(excel_path, repository=None, branch='main', local_assets=None, open_results=True):
    excel = Path(excel_path).expanduser().resolve()
    assert_excel_access(excel)
    logger = logger_for(excel)
    cleanup_stale_temp()
    logger.info('Iniciando agenda: %s', excel)
    try:
        workbook = load_workbook(excel, data_only=True, read_only=True)
        try:
            if 'Agenda' not in workbook.sheetnames:
                raise AgendaError('A aba Agenda não existe.')
            ws = workbook['Agenda']
            data = validate_and_sort(ws, logger)
            dates = read_week_dates(ws)
        finally:
            workbook.close()

        monday, friday = dates['segunda'], dates['sexta']
        folder = excel.parent / f'Agenda_Semanal_{name_of_day(monday)}_{name_of_day(friday)}'
        if folder.exists() and (folder / '.agenda-year').exists():
            previous_year = (folder / '.agenda-year').read_text(encoding='utf-8').strip()
            if previous_year != str(monday.year):
                raise AgendaError(f'A pasta {folder.name} já contém uma semana de outro ano. Renomeie-a antes de prosseguir.')
        with TemporaryDirectory(prefix=f'{TMP_PREFIX}{os.getpid()}-') as tmp:
            tmp_root = Path(tmp)
            (tmp_root / '.agenda-owned').touch()
            # Mantém o artefato de ordenação do MVP, mas somente durante esta execução.
            ordered_json = tmp_root / 'eventos_ordenados.json'
            ordered_json.write_text(json.dumps({
                'arquivo_origem': excel.name,
                'data_processamento': datetime.now().isoformat(timespec='seconds'),
                'dias': data,
            }, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
            logger.info('JSON temporário de ordenação criado com %d dias', len(data))
            assets = obtain_assets(data, tmp_root / 'assets', logger, repository=repository, branch=branch, local_assets=local_assets)
            png_dir = tmp_root / 'png'
            png_dir.mkdir()
            png_files = {}
            excel_images = {}
            for index, (day, _, _, anchor) in enumerate(DAYS):
                image = render_day(data[day], index, dates[day], assets)
                if image is None:
                    logger.info('%s: sem eventos, imagem não será gerada', day)
                    continue
                try:
                    name = 'Agenda_' + name_of_day(dates[day]) + '.png'
                    path = png_dir / name
                    image.save(path, 'PNG')
                    png_files[name] = path
                    excel_images[anchor] = path
                    logger.info('%s: gerado %s', day, name)
                finally:
                    image.close()
            candidate = tmp_root / 'candidate.xlsx'
            make_excel_candidate(excel, excel_images, candidate, logger)
            _publish(excel, candidate, png_files, folder, monday.year, logger, tmp_root)
        logger.info('Agenda concluída: %s', folder)
        if open_results:
            try:
                open_result(excel)
                open_result(folder)
            except OSError:
                logger.exception('Geração concluída, mas falhou a abertura automática')
        return folder
    except Exception:
        logger.exception('Processamento interrompido')
        raise
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
