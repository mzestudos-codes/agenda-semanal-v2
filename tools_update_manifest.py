import sys,hashlib,json
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).parent/'repo_github'
assets={}
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.name=='manifest.json':continue
    rel=p.relative_to(root).as_posix()
    if p.suffix.lower() not in ('.png','.ttf'):continue
    assets[rel]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'type':'font/ttf' if p.suffix.lower()=='.ttf' else 'image/png'}
(root/'manifest.json').write_text(json.dumps({'schema_version':1,'assets_version':'1.0.0','assets':assets},ensure_ascii=False,indent=2),encoding='utf8')
print('Manifesto atualizado:',len(assets),'arquivos')
