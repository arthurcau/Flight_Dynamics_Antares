# Onboarding — primeiros passos no Antares Flight Dynamics

Este guia apresenta a estrutura do repositório e o fluxo de trabalho para
configurar, simular e analisar um foguete. Destina-se a integrantes que vão
usar as ferramentas e a quem pretende desenvolver o código compartilhado.

O repositório usa Python e RocketPy. O pacote `antares_fd` concentra os
construtores, a execução e as análises; cada projeto fornece seus próprios
arquivos de engenharia. Os scripts de projeto são pontos de entrada pequenos.

**Fluxo recomendado na versão 0.2:** após instalar, execute `antares-fd doctor`
e `antares-fd gui`. O [guia da estação](GUI.md) mostra projetos, componentes,
OpenRocket, validação, execução e histórico. Para trabalhar só pelo terminal,
use `antares-fd project new NOME --from ORIGEM`, `antares-fd validate NOME` e
`antares-fd run NOME`. Os scripts citados abaixo continuam como compatibilidade;
projetos novos não precisam copiá-los.

O [roteiro de manutenção e sucessão](MANUTENCAO.md) inclui um exercício offline.
Novas áreas: `application/` reúne serviços; `design/` calcula massa e importa
geometria; `gui/` serve a estação; `catalog/` identifica evidências; `schemas/`
documenta contratos; `projects/<id>/revisions/` conserva edições do serviço.

## 1. Roteiro para o primeiro uso

1. Obtenha o código e instale o ambiente da seção 2.
2. Execute a ajuda da CLI e os testes para verificar a instalação.
3. Consulte o mapa da seção 3 e escolha o projeto em `projects/`.
4. Confira os YAMLs, os arquivos referenciados e a origem dos dados físicos.
5. Execute primeiro `simulations/nominal.py`; verifique resumo e artefatos.
6. Avance para outros cenários e Monte Carlo depois de conferir o modelo nominal.
7. Guarde o identificador da execução e seus manifestos ao compartilhar resultados.

Os comandos deste documento partem da **raiz do repositório**, onde estão
`README.md`, `setup.py` e `projects/`. Os caminhos reais são `source/`,
`projects/` e `tests/`, em minúsculas. Linux distingue maiúsculas de minúsculas.

## 2. Preparar o ambiente

### Requisitos

Use Git e **Python 3.12 ou superior**, conforme declarado em `setup.py`.
A instalação inicial precisa de acesso à rede para baixar dependências.
Simulações com meteorologia MAGI também podem precisar de rede ou de cache
compatível com o local, o modelo e o horário solicitados.

Para obter uma cópia nova:

```bash
git clone https://github.com/arthurcau/Flight_Dynamics_Antares.git
cd Flight_Dynamics_Antares
```

Se o repositório já está no computador, abra o terminal nessa pasta; não é
necessário cloná-lo novamente.

### Linux e macOS — Bash

Confirme que `python3 --version` aponta para uma versão compatível. Em seguida:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --require-hashes -r requirements-py314.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
source .venv/bin/activate
```

A partir da ativação, `python` usa o ambiente do projeto. `-e` faz a instalação
editável: alterações em `source/` e `MAGI/` passam a ser utilizadas sem reinstalar
o pacote. O extra `dev` inclui as ferramentas de teste e análise estática.

O exemplo usa Python 3.14. Para Python 3.12 selecione `requirements-py312.lock`.
Os locks já incluem as ferramentas de desenvolvimento e hashes; para outra
versão compatível, a instalação aberta `pip install -r requirements.txt -e ".[dev]"`
continua possível, mas não corresponde ao ambiente travado desta entrega.

Como alternativa para instalar as dependências de execução, há `bash setup.sh`.
Ele cria ou reaproveita `.venv`; para obter também as ferramentas de
contribuição, execute depois `.venv/bin/python -m pip install -e ".[dev]"`.

### Windows — PowerShell

Selecione explicitamente uma versão instalada compatível, por exemplo 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -e ".[dev]"
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, use diretamente
`.\.venv\Scripts\python.exe` no lugar de `python` nos comandos seguintes.
Em Linux/macOS, o equivalente é `.venv/bin/python`. Não é preciso mudar a
política do sistema para executar o interpretador pelo caminho completo.

### Conferir a instalação

Com o ambiente ativado:

```bash
python --version
python -m antares_fd.cli --help
python -m pytest -q
```

A ajuda deve listar `mc`, `report`, `archive` e `telemetry`. O pytest descobre
as suítes `tests/` e `MAGI/tests/` pela configuração de `pyproject.toml`.
Os testes usam dados de teste e diretórios temporários; não exigem que o usuário
já tenha os registros brutos de um voo real.

Na IDE, selecione explicitamente `.venv/bin/python` ou
`.venv\Scripts\python.exe` como interpretador e use a raiz como diretório de
trabalho. Não presuma que o botão de execução já esteja usando esse ambiente.
Para sair do ambiente ativado, use `deactivate`.

## 3. Mapa dos diretórios

```text
Flight_Dynamics_Antares/
├── README.md                 apresentação e links principais
├── setup.py / pyproject.toml instalação, extras e verificações
├── requirements.txt          dependências usadas na instalação
├── setup.sh                  instalador auxiliar para Bash
├── source/antares_fd/         código reutilizável de dinâmica de voo
├── MAGI/                     aquisição e processamento meteorológico
├── projects/
│   ├── 00_Copy_This/          molde para criar um novo foguete
│   ├── andorinha/             entradas do projeto Andorinha
│   └── neblina_1/             entradas e análises do Neblina 1
├── tests/                    testes do núcleo e suas integrações
├── scripts/                  ferramentas de manutenção do repositório
├── docs/                     guias, referências e estudos técnicos
├── data/                     dados locais, incluindo registros brutos
└── results/                  produtos gerados pelas execuções
```

`data/`, `results/`, `.venv/` e `MAGI/dados_cache/` são ignorados pelo Git.
Podem não existir ou estar vazios em uma cópia nova. Um `git clone` não recupera
os arquivos locais de experimentos nem os resultados de outra pessoa.

| Preciso encontrar ou alterar… | Local principal |
| --- | --- |
| Massa, inércia, geometria e aerodinâmica de um foguete | `projects/<projeto>/config/vehicle.yaml` |
| Local, data, fuso e orientação da rampa | `projects/<projeto>/config/launch.yaml` |
| Modelo atmosférico e política de fallback | `projects/<projeto>/config/environment.yaml` |
| Configuração do motor e sua curva medida | `projects/<projeto>/config/motor.yaml` e `motors/` |
| Paraquedas, gatilhos e atraso de abertura | `projects/<projeto>/config/recovery.yaml` |
| Tabelas de coeficiente de arrasto | `projects/<projeto>/aero/` |
| Scripts para iniciar simulações | `projects/<projeto>/simulations/` |
| Lógica reutilizável de construção e integração | `source/antares_fd/builders/` e `simulation/` |
| Estatística, requisitos e proveniência | `source/antares_fd/analysis/` |
| Geração e verificação de relatórios | `source/antares_fd/reporting/` |
| Auditoria de registros de sensores | `source/antares_fd/telemetry/` |
| Reconstrução observacional e comparação de modelos | `source/antares_fd/reconstruction/` e `validation/` |
| Metadados do registro bruto do Neblina 1 | `projects/neblina_1/telemetry/metadata/dataset.yaml` |
| Dados brutos locais de voo | `data/flight_data/`, conforme declarado nos metadados |
| Resultados de uma execução | `results/<projeto>/<identificador>/` |
| Ambiente meteorológico e caches | `MAGI/`, especialmente `interface.py` e `dados_cache/` |
| Testes meteorológicos | `MAGI/tests/` |
| Testes unitários, integrações e fixtures do núcleo | `tests/unit/`, `tests/integration/` e `tests/fixtures/` |
| Configuração de integração contínua | `.github/workflows/ci.yml` |

Arquivos NetCDF `.nc` e caches meteorológicos eventualmente encontrados na
raiz são produtos locais de exportação. Não substituem os YAMLs do projeto.
Diretórios como `build/`, `__pycache__/` e `*.egg-info/` são gerados por
ferramentas; não são locais para editar a implementação.

## 4. Como um projeto é organizado

O template tem quatro grupos principais:

```text
projects/<projeto>/
├── config/       parâmetros e referências de entrada em YAML
├── aero/         tabelas Mach × Cd, normalmente em CSV
├── motors/       curvas de empuxo, incluindo arquivos RASP .eng
└── simulations/  pontos de entrada que chamam o pacote compartilhado
```

O Neblina 1 também tem `telemetry/` e `reconstruction/`. Esses diretórios não
são obrigatórios para um projeto que ainda não tenha dados de voo.

| Arquivo de configuração | Responsabilidade | Disponibilidade |
| --- | --- | --- |
| `vehicle.yaml` | Corpo, massas, inércias, posições, aletas e referências de arrasto. | Presente no template; exigido pelo carregador. |
| `launch.yaml` | Local, elevação, data/hora/fuso e rampa. | Presente no template; exigido pelo carregador. |
| `recovery.yaml` | Dispositivos, CdS, gatilhos, amostragem, atraso e reefing. | Presente no template; exigido pelo carregador, mesmo com recuperação desabilitada. |
| `motor.yaml` | Tipo e propriedades do motor, curva de empuxo e convenção própria do motor. | Presente no template; necessário para construir o motor de um voo. |
| `environment.yaml` | Atmosfera padrão ou MAGI, instante-alvo, cobertura e fallback. | Presente no template; revisar antes do voo. |
| `monte_carlo.yaml` | Contagem/opções do executor direto e parâmetros estocásticos. | Presente no template; necessário para esse fluxo Monte Carlo. |
| `uncertainties.yaml` | Distribuições, unidades e proveniência da população amostrada. | Existe no Neblina 1; não vem no template atual. |
| `requirements.yaml` | Limites e fontes dos requisitos específicos do projeto. | Existe no Neblina 1; não vem no template atual. |
| `simulation.yaml` | Opções numéricas aceitas pelo integrador, como tolerâncias e limites de passo. | Opcional, suportado pelo carregador; não vem no template atual. |

Os caminhos do motor e das curvas aerodinâmicas são relativos à pasta do
projeto. Por exemplo, `motors/motor.eng` em `motor.yaml` aponta para
`projects/<projeto>/motors/motor.eng`, e não para uma pasta `motors/` na raiz.

Os YAMLs usam indentação por espaços e devem ter raiz do tipo mapeamento.
Preserve os nomes das seções; não converta valores desconhecidos em zero.
Valores `null` representam informação ainda não preenchida, mas a presença de
um valor numérico de exemplo também não prova que ele serve ao seu foguete.

### Convenções de engenharia

- Use SI: metros, quilogramas, segundos, newtons e pascals. Campos angulares
  indicam graus ou radianos no nome/comentário; confira cada campo.
- A posição longitudinal do veículo usa bico → cauda: ponta do bico em `x = 0`
  e posições crescentes em direção à cauda. O motor tem sua própria orientação
  declarada em `motor.yaml`; confira a montagem no referencial do veículo.
- ASL/MSL indica altitude em relação ao nível do mar; AGL indica altura em
  relação ao solo. Não compare as duas sem considerar a elevação do local.
- Registre fonte, revisão e incerteza dos dados. Um parâmetro desconhecido
  continua desconhecido até haver evidência para preenchê-lo.
- Alterações de projeto pertencem aos seus YAMLs/dados. Fórmulas e mecanismos
  comuns pertencem ao pacote em `source/antares_fd/`.

## 5. Criar um novo foguete

Copie o template sem editar o original. Em Bash:

```bash
cp -R projects/00_Copy_This projects/meu_foguete
```

No PowerShell:

```powershell
Copy-Item -Recurse projects/00_Copy_This projects/meu_foguete
```

Escolha um nome sem espaços e confirme que o destino ainda não existe antes
de copiar. Depois:

1. Atualize nome, geometria, massas, inércias e posições em `vehicle.yaml`.
2. Coloque a curva correta em `motors/` e ajuste **todos** os parâmetros do motor.
3. Coloque as tabelas de arrasto em `aero/` e confira os caminhos, as unidades e
   a cobertura de Mach declarados em `vehicle.yaml`.
4. Preencha lançamento, recuperação e ambiente meteorológico.
5. Revise valores exemplificativos do template, inclusive os já numéricos.
6. Execute o nominal e examine os resultados antes de aumentar a complexidade.

Não basta renomear o projeto e preencher apenas os `null`: os demais valores
podem pertencer ao exemplo. O software interrompe a execução quando faltam
entradas obrigatórias ou quando encontra certas configurações incompatíveis.

## 6. Executar e conferir o primeiro voo

Com o ambiente ativado e os dados revisados:

```bash
python projects/meu_foguete/simulations/nominal.py
```

Para trabalhar com o modelo existente do Neblina 1:

```bash
python projects/neblina_1/simulations/nominal.py
```

Esses comandos **executam física e gravam resultados**. O Neblina 1 está
configurado para MAGI; dados atmosféricos indisponíveis podem impedir o voo.
Os arquivos atuais representam o modelo atual do projeto, não necessariamente
um snapshot da configuração efetivamente lançada.

O fluxo é: carregar YAMLs → aplicar o cenário em uma cópia da configuração →
construir ambiente/motor/veículo/recuperação → integrar o voo → exportar resultados.

Procure `FLIGHT SUMMARY` no terminal e confira apogeu, velocidade, Mach e eventos
de recuperação. Verifique também mensagens de falha de exportação: o voo pode
terminar enquanto um mapa, gráfico ou relatório auxiliar falha.

O diretório de saída é informado pelo programa. Para um voo individual, os
produtos ficam sob:

```text
results/<projeto>/<identificador>/
├── manifest.yaml
├── trajectory.kml
├── reports/
│   ├── flight_dynamics_report.pdf
│   └── master_metrics.json
└── ... mapas e gráficos disponíveis nessa execução
```

A árvore acima é uma referência de localização, não uma garantia de que toda
exportação terminou. O mapa de fundo pode precisar de internet. O KML usa
altitude absoluta e pode ser aberto em uma ferramenta compatível, como Google
Earth; ele representa a trajetória **simulada**. Os nomes dos demais gráficos
variam com o cenário e o executor.

## 7. Outros cenários e campanhas

Os projetos possuem pontos de entrada como:

| Script | Cenário/objetivo |
| --- | --- |
| `nominal.py` | Recuperação conforme o YAML do projeto. |
| `balistic.py` | Recuperação desabilitada; o identificador interno é `ballistic`. |
| `main_at_apogee.py` | Principal acionado no apogeu, com drogue desabilitado. |
| `only_reefing.py` | Representação em estágios usando a fração CdS configurada; exige `recovery.reefing.cd_s_fraction`. |
| `monte_carlo.py` | Campanha estocástica pelo executor escolhido no script. |
| `run_all.py` | Campanha consolidada com os cenários declarados e relatório conjunto, quando o projeto possui esse script. |

Exemplos para Neblina 1:

```bash
python projects/neblina_1/simulations/main_at_apogee.py
python projects/neblina_1/simulations/run_all.py
```

`run_all.py` executa vários voos e pode iniciar Monte Carlo. Não é uma verificação
rápida de instalação. Está disponível no template e no Neblina 1; não presuma que
todos os projetos tenham os mesmos scripts. Ele seleciona entradas conhecidas,
sem executar indiscriminadamente cada `.py` da pasta.

Na campanha consolidada, procure `flight_dynamics_report.pdf`,
`master_metrics.json` e `manifest.yaml` na raiz do diretório informado. Uma
campanha pode terminar parcialmente; confira os campos de status e as falhas
registradas no manifesto, além da existência do PDF.

### Monte Carlo pela CLI

A CLI é o módulo `antares_fd.cli`. A instalação também fornece o comando
`antares-fd`; `python -m antares_fd.cli` ajuda a manter explícito qual ambiente
Python está sendo utilizado. `--repo-root` é uma opção global, antes do subcomando:

```bash
python -m antares_fd.cli --repo-root . mc neblina_1 --profile debug --workers 2
python -m antares_fd.cli --repo-root . mc neblina_1 --profile debug --workers 2 --all-scenarios
```

O primeiro comando processa o nominal; o segundo usa os cenários configurados
para a campanha. Mesmo `debug` realiza simulações reais.

| Perfil da CLI | Meta padrão de casos | Uso pretendido |
| --- | ---: | --- |
| `debug` | 50 | Diagnóstico do fluxo. |
| `development` | 500 | Desenvolvimento e comparação inicial. |
| `engineering` | 2.000 | Análise com população maior. |
| `official` | 10.000, com teto padrão de 20.000 | Execução com critérios adaptativos de convergência. |

Essas metas são da CLI. O script direto `simulations/monte_carlo.py` pode usar a
contagem e as opções de seu YAML/executor; não suponha que
`monte_carlo.num_simulations` substitua a meta do perfil escolhido na CLI.
Use o manifesto da execução para conferir meta efetiva, semente, sucessos,
falhas e convergência. `COMPLETE_NOT_CONVERGED` não significa convergência atendida.

Para retomar uma campanha compatível, substitua `ID_DA_CAMPANHA` pelo nome
exato do diretório da execução:

```bash
python -m antares_fd.cli --repo-root . mc neblina_1 --resume ID_DA_CAMPANHA --workers 2 --all-scenarios
```

Preserve o conjunto de cenários e as entradas da campanha original. Retomada
não é um comando para juntar resultados de configurações físicas diferentes.
Os manifests e hashes verificam a identidade das entradas.

### Ler e compartilhar os artefatos

Em campanhas estocásticas canônicas, procure `manifest.json`,
`samples/inputs.parquet` e os diretórios por cenário, com saídas, estatísticas
e resumos. JSON guarda metadados; Parquet guarda tabelas de análise. Produtos
compactos podem omitir logs redundantes ou trajetórias individuais.

Para campanhas compatíveis que já possuam `master_metrics.json` e os artefatos
necessários ao renderizador:

```bash
python -m antares_fd.cli --repo-root . report ID_DA_CAMPANHA --project neblina_1
```

Esse comando lê os resultados existentes e escreve `evidence_report.pdf`.
Não integra um novo voo nem adquire uma nova atmosfera. Nem todo diretório em
`results/` atende a esse contrato; a pasta de um voo individual, por exemplo,
pode ter as métricas dentro de `reports/`.

Para criar um arquivo de campanha pelo mecanismo disponível:

```bash
python -m antares_fd.cli --repo-root . archive ID_DA_CAMPANHA --project neblina_1
```

O programa informa o caminho do arquivo gerado. Ao compartilhar uma análise,
inclua identificação do projeto, ID da execução, configuração/snapshot,
manifestos e tabelas relevantes; um PDF isolado não contém toda a evidência.

## 8. Meteorologia: o papel do MAGI

O MAGI fornece aquisição, processamento e exportação atmosférica. Sua interface
com a simulação é `MAGI/interface.py`. Os principais componentes são:

| Componente | Papel |
| --- | --- |
| `balthasar.py` | Aquisição de perfis, cache e identificação da fonte/tempo. |
| `melchior.py` | Leitura e análise de climatologia disponível. |
| `casper.py` | Interpolação vertical, grandezas termodinâmicas e qualidade. |
| `state_manager.py` | Estado e frescor dos dados. |
| `scoring.py` | Índice atmosférico exploratório. |
| `MAGI_App.py` | Aplicação integrada de aquisição, visualização e exportação. |

Revise em `environment.yaml` o tipo de atmosfera, instante-alvo e política de
fallback. Atmosfera padrão é uma hipótese de modelo; não deve ser apresentada
como medição meteorológica do lançamento. No modo MAGI, fallback só ocorre
quando explicitamente habilitado. Não ative fallback apenas para esconder
uma falha de dados sem avaliar sua adequação ao estudo.

O cache não é uma fonte meteorológica universal: cobertura, origem e horário
precisam corresponder ao pedido. Sem histórico local, MELCHIOR informa
indisponibilidade; não cria climatologia presumida. Caches históricos antigos
podem estar marcados `PROVENANCE_UNVERIFIED`.

Para perfis usados em simulações, execute os pontos de entrada de projeto.
A aplicação completa `python MAGI/MAGI_App.py` realiza aquisições e exportações
próprias; não é necessária para simplesmente pedir um voo. Importar esse módulo
como se fosse uma biblioteca também inicia seu processamento. Veja o
[guia do MAGI](../MAGI/README.md) antes de utilizá-lo diretamente.

## 9. Telemetria e dados de voo

O fluxo de sensores é separado do fluxo de simulação. Para Neblina 1:

1. Obtenha uma cópia verificada do registro bruto e confira sua identidade.
2. Coloque-o no caminho declarado por `telemetry/metadata/dataset.yaml`,
   normalmente sob `data/flight_data/`.
3. Confira cabeçalho, canais, unidades e referências nos metadados.
4. Execute a auditoria, que grava novos produtos em `results/`.

```bash
python -m antares_fd.cli --repo-root . telemetry audit neblina_1
```

A auditoria gera inventário, manifesto de integridade, amostras em Parquet,
segmentos temporais, diagnósticos e `telemetry_quality_report.md`.
Ela preserva o arquivo bruto; não aplica automaticamente calibração,
sincronização ou correção de relógio.

Para processar uma seção declarada a partir de uma auditoria existente:

```bash
python -m antares_fd.cli --repo-root . telemetry process neblina_1 --audit results/neblina_1/ID_DA_AUDITORIA
```

Esse exemplo usa a seção única declarada nos metadados. Caso não haja exatamente
uma seção, consulte `telemetry process --help` e informe `--section` com o nome
real do marcador. Não trate uma unidade no cabeçalho como prova de calibração,
nem componentes de giroscópio sem referência conhecida como atitude reconstruída.

Veja o [guia de telemetria](../projects/neblina_1/telemetry/README.md) e o
[guia de reconstrução](../projects/neblina_1/reconstruction/README.md) para os
contratos completos. O comparador de telemetria com Monte Carlo usa caminhos
de execuções previamente selecionadas; não é uma etapa automática de instalação.

## 10. Contribuir com código ou documentação

Antes de alterar algo, localize a responsabilidade na tabela da seção 3.
Evite copiar a lógica de integração para um script específico de foguete.
Mantenha novos dados físicos no projeto e acrescente regressões quando corrigir
um comportamento do núcleo.

Com as dependências `dev` instaladas, execute:

```bash
python -m ruff check source MAGI projects scripts tests setup.py
python -m pytest -q
python scripts/generate_function_reference.py --check
```

Se alterar uma assinatura ou docstring, atualize a referência e confira o diff:

```bash
python scripts/generate_function_reference.py
git diff --check
git status --short
```

O gerador documenta funções de execução e ferramentas sem importar os módulos.
A CI repete análise estática, verificação da referência e testes. Revise os
arquivos antes de adicioná-los ao Git; não versione o ambiente virtual, caches
ou saídas de simulação para contornar as regras de `.gitignore`.

Para executar sem janela gráfica em Bash, prefixe o comando com
`MPLBACKEND=Agg`, por exemplo:

```bash
MPLBACKEND=Agg python projects/neblina_1/simulations/nominal.py
```

## 11. Problemas frequentes

| Sintoma | O que conferir |
| --- | --- |
| `No module named antares_fd` | Interpretador selecionado, ativação do `.venv` e instalação editável `python -m pip install -e ".[dev]"` na raiz. |
| `No projects/ directory` | Diretório informado em `--repo-root`; essa opção fica antes do subcomando. |
| Pasta ou script não encontrado no Linux | Grafia e capitalização: `projects/`, `source/`, `neblina_1/` e o nome histórico `balistic.py`. |
| `ConfigurationError`, campo ausente ou raiz YAML inválida | Arquivo/campo citado na mensagem, indentação, tipo do valor e dados obrigatórios ainda `null`. Não substitua por valores arbitrários. |
| Curva de motor ou arrasto não encontrada | Caminho relativo à pasta do projeto e presença do `.eng`/CSV indicado. |
| `AtmosphereUnavailableError` ou pedido fora da cobertura | Instante e fuso, extensão vertical, fonte e disponibilidade meteorológica. Verifique a causa registrada antes de mudar o modelo atmosférico. |
| Existe PDF, mas houve erro na campanha | Status e falhas nos manifestos; o relatório pode ter sido gerado para registrar um resultado parcial. |
| Não há mapa, KML ou relatório esperado | Mensagens de exportação, dependências e modo compacto. Nem todo executor produz os mesmos arquivos. |
| Arquivo bruto não veio com o clone | `data/` é ignorado pelo Git. Obtenha a fonte original e verifique os hashes declarados. |
| Retomada rejeitada | ID, cenários, manifesto, snapshot e população original; entradas alteradas exigem uma nova campanha. |
| Teste paralelo falha por permissão de socket/processo | Restrições do ambiente de execução; os testes Monte Carlo usam comunicação local entre processos. |

## 12. Onde aprofundar

| Documento | Quando ler |
| --- | --- |
| [Referência das funções](referencia_funcoes/README.md) | Para entender objetivo, assinatura, mecanismo e colaboradores de uma rotina. |
| [Metodologia Monte Carlo](MONTE_CARLO_METHODOLOGY.md) | Para interpretar a população amostrada e a análise estocástica. |
| [Modelo de incertezas](UNCERTAINTY_MODEL.md) | Para revisar distribuições, proveniência e hipóteses. |
| [Configuração do Neblina 1](../projects/neblina_1/config/README.md) | Para localizar entradas específicas desse modelo. |
| [Telemetria do Neblina 1](../projects/neblina_1/telemetry/README.md) | Para obter e auditar registros de sensores. |
| [Revisão de código](REVISAO_CODIGO_2026-11-16.md) | Para conhecer correções, exclusões e limites das verificações. |
| [Catálogo histórico](CATALOGO_NOTEBOOKS_E_SCRIPTS.md) | Para consultar a evolução dos notebooks e scripts antigos. |

Os estudos e auditorias em `docs/` podem descrever revisões passadas. Confira a
data e a revisão de referência antes de usar um comando antigo. Este onboarding
descreve a estrutura atual; a existência de uma simulação concluída não comprova,
por si só, validade física ou equivalência com a configuração de um voo real.
