"""Interface mínima de desktop Windows."""
import json,threading,sys,os
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from .engine import run

DEFAULT_CONFIG={'github_repository':'mzestudos-codes/agenda-semanal-v2','github_branch':'master','github_assets_subdir':'agenda-assets'}

def config_path():
    # Em executáveis PyInstaller, configuração editável ao lado do .exe.
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent / 'config.json'
    return Path(__file__).resolve().parent.parent / 'config.json'

def main():
    root=tk.Tk();root.title('Agenda Semanal');root.geometry('480x185');root.resizable(False,False)
    root.columnconfigure(0,weight=1)
    filepath=tk.StringVar(value='Nenhum arquivo selecionado')
    ttk.Label(root,text='Agenda Semanal',font=('Segoe UI',16,'bold')).grid(row=0,column=0,padx=18,pady=(15,8),sticky='w')
    line=ttk.Frame(root);line.grid(row=1,column=0,padx=18,sticky='ew');line.columnconfigure(0,weight=1)
    ttk.Label(line,textvariable=filepath,width=44).grid(row=0,column=0,sticky='ew')
    def choose():
        selected=filedialog.askopenfilename(title='Selecione a planilha',filetypes=[('Excel','*.xlsx')]);
        if selected:filepath.set(selected);button.configure(state='normal')
    ttk.Button(line,text='Selecionar Excel',command=choose).grid(row=0,column=1,padx=(8,0))
    button=ttk.Button(root,text='Gerar agenda',state='disabled');button.grid(row=2,column=0,padx=18,pady=20,sticky='ew')
    def execute():
        file=filepath.get();button.configure(state='disabled',text='Processando...')
        def job():
            try:
                config=json.loads(config_path().read_text(encoding='utf8'))
                run(file,repository=config['github_repository'],branch=config.get('github_branch','master'),assets_subdir=config.get('github_assets_subdir',''))
            except Exception as exc:
                message=str(exc)
                def report():
                    messagebox.showerror('Erro na Agenda Semanal', message, parent=root)
                    button.configure(text='Gerar agenda', state='normal')
                    # Validação de dados: abrir a planilha para a pessoa corrigir.
                    if any(keyword in message.casefold() for keyword in ('duplicad', 'período', 'horário', 'marcador')):
                        try: os.startfile(file)
                        except (AttributeError, OSError): pass
                root.after(0, report)
            else:root.after(0,root.destroy)
        threading.Thread(target=job,daemon=True).start()
    button.configure(command=execute)
    root.mainloop()
