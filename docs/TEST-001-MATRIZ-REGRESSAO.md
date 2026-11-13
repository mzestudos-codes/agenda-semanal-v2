# TEST-001 — Matriz de regressão da Agenda Semanal

**Status:** cenários especificados; execução e evidências de imagens ainda pendentes.  
**Referências:** `SPEC-001.md` v0.2, `NomesSemanal.xlsx` (amostra 17–21/11/2025), `Recursos_Visuais.zip`.

## Evidência da planilha de exemplo (somente leitura)

| Dia | Linhas | Divulgação | Conferências | Investor Day | Imagem existente |
|---|---|---|---|---|---|
| Segunda 17/11 | 4–8 | `XP` (Após Fech.) | `RUMO`, `ONCOCLINICAS`, `SER EDUCACIONAL`, `COSAN` e `VejaMaisConferencias` | — | `P4` |
| Terça 18/11 | 12–16 | — | — | `FRAS-LE`, `ÂNIMA`, `ASSAÍ` | `AB4` |
| Quarta 19/11 | 20–24 | — | — | `IGUÁ`, `COPEL` | `AN4` |
| Quinta 20/11 | 28–32 | `LOJAS RENNER` (Antes Abert.) | — | — | `AZ4` |
| Sexta 21/11 | 36–40 | `CONTAX` (`-`) | — | — | `BL4` |

O arquivo de origem possui cinco objetos gráficos nas âncoras acima. **Isso não demonstra que a remoção seletiva já funciona**: precisa ser testada em cópia.

## Casos de regressão planejados

| ID | Cenário | Resultado esperado | Evidência necessária |
|---|---|---|---|
| T01 | Executar com a planilha de exemplo intacta | Cinco PNGs, nomes de datas corretos, cinco imagens substituídas no Excel | Comparação das imagens antes/depois e inspeção do `.xlsx` |
| T02 | Segunda, conferências com K=`09:00`, `10:00`, `10:00`, `11:00` e L=`Trad. Simul.` | Ordenação por horário válido; empate das 10:00 por nome; exibição intacta dos rótulos | JSON/log e pixels |
| T03 | Marcador `VejaMaisConferencias` | Quinta posição, sem rótulos adicionais | Pixel/layout e JSON |
| T04 | Sexta, `CONTAX`, J=`-` | Válido; renderiza hífen e ordena após os períodos conhecidos | JSON/log e PNG |
| T05 | Empresa em A com J verdadeiramente vazia | Bloqueia antes de modificar o Excel ou gerar saídas definitivas | Erro e hash do Excel antes/depois |
| T06 | Investor Day com N=`-` (`ASSAÍ`) | Ausência de horário de ordenação; exibir texto normalizado | JSON/log e PNG |
| T07 | Esvaziar terça e quarta em cópia | Não criar PNGs desses dias; remover somente as imagens da agenda nesses dias | Conteúdo da pasta e imagens no Excel |
| T08 | Semana completamente vazia em cópia | Informar ausência e não alterar Excel | Hash da planilha e ausência de novos PNGs |
| T09 | Empresa duplicada na mesma categoria/dia | Bloquear com dia/categoria/nome | Mensagem/log |
| T10 | Empresa em categorias diferentes no mesmo dia | Permitir | JSON/log |
| T11 | Ícone de empresa necessário ausente no manifesto | Bloquear toda a geração com empresa/dia | Mensagem/log, nenhuma saída definitiva |
| T12 | Fundo requerido ausente | Bloquear toda a geração indicando o nome do fundo | Mensagem/log |
| T13 | Falha de rede ou download incompleto | Não atualizar Excel, limpar temporários da execução | Mensagem/log, hash Excel |
| T14 | Excel bloqueado por outra instância | Não começar downloads/geração; permitir nova tentativa | Mensagem/log |
| T15 | Reexecutar mesma semana e depois esvaziar dia | Substituir PNGs antigos e remover PNG de dia vazio | Comparação da pasta |
| T16 | Arquivo com imagem não relacionada à agenda | Preservar objeto não pertencente à agenda | Inspeção das imagens após salvar |
| T17 | Fórmulas normalizadas sem valor em cache | Não confundir fórmula presente com resultado calculado; diagnóstico claro | Cópia sintética do Excel |
| T18 | Semana cruzando o ano (ex. dezembro–janeiro) | Usar datas reais, sem interpretar ano corrente | Nomes e datas nos PNGs |
| T19 | Mesmo nome PNG em caminhos distintos por case-insensitive | Detectar ambiguidade, não escolher recurso arbitrariamente | Resultado do resolvedor de ícones |
| T20 | Limpeza após interrupção da geração | Excluir apenas temporários pertencentes à aplicação | Log e listagem de arquivos |

## Auditoria de layout e recursos

Foram encontrados **sete fundos** (todas as combinações não vazias de três categorias, com zero ou uma linha por categoria):

```
Base0Divul0Conf1Inv.png
Base0Divul1Conf0Inv.png
Base0Divul1Conf1Inv.png
Base1Divul0Conf0Inv.png
Base1Divul0Conf1Inv.png
Base1Divul1Conf0Inv.png
Base1Divul1Conf1Inv.png
```

Como cada bloco da planilha possui até cinco slots por categoria, uma categoria ocupa no máximo uma linha nesta estrutura. Caso a estrutura de entrada mude para comportar mais de cinco slots, o layout exigirá revisão específica.

Também estão presentes `VejaMaisDivulgacoes.png`, `VejaMaisConferencias.png`, `VejaMaisInvestorDay.png` e `Icones/MZ/icon-calendar@3x.png`.

## Cuidados para a comparação visual

- Preservar a planilha de exemplo e gerar testes somente em cópias.
- Guardar imagens de referência do script original antes de qualquer refatoração.
- Comparar resolução, fundo, posição das categorias, ícones, datas, fontes e textos.
- Não exigir igualdade binária de PNGs se metadados/encoder diferirem; comparar pixels e avaliar diferenças visuais relevantes.
- O script original completo e o MVP de ordenação ainda precisam ser confrontados com a especificação para confirmar todas as regras do layout.

## Pendências técnicas que não devem virar regra sem aprovação

1. Tratamento dos horários K/L quando ambos são horários válidos e divergentes.
2. Identificação confiável das imagens da agenda para remoção seletiva, especialmente se houver imagens externas com a mesma âncora.
3. Política para nomes de pasta sem ano quando duas semanas de anos diferentes tiverem as mesmas datas de início/fim.
4. Resolução de fontes e outros auxiliares usados pelo script de referência.
