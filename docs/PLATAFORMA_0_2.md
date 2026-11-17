# Entrega da plataforma 0.2 — 2026-11-17

## Resultado

Foi implementada uma estação local sobre serviços comuns à CLI, com dados de
projeto separados da execução. O núcleo físico continua em RocketPy; a GUI
apresenta, edita e solicita operações pelos serviços Python. O projeto Neblina 2
é preliminar e mantém ausências explícitas até chegar o OpenRocket original.

| Critério de aceitação | Implementação e evidência |
| --- | --- |
| Criar projeto sem alterar origem | `application/projects.py`; teste de cópia isolada, colisão de ID e hashes |
| Inventário com cálculo verificável | `design/components.py`; cilindros, CG e tensor contra casos analíticos |
| Variantes sem desconto global indevido | `design/variants.py`; payload/eletrônica mantêm massa, apenas estrutura recebe fator |
| Validar antes de adquirir atmosfera/integrar | Diagnóstico offline e construção local de motor/veículo; teste com curva corrompida |
| Preservar entradas e versões | Snapshots, hashes, revisão esperada, proveniência do software e perfis atmosféricos usados |
| Cancelar processamento local | Subprocesso por job, término do grupo e estado CANCELLED; testes com worker real |
| Ler OpenRocket sem inventar equivalência | ZIP/GZIP/XML limitados; original preservado, cobertura e revisão obrigatória |
| Uma entrada Monte Carlo mantida | CLI/GUI e scripts de projeto apontam ao motor com falhas; módulo antigo documentado como compatibilidade |
| Consultar resultados sem reexecutar | Métricas, comparação, dispersão, ECDF, artefatos e verificação de hashes |
| Preservar conhecimento entre gestões | Onboarding, contribuição, ADR, catálogo, manutenção, exercício offline e funções de custódia |

## Verificação executada

- Suíte completa em Linux/Python 3.14.4: **277 testes e 4 subtestes passaram**;
  teste opcional de navegador não carregado nessa execução.
- Após ajustes finais de leitura UTF-8 e consistência de revisões: **25 testes
  afetados passaram**, incluindo HTTP, workers, validação e histórico.
- Fluxo Chromium/Playwright separado: criação de inventário, revisão, voo real
  offline, Monte Carlo, consulta, hashes, cancelamento e importação da fixture.
  Capturas e evidência: [pasta da GUI](evidence/gui/CONTRATO.md).
- Verificados lint Ruff, sintaxe JavaScript/Bash, referência gerada de funções,
  construção da distribuição wheel e presença dos assets da GUI no pacote.
- `doctor` encontrou o ambiente local instalado e o lock Python 3.14.
  `validate neblina_2` retorna código 1 pelas pendências esperadas.

Há avisos de bibliotecas, incluindo compatibilidade binária declarada pelo
NumPy/netCDF4, depreciações e avisos deliberados das fixtures RocketPy. Não
foram tratados como falhas silenciosas nem removidos por filtros globais.
Mudança de NumPy/netCDF4 deve ser validada novamente nos testes científicos.

Os locks 3.12/3.14 foram resolvidos com hashes e versões fixadas. Python 3.12 e
a execução da CI remota não foram executados neste computador; o workflow foi
preparado para ambos os intérpretes e para o navegador. Instalação, testes e
regressão local não representam validação experimental nem certificação NASA.

## Pendências externas explícitas

1. Fornecer o `.ork` real e conferir sua conversão. Sem ele não é possível
   verificar fidelidade do gêmeo digital ou concluir massa/CG/inércias do Neblina 2.
2. Confirmar massas/posições de eletrônica, gaiola e estruturas, envelope e
   geometria interna do novo motor, curva de empuxo, recuperação e lançamento.
3. Indicar titulares/suplentes e armazenamento institucional com backup e
   controle de acesso. Arquivos locais não atribuem contas ou permissões remotas.

O histórico local preserva edições feitas pelos serviços. Edições diretas
exigem Git e revisão da equipe; não há sincronização de nuvem automática.
Encerramento forçado do servidor pode exigir conferir processos remanescentes;
reinício marca estados órfãos como interrompidos sem matar PIDs antigos.

## Autoavaliação da entrega

| Eixo | Nota / 5 | Evidência e melhoria concreta |
| --- | --- | --- |
| Exatidão | 4 | Regressão física e integração executadas; ampliar comparação com `.ork` real e dados de voo |
| Completude | 4 | Plataforma, GUI e continuidade implementadas; dados físicos e titulares dependem da equipe |
| Clareza | 4 | Guias em português e contratos explícitos; revisar didática com novos integrantes durante treinamento |
| Aplicabilidade | 4 | Comando de GUI disponível e exercício offline reproduzível; executar a CI remota nos intérpretes previstos |
| Concisão | 4 | Interface sem framework e fluxo central; parte da configuração avançada ainda usa edição estruturada |

Média: **4,0/5**. Próximas melhorias por impacto: conferir o `.ork` real,
executar transferência com sucessores e validar demais plataformas. A avaliação
é compatível com os limites observáveis: não atribui equivalência entre
simuladores nem considera preenchidos os dados e acessos ainda não fornecidos.
