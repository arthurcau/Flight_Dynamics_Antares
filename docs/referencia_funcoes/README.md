# Referência funcional do Antares Flight Dynamics

Inventário gerado por `scripts/generate_function_reference.py`, sem executar os módulos.

Cada entrada reúne objetivo/mecanismo da docstring, assinatura, parâmetros, expressões de retorno, exceções explícitas e colaboradores locais.

Os nomes de chamadas não constituem um grafo de dependências resolvido. Exceções de bibliotecas e efeitos externos transitivos podem existir mesmo sem `raise` local. Tipos não anotados não são inferidos. `self` e `cls` representam a instância/classe da seção.

Escopo: funções próprias de execução e ferramentas; dependências, testes, caches e cópias de build não fazem parte desta referência de API. A verificação dos testes é registrada no relatório de revisão.

| Grupo | Módulos Python | Definições documentadas | Referência |
| --- | ---: | ---: | --- |
| source | 82 | 413 | [source](source.md) |
| MAGI | 21 | 79 | [MAGI](MAGI.md) |
| projects | 20 | 45 | [projects](projects.md) |
| scripts | 1 | 6 | [scripts](scripts.md) |

Para atualizar: `.venv/bin/python scripts/generate_function_reference.py`.
Para verificar sem gravar: acrescente `--check`.
