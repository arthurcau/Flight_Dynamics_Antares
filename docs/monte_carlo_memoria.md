# Monte Carlo de falha: redução de RAM e disco

## Diagnóstico e implementação

O orquestrador exportava as funções completas do RocketPy em cada registro de
entrada. Em 24 voos, isso gerou 345.800.866 bytes. Ao terminar, o RocketPy relia
essas entradas para `inputs_log`, somando esse volume ao restante da memória.
Também havia uma lista compartilhada que acumulava todas as trajetórias e era
copiada para o processo principal no final.

Mudanças em `source/antares_fd/simulation/monte_carlo_failure.py`:

- `include_function_data=False` na execução: preserva os valores escalares
  sorteados e todas as métricas de saída, eliminando a serialização repetida de
  funções e suas fontes.
- `TrajectoryStore`: mantém os caminhos com impactos extremos em X/Y e uma
  amostra uniforme de cinco trajetórias para o KML. São no máximo nove caminhos,
  independentemente do número de iterações, com todos os pontos e a precisão
  originais. As estatísticas, elipses e nuvens de impactos usam todos os voos.
- Amostragem incremental com gerador aleatório próprio; não consome a sequência
  de números aleatórios usada pela física. Uma trava protege as atualizações
  concorrentes no servidor do manager.
- O processo principal recebe apenas os caminhos selecionados. O KML recebe a
  amostra separadamente para não privilegiar os extremos na escolha aleatória.
- Remoção da construção duplicada de motor/foguete que não era utilizada e do
  contador compartilhado redundante; o progresso continua sendo mostrado pelo
  próprio RocketPy.
- O manifesto registra o modo de exportação e a contagem de caminhos recebidos
  e retidos.

O integrador, suas tolerâncias e as duas integrações do modelo de falha não foram
simplificados. O armazenamento dos caminhos para gráficos fica limitado; os
pequenos registros escalares ainda crescem proporcionalmente ao número de voos.

## Comparação medida, 24 iterações e 6 processos

| Medida | Antes | Depois |
|---|---:|---:|
| Tempo total do orquestrador | 23,98 s | 17,54 s |
| Tempo de `MonteCarlo.simulate` | 21,49 s | 15,27 s |
| Arquivo de entradas | 345.800.866 bytes | 90.806 bytes |
| Pico da soma dos working sets dos processos | 1.853,57 MiB | 1.011,53 MiB |
| Pico do processo principal | 533,96 MiB | 182,08 MiB |
| Trajetórias retidas para gráficos | 24 | 6 |

Nesse ensaio: aproximadamente 27% menos tempo total, 45% menos working set de
pico e 99,97% menos espaço para entradas. A diferença no número de trajetórias
retidas abaixo do limite de nove decorre de sobreposição entre extremos/amostra.

Método: Windows, Python 3.14.6, ambiente configurado no PyCharm; voos e exports
reais, atmosfera local fixa, downloads e gráficos substituídos por mocks. Os
processos foram monitorados a cada 0,1 s pelas APIs de memória do Windows. A soma
de working sets pode contar páginas compartilhadas mais de uma vez; foi usada a
mesma métrica nos dois casos. Sorteios paralelos diferem entre campanhas, e esta
comparação isolada não garante uma porcentagem de ganho em qualquer execução.
O benchmark mantém as distribuições angulares antigas nos dois casos para medir
o efeito das otimizações separadamente do ajuste da rampa.

Script reproduzível: `tests/integration/benchmark_monte_carlo_memory.py`.
O argumento `--source` permite comparar com uma cópia anterior do orquestrador.

## Precisão e conteúdo exportado

O teste de equivalência usa entradas físicas fixas e compara a exportação
completa com a compacta: exige igualdade das métricas e de todos os pontos X/Y/Z
retidos. Os testes do armazenamento verificam limites, extremos, concorrência e
independência do gerador aleatório. Há também teste real de inicialização de
processos e exportação no Windows, além do teste de falha silenciosa dos workers.

O arquivo compacto não contém funções RocketPy completas para reconstrução
autônoma dos objetos apenas a partir do log. Os dados nominais e o perfil
atmosférico continuam necessários para uma reconstrução integral. As métricas
de todos os voos continuam disponíveis. Os arquivos grandes de campanhas
anteriores não são apagados nem convertidos automaticamente.

## Ajuste solicitado anteriormente para a rampa

A configuração agora usa sorteio uniforme de inclinação entre 70° e 90° e
azimute entre 230° e 250°. Foi acrescentado suporte explícito a esses intervalos
nos dois orquestradores, com validação e testes dos sorteios. Configurações
antigas com `std` continuam aceitas. Essa mudança de entradas é independente da
otimização de armazenamento; preservou-se `num_simulations: 1500` já definido
pelo usuário.
