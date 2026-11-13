"""Autenticação Device Flow e publicação atômica de ícones no GitHub."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from PIL import Image
from .assets import manifest_index, safe_rel

API = 'https://api.github.com'
LOGIN = 'https://github.com/login'
SERVICE = 'AgendaSemanal-GitHub'
MAX_PNG = 2_000_000

class GitHubIconError(Exception):
    pass

def request_json(url, token=None, method='GET', data=None, form=False):
    headers={'Accept':'application/vnd.github+json','User-Agent':'AgendaSemanal/2.0','X-GitHub-Api-Version':'2022-11-28'}
    if token: headers['Authorization']='Bearer '+token
    if data is not None:
        if form:
            payload=urlencode(data).encode('utf-8');headers['Content-Type']='application/x-www-form-urlencoded'
        else:
            payload=json.dumps(data).encode('utf-8');headers['Content-Type']='application/json'
    else: payload=None
    try:
        with urlopen(Request(url,data=payload,headers=headers,method=method),timeout=25) as r:
            return json.loads(r.read(5_000_000))
    except HTTPError as exc:
        try: detail=json.loads(exc.read().decode('utf-8')).get('message','')
        except Exception: detail=''
        raise GitHubIconError(f'GitHub HTTP {exc.code}: {detail or exc.reason}') from exc
    except (URLError,TimeoutError,ValueError) as exc:
        raise GitHubIconError(f'Falha na comunicação com o GitHub: {exc}') from exc

def begin_device_flow(client_id):
    if not re.fullmatch(r'[A-Za-z0-9]+',client_id or ''):raise GitHubIconError('Client ID inválido.')
    result=request_json(LOGIN+'/device/code',method='POST',data={'client_id':client_id,'scope':'repo'},form=True)
    if not all(k in result for k in ('device_code','user_code','verification_uri')):raise GitHubIconError('Resposta inesperada do GitHub ao iniciar autorização.')
    return result

def poll_device_flow(client_id,device_code,interval,expires_in,cancel=None):
    end=time.monotonic()+int(expires_in)
    delay=max(5,int(interval))
    while time.monotonic()<end:
        for _ in range(delay*2):
            if cancel is not None and cancel.is_set():raise GitHubIconError('Autorização cancelada.')
            if time.monotonic()>=end:break
            time.sleep(.5)
        result=request_json(LOGIN+'/oauth/access_token',method='POST',data={'client_id':client_id,'device_code':device_code,'grant_type':'urn:ietf:params:oauth:grant-type:device_code'},form=True)
        if result.get('access_token'):return result['access_token']
        error=result.get('error')
        if error=='authorization_pending':continue
        if error=='slow_down':delay+=5;continue
        if error=='expired_token':break
        if error=='access_denied':raise GitHubIconError('A autorização foi recusada no navegador.')
        raise GitHubIconError('Falha na autorização: '+str(result.get('error_description',error)))
    raise GitHubIconError('O código de autorização expirou. Tente novamente.')

def _keyring():
    try:import keyring
    except ImportError as exc:raise GitHubIconError('Dependência keyring não instalada.') from exc
    return keyring

def get_token(repository):return _keyring().get_password(SERVICE,repository)
def save_token(repository,token):_keyring().set_password(SERVICE,repository,token)
def delete_token(repository):
    try:_keyring().delete_password(SERVICE,repository)
    except Exception:pass

def validate_company(name):
    name=name.strip()
    if not name or len(name)>100 or name in ('.','..') or any(ch in name for ch in '/\\<>:"|?*\r\n\t') or name.endswith(('.', ' ')) or any(ord(ch)<32 for ch in name):
        raise GitHubIconError('Nome da empresa inválido. Use um nome de arquivo simples, sem barras ou caracteres especiais de caminho.')
    if name.casefold() in {'con','prn','aux','nul'} or re.fullmatch(r'(com|lpt)[1-9]',name,re.I):raise GitHubIconError('Nome reservado pelo Windows.')
    return name

def validate_png(content):
    if not content or len(content)>MAX_PNG:raise GitHubIconError('O PNG deve ter até 2 MB.')
    if not content.startswith(b'\x89PNG\r\n\x1a\n'):raise GitHubIconError('O arquivo selecionado não é um PNG válido.')
    try:
        with Image.open(io.BytesIO(content)) as im:
            if im.format!='PNG':raise ValueError('formato incorreto')
            width,height=im.size
            im.verify()
    except Exception as exc:raise GitHubIconError('O PNG está corrompido ou é inválido.') from exc
    if (width,height)!=(119,50):raise GitHubIconError(f'Dimensões inválidas: {width} × {height} pixels. O ícone deve ter exatamente 119 × 50 pixels.')

def repository_config(config):
    repo=config['github_repository'];branch=config.get('github_branch','master');subdir=config.get('github_assets_subdir','agenda-assets')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise GitHubIconError('Repositório inválido.')
    if not re.fullmatch(r'[A-Za-z0-9_.\-/]+',branch) or '..' in branch:raise GitHubIconError('Branch inválida.')
    return repo,branch,safe_rel(subdir.strip('/'))

def current_manifest(config, revision=None):
    repo,branch,subdir=repository_config(config)
    # O endpoint Contents devolve o conteúdo da revisão selecionada.
    path=quote(f'{subdir}/manifest.json',safe='/')
    response=request_json(f'{API}/repos/{repo}/contents/{path}?ref={quote(revision or branch,safe="")}')
    if response.get('encoding')!='base64':raise GitHubIconError('Manifesto inesperado no GitHub.')
    manifest=json.loads(base64.b64decode(response['content']))
    return manifest,manifest_index(manifest)

def icon_names(index):
    return sorted((path[len('Icones/'):-4] for path,_ in index.values() if path.startswith('Icones/') and '/' not in path[len('Icones/'): ] and path.lower().endswith('.png')),key=str.casefold)

def get_existing_png(config,company):
    repo,branch,subdir=repository_config(config)
    manifest,index=current_manifest(config)
    key=('Icones/'+company+'.png').casefold()
    if key not in index:raise GitHubIconError('Ícone não encontrado no manifesto.')
    path,sha=index[key]
    response=request_json(f'{API}/repos/{repo}/contents/{quote(subdir+"/"+path,safe="/")}?ref={quote(branch,safe="")}')
    content=base64.b64decode(response['content'])
    if hashlib.sha256(content).hexdigest()!=sha:raise GitHubIconError('O ícone atual não corresponde ao manifesto.')
    return content

def publish_icon(config,token,company,content,replace=False):
    """Publica PNG + manifesto num único commit, com CAS e retry de concorrência."""
    validate_png(content)
    company=validate_company(company)
    repo,branch,subdir=repository_config(config)
    if not token:raise GitHubIconError('Conecte-se ao GitHub antes de publicar.')
    ref_url=f'{API}/repos/{repo}/git/ref/heads/{quote(branch,safe="/")}'
    for attempt in range(3):
        ref=request_json(ref_url,token)
        parent_sha=ref['object']['sha']
        commit=request_json(f'{API}/repos/{repo}/git/commits/{parent_sha}',token)
        tree_sha=commit['tree']['sha']
        manifest,index=current_manifest(config,parent_sha)
        key=('Icones/'+company+'.png').casefold()
        exists=key in index
        if replace and not exists:raise GitHubIconError('O ícone foi removido. Atualize a lista antes de substituir.')
        if not replace and exists:raise GitHubIconError('Esta empresa já está cadastrada. Utilize “Substituir ícone existente”.')
        # Substituições preservam o nome/capitalização original do arquivo.
        path=index[key][0] if exists else 'Icones/'+company+'.png'
        digest=hashlib.sha256(content).hexdigest()
        manifest['assets'][path]={'sha256':digest,'type':'image/png'}
        png_blob=request_json(f'{API}/repos/{repo}/git/blobs',token,'POST',{'content':base64.b64encode(content).decode('ascii'),'encoding':'base64'})['sha']
        manifest_blob=request_json(f'{API}/repos/{repo}/git/blobs',token,'POST',{'content':json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','encoding':'utf-8'})['sha']
        tree=request_json(f'{API}/repos/{repo}/git/trees',token,'POST',{'base_tree':tree_sha,'tree':[
            {'path':subdir+'/'+path,'mode':'100644','type':'blob','sha':png_blob},
            {'path':subdir+'/manifest.json','mode':'100644','type':'blob','sha':manifest_blob}
        ]})['sha']
        new_commit=request_json(f'{API}/repos/{repo}/git/commits',token,'POST',{'message':f'assets: {"atualiza" if replace else "adiciona"} ícone {company}','tree':tree,'parents':[parent_sha]})['sha']
        try:
            request_json(ref_url,token,'PATCH',{'sha':new_commit,'force':False})
            return new_commit
        except GitHubIconError as exc:
            if attempt==2 or 'HTTP 422' not in str(exc):raise
    raise GitHubIconError('O repositório foi alterado simultaneamente. Tente novamente.')
