# Contrato de interface — estação Antares 0.2

Superfície: aplicação local de engenharia, servida em loopback pelo mesmo
pacote da CLI. Usuários: integrantes que precisam revisar e simular um modelo
sem editar scripts de cada foguete. A ação principal é validar e executar;
campos desconhecidos permanecem vazios e impedem cálculos que dependem deles.

Hierarquia: projeto ativo e navegação à esquerda, área de trabalho ao centro,
prontidão e fontes próximas da geometria. Tabelas concentram componentes e
resultados; detalhes estruturados ficam em controles expansíveis. Referência
local: divisão existente `projects/*/{config,aero,motors}` e métricas canônicas
de `analysis/flight_metrics.py`. Não foi copiado um produto externo.

Direção visual: estação técnica discreta, fundo claro, navegação azul escura,
ações azuis, estados assumidos âmbar e dados verificados verdes. A montagem
lateral comunica a orientação bico–cauda; é explicitamente um esquema.
Tipografia do sistema evita recursos de rede. Não há dependência de imagens,
fontes remotas, CDN ou compilador de frontend.

Alvos verificáveis: desktop 1440×900 e telefone 390×844; tabelas podem rolar
horizontalmente dentro do painel, sem causar overflow da página. Todos os
controles têm rótulos, foco visível e operação por teclado. Diálogos nativos
contêm o foco. Avisos usam região viva. Movimento reduzido é respeitado.

| Estado | Gatilho | Resposta e próxima ação |
| --- | --- | --- |
| Carregando | Consulta de entradas ou worker ativo | Texto de fase; cancelar job ativo |
| Vazio | Sem resultados/fontes/componentes | Explicação e ação para criar registro |
| Erro | Entrada inválida, conflito ou arquivo indisponível | Diagnóstico; revisar/recarregar |
| Parcial | Inventário incompleto ou ausência de métricas | Valores ausentes explícitos; completar fontes |
| Sucesso | Salvar, executar ou verificar hashes | Confirmação; histórico ou resultados |
| Permissão | Token expirado ou origem externa | Sessão expirada; recarregar a estação local |

Evidências renderizadas e observações ficam no JSON desta pasta. Testes de
estado por resposta HTTP simulada são identificados como tais; não são
evidência de qualidade física do modelo.
