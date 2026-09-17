# Estudo das incertezas do Monte Carlo — Neblina 1

Data: 15/09/2026. Escopo: `projects/neblina_1/config/monte_carlo.yaml`, configurações nominais e ligação com `source/antares_fd/simulation/monte_carlo_failure.py`. O Monte Carlo convencional tem o mesmo mapeamento inicial de incertezas.

**Atualização de 16/09/2026:** a equipe informou que não controla a rampa.
As recomendações condicionais de baixa dispersão angular abaixo não se aplicam
ao lançamento. Foi adotada distribuição uniforme de 70° a 90° para inclinação
e de 230° a 250° para azimute (±10° em torno do nominal), com suporte nos dois
orquestradores. As tabelas seguintes registram a configuração original estudada.

## Conclusão

O YAML mistura dispersões grandes de montagem com hipóteses muito exigentes de medição. A inclinação e o azimute podem ser reduzidos bastante **se a rampa for medida e conferida**. Massa, centro de massa e densidade não devem ser considerados conhecidos com alta precisão apenas porque o foguete é universitário.

Há também uma limitação anterior à escolha dos números: muitos campos do YAML não chegam aos objetos estocásticos. Alterá-los hoje não altera os sorteios.

As recomendações abaixo são **hipóteses de engenharia para um cenário de baixa incerteza**, condicionadas às verificações indicadas. Não são tolerâncias medidas do Neblina, limites certificados, nem valores prescritos pelas fontes consultadas. Na ausência de registros da equipe, não existe um mínimo estatisticamente demonstrado. Este estudo não altera a configuração executada.

## 1. Como interpretar os valores

Nos campos efetivamente ligados ao código, `std` representa um desvio padrão, σ. O código usa distribuições normais: aproximadamente 68% dos sorteios ficam em nominal ±σ e 95,45% em nominal ±2σ. Essas faixas não são limites rígidos; sorteios fora delas são esperados. O comportamento foi confirmado no código instalado de `StochasticModel` e na [documentação do RocketPy](https://docs.rocketpy.org/en/latest/user/stochastic.html).

- `std: 0.01` na massa significa 0,01 kg = 10 g, não 1%.
- `std: 0.05` em `total_impulse_scale` significa 5% do impulso nominal: o adaptador faz essa conversão.
- `std: 0.1` nos fatores de arrasto significa σ de 10% na escala da curva inteira, aproximadamente ±20% em 95% dos sorteios.
- `factor_std: 0.2` no vento significa σ de 20% em um multiplicador de cada componente, quando esse valor é usado.

Tolerância máxima de fabricação não é automaticamente σ. Se só conhecemos um intervalo ±a e adotamos distribuição uniforme, σ = a/√3; uma faixa normal de aproximadamente 95% corresponde a cerca de 2σ. Essa conversão segue o [NIST, avaliação tipo B](https://physics.nist.gov/cuu/Uncertainty/typeb.html). A resolução do instrumento, isoladamente, não cobre calibração, repetibilidade, montagem ou alterações após a medição.

## 2. O que realmente varia hoje

Referências de implementação: `monte_carlo_failure.py`, linhas 62–95, 101–112 e 138–151.

| Grandeza | Nominal | σ configurado | Faixa aproximada de 95% / efeito real |
|---|---:|---:|---|
| Inclinação da rampa | 80° | 5° | 70° a 90°; a normal ainda permite valores acima de 90° |
| Azimute da rampa | 240° | 10° | 220° a 260° |
| Elevação do terreno | 495 m | 5 m | 485 a 505 m |
| Impulso total | ≈9.966 N·s | 5%, ≈498 N·s | ≈8.970 a 10.963 N·s |
| Massa sem motor | 21,186 kg | 0,010 kg | 21,166 a 21,206 kg; σ relativo de apenas 0,047% |
| Fator de arrasto sem propulsão | 1 | 0,10 | 0,80 a 1,20 vezes a curva nominal |
| Fator de arrasto com propulsão | 1 | 0,10 | 0,80 a 1,20 vezes a curva nominal |
| Fator de vento X | 1 | 0,20, como alternativa ao MAGI | 0,60 a 1,40 somente quando a alternativa do YAML é usada |
| Fator de vento Y | 1 | 0,20, como alternativa ao MAGI | Idem; cada componente recebe seu próprio fator |

O impulso acima foi estimado por integração trapezoidal dos pontos do arquivo `Yaripo_teste_est_2_2.eng`, coerente com a interpolação linear configurada; não foi obtido executando uma campanha.

### Vento: o YAML não conta toda a história

O código obtém σ de cada componente entre os perfis MAGI a **1.000 m de altitude**, divide esse número por `3.0` e o usa como σ de um fator adimensional. Havendo σ positivo, esse valor substitui o `factor_std` do YAML, separadamente por componente.

No log fornecido, σX ≈0,50 m/s e σY ≈0,06 m/s resultam em fatores com σ ≈16,7% e ≈2%. Logo, a dispersão relativa em Y fica aproximadamente dez vezes menor que os 20% escritos no YAML. Esses números pertencem àquela execução e não são constantes do modelo.

Problemas a resolver antes de reduzir o vento:

1. `wind_velocity_x.std: 1.0` é ignorado: nenhum ruído aditivo de 1 m/s é aplicado.
2. A divisão por `3.0` não declara nem deriva uma velocidade de referência. Não há conversão física justificada no adaptador entre a dispersão em m/s e o fator adimensional.
3. Um fator multiplicativo dá dispersão nula onde a componente nominal é zero. Também impõe a mesma escala a todas as alturas daquela componente.
4. O conjunto de 13 perfis vem de deslocamentos temporais, interpolados da mesma previsão horária (`MAGI/balthasar.py`, a partir da linha 200). Não são 13 previsões independentes de erro meteorológico.
5. A dispersão em uma única altitude não caracteriza a incerteza de todo o perfil, nem rajadas ou erro sistemático da previsão.

**Recomendação:** manter 20% como hipótese inicial de fator, sem afirmar que é suficiente. Estudar adicionalmente um erro aditivo por componente com σ de 1 m/s, já sugerido pelo próprio YAML, como cenário de sensibilidade. Isso exige implementação e validação meteorológica; o valor não é um limite inferior universal. Dados locais e diferenças previsão–observação devem definir a distribuição final. A condição de equipe universitária não reduz a incerteza da atmosfera.

## 3. Valores baixos propostos para os parâmetros ativos

Todos os valores abaixo são σ, não tolerâncias máximas.

| Campo | Atual | Proposta provisória | Condição para defender a proposta |
|---|---:|---:|---|
| `flight.inclination.std` | 5° | **0,5°** | Medir a rampa carregada com inclinômetro conferido; verificar flexão e repetibilidade. Faixa de 95%: 79° a 81° |
| `flight.heading.std` | 10° | **2°** | Referência de azimute conferida, correção entre norte magnético e verdadeiro quando aplicável, sem interferência metálica. Faixa: 236° a 244° |
| `environment.elevation.std` | 5 m | **5 m** | Manter com localização comum; 2 m só com levantamento/referência altimétrica melhor e datum compatível |
| `motor.total_impulse_scale.std` | 5% | **5%** | Manter como hipótese baixa provisória com curva de ensaio representativa. Poucos ensaios não demonstram repetibilidade de 5%; comparar também cenário de 10% |
| `vehicle.mass.std` | 10 g | **50 g** | Pesagem final sem motor, com todos os componentes de voo e montagem controlada. Faixa: 21,086 a 21,286 kg. Manter 10 g somente se a medição completa sustentar isso |
| `vehicle.power_off_drag_factor.std` | 10% | **10%** | Hipótese baixa para curva aerodinâmica nominal sem validação em voo; comparar também 20% |
| `vehicle.power_on_drag_factor.std` | 10% | **10%** | Mesmo critério; investigar correlação com o arrasto sem propulsão |
| `environment.wind_velocity_x.factor_std` | 20% | **20%, provisório** | Depende da revisão do tratamento do MAGI e da validação do perfil |
| `environment.wind_velocity_y.factor_std` | 20% | **20%, provisório** | Mesmo critério |

As propostas de 0,5° e 2° pressupõem um procedimento simples de medição; não são garantidas pela graduação de uma régua ou aplicativo. Os 50 g da massa são uma hipótese para o conjunto montado, não uma exigência de menor precisão da balança. Dados reais podem justificar números menores ou exigir maiores.

## 4. Campos presentes que atualmente são ignorados

As faixas ±2σ desta seção mostram **o que o YAML descreveria caso os campos fossem conectados ao sorteio**. Hoje essas dispersões não são aplicadas. As propostas são orçamentos preliminares de incerteza de propriedades medidas; não são instruções de fabricação nem alterações de projeto do motor.

### Ambiente e veículo

| Campo | σ atual | ±2σ declarado | Avaliação / σ proposto condicionado |
|---|---:|---:|---|
| `environment.wind_velocity_x.std` | 1 m/s | ±2 m/s | Estudar como erro aditivo; precisa de implementação e dados meteorológicos |
| `environment.latitude.std` | 0,0001° | ≈±22,3 m | σ de ≈11,1 m. Com posição de lançamento conferida, considerar 0,00005° (≈5,6 m) |
| `environment.longitude.std` | 0,0001° | ≈±20,7 m | σ de ≈10,3 m nessa latitude. Com posição conferida, considerar 0,00005° (≈5,2 m) |
| `vehicle.radius.std` | 0,2 mm | ±0,4 mm | Manter 0,2 mm se houver medição em várias posições e consideração de ovalização |
| `vehicle.center_of_mass_without_motor.std` | 1 mm | ±2 mm | Usar 3 mm como hipótese inicial de balanceamento repetido; 1 mm exige comprovação |

Incerteza de posição absoluta afeta o posicionamento geográfico da área de impacto. Deve-se distinguir esse deslocamento da dispersão relativa à rampa; variar latitude/longitude para refazer o ambiente não substitui necessariamente esse tratamento.

### Motor

| Campo | σ atual | ±2σ declarado | Avaliação / σ proposto condicionado |
|---|---:|---:|---|
| `burn_start_time` | 0,1 s | ±0,2 s | Definir primeiro a referência temporal. Se t=0 é a ignição real, manter início fixo e variar a duração; atraso após comando deve usar distribuição não negativa |
| `burn_out_time` | 0,1 s | ±0,2 s | Preservar como hipótese baixa de duração, dependente de ensaios repetidos; a curva termina em 6,586 s |
| `dry_mass` | 0,1 kg | ±0,2 kg | 0,02 kg com pesagem final do motor seco e controle de montagem; nominal 8,416 kg |
| `dry_inertia_11` | 0,01 kg·m² | ±0,02 kg·m² | Atual ≈1,85% do nominal; 0,027 kg·m² (≈5%) como hipótese para modelo de massa conferido |
| `dry_inertia_22` | 0,01 kg·m² | ±0,02 kg·m² | Mesmo critério; proposta 0,027 kg·m² |
| `dry_inertia_33` | 0,01 kg·m² | ±0,02 kg·m² | Atual ≈38,7% do nominal; proposta 0,0013 kg·m² (≈5%) se o modelo de massa estiver conferido |
| `dry_inertia_12`, `13`, `23` | 0,001 kg·m² cada | ±0,002 kg·m² cada | Não há piso escalar justificável sem informação de assimetria. Preferir derivação de massas/posições e tensor fisicamente consistente |
| `nozzle_radius` | 0,1 mm | ±0,2 mm | Manter 0,1 mm como incerteza de medição, se confirmada |
| `grain_density` | 1 kg/m³ | ±2 kg/m³ | Apenas 0,055% de 1.815 kg/m³: muito exigente sem evidência. Proposta inicial 18 kg/m³ (≈1%), condicionada à medição de massa e volume |
| `grain_outer_radius` | 1 mm | ±2 mm | 0,2 mm se medido em vários pontos; nominal 58 mm |
| `grain_initial_inner_radius` | 1 mm | ±2 mm | 0,2 mm se medido em vários pontos; nominal 20 mm |
| `grain_initial_height` | 5 mm | ±10 mm | 0,5 mm com medição dos grãos reais; nominal 129 mm |
| `grain_separation` | 1 mm | ±2 mm | 0,2 mm com montagem e espaçamento conferidos; nominal 2 mm |
| `grains_center_of_mass_position` | 10 mm | ±20 mm | 2 mm com posição de montagem conferida |
| `center_of_dry_mass_position` | 10 mm | ±20 mm | 3 mm com balanceamento repetido do conjunto seco |
| `nozzle_position` | 5 mm | ±10 mm | 1 mm com medição da posição; corrigir antes a ligação do nominal no builder |
| `throat_radius` | 0,5 mm | ±1 mm | 0,1 mm somente se medição real sustentar essa incerteza; nominal 10,3 mm |

Os valores propostos para geometria descrevem conhecimento da peça existente. Se ainda houver apenas desenho/CAD, não se pode assumir essas incertezas de medição como dispersões de fabricação.

Cuidados ao ativar esses campos:

- A normal atual para separação de grãos, se ativada sem limites, daria cerca de 2,3% de separações negativas. A inércia axial atual também permitiria valores negativos. É necessário preservar positividade, geometria válida e consistência do tensor de inércia.
- Densidade, dimensões, massa de propelente, impulso e duração não devem ser tratados como independentes por conveniência. A massa deriva de densidade e volume; devem ser usados dados conjuntos ou uma parametrização consistente.
- O construtor estocástico recebe uma propriedade comum para os grãos, não automaticamente erros independentes de cada um dos quatro grãos.
- O `build_motor` atual não repassa `motor.nozzle_position` ao `SolidMotor`, apesar de o YAML nominal declarar 0,7233 m. A posição nominal efetiva deve ser conferida antes de lhe atribuir incerteza.

### Campos comentados

`flight.rail_length`, `environment.gravity` e as seis componentes de inércia de `vehicle` estão comentados e também não têm ligação estocástica nesses orquestradores.

- Comprimento da rampa: uma hipótese de σ = 0,01 m pode ser adequada após medição do comprimento efetivo de guiamento; não confundir comprimento físico com distância disponível aos guias do foguete.
- Gravidade: não acrescentar 0,01 m/s² arbitrariamente a uma gravidade já calculada por posição/altitude; justificar qualquer incerteza residual por sua fonte.
- Inércias do veículo: para um orçamento preliminar de 5%, I11/I22 dariam σ ≈0,395 kg·m² cada e I33 ≈0,00377 kg·m². Isso exige um modelo de distribuição de massa conferido. Produtos de inércia exigem tratamento de assimetria e correlação; não copiar o mesmo desvio para todos os eixos.

## 5. Verificações do nominal e da falha

### Massa de propelente

As dimensões e a densidade nominais implicam, para quatro grãos cilíndricos anulares:

`m = 4 × 1815 × π × (0,058² − 0,020²) × 0,129 ≈ 8,721 kg`.

O cabeçalho do arquivo de ensaio contém 8,126 kg no campo de massa de propelente. Há diferença de aproximadamente 0,595 kg, ou 7,3% sobre 8,126 kg. Pode representar motor/lote diferente ou outra convenção, mas precisa ser conciliada antes de adotar σ de densidade de 0,055% ou de tratar a curva como representativa do conjunto atual. Um erro no nominal não é corrigido reduzindo σ.

### Separação e recuperação

O código calcula um voo e inicia outro a partir do primeiro estado amostrado abaixo de 200 m AGL na descida. Porém, o segundo objeto é uma cópia do foguete completo com os paraquedas removidos: massa, inércia, centro de massa e geometria não são repartidos entre dois corpos. Portanto, as duas integrações atuais não representam, por si só, dois fragmentos com propriedades distintas.

Além disso, o Monte Carlo de falha exclui o paraquedas cujo nome contém `main`, e os demais paraquedas são transferidos sem incertezas explícitas. O YAML não varia a altura física da separação, impulso de separação, propriedades de cada fragmento, CdS ou atraso de abertura. O limiar de 200 m é fixo, e sua detecção pelo primeiro ponto abaixo do limiar introduz uma diferença numérica em relação ao cruzamento exato.

Esses pontos afetam a validade física da dispersão de uma ruptura em dois corpos e merecem prioridade sobre ajustes pequenos de tolerâncias. Não foram alterados neste estudo. A campanha representa um cenário condicionado à falha, não a probabilidade de ela ocorrer.

## 6. Número de simulações e precisão

`num_simulations: 500` define o tamanho da amostra; não a resolução da integração de cada voo. É adequado como início para estudar tendências e convergência. Em 500 sorteios independentes, uma região com probabilidade de 1% recebe apenas cinco casos em média; sua estimativa é instável. Avaliar estabilidade de médias, dispersões e quantis em lotes antes de aumentar ou reduzir a campanha.

Reduzir `std` estreita a distribuição de entradas e geralmente a dispersão prevista, mas **não melhora a exatidão numérica**. Se a incerteza real for maior, a previsão fica artificialmente otimista. Isso é diferente de reduzir o custo de exportação de arquivos, discutido anteriormente.

## 7. Ordem recomendada

1. Conciliar os valores nominais de massa/propelente e a representação dos dois corpos.
2. Conferir os campos do YAML efetivamente conectados e registrar no resultado os desvios realmente usados, especialmente os de vento.
3. Adotar o cenário baixo proposto somente para parâmetros sustentados por medição; preservar cenários comparativos para impulso, arrasto e vento.
4. Priorizar medições repetidas da rampa, massa/CM montados, ensaios do motor e dados de vento. Estimar repetibilidade e incerteza dos instrumentos separadamente.
5. Revisar limites físicos e correlações antes de ativar todas as variações de geometria e inércia.

## Fontes e limites do estudo

- Código local dos orquestradores, builders, MAGI e RocketPy instalado; configurações nominais e curva de ensaio citadas acima.
- [RocketPy — Working with Stochastic objects](https://docs.rocketpy.org/en/latest/user/stochastic.html): interpretação dos argumentos e valores mantidos constantes quando não são passados.
- [NIST — Evaluating uncertainty components: Type B](https://physics.nist.gov/cuu/Uncertainty/typeb.html): uso de informação disponível e conversão de intervalos em incerteza padrão.

As fontes fundamentam o tratamento das incertezas, não os números propostos para o Neblina. Os números são hipóteses condicionais, a substituir por registros da equipe. Foi feita inspeção estática e aritmética dos dados existentes; não foi executada nova campanha de voo ou análise quantitativa de sensibilidade.
