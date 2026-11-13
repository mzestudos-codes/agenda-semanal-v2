"""Entrada de execução para interface e automação de testes."""
import argparse
import json
from app.gui import config_path
from app.engine import run
from app.gui import main as gui_main

def main():
    parser=argparse.ArgumentParser(description='Geração da Agenda Semanal')
    parser.add_argument('--excel',help='Planilha .xlsx de entrada')
    parser.add_argument('--repository',help='GitHub público owner/repository')
    parser.add_argument('--branch',default=None)
    parser.add_argument('--assets-dir',help='SOMENTE TESTE: diretório de assets com manifest.json')
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    if args.excel:
        config = json.loads(config_path().read_text(encoding='utf-8')) if config_path().is_file() else {}
        folder=run(args.excel,repository=args.repository or config.get('github_repository'),branch=args.branch or config.get('github_branch','master'),assets_subdir=config.get('github_assets_subdir',''),local_assets=args.assets_dir,open_results=not args.no_open)
        print(folder)
    else:gui_main()

if __name__=='__main__':main()
