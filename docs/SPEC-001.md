# SPEC-001 — Aplicação Agenda Semanal

**Status:** Discovery consolidado — versão 0.2  
**Data:** 13/11/2026  
**Escopo:** leitura e validação do Excel, ordenação de eventos, aquisição online de recursos visuais, geração de imagens, atualização da planilha, saídas e interface Windows.

> Este documento registra decisões confirmadas nas conversas do projeto e distingue explicitamente pontos ainda sujeitos à validação. Não é uma declaração de que a implementação já existe.

## 1. Objetivo

Evoluir o gerador de agendas semanais mantendo **o visual atual** das imagens e a lógica funcional válida do script original, incorporando o MVP de ordenação já desenvolvido, com distribuição de recursos visuais pelo GitHub público e operação simplificada para o usuário.

## 2. Fontes de referência e precedência

- **Script original `Agenda_Semanal_Old.py`:** referência para aparência e composição visual existente; deve ser estudado antes de alterar comportamentos.
- **MVP de ordenação (`main.py`):** evolução ainda não integrada; preservar regras confirmadas e validar sua equivalência com os dados reais.
- **Decisões de Discovery:** prevalecem quando alteram explicitamente o comportamento antigo (por exemplo, dias vazios, saída PNG, recursos online e logs).
- **Inventário de recursos:** `Recursos_Visuais.zip`, `inventario_recursos_visuais.csv` e `manifest_recursos_rascunho.json` são insumos para a implementação; o manifesto atual é preliminar.

## 3. Entrada e estrutura da planilha

**RN-001 — Seleção de arquivo.** A aplicação permitirá selecionar uma planilha `.xlsx` por meio de uma interface simples no Windows. Cancelar a seleção não iniciará processamento.

**RN-002 — Aba e blocos.** O MVP de ordenação utiliza a aba `Agenda`, com cinco blocos de dias:

| Dia | Linhas de eventos | Âncora da imagem |
|---|---|---|
| Segunda | 4–8 | `P4` |
| Terça | 12–16 | `AB4` |
| Quarta | 20–24 | `AN4` |
| Quinta | 28–32 | `AZ4` |
| Sexta | 36–40 | `BL4` |

O script original utiliza a aba ativa. **Integração pendente:** validar a aba de destino e o comportamento real com a planilha atual antes de implementar.

**RN-003 — Campos de entrada.** Nomes das empresas: divulgação `A`, conferências `C`, Investor Day `F`. Atributos normalizados, fonte de verdade para processamento: divulgação/período `J`; conferências/horários PT e EN `K` e `L`; Investor Day/modalidade e horário `M` e `N`. Não usar as colunas originais `B`, `D`, `E`, `G` e `H` para validar ou ordenar os atributos normalizados.

**RN-004 — Datas.** O script original lê datas e dias da semana nas células `I2/I3`, `I9/I10`, `I17/I18`, `I25/I26`, `I33/I34`. A interpretação exata dos tipos de célula e dos formatos deverá ser testada com uma planilha real.

## 4. Validações de negócio

**RN-005 — Período de divulgação.** Quando houver empresa real na coluna `A`, aceitar na coluna normalizada `J` os valores `Antes Abert.`, `Após Fech.` e `-`. O hífen é um valor explícito válido e deve ser preservado na imagem. Se `J` estiver realmente vazia (`None` ou string vazia), bloquear a geração e informar o problema. Outros valores não reconhecidos continuam sujeitos a erro de validação. Marcadores especiais são tratados separadamente.

**RN-006 — Duplicidade.** A mesma empresa não poderá aparecer duas vezes na mesma categoria e no mesmo dia; comparação case-insensitive. É permitido repetir entre categorias e dias distintos. Marcadores especiais não contam como empresas.

**RN-007 — Horários ausentes.** Conferências e Investor Day podem não possuir horário. `Trad. Simul.` e `Sem informação` equivalem a ausência de horário **para fins de ordenação**, preservando-se o texto original para exibição. Textos temporais desconhecidos devem provocar erro de interpretação, não serem ignorados silenciosamente.

**RN-008 — Ícones ausentes.** Antes de gerar qualquer imagem, identificar os ícones efetivamente necessários após a seleção/ordenação dos eventos. Se algum não existir no repositório, informar empresa e dia e bloquear toda a geração. Comparação dos nomes case-insensitive, sem aliases, preservando nomes distintos mesmo quando imagens são idênticas.

**RN-009 — Fundos ausentes.** Se faltar o fundo necessário a uma composição de imagem, informar a ausência e bloquear a geração. Não substituir silenciosamente por outro layout.

**RN-010 — Arquivo bloqueado.** Antes do processamento e dos downloads, verificar se a planilha pode ser lida e atualizada. Se estiver bloqueada, pedir que a pessoa feche o Excel e permitir nova tentativa, sem modificar o arquivo.

**RN-011 — Semana completamente vazia.** Fora do uso normal previsto. Como proteção, informar ausência de eventos e encerrar sem modificar a planilha.

## 5. Ordenação e marcadores

**RN-012 — Divulgação.** Ordenar por período na sequência `Antes Abert.` (prioridade 1), `Após Fech.` (prioridade 2), `-` (prioridade 3). Dentro de cada grupo, ordenar pelo nome da empresa alfabeticamente, com comparação case-insensitive. O período exibido deve manter o conteúdo normalizado da coluna `J`.

**RN-013 — Conferências.** Ordenar pelo horário mais cedo considerado entre as representações normalizadas `K` e `L`, com ausências ao final e desempate pelo nome da empresa. A regra de interpretação de dois horários diferentes no mesmo evento deverá ser testada e validada na integração.

**RN-014 — Investor Day.** Ordenar pelo horário normalizado `N`, mais cedo primeiro, ausências ao final e desempate pelo nome da empresa.

**RN-015 — Marcadores.** `VejaMaisDivulgacoes`, `VejaMaisConferencias` e `VejaMaisInvestorDay` são indicadores visuais de eventos adicionais, não empresas. Reconhecimento case-insensitive e remoção de espaços nas extremidades, sem correspondência aproximada. Quando presentes e necessários, ocupam a quinta posição; aparecem os quatro primeiros eventos após ordenação. Sem excedentes, cinco eventos reais podem ocupar cinco posições. Os atributos normalizados dos marcadores podem conter `-` e isso não é erro.

**RN-016 — Não alterar Excel na etapa de ordenação.** A ordenação ocorrerá em memória/estrutura intermediária; a ordem física das linhas da planilha não será modificada.

**RN-017 — Auditoria.** Registrar no log as reordenações com dia, categoria, empresa, posição original, nova posição e critério de ordenação. A estrutura JSON usada no MVP para conferência deverá ser preservada ou reconciliada na integração; sua persistência no produto final não está aprovada.

## 6. Composição visual

**RN-018 — Preservação visual.** Manter fundos, dimensões, ícones, fontes, cores, títulos, espaçamentos, alinhamentos, textos complementares e posicionamento de datas conforme o script original, salvo alteração expressamente aprovada.

**RN-019 — Fundos por composição.** O mecanismo atual seleciona fundos no padrão `Base{numDiv}Divul{numConf}Conf{numInv}Inv.png`. O inventário identificou sete fundos; não presumir suporte a combinações além das efetivamente disponíveis sem conferir os arquivos e o código.

**RN-020 — Dia sem eventos.** Dia vazio é válido; não exige ponto, hífen ou outro caractere artificial. Não gerar PNG para esse dia. Continuar gerando os demais dias normalmente.

**RN-021 — Associação de dados.** Preservar o vínculo entre cada empresa e seus atributos ao filtrar e ordenar; evitar remover `None` separadamente de listas paralelas.

## 7. Recursos visuais online

**RN-022 — Repositório público.** Ícones, fundos, fontes e recursos auxiliares serão disponibilizados em repositório público no GitHub. A aplicação não exigirá login nem conterá credenciais embutidas.

**RN-023 — Sem distribuição de assets.** O executável não conterá os recursos visuais nem dependerá de pasta permanente de ícones, fundos ou fontes junto ao programa.

**RN-024 — Download sob demanda.** A cada execução, consultar o manifesto do GitHub e baixar **somente os recursos necessários** à geração daquela agenda. A internet é obrigatória; não haverá cache permanente ou funcionamento offline.

**RN-025 — Atualização automática.** Recursos publicados/alterados no GitHub deverão ser utilizados automaticamente na próxima execução, sem solicitação de autorização para atualização. Recomenda-se fixar uma revisão consistente do manifesto durante toda a execução e validar hashes SHA-256.

**RN-026 — Armazenamento temporário.** Os arquivos baixados serão utilizados em diretório temporário exclusivo da execução, excluído ao finalizar, inclusive em caso de erro quando possível. Na inicialização, limpar resíduos abandonados de execuções anteriores **somente** quando inequivocamente pertencentes à aplicação. Não apagar outros arquivos temporários do sistema.

**RN-027 — Falhas online.** Se faltar conexão, manifesto, recurso ou houver falha de integridade, bloquear a geração com diagnóstico claro. Não utilizar versões locais antigas como fallback.

**RN-028 — Resolução de ícones.** O nome na planilha corresponde ao nome do PNG; comparação case-insensitive, sem aliases. Os nomes existentes serão preservados no repositório.

## 8. Saída e atualização do Excel

**RN-029 — Atualização in-place.** Atualizar diretamente o Excel selecionado, sem gerar uma cópia permanente. Usar estratégia de gravação temporária e substituição segura para reduzir risco de corrupção. Preservar fórmulas e conteúdo da planilha.

**RN-030 — Substituição de imagens.** Substituir automaticamente as imagens anteriores da agenda nos dias com eventos; remover imagens antigas da agenda nos dias vazios. **Não remover imagens que não pertençam à agenda.** As âncoras originais constam em RN-002. Identificação seletiva de imagens existentes exige validação técnica; o script antigo removia todas as imagens da aba.

**RN-031 — Pasta de saída.** Criar a pasta da semana no **mesmo diretório do Excel selecionado**, no formato:

`Agenda_Semanal_09Novembro_13Novembro`

**RN-032 — Nomes dos PNGs.** Salvar imagens de dias com eventos como `Agenda_09Novembro.png`, `Agenda_10Novembro.png` etc., conforme as datas efetivas da planilha. Não criar PNG para dias vazios.

**RN-033 — Reexecução.** Reutilizar a pasta da mesma semana, substituir os PNGs anteriores da agenda e excluir PNGs antigos correspondentes a dias agora vazios. Não apagar arquivos alheios à aplicação.

**RN-034 — Abertura automática.** Ao concluir com sucesso, abrir o Excel atualizado e a pasta de imagens no Explorador de Arquivos. Não mostrar pop-up adicional de sucesso.

## 9. Interface e experiência

**RN-035 — Interface mínima.** Janela Windows com seleção do Excel e botão `Gerar agenda`. Não incluir barra de progresso. Durante a execução, exibir `Processando...`, desabilitar o botão e manter a interface responsiva.

**RN-036 — Erros.** Mostrar mensagem compreensível em falhas de validação, rede, recursos ou gravação, com detalhes técnicos no log. Não abrir Excel/pasta como se a geração tivesse sido concluída com sucesso.

## 10. Logs

**RN-037 — Localização.** Criar automaticamente a pasta `Logs` no **mesmo diretório do Excel selecionado**. Esta decisão substitui a proposta anterior de `%LOCALAPPDATA%\AgendaSemanal\logs`.

**RN-038 — Conteúdo.** Registrar validações, ordenação e mudanças de posição, consulta/download de recursos, geração de imagens, gravação do Excel, abertura dos resultados e falhas.

**RN-039 — Retenção.** Manter logs dos últimos **30 dias**. Ao iniciar, remover apenas arquivos antigos inequivocamente pertencentes aos logs da aplicação; preservar outros arquivos presentes na pasta.

## 11. Fluxo operacional consolidado

1. Selecionar Excel.
2. Validar existência/acesso ao arquivo, estrutura da planilha e possibilidade de gravação.
3. Ler, validar e ordenar eventos em memória.
4. Se a semana estiver vazia, informar e encerrar sem alterar o Excel.
5. Determinar os dias com eventos, a composição visual e os recursos necessários.
6. Consultar manifesto público, verificar presença dos ícones/fundos e baixar recursos temporários; validar integridade.
7. Gerar PNGs somente para dias com eventos, mantendo o visual atual.
8. Atualizar seletivamente imagens da agenda no Excel, inclusive removendo as dos dias vazios; salvar com proteção contra falhas.
9. Criar/atualizar pasta da semana com PNGs e remover saídas antigas da agenda que não correspondam mais aos dias gerados.
10. Limpar recursos temporários; registrar operações e erros no log.
11. Em caso de sucesso, abrir Excel e pasta da semana, sem mensagem adicional.

**Nota de implementação:** para minimizar inconsistência entre Excel e PNGs em caso de erro, preparar as saídas antes de substituir os arquivos definitivos. Definir estratégia de commit/rollback durante o desenho técnico.

## 12. Pontos pendentes antes de implementar

1. **Planilha real:** a aba `Agenda`, datas numéricas no formato serial Excel, fórmulas normalizadas e cinco imagens nas âncoras esperadas foram confirmadas na amostra de 17–21/11/2025. Ainda falta testar preservação de objetos não relacionados à agenda e valores calculados ausentes/desatualizados em fórmulas.
2. **Script original completo:** verificar todos os casos de layout, posicionamento e caminhos de ícones auxiliares; comparar saídas antigas e novas com casos de teste.
3. **Marcadores:** confirmar como valores de entrada como `Veja+` no script antigo se relacionam com os nomes `VejaMais...` na planilha atual, sem reabrir regras já aprovadas.
4. **Conferências:** confirmar com exemplos reais a interpretação de `K` e `L` quando horários divergirem.
5. **GitHub:** definir nome/URL do repositório, formato final do manifesto, publicação de revisões e compatibilidade com versões do executável.
6. **Recursos:** identificar fontes e arquivos auxiliares efetivamente utilizados, inventariar os nomes dos sete fundos e conferir a resolução case-insensitive em ambientes com nomes de arquivos conflitantes.
7. **Datas e nomes:** definir tratamento de mudança de ano e colisões de nomes para semanas com mesmos dias e meses em anos diferentes (o formato aprovado não inclui ano).
8. **Segurança da gravação:** validar substituição seletiva de imagens em `openpyxl`, comportamento com Excel aberto e estratégia de recuperação em falhas.
9. **Logs:** decidir convenção final de nomes e rotação para múltiplas execuções no mesmo dia.
10. **Testes:** estabelecer casos de regressão para dias vazios, semana vazia, duplicidades, ícones/fundos ausentes, ordenação, marcadores, reexecução e falhas de rede.

## 13. Critérios mínimos de aceite

- [ ] Executável opera sem assets empacotados e sem login.
- [ ] Recursos públicos necessários são obtidos online e descartados após uso.
- [ ] Imagens geradas são visualmente equivalentes às atuais para os casos existentes.
- [ ] Divulgação com `J = "-"` é aceita e ordenada depois de `Antes Abert.` e `Após Fech.`; divulgação com `J` verdadeiramente vazia é rejeitada.
- [ ] Ordenação validada e auditável; planilha não tem suas linhas reordenadas.
- [ ] Dias vazios não exigem caracteres fictícios nem geram PNG.
- [ ] Imagens antigas da agenda são substituídas/removidas seletivamente, sem afetar outras imagens.
- [ ] Excel é atualizado de forma segura e aberto após sucesso.
- [ ] Pasta semanal ao lado do Excel contém somente PNGs atuais da agenda.
- [ ] Pasta `Logs` ao lado do Excel contém registros, com retenção de 30 dias.
- [ ] Interface permanece simples e responsiva, com mensagens apenas quando necessário.
