"""Orquestrador do AgendaMercado. Preserva app.engine.run para testes legados."""
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory,NamedTemporaryFile
from zipfile import ZipFile
import json,os,shutil,uuid
from openpyxl import load_workbook
from .assets import obtain_assets
from .daily import read_daily_date,validate_daily,render_daily
from .engine import assert_excel_access,cleanup_stale_temp,logger_for,open_result
from .excel_write import make_excel_candidate
from .render import render_day
from .validation import AgendaError,DAYS,MONTHS,read_week_dates,validate_and_sort


def image_name(mode,day):
    return f'Agenda_{"Semanal" if mode=="semanal" else "Diaria"}_{day.day:02d}-{MONTHS[day.month-1]}-{day.year}.png'


def period_folder(mode, start, end=None):
    """Subpasta legível para uma semana ou uma data diária."""
    def label(day):
        return f'{day.day:02d}-{MONTHS[day.month-1]}-{day.year}'
    if mode == 'semanal':
        if end is None:
            raise ValueError('Informe o último dia da semana.')
        return f'Agenda Semanal de {label(start)} até {label(end)}'
    if mode == 'diaria':
        return f'Agenda Diária de {label(start)}'
    raise ValueError(f'Modalidade desconhecida: {mode}')


def publish(excel,candidate,outputs,logger):
    """Substitui arquivos estagiados, faz rollback em erros comuns e preserva imagens históricas."""
    backup=excel.with_name('.agenda-backup-'+uuid.uuid4().hex+'.xlsx')
    stages=[];old={};installed=[];created=[];success=False
    try:
        shutil.copy2(excel,backup)
        for dest in outputs:
            if not dest.parent.exists():dest.parent.mkdir(parents=True);created.append(dest.parent)
            old[dest]=dest.read_bytes() if dest.exists() else None
        for dest,src in [(excel,candidate),*outputs.items()]:
            with NamedTemporaryFile(dir=dest.parent,prefix='.agenda-stage-',suffix=dest.suffix,delete=False) as f:stage=Path(f.name)
            stages.append(stage);shutil.copyfile(src,stage)
        with ZipFile(stages[0]) as archive:
            if archive.testzip():raise AgendaError('Cópia temporária do Excel inválida.')
        os.replace(stages[0],excel)
        for dest,stage in zip(outputs,stages[1:]):os.replace(stage,dest);installed.append(dest)
        logger.info('Publicados %d PNGs',len(outputs));success=True
    except Exception as exc:
        logger.exception('Falha na publicação; tentando restaurar')
        try:
            if backup.exists():os.replace(backup,excel)
            for target in installed:
                content=old[target]
                if content is None:target.unlink(missing_ok=True)
                else:
                    with NamedTemporaryFile(dir=target.parent,prefix='.agenda-restore-',suffix='.png',delete=False) as f:restore=Path(f.name)
                    try:restore.write_bytes(content);os.replace(restore,target)
                    finally:restore.unlink(missing_ok=True)
        except Exception as restore_error:
            logger.exception('Não foi possível restaurar todos os arquivos')
            raise AgendaError(f'Restauração incompleta. Backup do Excel: {backup}') from restore_error
        if isinstance(exc,PermissionError):raise AgendaError('Feche o Excel e verifique as permissões de gravação.') from exc
        raise
    finally:
        for stage in stages:stage.unlink(missing_ok=True)
        if success:backup.unlink(missing_ok=True)
        for folder in reversed(created):
            if folder.exists() and not any(folder.iterdir()):folder.rmdir()


def run(excel_path,mode='semanal',repository=None,branch='master',local_assets=None,assets_subdir='',open_results=True,progress=None):
    if mode not in ('semanal','diaria','ambas'):raise AgendaError('Modalidade desconhecida.')
    excel=Path(excel_path).expanduser().resolve();assert_excel_access(excel)
    logger=logger_for(excel);cleanup_stale_temp()
    def report(value):
        logger.info(value)
        if progress:progress(value)
    try:
        report('Validando dados de ambas as agendas...' if mode=='ambas' else 'Validando a planilha...')
        book=load_workbook(excel,data_only=True,read_only=True)
        try:
            names=['Semanal'] if mode=='semanal' else ['Diária'] if mode=='diaria' else ['Semanal','Diária']
            for name in names:
                if name not in book.sheetnames:raise AgendaError(f'A aba {name} não existe na planilha.')
            weekly=dates=daily=daily_day=None
            if 'Semanal' in names:
                weekly=validate_and_sort(book['Semanal'],logger);dates=read_week_dates(book['Semanal'])
            if 'Diária' in names:
                daily_day=read_daily_date(book['Diária']);daily=validate_daily(book['Diária'],logger)
        finally:book.close()
        groups=dict(weekly or {})
        if daily is not None:groups['diaria']=daily
        with TemporaryDirectory(prefix='agenda-mercado-') as dirname:
            tmp=Path(dirname)
            (tmp/'eventos_ordenados.json').write_text(json.dumps({'semanal':weekly,'diaria':daily},ensure_ascii=False,indent=2,default=str),encoding='utf-8')
            report('Conferindo ícones e recursos visuais...')
            assets=obtain_assets(groups,tmp/'assets',logger,repository=repository,branch=branch,local_assets=local_assets,assets_subdir=assets_subdir)
            png_dir=tmp/'png';png_dir.mkdir();outputs={};sheets={}
            if weekly is not None:
                images={}
                week_folder=excel.parent/'Imagens'/'Semanal'/period_folder('semanal',min(dates.values()),max(dates.values()))
                for i,(day,_,_,anchor) in enumerate(DAYS):
                    image=render_day(weekly[day],i,dates[day],assets)
                    if image is None:continue
                    try:
                        name=image_name('semanal',dates[day]);file=png_dir/name;image.save(file,'PNG')
                        images[anchor]=file;outputs[week_folder/name]=file
                    finally:image.close()
                sheets['Semanal']=images
                report('Imagens semanais prontas.')
            if daily is not None:
                image=render_daily(daily,daily_day,assets)
                try:
                    name=image_name('diaria',daily_day);file=png_dir/name;image.save(file,'PNG')
                    outputs[excel.parent/'Imagens'/'Diaria'/period_folder('diaria',daily_day)/name]=file;sheets['Diária']={'Q3':file}
                finally:image.close()
                report('Imagem diária pronta.')
            candidate=tmp/'candidate.xlsx'
            make_excel_candidate(excel,{},candidate,logger,sheets=sheets)
            report('Publicando Excel e imagens...')
            publish(excel,candidate,outputs,logger)
        report(f'Concluído: {len(outputs)} imagem(ns).')
        if open_results:
            try:
                open_result(excel)
                for folder in set(output.parent for output in outputs):open_result(folder)
            except OSError:logger.exception('Geração concluída; abertura automática indisponível.')
        return list(outputs)
    except Exception:
        logger.exception('Processamento interrompido')
        raise
    finally:
        for handler in list(logger.handlers):handler.close();logger.removeHandler(handler)
