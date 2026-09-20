**Análise técnica do Antares Flight Dynamics — 20/09/2026**

A separação entre configuração dos veículos e código reutilizável é uma boa base. Entretanto, o estado examinado contém erros que alteram resultados físicos e estatísticos, além de caminhos que apresentam dados artificiais como previsões ou observações. A prioridade deve ser corrigir esses comportamentos e estabelecer verificações físicas antes de otimizar desempenho.

Escopo: commit `57cd2b3e63e6e30e9eb5751fca25916743dcad03`, inicialmente sem alterações locais; inventário de 282 arquivos versionados; inspeção dos 45 arquivos Python, das configurações, documentação e células do notebook. Foram executadas a suíte existente e reproduções controladas. Este trabalho acrescenta somente este relatório: o código, os dados dos projetos e os resultados anteriores foram preservados.

Ambiente observado: Python 3.14.4, RocketPy 1.13.0, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.5, scikit-learn 1.9.0, xarray 2026.7.0, netCDF4 1.7.4 e pytest 9.1.1. Resultados de compatibilidade abaixo se referem a esse ambiente.

**O que o código executa**

| Parte | Responsabilidade efetiva |
| --- | --- |
| `source/antares_fd/config/` | Lê YAMLs e cria dicionários acessíveis por atributos. Faz verificações pontuais, sem validar integralmente um esquema físico. |
| `source/antares_fd/builders/` | Constrói ambiente, motor sólido, foguete e paraquedas usando RocketPy. |
| `source/antares_fd/simulation/` | Orquestra os construtores, chama `Flight` e produz resumo, KML e mapa PDF. A integração das equações de movimento é delegada ao RocketPy. |
| `projects/00_Copy_This/` | Único projeto versionado nesta revisão: contém dados de demonstração e entradas para voo nominal, balístico, diferentes recuperações, separação e Monte Carlo. |
| `MAGI/melchior.py` | Lê histórico de CSV local, calcula estatísticas verticais e covariância, seleciona um caso histórico de maior pontuação de severidade. |
| `MAGI/balthasar.py` | O caminho chamado de previsão operacional lê um CSV local e acrescenta perturbações aleatórias. METAR/TAF têm uma rotina separada de consulta; diversas outras fontes anunciadas são funções vazias. |
| `MAGI/casper.py` e `MAGI/magi/` | Interpolam perfis, calculam grandezas atmosféricas, geram ensembles sintéticos e exportam NetCDF. Há duas implementações de geração sintética com comportamentos distintos. |
| `MAGI/MAGI_App.ipynb`, `MAGI_App.py`, `visuals.py` | Interfaces de orquestração, classificação e apresentação. Notebook e script atualmente divergem. |
| `results/` | Registros de execuções anteriores, incluindo projetos ausentes da árvore atual. O orquestrador atual não implementa a organização por manifesto encontrada nesses registros. |

O fluxo principal é `YAML → configuração → ambiente/motor/foguete/recuperação → RocketPy Flight → resultados`. A integração com MAGI seleciona somente o primeiro perfil quando recebe uma lista de membros. Portanto, o Monte Carlo atual não amostra diretamente todo o ensemble vertical do MAGI.

**Verificações realizadas**

Comando da suíte, executado no interpretador configurado pelo PyCharm:

```bash
PYTHONPATH=source MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -q -p no:cacheprovider tests/ MAGI/tests/
```

Resultado: **32 testes aprovados, 2 falhas e 34 avisos**. Os 18 testes de `tests/unit/` passaram; os outros 16 pertencem ao MAGI. Os 45 arquivos Python passaram pela análise sintática com `ast.parse`.

| Falha | Causa observada |
| --- | --- |
| `MAGI/tests/test_ensemble_export.py:117` | O teste tenta carregar `Ensemble` sem configurar data no `Environment`. RocketPy lança `ValueError`. |
| `MAGI/tests/test_rocketpy_exporter.py:111` | O teste chama `env.get_temperature`, inexistente na versão instalada; a interface disponível é `env.temperature(altitude)`. |

Essas duas falhas estão no preparo/uso da API pelos testes. Corrigi-las não resolveria os erros físicos descritos a seguir. Parte dos testes atuais aceita dados vazios como integração bem-sucedida, e o teste de densidade cobre apenas ar seco.

As reproduções adicionais usaram perfis matemáticos artificiais identificados como entradas de teste, arquivos temporários e atmosfera padrão escolhida explicitamente. Não houve busca de previsão meteorológica para alimentar simulações nem execução completa do notebook operacional. Foram consultadas referências primárias para as interfaces e equações mencionadas.

**Achados por prioridade**

P1 indica correção necessária antes de confiar no resultado do caminho afetado. P2 indica erro ou limitação de manutenção, contrato ou precisão que deve entrar na sequência de correções. As recomendações abaixo não foram aplicadas nesta análise.

1. **P1 — Motor do template produz impulso `NaN` e vazão de massa incorreta.**

   Referências: [motor.eng](../projects/00_Copy_This/motors/motor.eng), linha 3; [construtor do motor](../source/antares_fd/builders/motor.py), linha 27; [teste do motor](../tests/unit/test_motor_builder.py), linha 36.

   O `.eng` inclui `(0, 0)`, mas o leitor RocketPy já acrescenta esse ponto. Na versão instalada, a duplicidade contamina o valor inicial durante o tratamento da curva: `motor.total_impulse`, `motor.thrust(0)` e `motor.thrust(0.05)` resultaram em `NaN`; `motor.total_mass_flow_rate(1)` retornou zero. O objeto continua sendo construído e o teste atual passa.

   Em cópia temporária do mesmo arquivo, retirar somente o ponto redundante produziu impulso de **3.905 N·s**, empuxo de **750 N em 0,05 s** e vazão de aproximadamente **−0,8295 kg/s em 1 s**. No caso de demonstração com atmosfera padrão, isso mudou o apogeu ASL de aproximadamente **1.735,94 m para 1.859,91 m**, diferença de **123,97 m**. Esses números caracterizam o defeito do exemplo; não constituem previsão de um veículo real.

   Correção recomendada: adequar as entradas ao contrato do leitor; verificar tempos estritamente crescentes, finitude, integral do empuxo e evolução da massa antes de integrar o voo. Adicionar uma referência independente para a integral dessa curva linear. O contrato do leitor proíbe expressamente a presença do ponto inicial no arquivo. [Código oficial do leitor RocketPy](https://docs.rocketpy.org/en/latest/_modules/rocketpy/motors/motor.html).

2. **P1 — Monte Carlo perde componentes essenciais do foguete.**

   Referência: [monte_carlo.py](../projects/00_Copy_This/simulations/monte_carlo.py), linhas 45–50.

   Criar `StochasticRocket(rocket=flight.rocket, ...)` não registra automaticamente os componentes do foguete base. A reprodução com `create_object()` mostrou:

   | Componente | Foguete nominal | Foguete sorteado |
   | --- | --- | --- |
   | Motor | `SolidMotor` | `EmptyMotor` |
   | Superfícies aerodinâmicas | 2 | 0 |
   | Paraquedas | 2 | 0 |
   | Conjuntos de botões de trilho | 1 | 0 |

   Consequentemente, as amostras não representam o veículo configurado. Registrar explicitamente motor, superfícies, botões e paraquedas, preservando posições e propriedades mesmo quando não houver incerteza. O primeiro teste de aceitação deve exigir que incertezas nulas recuperem o modelo nominal. Essa necessidade também aparece no [código oficial de StochasticRocket](https://docs.rocketpy.org/en/latest/_modules/rocketpy/stochastic/stochastic_rocket.html).

3. **P1 — Dados sintéticos e datas reatribuídas são apresentados como previsão real.**

   Referências: [balthasar.py](../MAGI/balthasar.py), linhas 42–89 e 179–201; [environment.py](../source/antares_fd/builders/environment.py), linhas 68–83; [MAGI_App.py](../MAGI/MAGI_App.py), linhas 63–81.

   `fetch_operational_forecast()` lê `atmosfera_atual.csv`, gera 20 membros com ruído e retorna `is_real_ensemble=True`. Na reprodução, os 21 perfis incluíram membros sintéticos rotulados `source='gfs_ensemble'`, `data_type='forecast'` e idade zero. As funções de INMET, satélite, radiossonda e rodadas anteriores apenas imprimem mensagens; não consultam essas fontes.

   Informar uma data futura somente substitui `valid_time_utc`; não busca, seleciona nem calcula o perfil desse instante. A latitude e a longitude do lançamento não são transmitidas ao carregador do cache. Assim, alterar projeto/local/data pode reutilizar a mesma atmosfera sem verificar sua representatividade.

   Correção: carregar dados com local, emissão e validade verificáveis; manter o instante original; rejeitar datas fora da cobertura; identificar explicitamente ensembles sintéticos e seus métodos/sementes. Funções ainda não implementadas devem informar indisponibilidade em vez de declarar consulta concluída.

4. **P1 — Leitura de cache antigo renova artificialmente sua validade.**

   Referência: [state_manager.py](../MAGI/state_manager.py), linhas 57–71.

   Um cache com 8 horas, avaliado com `is_online=False` e `fetch_success=False`, passa para `DEGRADED_DATA`. Mesmo assim, o código sobrescreve `last_successful_update_utc` com o instante atual e zera a idade. A próxima consulta o classifica como `CACHED_FORECAST` recente. Além disso, o chamador fornece sucesso/conectividade como constantes, independentemente da origem efetiva.

   Atualizar a emissão somente após aquisição efetiva e validada. Separar instante de acesso, instante de download, emissão do provedor e validade meteorológica. Testar transições com relógio controlado, inclusive sem cache e sem histórico.

5. **P1 — Domínio atmosférico e diagnóstico físico não bloqueiam dados inadequados.**

   Referências: [casper.py](../MAGI/casper.py), linhas 168–193, 209–242; [environment.py](../source/antares_fd/builders/environment.py), linhas 95–121.

   Embora o interpolador use `extrapolate=False`, o código preenche manualmente os níveis acima do topo observado com vento/temperatura constantes e pressão estimada. Mantém a marca `OUT_OF_VERTICAL_RANGE`, mas o adaptador do RocketPy filtra apenas `NaN`, aceitando esses valores. Com observações até 1.000 m AGL, a reprodução injetou valores finitos também acima desse limite.

   Abaixo do primeiro nível, pressão constante é usada em várias alturas: isso implica `dp/dz=0` e viola o equilíbrio hidrostático para densidade positiva. O diagnóstico imprime falha, mas não registra reprovação no estado nem impede exportação. Se o MAGI não retorna perfil, o ambiente muda para atmosfera padrão com vento zero após um aviso.

   Definir políticas explícitas de cobertura e de modelos aproximados; propagá-las até o consumidor. Não confundir uma extensão atmosférica aprovada com interpolação de dados observados. Validar finitude, pressão/temperatura positivas, ordenação vertical e resultado hidrostático. Interpolação com lacunas parciais também merece tratamento explícito: uma única amostra `NaN` em uma variável atualmente causa `ValueError` no PCHIP, apesar da verificação `notna().any()`.

6. **P1 — Perfil sem vento/cisalhamento válidos recebe 100/100.**

   Referência: [scoring.py](../MAGI/scoring.py), linhas 22–44 e 95–100.

   A reprodução com um membro contendo somente `NaN` nessas grandezas e climatologia válida retornou **`(100.0, 'Highly Favourable')`**. Os máximos permanecem zero e a ausência de outros membros deixa o espalhamento em zero. Atividade meteorológica e qualidade ainda somam 20 pontos fixos, sem medição correspondente.

   Exigir cobertura válida mínima e devolver resultado indisponível quando faltarem entradas. Critérios, pesos e limites devem ter calibração e justificativa documentadas. O estado de qualidade precisa participar efetivamente da avaliação.

7. **P1 — Média e percentis da velocidade do vento são calculados incorretamente.**

   Referência: [melchior.py](../MAGI/melchior.py), linhas 212–243.

   A norma do vetor médio não é a média da velocidade. Da mesma forma, a norma dos percentis marginais de `u` e `v` não é o percentil da velocidade. Reproduções em uma mesma altitude:

   | Entradas de vento | Resultado atual | Resultado esperado para velocidade |
   | --- | --- | --- |
   | `u = +10, −10 m/s`, `v = 0` | Média e mediana = 0 m/s | Média e mediana = 10 m/s |
   | `u = −10, −20 m/s`, `v = 0` | P5 = 19,5; P95 = 10,5 m/s | P5 = 10,5; P95 = 19,5 m/s |

   O bloco que tenta consertar P5 procura o sufixo `p05`, mas a geração usa `p5`. Trocar percentis entre si também não corrige a definição estatística.

   Calcular `sqrt(u²+v²)` para cada amostra e só depois obter média, mediana e quantis. Preservar o vetor médio como uma grandeza distinta, com nome e interpretação próprios.

8. **P1 — Regularização da covariância mistura escalas físicas e pode gerar umidade impossível.**

   Referências: [melchior.py](../MAGI/melchior.py), linhas 261–290; [casper.py](../MAGI/casper.py), linhas 263–299.

   `LedoitWolf` é aplicado diretamente a `[u, v, T, q]`, com unidades e escalas muito diferentes. O estimador acrescenta um termo proporcional à identidade baseado no traço da covariância; nessa aplicação, a estimativa passa a depender fortemente da unidade usada para cada variável. [Definição oficial do estimador](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html).

   Em 40 perfis artificiais, com desvio de entrada de `q` igual a 0,0005 kg/kg, a rotina estimou aproximadamente **1,162 kg/kg** para o desvio da umidade. Apenas representar a umidade em g/kg antes da estimação e converter o resultado de volta mudou esse valor para aproximadamente **0,00126 kg/kg**. Isso evidencia a dependência de escala; a segunda representação não é apresentada como solução física validada.

   Recomenda-se regularizar variáveis adimensionais ou adotar um alvo de covariância com escalas fisicamente justificadas, restaurando depois as unidades. A matriz também deve corresponder exatamente à grade e à ordem dos componentes. Hoje, `isin(altitude_grid)` exige coincidência exata e pode eliminar todo o histórico ou retornar matriz com dimensão incompleta.

   O gerador limita temperatura/umidade por recorte e satura RH, mas pode conservar no campo `q` um valor incompatível com a RH/densidade exportada. Preservar relações termodinâmicas após perturbação e rejeitar covariância materialmente inválida; tolerar autovalores negativos somente dentro de um limite documentado de arredondamento. Distinguir ainda variabilidade climatológica de erro de previsão: elas não são automaticamente a mesma incerteza.

9. **P1 — Cenário de separação altera a massa desde o lançamento.**

   Referência: [separation_at_main_opening.py](../projects/00_Copy_This/simulations/separation_at_main_opening.py), linhas 27–36.

   O código subtrai 2 kg antes de construir o foguete e executar o voo. Não há evento de separação na abertura do principal; subida, apogeu e descida usam a massa reduzida, mantendo CG e inércia originais. Logo, o cenário não executa o fenômeno anunciado pelo nome.

   Modelar a transição no evento correto, com massa, CG, tensor de inércia e estado de cada corpo consistentes. Os dados de separação devem vir do YAML. Em [only_reefing.py](../projects/00_Copy_This/simulations/only_reefing.py), linha 38, a fração de 15% também é uma hipótese física embutida e deve ser uma entrada fundamentada, não um valor universal.

10. **P2 — Umidade específica é confundida com razão de mistura.**

    Referência: [casper.py](../MAGI/casper.py), linhas 56–77.

    A função denominada `calc_specific_humidity` calcula `r = 0.622 e / (p − e)`, que é razão de mistura. Para umidade específica, `q = r/(1+r) = 0.622 e / (p − 0.378 e)`, usando a mesma unidade para ambas as pressões. A inversa correspondente também precisa ser corrigida. [Relação entre as grandezas no MetPy/Unidata](https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.specific_humidity_from_mixing_ratio.html).

    Para 100.000 Pa, 300 K e 80% RH, usando a mesma pressão de saturação do código: resultado atual **0,01809956**, esperado **0,01777779 kg/kg**; erro relativo de **1,81% em q**. Nesse caso, a diferença na densidade contra a mistura ideal é aproximadamente 0,020%, menor mas sistemática. Não confundir a magnitude desses dois erros.

    Centralizar as equações e constantes usadas também por MELCHIOR e pelo gerador hipsométrico. Acrescentar testes com ar úmido, valores de referência independentes e conversão de ida/volta. O adaptador de atmosfera do RocketPy atualmente transmite P/T/u/v, não a densidade úmida calculada pelo MAGI; essa escolha física também precisa ser explicitada e validada.

11. **P1 — Configurações ausentes ou não suportadas podem mudar silenciosamente o modelo.**

    Referências: [vehicle.py](../source/antares_fd/builders/vehicle.py), linhas 5–27 e 134–160; [runner.py](../source/antares_fd/simulation/runner.py), linhas 23–31; [loader.py](../source/antares_fd/config/loader.py), linhas 56–59.

    Reprodução: configuração de arrasto vazia ou `source_type` desconhecido retorna `Cd=0`. Um tipo de aleta desconhecido é ignorado, reduzindo as superfícies de 2 para 1. `simulation_config` é recebido, mas não transmite `rtol`, `atol`, `max_time_step`, `max_time`, eventos de término ou outras opções ao integrador. Um pedido de `max_time=1` não limitou o voo de demonstração.

    A extrapolação de arrasto declarada `forbidden` no YAML também não é imposta: a curva de exemplo termina em Mach 1,6, mas a consulta em Mach 5 retorna `Cd=0,65`. Campos como alinhamentos, excentricidades, dados de aerofólio, condições iniciais e sentido do gatilho de altitude não são integralmente implementados. Alguns campos são descritos como futuros; habilitá-los deve ser rejeitado ou explicitamente sinalizado.

    Validar esquema, tipos, valores finitos, domínios e combinações de recursos antes da construção. Verificar também que a raiz do YAML é um mapeamento. Preservar documentação de extensões planejadas, indicando o estado de suporte. Não é correto afirmar que toda entrada negativa é aceita: massa negativa, por exemplo, foi rejeitada pelo RocketPy neste ambiente; o problema é a ausência de um contrato completo e consistente na camada do projeto.

12. **P1 — Exportador NetCDF perde o alinhamento físico entre membros.**

    Referência: [magi/casper/export/rocketpy.py](../MAGI/magi/casper/export/rocketpy.py), linhas 110–165.

    Os níveis de pressão são definidos pelo primeiro membro; os demais são colocados nessas coordenadas pela posição das linhas, depois de `dropna` independente. Inverter a ordem de um segundo perfil foi aceito: o nível de 988,68 hPa recebeu a altura que pertencia a aproximadamente 892,37 hPa. Perfis com quantidades diferentes de linhas podem falhar por dimensão, e perfis do mesmo tamanho podem ser exportados incorretamente sem erro.

    Alinhar explicitamente por pressão, membro e instante antes de construir o cubo. Verificar coordenadas únicas/estritamente monótonas, correspondência entre variáveis e ausência de valores inválidos. A verificação atual de monotonicidade do índice aceita pressões repetidas.

    Há outras limitações relevantes: a chamada que promete evolução temporal repete exatamente o mesmo perfil em todos os horários e nove posições espaciais; `horizon_hours=168` não cria uma previsão de sete dias. O modelo de persistência/homogeneidade, se desejado, precisa ser identificado. Coordenadas geográficas recebem valores fixos se ausentes. `tz_localize(None)` remove o fuso sem converter antes para UTC; entradas com deslocamento diferente de zero mudam de instante. Exportadores também perdem indicadores de qualidade e o método específico de geração.

13. **P1 — Gráficos operacionais incluem previsões, frequências e imagens artificiais sem identificação suficiente.**

    Referências: [visuals.py](../MAGI/visuals.py), linhas 429–435, 504–505, 541–543, 597, 632–633, 737–764 e 870–893.

    O gráfico de vento das próximas 24 horas usa seno e tendência linear sobre um valor do perfil. As rosas históricas usam amostras normais artificiais ao redor da direção média. O espalhamento exibido é fixo em `±1.5 m/s`. Fontes, idade e qualidade são textos fixos. Uma textura aleatória de nuvens ativa `has_sat=True` e o título de camada de satélite. O rodapé declara `Validation: PASSED` sem ligação com aprovação física dos dados.

    Esses comportamentos existem no caminho operacional, além do modo de exemplo. As figuras podem, portanto, comunicar evidência que não foi adquirida ou calculada como a legenda afirma. Manter gráficos demonstrativos em modo explicitamente identificado e usar dados indisponíveis quando não houver fonte; derivar legendas e estado dos metadados reais. Separar validação de layout de validação científica. O código visual também redefine o gerador aleatório global, interferindo em reproduções estocásticas feitas posteriormente no mesmo processo.

14. **P2 — Resumos e exportações têm contratos ambíguos.**

    Referências: [results.py](../source/antares_fd/simulation/results.py), linhas 12, 19–20 e 24–63; [orchestrator.py](../source/antares_fd/simulation/orchestrator.py), linhas 5 e 26–27.

    `flight.apogee` é apresentado sem distinguir ASL de AGL. O horário do gatilho do paraquedas é impresso como implantação, sem somar `lag`: no exemplo, o drogue foi reportado em 16,99 s e a inflação começou em 17,99 s. O argumento `export_kml` não é utilizado; imprimir o resumo controla também as exportações. Os mesmos nomes de arquivos podem sobrescrever execuções e falhas de exportação são apenas impressas.

    Separar cálculo, relatório e escrita. Identificar referência de altitude, gatilho e inflação; retornar estado dos produtos gerados. Registrar por execução configuração efetiva, hashes dos dados, commit, versões, semente e parâmetros numéricos. Manifestos antigos existem, mas a implementação atual não os gera.

15. **P2 — Notebook, script e instalação não formam uma interface reproduzível.**

    Referências: [MAGI_App.py](../MAGI/MAGI_App.py), linhas 26, 156, 172, 183, 225–245; [build_notebook.py](../MAGI/build_notebook.py), linha 1; [requirements.txt](../requirements.txt).

    `IPython` e `nbformat` não estão instalados no ambiente examinado nem declarados em `requirements.txt`; são importados pelo aplicativo e pelo gerador de notebook. Dependências diretamente utilizadas também dependem parcialmente de instalações transitivas. As versões não são fixadas para reprodução.

    A inspeção das células confirmou que o notebook chama os panoramas, enquanto o `.py` comenta essas chamadas. A célula de pior dia e o script usam `__file__`; em um kernel Jupyter normal esse nome não existe. No script, há mensagens de painel gerado com a geração comentada. A chamada de testes por `os.system` ignora o retorno e depende do diretório corrente. O filtro global de warnings oculta avisos científicos e de compatibilidade.

    Recomenda-se um módulo de aplicação comum e interfaces finas de script/notebook; ponto de entrada explícito; configuração de caminhos independente do diretório corrente; dependências declaradas por funcionalidade; ambiente de referência reproduzível. O notebook deve continuar disponível como interface documentada.

**Pontos que exigem revisão técnica adicional**

- O referencial longitudinal é descrito como `x` na documentação; o RocketPy usa seu terceiro eixo para o eixo longitudinal do tensor de inércia. O template contém `I11=0,05` e `I22=I33=4`. Isso merece verificar a correspondência dos eixos com os dados CAD/medidos, mas não autoriza trocar componentes automaticamente sem conhecer sua origem. A convenção está descrita na [API oficial de Rocket](https://docs.rocketpy.org/en/develop/reference/classes/Rocket.html).
- Os dados de demonstração já possuem massas, inércias, curva de empuxo e recuperação preenchidas; há campos como `method: measured` sem proveniência. Separar claramente exemplo executável de configuração de engenharia a preencher. Não tomar esses valores como dados aprovados do veículo.
- Os modelos de camada superficial, pressão acima do topo, geração estocástica, correlação vertical, severidade e recuperação precisam registrar hipóteses, domínio de validade e referências. Testar o código não substitui essa revisão.
- A validade dos arquivos históricos de `results/` não foi reavaliada individualmente. Os manifestos consultados apontam commits diferentes e `dirty_worktree: true`; os defeitos do código atual não devem ser atribuídos retroativamente a todas as execuções antigas sem reconstruir o respectivo ambiente/configuração.

**Arquivos redundantes e organização**

| Arquivos | Evidência | Ação recomendada |
| --- | --- | --- |
| `MAGI/figures/.ipynb_checkpoints/` | 25 PNGs versionados; 22 têm conteúdo SHA-256 idêntico a arquivos fora dessa pasta, somando 14.363.097 bytes, aproximadamente 13,70 MiB. | Retirar os 22 duplicados depois de conferir referências e ignorar checkpoints futuros. Preservar os outros 3 até verificar se contêm informação única. |
| Figuras datadas e `*_latest.png` | Há duplicatas adicionais; nomes `latest` podem servir a documentação ou interfaces. | Escolher figuras de referência e política de retenção. Não eliminar todos os gráficos: alguns documentam resultados e evolução. |
| `source/.keep`, `source/antares_fd/.keep`, `tests/.keep` | As pastas já contêm arquivos versionados. | Placeholders dispensáveis. Os `.keep` de diretórios ainda vazios têm utilidade estrutural. |
| `projects/00_Copy_This/README.md` | Contém somente uma quebra de linha. | Preencher com instruções do template ou encaminhar ao guia principal. |
| `MAGI/contexto_atual_magi.md` | Cerca de 264 kB de contexto e grandes cópias de versões de código; descreve caminhos e estados antigos. | Preservar decisões e justificativas, substituindo cópias integrais por referências a versões no Git. |
| `.idea/` versionado | Já está listado no `.gitignore`, que não remove arquivos previamente rastreados. | Decidir quais configurações de IDE são compartilhadas pela equipe; retirar somente estado local desnecessário. |
| `compute_covariance` em `MAGI/magi/casper/ensemble/eof.py` | Função contém apenas `pass`; a busca no projeto encontrou somente sua definição. | Implementar o contrato ou retirar a função não utilizada. Isso não torna o arquivo inteiro dispensável: `apply_eof_perturbation` é utilizado. |
| `results/` local | Aproximadamente 5,6 GiB em disco; o conteúdo versionado soma cerca de 4,8 MB. Um `mc_sim.inputs.txt` ocupa cerca de 3,4 GiB e está ignorado pelo Git. | Arquivar/comprimir registros com verificação de integridade e retenção definida. Não tratar logs/entradas únicas como lixo. |

Não foi identificado um módulo Python inteiro cuja remoção incondicional seja justificada. `__init__.py`, exportadores e módulos usados por interfaces/testes têm função; ausência de chamada no caminho nominal não os torna inúteis. Importações sem uso e comentários especulativos podem ser limpos pontualmente, mantendo as explicações das equações e decisões.

A documentação também precisa ser atualizada: `MAGI/README.md` ainda diz que o diretório está reservado para implementação futura; o guia usa `Projects/` quando a árvore é `projects/`, o que falha em sistemas sensíveis a maiúsculas; o README principal termina com bloco de código não fechado. Esses são ajustes pequenos e úteis, separados da preservação da documentação técnica.

**Otimizações compatíveis com legibilidade e rigor**

| Oportunidade | Benefício e condição de preservação |
| --- | --- |
| `LedoitWolf(store_precision=False)` | A aplicação usa a covariância, mas não sua pseudoinversa. Evita calculá-la. Em verificação controlada, a covariância foi exatamente igual com as duas opções. Aplicar depois de resolver a escala física da estimação. |
| Exportar NetCDF em blocos | Para 21 membros × 2.881 instantes × 61 níveis × 3 × 3 posições, quatro arrays `float64` alocam **1.062.881.568 bytes**, antes de cópias/serialização. Evitar materializar simultaneamente todo o cubo. Corrigir primeiro a semântica da repetição temporal. |
| Broadcasting em vez de atribuições por latitude/longitude/tempo | Reduz sobrecarga Python preservando índices e valores. Manter nomes explícitos para as dimensões e testes de equivalência. Não reduzir para `float32` apenas para economizar memória. |
| Reutilizar perfis históricos já alinhados | Estatísticas e covariância podem partir da mesma grade validada, reduzindo interpolações repetidas e divergências. Calcular conjuntos de quantis em uma operação sobre as amostras corretas. |
| Preparar a transformação da covariância uma vez | Calcular a raiz dos autovalores fora do laço de membros; usar um gerador aleatório explícito por execução. Preservar reprodutibilidade e critérios de aceitação estatística. |
| Separar visualização e aquisição de dados do núcleo físico | `casper.py` importa plotting no caminho dos cálculos. Imports opcionais e módulos menores reduzem dependências de execução e simplificam testes. Para imagens de mapas, buffers em memória evitam arquivos temporários com nomes concorrentes. |
| Saídas opcionais independentes | Evitar mapas/rede quando o objetivo é calcular métricas. Preservar os relatórios existentes por opções explícitas, com estado de sucesso/falha. |
| Empacotamento e configuração tipada | Um pacote instalável e esquemas claros eliminam ajustes repetidos de `sys.path`, melhoram inspeções da IDE e tornam recursos suportados visíveis aos mantenedores. Não requer abstrair ou esconder as equações. |

Essas são oportunidades identificadas, não ganhos de velocidade medidos em toda a aplicação. Não há evidência que justifique GPU, JIT, menor precisão, tolerâncias relaxadas ou camadas adicionais de abstração neste momento.

**Sequência recomendada de trabalho e critérios de aceitação**

1. Corrigir motor e montagem do Monte Carlo; exigir impulso/massa finitos, conservação de massa no motor e equivalência com o nominal quando a incerteza é zero.
2. Corrigir procedência, validade temporal, cobertura atmosférica, estado de cache e dados ausentes; exigir que indisponibilidade não produza aprovação nem previsão fictícia.
3. Corrigir estatísticas de vento, umidade, covariância, alinhamento NetCDF e eventos de separação; usar casos de referência independentes e verificar unidades e referenciais.
4. Tornar opções YAML efetivas ou rejeitadas, unificar as interfaces e recuperar rastreabilidade por execução; executar ambas as suítes em integração contínua.
5. Aplicar otimizações localizadas, medir tempo/memória e comparar resultados antes/depois. Limpar duplicatas documentadas preservando registros únicos.

Como sondagem de sensibilidade numérica, foram comparados dois voos do mesmo exemplo com atmosfera padrão e motor normalizado somente em arquivo temporário. O caso padrão atingiu 1.859,9099 m ASL; o caso com `rtol=1e-9`, `atol=1e-9` e `max_time_step=0.05` atingiu 1.859,9496 m ASL, diferença de aproximadamente 0,040 m. As soluções foram finitas, mas houve avisos da biblioteca. Uma comparação de dois ajustes em um único caso não demonstra convergência geral nem valida o modelo físico: uma campanha de verificação deve incluir refinamentos sucessivos, eventos de recuperação, ventos não nulos e métricas de interesse da equipe, com tolerâncias justificadas.

As reproduções desta análise ficaram em arquivos temporários (`/tmp/antares_audit_probes.py`, `/tmp/antares_audit_flight.py` e respectivos resultados). Nenhuma configuração operacional foi substituída por esses exemplos. A entrega permanente é este relatório, com causas, exemplos e critérios para orientar correções revisáveis.
