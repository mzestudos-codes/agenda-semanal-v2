# Publicação do sistema em dois repositórios GitHub

## A. Recursos visuais (público)

1. Crie um repositório **público** chamado, por exemplo, `agenda-assets`.
2. Extraia `AgendaSemanal_Recursos_GitHub.zip`.
3. Envie **o conteúdo** da pasta extraída, incluindo `manifest.json`, `Icones/`, `Fundo/` e `Fonte/`, à raiz do repositório.
4. Confirme que `manifest.json` pode ser visto no navegador no topo do repositório e que os nomes com acentos estão corretos.
5. Ao editar um recurso, execute `python tools_update_manifest.py <pasta-dos-recursos>` no projeto da aplicação e publique o manifesto atualizado no mesmo commit.

**Atenção:** antes de publicar imagens de marcas/logotipos em repositório público, verifique as permissões de distribuição que se aplicam ao material.

## B. Aplicação

1. Extraia `AgendaSemanal_Codigo.zip`.
2. Altere `config.json`, preenchendo `github_repository` com `seu-usuario/agenda-assets`.
3. Para executar com Python no Windows: instale dependências e abra `main.py`.
4. Para obter o `.exe` localmente: execute `build_windows.bat` no Windows.
5. Para obter o `.exe` pelo GitHub Actions: publique o **código** da aplicação num repositório de código (sem a planilha de exemplo), abra **Actions**, execute **Compilar Agenda Semanal (Windows)** e baixe `AgendaSemanal-Windows`.
6. Distribua somente `AgendaSemanal.exe` e `config.json` juntos aos usuários.

O usuário final não precisa de uma conta GitHub, baixar ícones, guardar cache nem manter arquivos de fundo ou fonte. **Uma conexão com a internet é necessária a cada geração.**
