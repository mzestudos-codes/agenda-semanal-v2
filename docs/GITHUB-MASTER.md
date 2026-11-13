# Publicação no GitHub — branch master

Repositório: `mzestudos-codes/agenda-semanal-v2`

Recursos públicos: `agenda-assets/manifest.json`, `agenda-assets/Icones/`, `agenda-assets/Fundo/`, `agenda-assets/Fonte/`.

O carregador usa o campo `github_assets_subdir` do `config.json` para localizar o manifesto e os arquivos no subdiretório. O download consulta um commit fixo e valida SHA-256.

## Como atualizar

Substitua no repositório: `app/assets.py`, `app/engine.py`, `app/gui.py`, `main.py`, `config.json`, `.github/workflows/build-windows.yml`.

O `config.json` distribuído com o executável deve ficar ao lado de `AgendaSemanal.exe`.

## Compilar via Actions

Abra o repositório → Actions → Compilar Agenda Semanal (Windows) → Run workflow → branch master → Run workflow. Após sucesso, na execução do workflow, baixe o artefato `AgendaSemanal-Windows`. Ele deverá conter `AgendaSemanal.exe` e `config.json`.

Nota: testes que exigem recursos locais poderão ser ignorados quando esses recursos não estiverem no checkout; realize teste de geração real com uma cópia do Excel antes da distribuição.

## Atualizar imagens/fundos/fontes

Ao alterar recursos, regenere o manifesto (hashes), publique os dois no mesmo commit na branch `master`, e a próxima execução utilizará a nova versão.
