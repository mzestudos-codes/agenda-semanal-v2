# Agenda Semanal — Aplicação integrada (Windows)

Aplicativo Python para validar/ordenar a planilha `Agenda`, compor imagens com o **mesmo layout do script original**, atualizar o próprio `.xlsx` e salvar os PNGs da semana. **Os ícones, fundos e fontes são consultados em um repositório GitHub público a cada execução e descartados após o uso.** Não requer login.

## O que está implementado

- Reutilização das regras do MVP de validação e ordenação (`main.py` original), incorporando divulgação com `J = "-"` em último lugar e marcadores na quinta posição.
- Visual preservado. A composição foi comparada **pixel a pixel** com as cinco saídas do `Agenda_Semanal_Old.py`, mantendo a ordem original exclusivamente no teste visual; todas tiveram diferença zero.
- Dias sem eventos não geram imagens. As imagens antigas da agenda desses dias são removidas do Excel.
- Validação de ausência de ícones/fundos antes da renderização, com indicação de arquivo e dia para ícones de empresas.
- Recursos obtidos do GitHub público **sem cache permanente**, somente os necessários, a partir de uma revisão fixada no começo da execução e conferidos com SHA-256.
- Inserção seletiva nas posições `P4`, `AB4`, `AN4`, `AZ4`, `BL4`, sem remover imagens de outras posições.
- Preservação das fórmulas **e dos seus resultados previamente calculados** após atualizar as imagens do Excel. O aplicativo não calcula fórmulas.
- PNGs ao lado do Excel, em `Agenda_Semanal_09Novembro_13Novembro`, com nomes `Agenda_09Novembro.png`, etc. Reexecuções atualizam/removem os PNGs antigos de agenda.
- Logs ao lado do Excel em `Logs/`, com retenção de 30 dias.
- Interface com dois botões, mensagem `Processando...`, sem pop-up de sucesso. Ao terminar, abre Excel e pasta.
- Salvamento com cópia temporária, substituição atômica por arquivo e tentativa de recuperação em caso de falha. Não é uma transação ACID entre vários arquivos.

## Passo 1 — Publicar recursos no GitHub

O ZIP `AgendaSemanal_Recursos_GitHub.zip` acompanha esta entrega e contém 434 recursos e `manifest.json`. **O repositório não é publicado automaticamente**; você precisa criar um repositório **público** na sua conta GitHub, por exemplo, `seu-usuario/agenda-assets`, e enviar o conteúdo extraído da pasta `repo_github` para a raiz dele.

A organização que deve aparecer no GitHub é:

```text
manifest.json
Icones/
Fundo/
Fonte/
```

**Não altere acentos nos nomes dos arquivos.** No projeto, os nomes foram recuperados da codificação CP850 do ZIP original (ex.: `Ânima.png`, `icon-Divulgações@3x.png`).

Na próxima atualização de PNG/TTF, rode `python tools_update_manifest.py /caminho/da/pasta/repo_github` **antes de enviar os arquivos ao GitHub**. O script recalcula os SHA-256. Sem atualizar o manifesto, o aplicativo bloqueará o uso de um arquivo alterado.

## Passo 2 — Configurar o endereço público

Edite `config.json`:

```json
{
  "github_repository": "seu-usuario/agenda-assets",
  "github_branch": "main"
}
```

É necessário usar o nome real do **repositório de recursos**, e não a URL completa. No executável, o arquivo `config.json` fica **ao lado de `AgendaSemanal.exe`**, e não dentro dele.

## Passo 3 — Executar e compilar no Windows

Requer Python 3.10+ (recomendado 3.12). Em um terminal na pasta do projeto:

```powershell
py -m pip install -r requirements.txt
py main.py
```

Para gerar o executável sem incluir os recursos visuais:

```bat
build_windows.bat
```

A saída será `dist/AgendaSemanal.exe` + `dist/config.json`. Distribua **esses dois arquivos juntos**. Não é necessário distribuir `repo_github/`, `Fonte/`, `Fundo/` ou `Icones/` com o EXE.

Alternativamente, envie o **código da aplicação** para um repositório GitHub próprio: o fluxo `.github/workflows/build-windows.yml` permite compilar um EXE no GitHub Actions usando um runner Windows e baixar o pacote `AgendaSemanal-Windows` na aba *Actions*. **Não publique a planilha de exemplo da pasta `tests/fixtures` em um repositório público sem revisá-la**.

## Interface

1. Abra o aplicativo.
2. Clique em **Selecionar Excel** e escolha um `.xlsx` que contenha a aba `Agenda`.
3. Clique em **Gerar agenda**. O botão exibirá `Processando...`.
4. Com internet disponível, o programa busca recursos e prepara as saídas.
5. Em caso de sucesso, abre o Excel atualizado e a pasta da semana. Não mostra mensagem de sucesso adicional.

**Feche o Excel antes de executar**, salve a planilha após qualquer edição para atualizar os resultados das fórmulas normalizadas. Em caso de erro, a mensagem explica o problema; detalhes ficam em `Logs/`.

## Testes

```powershell
py -m unittest discover -s tests -v
```

Os testes completos que dependem de recursos devem encontrar `repo_github/` na pasta do código. Testes com planilha real e comparação visual também requerem os arquivos de referência em `tests/fixtures/`. Os testes que não tiverem esses insumos são pulados automaticamente.

Para testar localmente **sem GitHub**, existe uma opção exclusiva de desenvolvimento:

```powershell
py main.py --excel "C:\planilhas\NomesSemanal.xlsx" --assets-dir "C:\repo_github" --no-open
```

O modo normal da interface **sempre consulta o GitHub**. A opção `--assets-dir` não é utilizada por quem recebe o executável.

## Estrutura

```text
app/validation.py       # MVP integrado: validação e ordenação
app/render.py           # Composição visual exata
app/assets.py           # GitHub, manifesto e downloads temporários
app/excel_write.py      # Inserção seletiva e preservação de caches das fórmulas
app/engine.py           # Fluxo, logs, transação aproximada e limpeza
app/gui.py              # Interface mínima
main.py                 # Entrada CLI/GUI
config.json             # Nome do repositório de recursos
build_windows.bat       # Compilação Windows
.github/workflows/      # Compilação opcional pelo GitHub Actions
repo_github/            # Recursos para publicar (não distribuídos com o EXE)
tests/                  # Testes de regras, integração e equivalência visual
docs/                   # Especificações e decisões
```

## Limitações conhecidas

- **GitHub:** você ainda precisa publicar os recursos em seu próprio repositório público e configurar `config.json`. Não há token nem autenticação.
- **Windows EXE:** o `.exe` deve ser compilado em Windows ou GitHub Actions Windows; o pacote entregue contém código-fonte e receita de compilação, não um executável Windows já testado.
- **Fórmulas:** é obrigatório que as colunas normalizadas tenham resultados calculados salvos no Excel. O programa conserva caches existentes, mas não recalcula dados desatualizados.
- **Planilhas complexas:** o openpyxl preserva imagens e formas suportadas, mas não garante preservação de todos os tipos de objeto Excel (controles ActiveX e outros recursos não suportados). Teste numa cópia antes de usar em planilhas com elementos além dos da amostra.
- **Âncoras:** `P4`, `AB4`, `AN4`, `AZ4`, `BL4` são posições reservadas às imagens da agenda. Não existe identificação segura de uma imagem alheia exatamente nessas âncoras.
- **Pasta sem ano:** o nome aprovado da pasta não contém ano; o aplicativo guarda um arquivo oculto `.agenda-year` e bloqueia reutilização quando detecta edição de outro ano.
- **Substituição de múltiplos arquivos:** os arquivos são preparados antes de publicação e possuem rollback de falhas comuns. Não é possível garantir uma transação entre Excel e todos os PNGs numa falha de energia.
- **Funcionamento offline:** não é suportado por decisão de produto. Sem internet, a geração não prossegue.
