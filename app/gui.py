"""Interface desktop: geração da agenda e gerenciamento de ícones GitHub."""
import io
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from .engine import run
from . import github_icons as gh

DEFAULT_CONFIG={'github_repository':'mzestudos-codes/agenda-semanal-v2','github_branch':'master','github_assets_subdir':'agenda-assets','github_oauth_client_id':'Ov23limSoKRrQmtLzHYo'}

def config_path():
    if getattr(sys,'frozen',False):return Path(sys.executable).resolve().parent/'config.json'
    return Path(__file__).resolve().parent.parent/'config.json'

def main():
    root=tk.Tk();root.title('Agenda Semanal');root.geometry('650x610');root.minsize(620,580)
    root.columnconfigure(0,weight=1)
    config={**DEFAULT_CONFIG,**json.loads(config_path().read_text(encoding='utf-8'))}
    filepath=tk.StringVar(value='Nenhum arquivo selecionado')
    ttk.Label(root,text='Agenda Semanal',font=('Segoe UI',16,'bold')).grid(row=0,column=0,padx=18,pady=(12,6),sticky='w')
    agenda=ttk.LabelFrame(root,text='Gerar agenda',padding=12);agenda.grid(row=1,column=0,padx=18,pady=6,sticky='ew');agenda.columnconfigure(0,weight=1)
    ttk.Label(agenda,textvariable=filepath).grid(row=0,column=0,sticky='ew')
    def choose_excel():
        selected=filedialog.askopenfilename(title='Selecione a planilha',filetypes=[('Excel','*.xlsx')])
        if selected:filepath.set(selected);generate.configure(state='normal')
    ttk.Button(agenda,text='Selecionar Excel',command=choose_excel).grid(row=0,column=1,padx=(8,0))
    generate=ttk.Button(agenda,text='Gerar agenda',state='disabled');generate.grid(row=1,column=0,columnspan=2,pady=(12,0),sticky='ew')
    def execute():
        file=filepath.get();generate.configure(state='disabled',text='Processando...')
        def job():
            try:run(file,repository=config['github_repository'],branch=config.get('github_branch','master'),assets_subdir=config.get('github_assets_subdir',''))
            except Exception as exc:
                message=str(exc)
                def report():
                    messagebox.showerror('Erro na Agenda Semanal',message,parent=root)
                    generate.configure(text='Gerar agenda',state='normal')
                    if any(keyword in message.casefold() for keyword in ('duplicad','período','horário','marcador')):
                        try:os.startfile(file)
                        except (AttributeError,OSError):pass
                root.after(0,report)
            else:root.after(0,root.destroy)
        threading.Thread(target=job,daemon=True).start()
    generate.configure(command=execute)

    panel=ttk.LabelFrame(root,text='Gerenciar ícones',padding=12);panel.grid(row=2,column=0,padx=18,pady=(8,10),sticky='nsew')
    panel.columnconfigure(1,weight=1)
    mode=tk.StringVar(value='add');company=tk.StringVar();png_path=tk.StringVar(value='Nenhum PNG selecionado');status=tk.StringVar(value='Os ícones são publicados diretamente no GitHub.')
    token=[None];loaded=[False];current_names=[[]];new_bytes=[None];old_bytes=[None];busy=[False];cancel=threading.Event()
    ttk.Radiobutton(panel,text='Adicionar nova empresa',variable=mode,value='add',command=lambda:update_mode()).grid(row=0,column=0,columnspan=2,sticky='w')
    ttk.Radiobutton(panel,text='Substituir ícone existente',variable=mode,value='replace',command=lambda:update_mode()).grid(row=1,column=0,columnspan=2,sticky='w')
    ttk.Label(panel,text='Empresa:').grid(row=2,column=0,sticky='w',pady=(10,3))
    name_entry=ttk.Entry(panel,textvariable=company);name_entry.grid(row=2,column=1,sticky='ew',pady=(10,3))
    name_combo=ttk.Combobox(panel,textvariable=company,state='readonly');name_combo.grid(row=2,column=1,sticky='ew',pady=(10,3))
    ttk.Label(panel,textvariable=png_path).grid(row=3,column=1,sticky='w')
    ttk.Button(panel,text='Selecionar PNG',command=lambda:choose_png()).grid(row=3,column=0,sticky='w',pady=8)
    preview=ttk.Frame(panel);preview.grid(row=4,column=0,columnspan=2,sticky='ew',pady=8);preview.columnconfigure((0,1),weight=1)
    ttk.Label(preview,text='Ícone atual').grid(row=0,column=0)
    ttk.Label(preview,text='Novo ícone').grid(row=0,column=1)
    old_label=ttk.Label(preview,text='—',anchor='center');old_label.grid(row=1,column=0,pady=6)
    new_label=ttk.Label(preview,text='—',anchor='center');new_label.grid(row=1,column=1,pady=6)
    buttons=ttk.Frame(panel);buttons.grid(row=5,column=0,columnspan=2,sticky='ew',pady=6);buttons.columnconfigure(2,weight=1)
    connect=ttk.Button(buttons,text='Conectar ao GitHub');connect.grid(row=0,column=0,padx=(0,8))
    refresh=ttk.Button(buttons,text='Atualizar empresas');refresh.grid(row=0,column=1,padx=(0,8))
    publish=ttk.Button(buttons,text='Publicar ícone');publish.grid(row=0,column=2,sticky='e')
    ttk.Label(panel,textvariable=status,wraplength=565,foreground='#555555').grid(row=6,column=0,columnspan=2,sticky='w',pady=(10,0))
    def show_preview(label,data):
        label.configure(image='',text='—');label.image=None
        if data:
            try:
                image=Image.open(io.BytesIO(data)).convert('RGBA')
                image.thumbnail((238,100))
                photo=ImageTk.PhotoImage(image,master=root)
                label.configure(image=photo,text='');label.image=photo
            except Exception:label.configure(text='Prévia indisponível')
    def async_task(fn,on_success=None):
        if busy[0]:return
        busy[0]=True;publish.configure(state='disabled');connect.configure(state='disabled');refresh.configure(state='disabled')
        def job():
            try:result=fn()
            except Exception as exc:
                error=str(exc)
                def failure():
                    busy[0]=False;publish.configure(state='normal');connect.configure(state='normal');refresh.configure(state='normal')
                    status.set(error);messagebox.showerror('Gerenciador de ícones',error,parent=root)
                root.after(0,failure)
            else:
                def success():
                    busy[0]=False;publish.configure(state='normal');connect.configure(state='normal');refresh.configure(state='normal')
                    if on_success:on_success(result)
                root.after(0,success)
        threading.Thread(target=job,daemon=True).start()
    def refresh_names():
        status.set('Consultando empresas no GitHub...')
        def done(result):
            names=gh.icon_names(result[1]);current_names[0]=names;loaded[0]=True
            name_combo.configure(values=names)
            status.set(f'{len(names)} empresas disponíveis no GitHub.')
            if mode.get()=='replace' and company.get() not in names:company.set('')
        async_task(lambda:gh.current_manifest(config),done)
    def update_mode():
        company.set('');old_bytes[0]=None;show_preview(old_label,None)
        if mode.get()=='replace':
            name_entry.grid_remove();name_combo.grid();refresh_names() if not loaded[0] else None
        else:name_combo.grid_remove();name_entry.grid()
    def choose_png():
        selected=filedialog.askopenfilename(title='Selecione um ícone PNG',filetypes=[('Imagem PNG','*.png')])
        if not selected:return
        try:
            content=Path(selected).read_bytes();gh.validate_png(content)
        except (OSError,gh.GitHubIconError) as exc:
            messagebox.showerror('PNG inválido',str(exc),parent=root);return
        png_path.set(selected);new_bytes[0]=content;show_preview(new_label,content)
    def changed_company(*_):
        old_bytes[0]=None;show_preview(old_label,None)
        if mode.get()!='replace' or not company.get():return
        name=company.get()
        def done(content):
            if company.get()==name and mode.get()=='replace':old_bytes[0]=content;show_preview(old_label,content)
        async_task(lambda:gh.get_existing_png(config,name),done)
    name_combo.bind('<<ComboboxSelected>>',lambda _:changed_company())
    def connect_github():
        if token[0]:status.set('GitHub conectado.');return
        try:
            saved=gh.get_token(config['github_repository'])
        except Exception as exc:messagebox.showerror('Credenciais',str(exc),parent=root);return
        if saved:
            def verify():return gh.request_json(gh.API+'/user',saved)
            def verified(_):token[0]=saved;status.set('GitHub conectado com credencial salva.')
            # Credencial expirada: limpar e oferecer nova autorização.
            def verify_and_cleanup():
                try:return verify()
                except gh.GitHubIconError:
                    gh.delete_token(config['github_repository'])
                    raise gh.GitHubIconError('A autorização salva expirou. Clique em Conectar ao GitHub novamente.')
            async_task(verify_and_cleanup,verified);return
        client_id=config.get('github_oauth_client_id','')
        if not client_id:messagebox.showerror('Configuração','Client ID não configurado.',parent=root);return
        status.set('Solicitando código de autorização ao GitHub...')
        def start():return gh.begin_device_flow(client_id)
        def got_code(info):
            code=info['user_code'];url=info['verification_uri']
            status.set(f'Acesse {url} e informe o código {code}.')
            root.clipboard_clear();root.clipboard_append(code)
            webbrowser.open(url)
            messagebox.showinfo('Autorizar GitHub',f'O código {code} foi copiado.\n\nNo navegador, abra {url}, informe o código e autorize a Agenda Semanal.\n\nApós clicar em OK, o programa aguardará a autorização.',parent=root)
            def wait():
                access=gh.poll_device_flow(client_id,info['device_code'],info.get('interval',5),info.get('expires_in',900),cancel)
                gh.request_json(gh.API+'/user',access)
                gh.save_token(config['github_repository'],access)
                return access
            def ready(access):token[0]=access;status.set('GitHub conectado. Agora você pode publicar ícones.')
            async_task(wait,ready)
        async_task(start,got_code)
    def publish_icon():
        name=company.get().strip();replace=mode.get()=='replace'
        try:gh.validate_company(name)
        except gh.GitHubIconError as exc:messagebox.showerror('Empresa inválida',str(exc),parent=root);return
        if not new_bytes[0]:messagebox.showwarning('PNG necessário','Selecione um PNG de 119 × 50 pixels.',parent=root);return
        if not token[0]:messagebox.showinfo('Conectar ao GitHub','Clique em Conectar ao GitHub antes de publicar.',parent=root);return
        if replace and not messagebox.askyesno('Confirmar substituição',f'Deseja realmente substituir o ícone de {name}?\n\nA alteração será disponibilizada para toda a equipe.',parent=root):return
        status.set('Publicando PNG e manifesto no GitHub...')
        def done(sha):
            status.set('Ícone publicado com sucesso! Commit: '+sha[:12])
            new_bytes[0]=None;png_path.set('Nenhum PNG selecionado');show_preview(new_label,None)
            loaded[0]=False
            refresh_names()
            messagebox.showinfo('Publicação concluída','O ícone e o manifesto foram atualizados no GitHub.',parent=root)
        async_task(lambda:gh.publish_icon(config,token[0],name,new_bytes[0],replace),done)
    connect.configure(command=connect_github);refresh.configure(command=refresh_names);publish.configure(command=publish_icon)
    update_mode()
    root.mainloop()
