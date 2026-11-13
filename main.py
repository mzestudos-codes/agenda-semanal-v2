import argparse,json
from app.gui import config_path,main as gui_main
from app.mercado import run

def main():
    p=argparse.ArgumentParser(description='AgendaMercado')
    p.add_argument('--excel');p.add_argument('--mode',choices=['semanal','diaria','ambas'],default='semanal')
    p.add_argument('--repository');p.add_argument('--branch');p.add_argument('--assets-dir');p.add_argument('--no-open',action='store_true')
    a=p.parse_args()
    if not a.excel:return gui_main()
    cfg=json.loads(config_path().read_text(encoding='utf-8')) if config_path().exists() else {}
    paths=run(a.excel,mode=a.mode,repository=a.repository or cfg.get('github_repository'),branch=a.branch or cfg.get('github_branch','master'),local_assets=a.assets_dir,assets_subdir=cfg.get('github_assets_subdir',''),open_results=not a.no_open)
    for path in paths:print(path)

if __name__=='__main__':main()
