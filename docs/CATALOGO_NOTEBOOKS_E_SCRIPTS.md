# Catálogo dos notebooks e scripts Python

Data da análise: 20/09/2026. Revisão de referência:
`07d6cc2ac0818a62c41a3e93f3b3e9152d40f4c5`.

## Resultado do inventário

**Não havia arquivos `.ipynb` no diretório no início desta análise.** A busca
incluiu arquivos ocultos, ignorados pelo Git, caches, resultados e `.venv`, com
verificação da extensão sem distinguir maiúsculas de minúsculas. Foram percorridas
24.047 entradas de arquivos fora de `.git`; os links simbólicos encontrados
pertencem ao ambiente virtual. O inventário Git inicial tinha 333 arquivos
versionados, dos quais 124 com extensão `.py`.

O histórico acessível por `git log --all` contém **dois caminhos de notebooks**, já
excluídos em commits anteriores. Foram lidas todas as células das duas últimas
versões e também da primeira versão do notebook Neblina. Os scripts atuais já
executam os fluxos de simulação e de atmosfera em Python comum.

Nesta análise foram convertidos **zero notebooks** e excluídos **zero notebooks**:
não havia originais na árvore de trabalho para essas operações. Este catálogo
registra o histórico, as correspondências funcionais e as diferenças observadas.
A correspondência com scripts atuais **não comprova equivalência exata** com os
notebooks históricos; diferenças anteriores estão descritas abaixo. Nenhuma
equação, configuração física ou implementação Python foi alterada nesta análise.

## Mapa do diretório

| Local | Conteúdo e função |
| --- | --- |
| [`source/antares_fd/`](../source/antares_fd/) | 49 módulos Python: configuração, construção de objetos RocketPy, execução, incertezas, análise e relatórios. |
| [`projects/neblina_1/`](../projects/neblina_1/) | Configurações YAML, motores `.eng`, tabelas de arrasto e oito scripts de execução do Neblina. |
| [`projects/andorinha/`](../projects/andorinha/) | Configurações, motores, tabelas e seis scripts de execução do Andorinha. |
| [`projects/00_Copy_This/`](../projects/00_Copy_This/) | Template de projeto com configurações, dados e sete scripts de execução. |
| [`MAGI/`](../MAGI/) | 20 arquivos Python fora dos testes: aplicação atmosférica, física, aquisição, estatísticas, visualização, exportação e gerador opcional de notebook. |
| [`MAGI/tests/`](../MAGI/tests/) | Quatro arquivos Python de testes atmosféricos e exportação. |
| [`tests/`](../tests/) | 19 arquivos Python de testes e benchmarks; fixtures e resultados de medições de desempenho. |
| [`docs/`](./) | Documentação técnica, auditorias anteriores e imagens institucionais. |
| `data/`, `MAGI/dados_cache/`, `dados_cache/` | Dados locais e caches meteorológicos; não são notebooks. |
| `results/` | Artefatos das campanhas: trajetórias, tabelas, manifestos, figuras e relatórios. |
| [`MAGI/figures/`](../MAGI/figures/) | Panoramas e painéis PNG. Os arquivos em `.ipynb_checkpoints/` também são PNG, não notebooks. |
| Arquivos `.nc` na raiz | Exportações atmosféricas NetCDF existentes. |
| [`setup.py`](../setup.py), [`setup.sh`](../setup.sh), [`requirements.txt`](../requirements.txt) | Empacotamento, preparação do ambiente e dependências. |
| `fix.py`, `patch.py`, `patch_*.py` na raiz | Dez utilitários de manutenção anteriores; não são entradas de simulação nem conversões de notebooks. |
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Integração contínua e execução de testes. |
| [`.ai/`](../.ai/), `.agents/`, `.codex/`, `.idea/` | Contexto para ferramentas e metadados de desenvolvimento. |
| `.venv/`, `__pycache__/`, `.pytest_cache/`, `antares_fd.egg-info/` | Ambiente, caches e metadados gerados. |
| `.git/` | Histórico; consultado para recuperar o conteúdo antigo em memória, sem restaurar notebooks na árvore de trabalho. |

O diretório `scripts/` citado no README principal não existe nesta revisão; as
entradas efetivas estão em `projects/*/simulations/` e `MAGI/MAGI_App.py`.

## Notebooks históricos

As contagens incluem células vazias. A numeração de células usada neste documento
começa em 1 e segue a ordem armazenada, independentemente de `execution_count`.

| Identidade | Fonte examinada no Git | Células | Exclusão anterior | Correspondência atual |
| --- | --- | --- | --- | --- |
| `MAGI/MAGI_App.ipynb` | `b8fb381^:MAGI/MAGI_App.ipynb` | 22: 11 Markdown, 11 código; uma célula de código vazia; 146 linhas de código | `b8fb381`, 10/09/2026 | [`MAGI/MAGI_App.py`](../MAGI/MAGI_App.py) e seus subsistemas |
| `rocketPy_neblina.ipynb` | `e482c15^:rocketPy_neblina.ipynb` | 26: 7 Markdown, 19 código; 229 linhas de código | `e482c15`, 17/09/2026 | [`projects/neblina_1/simulations/`](../projects/neblina_1/simulations/), YAMLs e `source/antares_fd/`; correspondência por responsabilidade, sem exportação literal única |
| Versão inicial de `rocketPy_neblina.ipynb` | `887ce27^:rocketPy_neblina.ipynb` | 27: 9 Markdown, 18 código; 155 linhas de código | `887ce27`, 08/09/2026; o mesmo caminho foi adicionado novamente em `dff5723`, 10/09/2026 | Antecedente do fluxo Neblina, com dependências do Google Colab |

Os conteúdos históricos tinham, respectivamente, 11, zero e 21 blocos de saída
salvos. Saídas antigas não constituem evidência de que o programa atual reproduz
aqueles resultados. Permanecem disponíveis no histórico Git.

### MAGI: funcionamento das células e aplicação atual

O notebook coordenava aquisição meteorológica, climatologia, interpolação,
ensembles, classificação atmosférica, painéis e exportação. A lógica física fica
nos módulos chamados, e não nas células de apresentação.

| Células de código | Trabalho executado | Correspondência no script atual |
| --- | --- | --- |
| 3 | Importa NumPy, pandas, Matplotlib, IPython e os subsistemas. Define elevação de 450 m e a grade vertical. | Seção 0 de `MAGI_App.py`; imports de IPython removidos anteriormente, com suporte a imports como pacote ou execução direta. |
| 5 | Obtém o perfil operacional, solicita uma data, substitui timestamps se informada e avalia o estado do cache. | Seção 1; a leitura de teclado atual só acontece em TTY, com tratamento de EOF/interrupção. A data ainda é tratada depois da aquisição. |
| 7 | Carrega o histórico, calcula estatísticas na grade e a média/covariância multivariada. | Seção 2; `Melchior.fetch_historical_data`, `calc_stats_hist` e `calculate_multivariate_covariance`. |
| 9 | Interpola o nominal; na ausência de ensemble real, gera 50 membros sintéticos se houver covariância. Para uma lista de ensemble, trata o primeiro perfil como nominal e os demais como membros. | Seção 3; `CasperProcessor` e `MagiSchema`. |
| 11 | Calcula e imprime pontuação e classe atmosférica. | Seção 4; agora passa `operational_state` e usa um dicionário `score_info`, enquanto o notebook usava tupla. |
| 13 | Gera o panorama operacional. | Seção 5; o script fecha a figura e trata falhas de apresentação. |
| 15 | Seleciona o pior dia histórico, interpola e gera um painel de exemplo. | Seção 5b; usa `__file__` para localizar `MAGI/figures/`. |
| 17 | Exporta perfil nominal, membros, estatísticas e metadados para `magi_export_latest.nc`. | Seção 6; também foram acrescentadas três exportações compatíveis com RocketPy. |
| 19 | Executa `pytest tests/ -v` pelo shell. | Seção 7; o script usa `sys.executable` e o caminho absoluto de `MAGI/tests/`. |
| 21, 22 | Imprime conclusão; última célula vazia. | Mensagem de término na seção 8. |

A expressão da grade, presente nas duas versões, é
`np.arange(10, 6000 + 100, 100)`: produz **61 níveis de 10 a 6.010 m AGL**.
O limite parametrizado de 6.000 m não é o último ponto efetivamente produzido.

Entradas e efeitos do script atual:

- BALTHASAR usa sua configuração padrão de local/modelo e consulta previsão ou
  cache. MELCHIOR lê `MAGI/dados_cache/historico_openmeteo.csv`; sua implementação
  atual gera climatologia sintética de contingência quando esse arquivo falta.
- A classificação depende dos perfis, da climatologia, do estado operacional e
  das regras de `scoring.py`. A execução de hoje usa as implementações atuais
  desses módulos, que também evoluíram desde o notebook.
- Figuras são gravadas em `MAGI/figures/`, com nomes datados e sufixo `latest`.
- `magi_export_latest.nc`, `magi_rocketpy_ensemble.nc`,
  `magi_rocketpy_ensemble_1week_1h.nc` e
  `magi_rocketpy_ensemble_24h_30s.nc` são destinos relativos ao diretório de
  execução. Os dois primeiros ensembles RocketPy cobrem 168 horas com passo de
  uma hora; o terceiro cobre 24 horas com passo de 30 segundos.
- `StateManager()` usa `dados_cache/` relativo ao diretório de execução;
  BALTHASAR e MELCHIOR resolvem seu cache relativo ao diretório `MAGI/`.
- O código da aplicação está no nível superior do módulo: importá-lo também
  inicia o processamento, aquisições, exportações e testes. Os consumidores de
  atmosfera usam `MAGI/interface.py` para acessar os perfis.

Há diferenças observáveis anteriores à análise: tratamento de entrada,
estrutura da pontuação, tratamento de erros gráficos, fechamento das figuras,
coordenadas dos metadados, exportações adicionais e seleção do executável de
testes. O notebook também usava `__file__`, indisponível por padrão em uma célula
Jupyter, e importava `display`/`Markdown` sem utilizá-los. Portanto, o script é o
ponto de entrada atual, mas não uma cópia de comportamento comprovadamente
idêntico a todas as células históricas.

### Neblina: funcionamento da última versão

| Células de código | Trabalho executado | Local atual da responsabilidade |
| --- | --- | --- |
| 4 | Importa RocketPy e auxiliares; ativa `autoreload` e `%matplotlib widget`. | Imports Python nos módulos e scripts. Esses comandos de interface Jupyter não existem nas entradas atuais. |
| 5–6 | Configura ambiente, data, temperatura e vento e imprime suas propriedades. | `config/launch.yaml`, `config/environment.yaml` e `builders/environment.py`. |
| 8–10 | Constrói o motor Yaripo, inspeciona impulso/massa/NaN/Inf e desenha o motor. | `config/motor.yaml`, `motors/`, `builders/motor.py`; os diagnósticos e desenhos antigos não são todos chamadas literais dos scripts atuais. |
| 12 | Constrói corpo, motor, botões, nariz, aletas e cauda. | `config/vehicle.yaml`, `aero/` e `builders/vehicle.py`. |
| 13–15 | Copia o foguete em três variantes, define geometrias/CdS/gatilhos dos paraquedas e imprime a configuração. | `config/recovery.yaml`, `builders/recovery.py` e `simulation/scenarios.py`. |
| 16 | Limpa as listas de paraquedas do nominal e do principal no apogeu. | Célula de manutenção interativa; não faz parte do fluxo nominal atual. |
| 17–18 | Plota margens de estabilidade e desenha o foguete, inclusive em `neblina.png`. | Objetos RocketPy e rotinas de visualização/relatório; não há reprodução literal de todos esses arquivos na entrada nominal. |
| 20–22 | Simula três voos com rampa de 6 m, inclinação de 80° e direção de 90°; imprime balanço de massa/empuxo e resumo de voo. | `nominal.py`, `balistic.py`, `main_at_apogee.py`, `runner.py`, `results.py` e YAMLs de lançamento. |
| 23 | Compara trajetórias e exporta `3d_comparison.png` e `xy_comparison.png`. | Campanha e relatórios atuais com seus próprios formatos e nomes. |
| 24 | Exporta `fullNominal.kml`, `ballistic.kml` e `mainOnApogee.kml` com altitude relativa ao solo. | `results.py`; a implementação atual organiza resultados por campanha e exporta KML com altitude absoluta. |
| 26 | Varre massa de 5 a 20 kg em dez pontos com `apogee_by_mass`; plota aerodinâmica e cinemática. | A varredura não é chamada pelos scripts atuais. Há gráficos de telemetria em `simulation/plotters.py` e `reporting/`. |

O notebook dependia de arquivos externos em `../neblinaPy/data/`:
`Yaripo_teste_est_2.eng`, `cd_poweroff.CSV` e `cd_poweron.CSV`. A árvore atual usa
arquivos em `projects/neblina_1/motors/` e `aero/`. Os nomes não demonstram que os
conteúdos antigos e atuais são iguais.

As principais diferenças que impedem declarar uma conversão exata são:

- Executar todas as células antigas em ordem inclui a célula 16, removendo os
  paraquedas antes de construir os três voos. A intenção descrita no Markdown e
  o resultado dessa execução sequencial são diferentes.
- Local de lançamento, direção da rampa, atmosfera, propriedades e opções de
  recuperação agora vêm dos YAMLs e diferem dos valores embutidos no notebook.
  Por exemplo, a direção atual do Neblina é 240°, contra 90° no notebook.
- Relatórios, organização de diretórios, modo de altitude do KML e gráficos
  evoluíram. A varredura explícita de apogeu por massa não foi localizada nos
  pontos de entrada atuais.
- Apesar de importar `MonteCarlo`, essa versão não instancia nem executa uma
  campanha Monte Carlo. O script `monte_carlo.py` atual é uma capacidade
  adicional do sistema.

Na primeira versão, a instalação com `!pip`, o backend PyVista/Trame e duas
montagens de Google Drive exigiam Colab/Jupyter. Havia apenas um voo nominal,
dados físicos diferentes, uma conta de dispersão com coordenadas fixas e uma
seção Markdown dizendo que Monte Carlo havia sido removido. Essa versão também
não é um terceiro notebook independente: é um conteúdo anterior do mesmo caminho.

## Catálogo dos scripts de execução atuais

Os 21 arquivos abaixo já existiam antes desta análise. Cada script de projeto
carrega dados do próprio projeto e possui `main()` protegido por
`if __name__ == "__main__"`. O nome legado `balistic.py` tem apenas um `l`;
o identificador interno do cenário é `ballistic`.

| Finalidade | Neblina 1 | Andorinha | Template | Comportamento efetivo |
| --- | --- | --- | --- | --- |
| Voo nominal | [nominal.py](../projects/neblina_1/simulations/nominal.py) | [nominal.py](../projects/andorinha/simulations/nominal.py) | [nominal.py](../projects/00_Copy_This/simulations/nominal.py) | Carrega YAMLs, chama `execute_scenario` e retorna `Flight`. |
| Voo balístico | [balistic.py](../projects/neblina_1/simulations/balistic.py) | [balistic.py](../projects/andorinha/simulations/balistic.py) | [balistic.py](../projects/00_Copy_This/simulations/balistic.py) | Executa o cenário `ballistic`, desabilitando todos os dispositivos de recuperação em uma cópia da configuração. |
| Principal no apogeu | [main_at_apogee.py](../projects/neblina_1/simulations/main_at_apogee.py) | [main_at_apogee.py](../projects/andorinha/simulations/main_at_apogee.py) | [main_at_apogee.py](../projects/00_Copy_This/simulations/main_at_apogee.py) | Desabilita drogue e configura o principal para disparar no apogeu. |
| Recuperação com reefing | [only_reefing.py](../projects/neblina_1/simulations/only_reefing.py) | [only_reefing.py](../projects/andorinha/simulations/only_reefing.py) | [only_reefing.py](../projects/00_Copy_This/simulations/only_reefing.py) | Representa a fase reefada pelo dispositivo drogue com fração de CdS do principal; mantém abertura plena na altitude configurada. Requer `recovery.reefing.cd_s_fraction`. |
| Separação aproximada | [separation_at_main_opening.py](../projects/neblina_1/simulations/separation_at_main_opening.py) | [separation_at_main_opening.py](../projects/andorinha/simulations/separation_at_main_opening.py) | [separation_at_main_opening.py](../projects/00_Copy_This/simulations/separation_at_main_opening.py) | Subtrai 2 kg da massa sem motor, se a massa original for maior que 2 kg, antes do voo nominal inteiro. Não implementa um evento de separação durante a descida. |
| Monte Carlo | [monte_carlo.py](../projects/neblina_1/simulations/monte_carlo.py) | [monte_carlo.py](../projects/andorinha/simulations/monte_carlo.py) | [monte_carlo.py](../projects/00_Copy_This/simulations/monte_carlo.py) | Neblina usa `simulation/monte_carlo_failure.py`; Andorinha e template usam `simulation/monte_carlo.py`. |
| Compatibilidade Monte Carlo | [monte_carlo_failure.py](../projects/neblina_1/simulations/monte_carlo_failure.py) | — | — | Chama o mesmo executor do `monte_carlo.py` do Neblina; o nome não força um cenário de falha. |
| Campanha consolidada | [run_all.py](../projects/neblina_1/simulations/run_all.py) | — | [run_all.py](../projects/00_Copy_This/simulations/run_all.py) | Descobre scripts, executa cenários determinísticos e estocásticos, centraliza artefatos e produz relatório mestre. Evita duplicar o wrapper `monte_carlo_failure.py`. |

O 22º ponto de entrada relacionado ao catálogo é
[`MAGI/MAGI_App.py`](../MAGI/MAGI_App.py), descrito acima; ele não faz parte dos
21 arquivos em `projects/*/simulations/`.

### Caminho do `monte_carlo.py` do Neblina

O arquivo indicado na solicitação prepara `sys.path`, encontra o diretório do
projeto com `__file__`, carrega a configuração e chama
`antares_fd.simulation.monte_carlo_failure.execute_monte_carlo`. Não contém células
Jupyter nem o integrador físico.

O executor seleciona `ANTARES_MC_SCENARIO` (padrão `nominal`), aplica os overrides
antes dos builders, prepara nominal e ensemble atmosférico, carrega as incertezas,
constrói os objetos estocásticos e roda os voos RocketPy. Com amostras canônicas,
o produtor associa sementes a IDs de casos e escolhe perfis atmosféricos completos.
Registra resultados, falhas, trajetórias selecionadas, análise e proveniência.

Executar apenas esse script processa o cenário selecionado. A iteração pelos
cenários configurados é responsabilidade de `run_all.py`/`campaign.py` ou da CLI
com `--all-scenarios`. O nome do módulo compartilhado `monte_carlo_failure.py`
não significa que a execução padrão remove paraquedas.

`config/monte_carlo.yaml` do Neblina define atualmente dez simulações no perfil
`development`; variáveis `ANTARES_MC_TARGET`, `ANTARES_MC_WORKERS` e outras opções
de campanha podem substituir parte da configuração. `uncertainties.yaml` fornece
o registro de incertezas quando presente.

### Módulos que sustentam os scripts

| Módulos/diretório | Responsabilidade |
| --- | --- |
| `config/{loader,models,exceptions}.py` | Leitura de YAMLs, contêineres de configuração e erros explícitos. |
| `builders/{environment,motor,vehicle,recovery}.py` | Tradução dos dados para ambiente, motor, foguete e recuperação RocketPy. |
| `environment/atmosphere.py`, `MAGI/interface.py` | Contrato atmosférico validado e conexão entre MAGI e as simulações. |
| `simulation/{orchestrator,runner,scenarios}.py` | Montagem do cenário, opções numéricas e execução de `Flight`. |
| `simulation/{campaign,monte_carlo,monte_carlo_failure}.py` | Campanhas consolidadas e os dois executores Monte Carlo ainda presentes. |
| `simulation/{monte_carlo_parameters,monte_carlo_patch,monte_carlo_storage}.py` | Distribuições de lançamento, adaptadores locais RocketPy e armazenamento limitado de trajetórias. |
| `simulation/{uncertainty,uq_campaign,uq_pipeline,uq_storage}.py` | Registro/amostragem de incertezas, metadados, retomada, tabelas Parquet e pós-processamento. |
| `simulation/{results,plotters,statistics,report}.py` | Resumos, KML, gráficos, elipses de covariância e gerador LaTeX anterior. |
| `analysis/{metrics,flight_metrics,sensitivity,uq,scenario_uq}.py` | Métricas de voo, estatística, sensibilidade, convergência e comparação pareada. |
| `analysis/{compliance,requirements,provenance}.py` | Requisitos, conformidade e rastreabilidade dos dados/modelos. |
| `reporting/{builder,pdf_report,vector_report,charts,plot_registry,tables,theme,qa}.py` | Montagem, gráficos, tabelas, estilo e verificações dos relatórios. |
| `cli.py` | Comandos `mc`, `report` e `archive`; seleciona os scripts do projeto. |
| `MAGI/balthasar.py`, `MAGI/melchior.py` | Aquisição operacional/histórica e estatísticas da climatologia. |
| `MAGI/casper.py`, `MAGI/covariance.py` | Interpolação, relações termodinâmicas, validação e fatoração da covariância. |
| `MAGI/{state_manager,scoring}.py` | Estado/frescor dos dados e pontuação atmosférica exploratória. |
| `MAGI/{exporter,visuals}.py` | NetCDF canônico e painéis gráficos. |
| `MAGI/magi/casper/ensemble/{eof,generator,synthetic}.py` | Perturbações EOF e geração de ensembles/cubos atmosféricos. |
| `MAGI/magi/casper/export/rocketpy.py`, `MAGI/magi/visualization.py` | Conversão para o formato de ensemble RocketPy e visualizações adicionais. |
| Arquivos `__init__.py` | Definição dos pacotes e exportação de interfaces. |

## Execução em Python comum

Exemplos a partir da raiz, usando o ambiente já configurado no projeto:

```bash
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/nominal.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/monte_carlo.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/run_all.py
PYTHONPATH=source:. .venv/bin/python -m antares_fd.cli mc neblina_1 --profile development --all-scenarios
PYTHONPATH=source:. .venv/bin/python MAGI/MAGI_App.py
```

Esses comandos executam simulações/aquisições e produzem arquivos. Requerem os
dados dos YAMLs, arquivos de motor/arrasto e dados atmosféricos apropriados. São
exemplos de uso, não um registro de que todos foram executados nesta análise.
Para execução sem interface gráfica, acrescentar `MPLBACKEND=Agg`.

Os scripts `nominal.py` e `separation_at_main_opening.py` do Andorinha ainda
mencionam `Source` com maiúscula; alguns wrappers Monte Carlo dependem da
instalação do pacote ou do `PYTHONPATH`. O comando acima inclui explicitamente
`source` e a raiz para resolver os imports, sem modificar esses scripts.

## Vestígios de Jupyter

- [`MAGI/build_notebook.py`](../MAGI/build_notebook.py) é um **gerador opcional no
  sentido inverso**: lê `MAGI_App.py`, separa comentários/código e escreve
  `MAGI_App.ipynb` usando `nbformat`. Não é chamado pelos pontos de entrada de
  simulação examinados. Não foi executado nesta análise; executá-lo recria um
  notebook. Foi mantido para preservar a funcionalidade do utilitário existente.
- [`MAGI/contexto_atual_magi.md`](../MAGI/contexto_atual_magi.md) contém um snapshot
  extenso com referências e trechos antigos de notebooks. É documentação Markdown.
- [`ANALISE_TECNICA_2026-09-20.md`](ANALISE_TECNICA_2026-09-20.md) descreve outra
  revisão e menciona notebooks que existiam naquela análise.
- `.ipynb_checkpoints` sob `MAGI/figures/` contém imagens; o nome do diretório
  não transforma seus PNGs em notebooks.
- Os pontos de entrada atuais não contêm magics, chamadas `get_ipython`, imports
  `IPython.display` ou widgets necessários à execução.

## Validação e limites

O inventário foi cruzado por busca de arquivos incluindo ignorados, varredura do
sistema de arquivos, índice Git e histórico de todos os refs locais. Nenhum
notebook histórico foi restaurado ou executado. A comparação é uma inspeção do
código e dos fluxos, não uma regressão numérica entre programas de épocas distintas.

A análise sintática dos arquivos versionados aceitou 122 dos 124 arquivos `.py`.
`fix.py` e `patch.py` têm conteúdo com BOM de UTF-16, que não é fonte Python UTF-8
diretamente executável; são utilitários anteriores, fora dos fluxos catalogados.
`simulation/report.py` também emite um aviso de escape `\e` na string LaTeX.
Todos os scripts de simulação catalogados e `MAGI_App.py` passaram pela análise
sintática. Nenhuma dessas ocorrências foi introduzida por este trabalho.

Comando da suíte existente:

```bash
PYTHONPATH=source:. MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -q -p no:cacheprovider tests/ MAGI/tests/
```

Na primeira execução, 81 testes e quatro subtestes passaram. Três testes Monte
Carlo foram interrompidos pela proibição de sockets locais no sandbox
(`PermissionError` em `multiprocess`, seguido de `EOFError`). Um teste de
orquestração falhou porque sua fixture fornece o esquema antigo de arrasto:
`aerodynamics.power_on_drag/power_off_drag`, enquanto o construtor exige
`vehicle.drag.power_on/power_off`. Isso foi observado antes de qualquer
alteração no repositório.

Os três testes Monte Carlo foram repetidos com permissão para a comunicação
local entre processos e **todos passaram**. Resultado consolidado das duas
execuções: **84 testes aprovados, quatro subtestes aprovados e uma falha
preexistente** em `tests/integration/test_orchestrator.py`. A falha da fixture
foi documentada e permanece fora do escopo deste inventário.

A conferência final validou os 48 links locais dos quatro documentos envolvidos,
a sintaxe Python comum dos 22 pontos de entrada e a ausência de `.ipynb` em toda
a árvore examinada. Os 124 arquivos Python versionados permaneceram idênticos,
byte a byte, à revisão de referência.

### Identificação dos conteúdos históricos

SHA-256 dos blobs JSON completos consultados, incluindo metadados e saídas:

| Fonte Git | SHA-256 |
| --- | --- |
| `b8fb381^:MAGI/MAGI_App.ipynb` | `e406c7689363b8b3b78fb9cee4c6a7660402971d9bb4149a7ad2b405d514fb47` |
| `e482c15^:rocketPy_neblina.ipynb` | `4657545d6f5471e9095b31c4bd09c3a5771a1ce6a8513e01579443b46d9b59e3` |
| `887ce27^:rocketPy_neblina.ipynb` | `879d39bc2ae495caeb0a74f967042b2470094ec38adefcebe6eceaf014bba05f` |
