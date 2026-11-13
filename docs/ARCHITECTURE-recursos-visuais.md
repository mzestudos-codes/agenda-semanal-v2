# Arquitetura — distribuição de recursos visuais

## Status

Decisões aprovadas durante o Discovery. Este documento registra a arquitetura acordada para distribuir ícones, fundos e fontes sem incluí-los no executável nem exigir manutenção manual nas máquinas dos usuários.

## 1. Objetivo

A aplicação deve gerar as imagens mantendo a identidade visual atual, mas consultar os recursos visuais em um repositório público online. Os recursos não devem permanecer armazenados permanentemente no computador do usuário.

## 2. Decisões confirmadas

- O repositório de recursos será público no GitHub.
- A aplicação não exigirá login ou autenticação.
- Ícones, fundos e fontes não serão empacotados dentro do executável.
- A aplicação precisará de conexão com a internet para gerar imagens.
- Os recursos serão baixados para uma área temporária durante a execução.
- Ao terminar a execução, os arquivos temporários serão excluídos.
- Se a aplicação for encerrada inesperadamente, resíduos de execuções anteriores serão removidos na próxima inicialização.
- A limpeza deverá atingir somente diretórios temporários identificados como pertencentes à aplicação.
- O visual atual das imagens deverá ser preservado. A mudança trata da distribuição e do carregamento dos recursos, não do design.

## 3. Fluxo esperado

1. Na inicialização, localizar e limpar diretórios temporários abandonados de execuções anteriores.
2. Ler e validar a agenda e determinar quais recursos serão necessários para os dias que serão gerados.
3. Consultar o manifesto público do repositório no GitHub.
4. Resolver os caminhos dos recursos necessários: ícones utilizados, fundo correspondente a cada composição, fontes e demais imagens auxiliares.
5. Baixar os arquivos necessários para um diretório temporário exclusivo daquela execução.
6. Validar a integridade dos arquivos baixados antes de utilizá-los.
7. Gerar as imagens localmente, usando os recursos temporários.
8. Fechar os arquivos e liberar referências em memória.
9. Excluir o diretório temporário da execução, inclusive em caso de erro, sempre que o processo conseguir executar a rotina de finalização.

## 4. Organização proposta do repositório

Nome sugerido: `agenda-assets`.

```text
agenda-assets/
├── README.md
├── manifest.json
├── icons/
│   ├── empresas/
│   └── especiais/
├── backgrounds/
│   └── Base...png
├── fonts/
│   └── ...
└── auxiliary/
    └── ...
```

A estrutura acima é uma proposta inicial. Os nomes e subdiretórios finais deverão refletir os nomes reais dos arquivos usados pelo script original, para evitar alterações desnecessárias na lógica de composição.

## 5. Manifesto de recursos

O `manifest.json` será o catálogo oficial dos recursos publicados. Para cada arquivo, deverá informar pelo menos:

- identificador lógico do recurso;
- caminho relativo ou URL de origem;
- tipo/categoria;
- hash SHA-256 esperado;
- versão ou revisão do conjunto de recursos.

Exemplo ilustrativo:

```json
{
  "schema_version": 1,
  "assets_version": "1.0.0",
  "assets": {
    "icon_empresa_exemplo": {
      "path": "icons/empresas/EmpresaExemplo.png",
      "sha256": "HASH_SHA256_DO_ARQUIVO",
      "type": "image/png"
    }
  }
}
```

O exemplo não representa nomes ou hashes reais. Os valores serão preenchidos quando os arquivos forem incorporados ao repositório.

## 6. Publicação e consistência das versões

Recomendação técnica: o manifesto publicado deve apontar para arquivos de uma revisão imutável (por exemplo, uma tag/release do GitHub), em vez de misturar arquivos que possam mudar enquanto uma geração está em andamento.

A aplicação deverá:
- consultar o manifesto uma vez por execução;
- usar a mesma revisão do conjunto de recursos durante toda aquela execução;
- verificar o SHA-256 de cada arquivo baixado;
- rejeitar arquivo ausente, incompleto ou com hash divergente;
- nunca utilizar silenciosamente um arquivo que falhou na validação.

Isso evita que uma atualização feita no GitHub durante a geração misture versões diferentes de ícones, fundos e fontes.

## 7. Download seletivo

A aplicação não precisa baixar todos os ícones do repositório em todas as execuções.

Depois de ler a agenda e determinar a composição de cada imagem, deverá baixar apenas:
- os ícones das empresas efetivamente presentes nas imagens;
- os marcadores especiais que forem utilizados;
- os fundos correspondentes às composições necessárias;
- as fontes e imagens auxiliares exigidas pelo layout.

Assim, o volume transferido fica limitado aos recursos realmente usados naquela execução.

## 8. Arquivos temporários e limpeza

- Criar um diretório temporário exclusivo por execução, com nome/prefixo reservado à aplicação.
- Não usar a pasta do executável nem a pasta da planilha como cache de recursos.
- Remover o diretório da execução em uma rotina de finalização (`finally` ou mecanismo equivalente).
- Na inicialização, identificar e remover somente diretórios temporários antigos que correspondam exatamente ao padrão da aplicação.
- Não apagar pastas genéricas do sistema nem arquivos escolhidos pelo usuário.
- Se a remoção falhar, registrar o erro no log sem apagar caminhos fora do escopo autorizado.

## 9. Falhas de rede e integridade

Como foi aprovado que a geração depende da internet, se o manifesto ou algum recurso necessário não puder ser obtido, a geração deverá ser interrompida com uma mensagem clara. Não haverá fallback offline nem cache permanente.

A aplicação deverá distinguir, no log e na mensagem apresentada:
- ausência de conexão;
- manifesto indisponível ou inválido;
- recurso não encontrado;
- falha no download;
- hash divergente;
- falha ao remover arquivos temporários.

## 10. Segurança e robustez

- Não incluir tokens, senhas ou credenciais do GitHub no executável.
- Aceitar somente URLs HTTPS de origem previamente definida/confiável.
- Validar caminhos do manifesto para impedir traversal (`../`) e gravação fora do diretório temporário.
- Definir limites razoáveis de tamanho e timeout para downloads.
- Baixar para arquivo temporário e validar o conteúdo antes de disponibilizá-lo à geração.
- Não sobrescrever nem modificar arquivos da planilha ou outros arquivos do usuário durante a limpeza.

## 11. Fora do escopo desta decisão

Ainda não estão definidos:
- o nome definitivo do repositório GitHub;
- a lista completa e os nomes finais dos recursos;
- o processo operacional para publicar uma nova versão dos recursos;
- o formato final do manifesto;
- a política de compatibilidade entre versões do executável e versões dos recursos;
- a pasta e a política de armazenamento das imagens geradas.

Esses pontos serão decididos após inventariar os arquivos reais e concluir o mapeamento do script original.

## 12. Critério de aceitação

A implementação estará alinhada a esta decisão quando:
- o executável puder ser distribuído sem ícones, fundos ou fontes;
- uma execução online conseguir obter os recursos públicos necessários;
- somente os recursos necessários forem baixados;
- a imagem gerada mantiver o visual atual;
- os arquivos temporários forem removidos ao final;
- resíduos de uma execução interrompida forem removidos na próxima inicialização;
- nenhuma credencial for exigida;
- falhas de rede ou integridade interromperem a geração com diagnóstico claro.
