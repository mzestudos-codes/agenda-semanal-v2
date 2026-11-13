# ADR-001 — Recursos visuais remotos por execução

**Status:** aprovado e implementado.

**Contexto:** o script original dependia de pastas `Icones/`, `Fundo/` e `Fonte/` distribuídas manualmente com a aplicação. A solução deve usar sempre os arquivos atualizados, sem login nem cache permanente.

**Decisão:** manter os recursos visuais num repositório público GitHub. A aplicação resolve um commit atual, baixa apenas os recursos necessários para a execução, verifica cada SHA-256 e utiliza os arquivos numa pasta temporária excluída ao finalizar. Sem internet, não gera imagens.

**Consequências:** atualizar ícones não exige redistribuir o EXE. É necessário publicar um `manifest.json` junto com os arquivos e manter seus hashes corretos. Recursos temporários de execuções interrompidas são removidos na próxima inicialização quando não pertencem a um processo ativo.

**Preservação visual:** a implementação foi comparada pixel a pixel contra o renderizador original para cinco dias usando os dados da planilha de referência. Resultado: cinco imagens idênticas quando a ordem dos eventos é mantida para isolamento do desenho. Ordenação é responsabilidade de `validation.py`.
