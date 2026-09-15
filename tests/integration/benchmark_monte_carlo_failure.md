# Estudo de desempenho — Monte Carlo de falha

Data: 2026-09-15. Nenhuma alteração no código de produção ou na configuração
física foi feita neste estudo. Os dois voos usados pelo cenário de falha foram
mantidos em todos os experimentos.

## Ambiente e método

- Intel Core i5-9400F: 6 núcleos / 6 processadores lógicos; Radeon RX 570.
- Python 3.14.6 do ambiente configurado no PyCharm.
- Configuração e arquivos de motor/aerodinâmica do projeto `neblina_1`.
- Atmosfera padrão local, altitude de 600 m; MAGI e geração dos gráficos
  substituídos apenas no benchmark. Os resultados não medem essas duas etapas.
- Resultados temporários isolados dos resultados de produção.
- Uma execução por cenário, com amostras aleatórias diferentes. Estes são
  ensaios exploratórios, não testes de equivalência numérica nem estimativas
  garantidas para campanhas de 250 casos.
- `total_seconds` inclui preparação, gerenciadores, simulações, leitura dos
  resultados e voo nominal de falha; exclui importações iniciais e montagem da
  fixture. `simulate_seconds` mede somente a chamada a `MonteCarlo.simulate`.

## Primeiro lote: 12 casos

| Workers | Exportação das funções | Chamada simulate | Tempo total | Entradas |
| --- | --- | ---: | ---: | ---: |
| 1 (serial) | Completa | 27,70 s | 30,48 s | 172,78 MB |
| 3 | Completa | 17,82 s | 21,04 s | 172,90 MB |
| 6 | Completa | 18,64 s | 21,50 s | 172,90 MB |
| 6 | Compacta | 16,67 s | 19,12 s | 45,23 KB |

Unidades decimais. A exportação compacta usa `include_function_data=False`.
No primeiro lote ela reduziu o tempo total observado em cerca de 11% e o tamanho
das entradas em mais de 99,9%. Isso não permite extrapolar o mesmo percentual
de tempo para qualquer campanha. Inicializar seis processos no Windows pesa
muito em um lote de apenas 12 casos.

Um perfil separado de dois casos encontrou aproximadamente 10,47 s em
`__evaluate_flight_inputs` e 2,91 s na rotina que executa os dois voos de cada
caso. Dentro da exportação, `dill` e a codificação dos objetos em texto dominam.
O profiler acrescenta custo e esses tempos não devem ser comparados diretamente
com os tempos sem instrumentação.

## Segundo lote: concorrência com outros processos Python

| Casos | Workers | Exportação | Tempo total | Entradas |
| ---: | ---: | --- | ---: | ---: |
| 12 | 1 | Compacta | 21,59 s | 45,22 KB |
| 60 | 6 | Completa | 100,11 s | 864,50 MB |
| 60 | 6 | Compacta | 44,16 s | 226,16 KB |

Todos os casos solicitados foram exportados. A diferença de 100 para 44 s é
promissora, mas a carga externa não foi controlada entre as execuções: não é
uma comprovação isolada de aceleração de 2,27 vezes. O tamanho dos arquivos
e o perfil da serialização reforçam a prioridade da exportação compacta.

## Recomendações, em ordem

1. **Reduzir a exportação repetida de funções.** Testar a opção compacta em
   produção e preservar separadamente a configuração, o perfil atmosférico e
   as entradas aleatórias necessárias para reproduzir cada caso. A opção não
   modifica o integrador nem as métricas de saída, mas impede restaurar
   integralmente os objetos apenas a partir do arquivo de entradas compacto.
2. **Configurar workers conforme o tamanho da campanha.** O código já usa os
   seis disponíveis. Na versão instalada, RocketPy limita `n_workers` ao número
   de CPUs. Para lotes pequenos, três ficaram próximos de seis; para campanhas
   grandes, manter seis como candidato e medir com a máquina livre. Não criar
   outro conjunto de processos dentro de cada worker: os casos independentes
   já oferecem trabalho para todos os núcleos.
3. **Reduzir o que é enviado na inicialização dos workers.** O método local
   substituído captura um método ligado a `mc`, que referencia os modelos e o
   voo nominal. Avaliar uma implementação em nível de módulo/classe e uma
   inicialização por worker, com configurações menores. Ganho ainda não medido.
4. **Remover construções sem uso.** `nominal_motor` e `nominal_rocket` são
   construídos no início, mas não utilizados depois; outro motor/foguete é
   criado para a simulação. É um custo fixo, provavelmente secundário.
5. **Diminuir comunicação de progresso e trajetórias.** Já existe progresso
   nativo no RocketPy. O contador adicional usa chamadas remotas e conta casos
   iniciados, não concluídos. Avaliar remover essa duplicação e armazenar
   trajetórias em arquivos por worker ou transferi-las em lotes. Reduzir pontos
   apenas da representação gráfica, preservando solução e métricas completas.
6. **Reutilizar a consulta meteorológica quando os parâmetros coincidirem.**
   Perfil nominal e ensemble entram separadamente no MAGI. Verificar equivalência
   de data, janela e membro antes de compartilhar os dados; não escolher outro
   perfil para economizar tempo. O custo de rede não foi medido.

As duas trajetórias da separação permanecem necessárias. Compartilhar o trecho
anterior à separação só é uma otimização se houver cálculo duplicado desse trecho;
o segundo `Flight` atual já recebe `initial_solution` a partir de 200 m. Não há
motivo para excluir um ramo físico em nome do desempenho.

## GPU e opções numéricas

O caminho instalado usa `Flight` com LSODA/SciPy e funções Python/NumPy na CPU.
Não há um parâmetro deste fluxo para executar os voos na RX 570. Portar exigiria
reescrever o cálculo em lotes para um backend de GPU, incluindo eventos e
paraquedas, e validar novamente o modelo. Trocar apenas os arrays por arrays
de GPU não transfere automaticamente o integrador e as funções do RocketPy.
Para esta campanha, a primeira prioridade é a exportação e o custo dos processos.

Tolerâncias, integrador e frequência dos sensores podem afetar tempo e resultados.
Só devem ser ajustados com comparação das mesmas entradas, incluindo apogeu,
impacto e eventos da separação. A versão instalada de `__run_single_simulation`
não repassa `rtol`, `atol` ou `ode_solver` do voo nominal; mudar apenas esse voo
não garante que a campanha use esses ajustes.

Também é necessário controlar as sementes por caso antes de comparar precisão:
o código chama `np.random.seed(42)`, mas o caminho paralelo instalado cria
`SeedSequence()` sem essa semente. Assim, o texto `Seed=42` não assegura amostras
idênticas entre execuções ou números diferentes de workers.

## Artefatos e reprodução

- `benchmark_monte_carlo_failure.py`: executável diretamente com o Python do projeto.
- Sem argumentos: lote pequeno e perfil de dois casos.
- `--large`: 12 casos seriais compactos, 60 completos e 60 compactos com seis workers.
- `.json`, `.large.json` e `.profile.txt`: medições correspondentes.

Durante o segundo lote foram observados outros processos Python ativos e CPU
em 100%. Os resultados desse lote precisam ser tratados como medições sob
concorrência, sem atribuir toda a diferença à opção de exportação.

Referências oficiais:

- [MonteCarlo: workers e opções de exportação](https://docs.rocketpy.org/en/latest/reference/classes/monte_carlo/monte_carlo.html)
- [Flight: integradores e parâmetros](https://docs.rocketpy.org/en/latest/_modules/rocketpy/simulation/flight.html)
- [SciPy: LSODA e demais integradores](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
