# Revisão de código — 16/11/2026

## Resultado e escopo

A revisão examinou o código próprio do diretório: núcleo `source/antares_fd`,
meteorologia `MAGI`, entradas de `projects`, testes, instalação e CI. A árvore
Git estava sem alterações locais no início. Dependências em `.venv`, dados
brutos e resultados científicos não foram tratados como código descartável.

A versão final contém **108 módulos de execução/ferramentas e 466 definições de
funções e métodos**, incluindo funções locais. Todas essas definições possuem
docstring e entrada na [referência funcional](referencia_funcoes/README.md).
Os testes têm revisão sintática/estática e execução própria; não são parte da
referência de API. Não havia notebooks `.ipynb` na árvore examinada.

Foram combinados inventário de arquivos, inspeção de fluxos e referências,
análise sintática AST, Ruff, Vulture e testes de regressão. Uma ausência de
referência textual não foi usada isoladamente para excluir interfaces públicas:
Python permite importação dinâmica, instrumentação e uso externo ao repositório.

## Correções de comportamento

| Área | Defeito anterior | Comportamento após a revisão |
| --- | --- | --- |
| Atmosfera | Listas numéricas podiam falhar em comparações; escalares e matrizes não tinham contrato de forma; arrays externos podiam invalidar o perfil após a validação. | Vetores são convertidos para cópias NumPy 1D em float, validados e marcados somente para leitura. Erros de forma/conversão geram `ConfigurationError`. Umidade segue o mesmo armazenamento. |
| Elipse de dispersão | Entradas 2D e não finitas chegavam à covariância; arredondamento podia gerar raiz de autovalor ligeiramente negativo. | Exige vetores 1D finitos e pareados; rejeita covariância indefinida e anula somente negativos dentro da tolerância numérica declarada. A hipótese normal bivariada permanece explícita. |
| Recuperação | CdS, frequência, atraso, altitude e ruído podiam receber parâmetros não físicos. Um segundo dispositivo inválido podia deixar o primeiro instalado. | Valida finitude, CdS/frequência positivos, atraso/altitude não negativos, desvio não negativo e correlação em [-1,1]. Primeiro prepara todos os dispositivos; depois os adiciona ao foguete. |
| Requisitos | `NaN`/infinito podiam produzir resultados sem validade; havia variável de tolerância sem uso e ramo marginal inalcançável. | Valores/limites não finitos e intervalos inválidos ficam `NOT EVALUATED`, com margem `None`. Margem negativa continua reprovada; nenhuma tolerância transforma violação em aprovação. |
| MELCHIOR | A ausência de histórico gerava uma climatologia aleatória automaticamente, posteriormente rotulada como histórica. | Retorna esquema vazio e informa indisponibilidade. O gerador privado foi removido. CSVs antigos são `offline_profile` com `PROVENANCE_UNVERIFIED`; sua origem observacional não é presumida. |
| Tabelas PDF | Linhas curtas eram preenchidas para renderização, mas o cálculo de largura ainda acessava a matriz irregular original. | Dimensiona sobre linhas preenchidas antes da conversão em células ReportLab. |
| Tipos | `Any` era usado sem importação em métricas e no executor Monte Carlo. | As anotações podem ser resolvidas; o Ruff não encontra nomes indefinidos. |
| Telemetria GPS | A leitura do registro anterior dependia de estado indireto do laço e era marcada como nome não definido. | O fim de cada intervalo aponta explicitamente para o último registro válido acumulado. |
| Entradas de projeto | Andorinha usava `Source`, inexistente em sistemas sensíveis a maiúsculas. Entradas Monte Carlo do template/Andorinha não preparavam seus imports locais. | Usa `source`; os dois wrappers Monte Carlo incluem raiz e diretório fonte no caminho de importação. |
| METAR/TAF | A sondagem de conectividade não fechava a conexão criada. | A conexão é encerrada por gerenciador de contexto. |
| Relatórios instalados | O YAML de requisitos era procurado a partir da estrutura presumida do projeto consumidor e não era declarado como dado de pacote. | O arquivo é resolvido junto ao módulo; `package_data`/`MANIFEST.in` incluem o YAML no pacote. |
| Instalação | Dependências de execução não estavam declaradas nos metadados do pacote. | `setup.py` declara requisitos, extras `dev`/`notebook` e Python >=3.12; `pyproject.toml` declara o backend de build. |
| `setup.sh` | Podia continuar após erros e dependia do diretório de execução. | Ativa `set -euo pipefail`, resolve a própria raiz e apresenta exemplo com caminho atual. |
| CI | `setup.sh` instalava em `.venv`, mas etapas seguintes chamavam ferramentas do Python global. O MAGI não era testado e upload-artifact v3 estava descontinuado. | A instalação e os testes usam o mesmo `python -m`; inclui MAGI, Ruff, verificação da referência e upload-artifact v4. Não usa cache meteorológico como pré-condição dos testes. |

Também foram removidos imports, variáveis e expressões sem uso, uma chave
repetida em rótulos GPS e capturas `except:` sem tipo. Os blocos de tratamento
foram limitados quando o erro esperado estava identificado. Tratamentos amplos
que limpam recursos e relançam falhas foram preservados.

A instrumentação por nome de módulo foi verificada com os testes. A exportação
`monte_carlo_failure.MonteCarlo`, utilizada por `unittest.mock.patch`, foi
preservada explicitamente com alias homônimo; não é um import descartável.

## Arquivos e rotinas removidos

As exclusões de arquivos versionados são **17**. Podem ser recuperadas do
histórico Git; nenhum dado físico foi usado como substituto para código removido.

| Arquivo/grupo | Evidência e motivo |
| --- | --- |
| `fix.py`, `patch.py` | Scripts de substituição textual, em UTF-16, fora dos fluxos de execução. Reaplicavam correções sobre versões antigas do código. |
| `patch_builder.py`, `patch_builder_all.py`, `patch_builder_all2.py`, `patch_builder_fix.py`, `patch_builder_rep.py` | Variações de alteração automática do mesmo relatório, sem chamadas nos fluxos atuais. Algumas podiam inserir blocos em posições incompatíveis. |
| `patch_mc.py`, `patch_reqs.py`, `patch_tables.py` | Injetores pontuais de funcionalidades já presentes nas implementações atuais; não são ferramentas canônicas de migração. |
| `source/antares_fd/simulation/results.py.patch` | Diff antigo não aplicado por nenhum comando de instalação, CI ou execução. |
| `nose_help.txt`, `rocket_help2.txt`, `rocket_init.txt` | Capturas estáticas de ajuda/introspecção RocketPy, sem consumo no software. A versão instalada fornece sua própria API. |
| `projects/{00_Copy_This,andorinha,neblina_1}/simulations/separation_at_main_opening.py` | Três exemplos legados já excluídos do controlador de campanhas. Subtraíam 2 kg presumidos antes do voo inteiro, sem representar evento de separação. Foram removidos sem inventar massa substituta nem introduzir um modelo físico novo. |

Foram removidos ainda cinco métodos privados sem função operacional: quatro
stubs `_fetch_inmet_surface`, `_fetch_goes_satellite`, `_fetch_radiosonde_data`
e `_fetch_previous_model_runs` de BALTHASAR, que apenas lançavam
`NotImplementedError`, e o gerador de histórico presumido de MELCHIOR. As buscas
não localizaram chamadas atuais desses quatro stubs; menções em Markdown são
snapshots históricos, não uma integração implementada.

A cópia gerada em `build/` foi eliminada; a validação de empacotamento a recria
temporariamente, e ela é removida ao final. Não foram apagados históricos de
experimento, motores, tabelas aerodinâmicas, logs brutos, resultados ou imagens
científicas. `.venv` e metadados da instalação local foram preservados.

## Interfaces mantidas deliberadamente

- Os dois executores Monte Carlo continuam usados por entradas distintas.
- `balistic.py` continua como nome de compatibilidade dos projetos; o cenário
  interno permanece `ballistic`.
- `MAGI/build_notebook.py` é ferramenta opcional documentada e permanece disponível.
- A API antiga `dataframes_to_rocketpy_dataset` continua sinalizando depreciação
  por exceção; sua docstring agora descreve esse comportamento real.
- Módulos gráficos e de relatórios com interfaces diferentes não foram removidos
  por semelhança de nomes. Há consumidores, testes e superfícies públicas.
- Reexportações em `__init__.py` e `uq_storage.py` foram tornadas explícitas com
  `__all__`, em vez de apagadas como se fossem imports internos sem uso.

## Documentação de funções

A revisão acrescentou contratos em português às funções antes sem docstring.
Foram mantidas descrições existentes que já explicavam fórmulas ou mecanismos.
Cada entrada da referência inclui:

1. Nome qualificado, assinatura e link para a implementação.
2. Objetivo, mecanismo, unidades e efeitos descritos na docstring.
3. Parâmetros e tipos que o código efetivamente declara; tipo ausente é indicado.
4. Expressões locais de retorno/yield e exceções explícitas.
5. Colaboradores chamados diretamente.

A parte extraída por AST é determinística e não executa os módulos. Não tenta
inventar tipos, provar pureza, resolver chamadas dinâmicas ou enumerar todas as
exceções transitivas de bibliotecas. Funções locais têm entradas separadas.
O modo `--check` impede divergência entre o código e a referência versionada.

```bash
.venv/bin/python scripts/generate_function_reference.py
.venv/bin/python scripts/generate_function_reference.py --check
```

## Aplicação das diretrizes NASA/JPL

Referência primária: Gerard J. Holzmann, NASA/JPL,
[The Power of Ten — Rules for Developing Safety Critical Code](https://spinroot.com/gerard/pdf/P10.pdf).
As regras foram propostas principalmente para C. Nesta aplicação científica
Python, são uma orientação de verificabilidade; a revisão não constitui
certificação NASA, garantia de tempo real ou conformidade integral com as dez regras.

A adaptação priorizou entradas verificadas antes dos cálculos, erros explícitos,
estado local, fechamento de recursos, armazenamento limitado de trajetórias,
proveniência e análise estática. As validações de entrada usam exceções em vez
de depender de `assert`, pois Python pode remover assertions com `-O`.

| Princípio | Aplicação e limite observado |
| --- | --- |
| Fluxo simples e analisável | Remove ramos mortos e scripts de modificação ad hoc. Ainda há conversores recursivos de árvores e despachos dinâmicos usados pela aplicação. |
| Laços com limites | Amostragem e retenção têm limites próprios; o inventário registra todos os `while`. A colisão de nomes de campanha ainda usa tentativas sem teto explícito. Não se afirma uma prova global de terminação. |
| Memória previsível | Vetores de perfil possuem cópia própria; a retenção limitada de trajetórias existente foi preservada e testada. NumPy, pandas e Python continuam alocando dinamicamente. |
| Funções pequenas | Novos auxiliares são focados; funções grandes existentes estão inventariadas. Não foi aplicada divisão mecânica de integradores/relatórios sem avaliação funcional específica. |
| Pré/pós-condições verificáveis | Reforça forma, finitude, intervalos físicos e vínculo de IDs. Asserções artificiais por quantidade não foram inseridas. |
| Escopo mínimo | Remove nomes sem uso e preserva estado de execução por instância. Aplicativos de uso interativo ainda contêm processamento no nível de módulo. |
| Verificação de parâmetros e resultados | Regressões exercitam entradas inválidas, saídas de integração, erro de worker, hashes e artefatos. A revisão não prova todos os caminhos de bibliotecas externas. |
| Evitar mecanismos opacos | Remove os scripts que reescreviam fontes por regex. Adaptações locais do RocketPy continuam explícitas e testadas; não há preprocessor C. |
| Reduzir indireção | Não há ponteiros C geridos pelo projeto; callbacks e interfaces dinâmicas Python continuam necessários. Não existe equivalência literal com a regra C. |
| Análise estática contínua | Configura Ruff e execução em CI, com zero ocorrências nas regras `F`, `E9`, `E722`, `W605`. Vulture foi aplicado como diagnóstico adicional. |

O [inventário estruturado](INVENTARIO_REVISAO_CODIGO.json) registra **60 funções
com mais de 60 linhas físicas sem a docstring externa**, **68 tratamentos
`except Exception`**, **7 candidatos de recursão direta** e **7 laços `while`**.
Essas são contagens sintáticas, não uma classificação automática de defeitos:
limpeza com relançamento de exceção, por exemplo, pode justificar captura ampla.
Linhas contadas incluem comentários, espaços e funções locais. Os candidatos de
recursão não abrangem ciclos indiretos por imports ou callbacks.

## Verificação realizada

Ambiente: Python 3.14 configurado pelo PyCharm, executável `.venv/bin/python`.
Os testes foram executados com Matplotlib em modo `Agg`.

| Verificação | Resultado |
| --- | --- |
| Suíte inicial antes das alterações | 209 aprovados, 4 subtestes aprovados, 2 falhas de infraestrutura: API externa e sockets locais bloqueados. |
| Suíte completa após as correções | **235 testes aprovados, 4 subtestes aprovados**, 47 avisos, em 70,25 s. Inclui integração Monte Carlo paralela. |
| Seleção de campanhas e novas regressões após remover os três exemplos legados | **28 testes aprovados**. Os exemplos já eram excluídos da seleção; nenhum fluxo canônico foi retirado. |
| Ruff em source, MAGI, projects, scripts, tests e setup.py | **Zero ocorrências** nas regras configuradas; havia 137 ocorrências na primeira análise. |
| Vulture com confiança mínima de 90% | **Zero ocorrências** após a limpeza. Não prova ausência de código morto nem substitui o exame de APIs. |
| Compilação de source, MAGI, projects, scripts e tests | Aprovada com `compileall`. Os antigos patches UTF-16 foram removidos. |
| Referência funcional | Gerada; `--check` compara o conteúdo completo sem gravar. |
| Build wheel isolado | Aprovado. |
| Instalação do wheel em diretório temporário | Imports de `antares_fd`, `MAGI` e `magi` aprovados; YAML de requisitos presente e carregável. |
| `git diff --check` e `bash -n setup.sh` | Verificação de espaços/conflitos e sintaxe shell realizada no fechamento. |

O teste de previsão meteorológica usa uma resposta HTTP determinística, com
unidades, horários e níveis de pressão explícitos, e verifica a gravação do
cache em diretório temporário. Não depende de previsão atual nem da conectividade.
O teste de climatologia ausente confirma que nenhum CSV presumido é gerado.

Os testes novos cobrem também forma e propriedade dos vetores, números não
finitos, nuvem colinear, requisitos sem evidência válida, margem negativa,
tabelas irregulares, resolução de anotações e rejeição de recuperação antes de
modificar o foguete. Não se alteraram dados de voo para fazer testes passarem.

Os avisos restantes são majoritariamente das dependências RocketPy/xarray/NumPy,
uso de `fork` multithread e uma fixture propositalmente simples com margem
estática negativa. Foram mantidos visíveis. A suíte não foi repetida localmente
em Python 3.12; a CI está configurada para essa versão. A execução remota da CI
não faz parte desta verificação local.

## Limites e pontos para evolução

Uma varredura sintática e uma suíte aprovada não demonstram ausência de todos
os defeitos ou validade física de todos os modelos. Esta revisão não executou
campanhas longas, benchmark completo, inspeção visual de todos os relatórios
históricos nem revisão de segurança das dependências. Nenhuma autorização de
lançamento decorre dos resultados de testes.

As prioridades de evolução são reduzir as funções extensas com regressões
numéricas específicas, justificar individualmente capturas amplas e ampliar
anotações de tipo nas APIs ainda sem contrato estático completo. O inventário
fornece caminhos e posições para esse trabalho. A aplicação interativa MAGI e
o gerador opcional de notebook ainda têm execução no nível de módulo; devem
ser utilizados conforme seus pontos de entrada documentados.

## Autoavaliação da entrega

Foi aplicado o roteiro `ecc:agent-self-evaluation` para conferir precisão,
cobertura, clareza, uso e concisão antes da entrega.

| Critério | Nota / 5 | Evidência e melhoria identificada |
| --- | ---: | --- |
| Precisão | 4 | Testes, Ruff, Vulture e wheel verificados; não há prova formal nem regressão de todos os modelos físicos. Evoluir com casos numéricos independentes. |
| Cobertura | 4 | 466 definições documentadas e código próprio varrido; regras NASA/JPL não são integralmente satisfeitas. Priorizar funções extensas listadas no inventário. |
| Clareza | 4 | Referência navegável e contratos locais; docstrings anteriores em inglês foram preservadas e ainda há parâmetros não anotados. Uniformizar gradualmente a terminologia e os tipos. |
| Uso imediato | 5 | Mudanças locais revisáveis, ferramentas reproduzíveis e verificações de CI configuradas; não exige ação manual para completar as correções descritas. |
| Concisão | 4 | Relatório separa decisões e evidências da referência extensa; a extração de expressões gera volume alto. Uma interface de busca pode melhorar consulta sem retirar detalhe. |

Média: **4,2/5**. Não há critério <= 2. Veredito: entrega revisável com os limites
acima explícitos. A avaliação deve ser confrontada com os arquivos e testes,
não tomada como garantia de qualidade independente.
