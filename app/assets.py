"""Recursos públicos no GitHub, baixados para uso temporário."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
from urllib.request import Request,urlopen
from urllib.parse import quote
import hashlib,json,re
from .validation import AgendaError,MARKERS,CATEGORIES

PREFIX='https://raw.githubusercontent.com'
API='https://api.github.com'

def fetch(url,limit=12_000_000):
    req=Request(url,headers={'User-Agent':'AgendaMercado/1.0','Accept':'application/vnd.github+json'})
    try:
        with urlopen(req,timeout=15) as response:
            data=response.read(limit+1)
    except Exception as exc:raise AgendaError(f'Não foi possível consultar recurso online ({url}): {exc}') from exc
    if len(data)>limit:raise AgendaError('Recurso remoto excede o tamanho permitido.')
    return data

def safe_rel(path):
    p=PurePosixPath(path)
    if p.is_absolute() or '..' in p.parts or '\\' in path or not path or p.parts[0]=='.':raise AgendaError(f'Caminho inseguro no manifesto: {path!r}')
    return str(p)

def manifest_index(manifest):
    if manifest.get('schema_version')!=1 or not isinstance(manifest.get('assets'),dict):raise AgendaError('Manifesto do GitHub inválido (schema_version/assets).')
    idx={}
    for path, entry in manifest['assets'].items():
        p=safe_rel(path)
        if not isinstance(entry,dict) or not re.fullmatch('[0-9a-fA-F]{64}',str(entry.get('sha256',''))):raise AgendaError(f'Hash SHA-256 inválido no manifesto: {path}')
        key=p.casefold()
        if key in idx:raise AgendaError(f'Arquivos com nomes conflitantes no manifesto: {p}')
        idx[key]=(p,entry['sha256'].lower())
    return idx

def desired_paths(data,logger):
    required=set(['Fonte/Lato-SemiBold.ttf','Fonte/Lato-Bold.ttf','Icones/MZ/icon-calendar@3x.png'])
    for day,groups in data.items():
        present=[c for c in CATEGORIES if groups[c]]
        if not present:continue
        counts=[int(c in present) for c in CATEGORIES]
        required.add(f'Fundo/Base{counts[0]}Divul{counts[1]}Conf{counts[2]}Inv.png')
        for cat in present:
            category_icon={'divulgacoes':'icon-Divulgações@3x.png','conferencias':'icon-conferencias@3x.png','investor_day':'icon-investor-day@3x.png'}[cat]
            required.add('Icones/MZ/'+category_icon)
            for event in groups[cat]:
                required.add('Icones/'+event['empresa']+'.png')
                if cat=='investor_day' and event.get('mz_arena'):
                    required.add('Icones/MZ/MZArena.png')
    logger.info('Recursos requeridos: %d',len(required))
    return required

def obtain_assets(data,temporary_dir,logger,repository=None,branch='main',local_assets=None,assets_subdir=''):
    required=desired_paths(data,logger)
    if local_assets is not None:
        # Exclusivamente para teste e auditoria local; produção exige GitHub.
        root=Path(local_assets)
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf8'))
        idx=manifest_index(manifest)
        def read_asset(p):return (root/p).read_bytes()
    else:
        if not repository or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository):raise AgendaError('Configure o repositório público GitHub no arquivo config.json (campo github_repository).')
        if repository.startswith('SEU_USUARIO/'):
            raise AgendaError('Configure o repositório GitHub público em config.json antes de gerar a agenda.')
        assets_subdir = safe_rel(assets_subdir.strip('/')) if assets_subdir else ''
        commit=json.loads(fetch(f'{API}/repos/{repository}/commits/{quote(branch,safe="")}'))['sha']
        base=f'{PREFIX}/{repository}/{commit}'
        prefix = assets_subdir + '/' if assets_subdir else ''
        manifest=json.loads(fetch(base+'/'+quote(prefix+'manifest.json',safe='/')))
        idx=manifest_index(manifest)
        logger.info('GitHub: %s, revisão %s',repository,commit)
        def read_asset(p):return fetch(base+'/'+quote(prefix+p,safe='/'))
    missing = sorted((name for name in required if name.casefold() not in idx), key=str.casefold)
    if missing:
        locations = {}
        for day, groups in data.items():
            for category in CATEGORIES:
                for event in groups[category]:
                    key = 'Icones/' + event['empresa'] + '.png'
                    locations.setdefault(key.casefold(), set()).add(day)
        labels = []
        for name in missing:
            days = locations.get(name.casefold(), set())
            labels.append(f"{name.removeprefix('Icones/').removesuffix('.png')} ({', '.join(sorted(days))})" if days else name.removeprefix('Icones/').removesuffix('.png'))
        raise AgendaError('Recursos visuais ausentes no GitHub:\n' + '\n'.join(' - ' + name for name in labels))
    resolved={requested:idx[requested.casefold()][0] for requested in sorted(required)}
    for requested,real in resolved.items():
        content=read_asset(real)
        sha=idx[real.casefold()][1]
        if hashlib.sha256(content).hexdigest()!=sha:raise AgendaError(f'Integridade inválida do recurso: {real}')
        dest=temporary_dir/real
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(content)
        logger.info('Baixado: %s (%d bytes)',real,len(content))
    return {name:temporary_dir/path for name,path in resolved.items()}
