# Estação local de dinâmica de voo

## Abrir e encerrar

Com o ambiente instalado, na raiz do repositório:

```bash
antares-fd doctor
antares-fd gui
```

O navegador abre `http://127.0.0.1:8765`. Use `--no-browser` para abrir manualmente
e `--port 8766` se necessário. Para apontar a outro checkout:
`antares-fd --repo-root /caminho/do/repositorio gui`. O servidor atende somente
no computador local. Não há necessidade de Node, npm, conta ou acesso à internet
para carregar a interface. Aquisição de meteorologia pode precisar de rede.

Encerre pelo terminal com Ctrl+C. O servidor cancela os workers que iniciou;
fechar apenas a aba do navegador mantém o servidor e suas execuções ativos.
Um único servidor pode supervisionar cada workspace. Duas execuções podem ficar
ativas simultaneamente; campanhas maiores devem considerar RAM e CPU disponíveis.

## Fluxo recomendado

1. **Projetos:** selecione um foguete ou use “Novo foguete”. A cópia inclui
   entradas, não telemetria nem resultados. Confira o projeto de origem.
2. **Visão geral:** examine geometria, massa/CG declarados, prontidão e fontes.
   O desenho é um esquema lateral; não é CAD nem desenho de fabricação.
3. **Componentes:** registre a montagem ou importe o `.ork`. Complete os dados
   desconhecidos a partir das fontes e confira o referencial.
4. **Parâmetros:** revise motor, aerodinâmica, recuperação, atmosfera e lançamento.
   Campos avançados preservam a estrutura dos documentos originais.
5. **Salvar revisão:** escreva o que mudou e a fonte. Uma edição externa ou em
   outra aba pode causar conflito; recarregue para revisar antes de reaplicar.
6. **Validar:** corrija erros. Avisos de hipótese/proveniência continuam visíveis.
   Validação local não comprova disponibilidade meteorológica nem validade de voo.
7. **Simular:** comece pelo nominal determinístico. Depois use Monte Carlo com
   incertezas justificadas. Acompanhe fase/log ou cancele o processamento.
8. **Resultados:** abra métricas, gráficos e artefatos; verifique hashes. Compare
   duas a quatro execuções considerando revisões e hipóteses diferentes.
9. **Dados e fontes:** registre originais reais no catálogo com responsável e origem.

## Inventário de massa

Unidades: kg, m e kg·m². Origem axial no bico, positiva em direção à cauda.
`axial_position_m` é a posição do **CG do componente**, não sua borda frontal.
Posições radiais são `[x,y]`. Tensor local no CG, nos mesmos eixos do veículo:
`[I11,I22,I33,I12,I13,I23]`, com I33 longitudinal. As três últimas entradas são
elementos do tensor simétrico usados pelo RocketPy, não integrais de produto
com sinal implicitamente invertido. Reoriente tensores antes de informá-los.

Modelos disponíveis: tensor informado, massa pontual, cilindro maciço, cilindro
oco e paralelepípedo. Massa pontual é uma hipótese explícita, inadequada para
representar automaticamente componentes extensos. Cada linha registra origem
`MEASURED`, `CALCULATED`, `ASSUMED` ou `UNKNOWN`, além da referência documental.

O cálculo exige inventário `COMPLETE`, sem dados necessários ausentes. Usa soma
de massas, CG ponderado e teorema dos eixos paralelos. Motor e propelente são
contabilizados pelo modelo de propulsão; a categoria `motor` fica fora da soma
do veículo. Desmarque componentes excluídos da montagem. Um CG radial não nulo
é diagnosticado porque o builder atual não representa essa assimetria.

Para usar a soma no voo, selecione “Usar inventário no modelo de massa”, salve e
valide. Caso contrário, o modelo continua com propriedades agregadas declaradas;
ter uma lista parcial não substitui automaticamente valores históricos.
O rótulo legado `mass_properties.method: measured` continua aceito como
propriedades agregadas; ele sozinho não comprova que houve uma pesagem rastreável.

“Transformar montagem” troca duas posições conhecidas e aplica fator de massa
a itens classificados como `structure`. O fator 0.95 representa economia
assumida de 5%; não se aplica automaticamente a payload/eletrônica. Para tensor
informado, a hipótese mantém geometria e escala tensor linearmente com a massa.
Modelos analíticos são recalculados. As alterações ficam locais até salvar.

## Importar OpenRocket

“Importar OpenRocket” aceita `.ork` ZIP, GZIP ou XML compatível, até 16 MiB.
O original é preservado em `sources/` com hash e relatório JSON. O importador
mantém árvore/campos de origem e traduz geometrias reconhecidas, posições e
algumas propriedades de massa. Formas/assemblies não representadas, múltiplas
instâncias e overrides de subárvore produzem avisos e podem tornar o inventário
parcial. Não trate uma massa de subárvore como massa local de uma única peça.

Depois da importação, confira especialmente posições, espessuras/densidades,
formas do nariz/aletas, tensores, motor, arrasto e recuperação. Fontes antigas de
arrasto e empuxo são desativadas para evitar reutilização silenciosa. A revisão
fica pendente até a conferência explícita. A simples confirmação da revisão não
substitui campos faltantes nem elimina erros de validação.

Não há promessa de cópia física exata: os simuladores usam representações e
modelos diferentes. O importador inicial é conservador e cobre o subconjunto
verificado pelas fixtures locais. O `.ork` real do Neblina ainda precisa ser
fornecido e conferido. No Neblina 2, importar a origem não aplica sozinho as
mudanças de projeto: preserve a revisão importada, faça as transformações
solicitadas e revise `config/design.yaml` antes de ativar a simulação.

## Execuções e histórico

Snapshots ficam em `results/<projeto>/<run_id>/inputs/`; hashes e versão do
software acompanham a execução. Alterações posteriores do projeto não mudam as
entradas congeladas. `COMPLETE_NOT_CONVERGED` distingue uma campanha processada
de uma análise estatística convergida. Distribuições mostram casos válidos;
consulte falhas, sementes e convergência nos artefatos completos. Nuvens e ECDF
podem ser reduzidas para visualização; Parquet preserva os dados completos.

O botão cancelar encerra o grupo do worker e mantém os arquivos parciais. Não
rotula uma campanha cancelada como resultado completo. Estados interrompidos
após reinício são explícitos. Em falha, consulte o log antes de executar outra vez.

Histórico em `projects/<id>/revisions/` conserva as entradas anteriores às
edições feitas pelo serviço. Restauração verifica hashes e preserva o estado
atual antes de repor configurações e fontes antigas. Assets adicionais não são
apagados automaticamente. Git continua sendo o histórico compartilhado; inclua
as alterações intencionais em revisão de código e preserve backups dos resultados.

## CLI equivalente

```bash
antares-fd project list
antares-fd project new meu_foguete --from neblina_1
antares-fd project show meu_foguete
antares-fd validate meu_foguete
antares-fd components meu_foguete
antares-fd run meu_foguete --scenario nominal --no-report
antares-fd run meu_foguete --mode monte_carlo --samples 50 --workers 1
antares-fd results list meu_foguete
antares-fd results show meu_foguete ID_DA_EXECUCAO
antares-fd results verify meu_foguete ID_DA_EXECUCAO
antares-fd results compare meu_foguete ID_1 ID_2
antares-fd project history meu_foguete
```

Importação e restauração exigem a revisão atual exibida por `project show`:

```bash
antares-fd import-openrocket meu_foguete /caminho/original.ork --expected-revision SHA256_ATUAL
antares-fd project restore meu_foguete SHA256_ANTIGO --expected-revision SHA256_ATUAL
```

Esses IDs são exemplos; substitua pelos hashes reais. Erros de entrada retornam
código 2; validação/integridade negativa retorna 1. Progresso de execução e logs
antecedem o JSON final, portanto `run` não é um fluxo exclusivamente JSON.

## Verificar a interface

Testes HTTP e workers são parte da suíte normal. Para testes renderizados:

```bash
python -m pip install -e ".[gui-test]"
python -m playwright install chromium
python -m pytest tests/integration/test_station_browser.py -q
```

No Linux sem bibliotecas do navegador, use a instalação de dependências
Playwright apropriada ao sistema. Para atualizar capturas revisáveis, configure
`ANTARES_GUI_EVIDENCE_DIR=docs/evidence/gui` antes do pytest. O teste usa workspace
temporário e fixture offline. Leia [o contrato e as evidências](evidence/gui/CONTRATO.md)
e faça inspeção visual das capturas; teste automatizado não certifica acessibilidade.
