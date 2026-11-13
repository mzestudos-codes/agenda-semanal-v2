# Implementação — Entrega 1.0

**Status:** código integrado, execução local validada. Publicação no GitHub e criação do EXE Windows dependem do ambiente/conta do proprietário.

## Testes executados

- 13 testes automatizados passaram (`python -m unittest discover -s tests -v`).
- A composição de segunda a sexta foi comparada com saídas da função `criar_imagem` do `Agenda_Semanal_Old.py`: **zero pixels diferentes nos cinco dias**, com os eventos mantidos na ordem original apenas para isolar o desenho. O fluxo normal usa eventos ordenados.
- A planilha fornecida foi executada duas vezes numa cópia sem passar pelo Excel entre execuções. Os valores calculados das colunas normalizadas continuaram disponíveis após o primeiro salvamento.
- Um caso sintético com terça a sexta vazias gerou apenas a imagem de segunda, removeu uma imagem antiga de terça e preservou uma imagem alheia à agenda em `C42`.
- Ícone ausente bloqueou geração sem modificar o arquivo; manifesto com hash de ícone incorreto foi rejeitado.
- Foram conferidos 434 recursos e 434 entradas no manifesto, com SHA-256 compatíveis.

## Limitações não resolvidas neste ambiente

1. **Publicação remota:** não há endereço de repositório GitHub real fornecido nem conexão autorizada com a conta. Portanto o teste de rede real não foi executado. O código usa API pública de commits e conteúdo por SHA.
2. **Empacotamento Windows:** o EXE precisa ser compilado e testado em Windows (script e GitHub Actions incluídos). Não há EXE Windows criado nesta entrega.
3. **Excel com recursos não suportados:** planilhas além da amostra podem conter objetos que o openpyxl não preserva. Existe teste de imagem fora da área da agenda, mas controles ActiveX e objetos similares não foram validados.
4. **Arquivos finais em múltiplos volumes:** a publicação usa staging no volume de cada destino e tenta rollback. Desligamento abrupto pode deixar arquivos parcialmente atualizados.
5. **Fórmulas recalculadas:** a aplicação preserva os valores calculados anteriormente no Excel; não recalcula alterações ainda não salvas/calculadas pelo Excel.

## Itens entregues

- Aplicação modular (`app/`, `main.py`), GUI e compilação Windows.
- Manifesto e todos os arquivos visuais preparados para GitHub público.
- Testes unitários, integração e regressão visual.
- Documentos de arquitetura, especificação, ADR e este relatório.
- Códigos anteriores preservados em `legacy/` para auditoria e comparação.
