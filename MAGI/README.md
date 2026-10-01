# MAGI

O MAGI reúne aquisição meteorológica (BALTHASAR), climatologia (MELCHIOR),
interpolação e física atmosférica (CASPER), classificação, visualização e
exportação NetCDF.

A aplicação atual é [`MAGI_App.py`](MAGI_App.py). A partir da raiz do repositório,
com o ambiente do projeto configurado:

```bash
PYTHONPATH=source:. .venv/bin/python MAGI/MAGI_App.py
```

O script realiza aquisições, usa caches, gera figuras em `MAGI/figures/`, exporta
NetCDF no diretório de execução e executa os testes do MAGI. Seu processamento
também é iniciado quando o módulo é importado. Para consumir perfis atmosféricos
nas simulações, use [`interface.py`](interface.py).

O notebook antigo foi excluído do repositório em 10/09/2026. O
[catálogo de notebooks e scripts](../docs/CATALOGO_NOTEBOOKS_E_SCRIPTS.md)
documenta suas células, os módulos atuais, as diferenças históricas e a validação.
`build_notebook.py` é um utilitário opcional que recria o notebook; ele não é
necessário para executar a aplicação Python.
