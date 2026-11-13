# AgendaMercado — código-fonte Python

Aplicação desktop Windows para gerar **Agenda Semanal**, **Agenda Diária** ou **Ambas**, preservando os layouts das agendas e o gerenciador de ícones GitHub.

## Executar

```shell
py -m pip install -r requirements.txt
py main.py
```

A planilha `.xlsx` deve possuir as abas **Semanal** e **Diária** para executar ambas as modalidades. Para executar somente uma modalidade, basta a aba correspondente. A estrutura exige a nova coluna I (veja a seção MZ Arena). A Diária usa `J2` como data, `J3` como dia da semana calculado, e os eventos a partir da linha 3; a Semanal segue sua estrutura histórica, começando na linha 4.

No Windows, executar `build_windows.bat` para compilar `dist/AgendaMercado.exe` e copiar `config.json`. **O executável não acompanha este ZIP**; a compilação precisa ocorrer em Windows.

## Arquivos gerados

```text
Imagens/
  Semanal/Agenda_Semanal_16-Novembro-2026.png
  Diaria/Agenda_Diaria_13-Novembro-2026.png
Logs/
```

O arquivo original Excel é atualizado somente depois de pré-validação, download dos ícones e renderização. Somente as imagens da aba escolhida são substituídas. Os PNGs históricos não são apagados; um arquivo da mesma data é substituído. Uma falha comum de publicação tenta restaurar Excel e imagens anteriores.

## GitHub

Preservados os campos `github_repository`, `github_branch`, `github_assets_subdir` e `github_oauth_client_id` de `config.json`. Os recursos visuais são baixados em tempo de execução do manifesto GitHub, sem distribuição de fontes ou ícones neste pacote.

## Linha de comando

```shell
py main.py --excel "C:\\Agenda\\Nomes.xlsx" --mode ambas --no-open
```

O argumento `--assets-dir` existe exclusivamente para testes locais.

## Testes

```shell
py -m unittest discover -s tests -v
```

Os testes de integração/visual existentes dependem de recursos ou arquivos de referência fora deste pacote e podem ficar marcados como `skipped`. Os testes unitários da Agenda Diária não dependem desses recursos.

## Notas de validação

O renderizador diário foi reimplementado a partir do `diaria.py` antigo, com os posicionamentos, espaçamentos, cinco colunas e fontes de origem. Ainda é necessário comparar PNGs da versão antiga e da nova com dados equivalentes para comprovar identidade visual pixel a pixel. A interface utiliza `ttk` em tema claro, mantendo autenticação OAuth e ações de gerenciamento de ícones. Este código-fonte não foi compilado como EXE neste ambiente.

## Ajustes de organização e mensagens (13/11/2026)

- PNGs semanais são salvos em `Imagens/Semanal/Agenda Semanal de DD-Mês-AAAA até DD-Mês-AAAA/`, considerando as datas de segunda a sexta da aba `Semanal` (inclusive quando a semana atravessa o ano).
- PNG diário é salvo em `Imagens/Diaria/Agenda Diária de DD-Mês-AAAA/`.
- Os nomes dos PNGs permanecem inalterados; imagens anteriores de outros períodos são preservadas.
- A geração bem-sucedida não abre mais uma caixa de confirmação; o status da interface é atualizado e Excel/Explorador continuam abrindo.
- Em erros de validação do Excel, a caixa informa que, após OK, o Excel será aberto para conferência/correção. Erros de ícones mantêm o fluxo próprio do gerenciador.

**Para atualizar:** extraia este pacote numa pasta de teste, execute `python main.py` para validar e, depois, `build_windows.bat` para incorporar as mudanças ao executável. Faça backup da versão anterior.

## MZ Arena — atualização de 13/11/2026

**IMPORTANTE: antes de executar esta versão, insira manualmente uma coluna I nas duas abas `Semanal` e `Diária` de uma CÓPIA do Excel.** No Excel, selecione a coluna I inteira e use Inserir coluna. Isso desloca todas as colunas antigas de I em diante. Não basta digitar `Sim` na coluna I antiga: ela contém datas. Faça backup e confira as fórmulas depois da inserção. A aplicação **não altera a estrutura da planilha automaticamente**.

- Na nova coluna **I**, para as linhas com Investor Day, escreva `Sim` (sem distinção de maiúsculas/minúsculas) para exibir o selo, ou deixe vazio para não exibir. Outros valores são rejeitados para evitar enganos.
- Datas: `Semanal!J2,J9,J17,J25,J33`; `Diária!J2` e dia da semana `Diária!J3`.
- Período normalizado: **K**; horários de conferências: **L/M**; modalidade e horário do Investor Day: **N/O**.
- Imagens inseridas no Excel: `Semanal!Q4,AC4,AO4,BA4,BM4`; `Diária!Q3`. A substituição também limpa imagens antigas nas âncoras anteriores para evitar duplicações.
- PNG das agendas mantém dimensões originais; selo **50 × 7 pixels** centralizado sob o horário de cada Investor Day marcado.

### Publicar o recurso no GitHub (uma vez)

O PNG real da MZ Arena **não foi fornecido**, portanto não acompanha o ZIP. É necessário publicar o arquivo PNG oficial de 50 × 7 pixels em `agenda-assets/Icones/MZ/MZArena.png` no repositório de recursos configurado e adicionar a entrada `Icones/MZ/MZArena.png` ao `agenda-assets/manifest.json`, com `sha256` calculado a partir dos bytes exatos do arquivo e `type: image/png`. Por exemplo, calcule o SHA-256 com `python -c "import hashlib; print(hashlib.sha256(open('MZArena.png','rb').read()).hexdigest())"`.

O gerenciador de ícones de **empresas** existente aceita apenas 119 × 50 pixels e não deve ser usado para esse selo especial. Até o selo ser publicado e incluído no manifesto, a geração com `Sim` é bloqueada com uma mensagem de recurso ausente, antes de modificar o Excel. Uma vez publicado, as três modalidades usam o mesmo recurso online automaticamente, sem recompilar.

### Compilação

Teste com `python main.py` antes de recompilar. Para gerar o EXE atualizado no Windows, execute `build_windows.bat` e abra o novo `dist/AgendaMercado.exe`.
