# Gerenciador de Ícones — autenticação GitHub

## Configuração

1. Na OAuth App do GitHub, habilite **Device Flow**. O Client ID está no `config.json`; **não** crie Client Secret.
2. Execute `build_windows.bat` em um computador Windows com Python instalado.
3. Distribua `dist/AgendaSemanal.exe` e `dist/config.json` juntos.
4. No executável, use **Gerenciar ícones → Conectar ao GitHub**. O código é copiado para a área de transferência e a página de autorização abre no navegador.
5. Autorize a conta com acesso de escrita ao repositório. O token será armazenado pelo `keyring` no armazenamento de credenciais do Windows do usuário local.
6. Selecione adicionar ou substituir, informe a empresa, escolha um PNG de **119 × 50 pixels** e clique em **Publicar ícone**.

## Segurança e limitações

- O token **não** está embutido no executável. Cada computador realiza sua própria autorização.
- O escopo OAuth `repo` pode conceder acesso amplo aos repositórios dessa conta, não apenas a `agenda-assets/Icones`. Prefira contas separadas e acesso mínimo quando possível.
- Como a equipe usa a mesma conta, o histórico do GitHub não identifica individualmente a pessoa que publicou.
- O programa limita suas próprias operações aos ícones e ao manifesto, mas isso **não** é uma restrição imposta ao token pelo GitHub.
- As operações de escrita usam Git Data API para criar um único commit com o PNG e o manifesto. Atualizações simultâneas são detectadas pela atualização não forçada da referência e tentadas novamente.
- O manifesto é consultado na mesma revisão do commit pai para evitar inconsistência por concorrência.
- Para revogar uma autorização, acesse **GitHub → Settings → Applications → Authorized OAuth Apps**. Remova também a credencial local no Gerenciador de Credenciais do Windows.
- A geração da agenda não usa token e permanece disponível sem autenticação.

## Testes

`python -m unittest discover -s tests -v`

**Importante:** os testes automatizados não fazem publicação real no GitHub. Valide manualmente em uma cópia de teste do repositório antes de usar a publicação em produção.
