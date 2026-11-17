# Funções de scripts

[Índice e convenções](README.md)

## `scripts/generate_function_reference.py`

Gere referências funcionais por AST sem importar nem executar as simulações.

O inventário inclui funções, métodos e funções locais de source, MAGI,
projects e scripts. Docstrings são o contrato humano; assinaturas, retornos,
exceções explícitas e colaboradores são extraídos mecanicamente do código.

### `function_nodes`

[Implementação: scripts/generate_function_reference.py:20](../../scripts/generate_function_reference.py#L20)

```python
function_nodes(tree: ast.AST, prefix: str='') -> Iterator[tuple[str, ast.AST]]
```

Liste definições com nome qualificado, incluindo funções locais.

Percorre a árvore sintática, acrescenta classes/funções ao prefixo e
produz pares (nome, nó). Não resolve imports nem invoca o código lido.

**Entradas e tipos declarados**

- `tree: ast.AST`
- `prefix: str`

**Retornos/yields explícitos**

- `(qualified, child)`
- `function_nodes(child, qualified + '.')`
- `function_nodes(child, prefix)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ast.iter_child_nodes`
- `isinstance`
- `function_nodes`

### `local_nodes`

[Implementação: scripts/generate_function_reference.py:36](../../scripts/generate_function_reference.py#L36)

```python
local_nodes(node: ast.AST) -> Iterator[ast.AST]
```

Percorra instruções de uma função sem atribuir a ela corpos de funções locais.

Inclui o nó raiz e seus descendentes executáveis; corpos de definições
aninhadas são documentados nas próprias entradas. Retorna um iterador AST.

**Entradas e tipos declarados**

- `node: ast.AST`

**Retornos/yields explícitos**

- `node`
- `local_nodes(child)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ast.iter_child_nodes`
- `isinstance`
- `local_nodes`

### `code_list`

[Implementação: scripts/generate_function_reference.py:48](../../scripts/generate_function_reference.py#L48)

```python
code_list(values: list[str]) -> str
```

Formate expressões sintáticas como itens Markdown sem interpretá-las.

Elimina repetições mantendo ordem e escapa crases no texto. Lista vazia
recebe uma indicação explícita de ausência de ocorrência local.

**Entradas e tipos declarados**

- `values: list[str]`

**Retornos/yields explícitos**

- `'\n'.join(('- \`' + value.replace('\`', '\\\`') + '\`' for value in dict.fromkeys(values))) or '- Nenhuma ocorrência explícita no corpo local.'`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `'\n'.join`
- `value.replace`
- `dict.fromkeys`

### `function_entry`

[Implementação: scripts/generate_function_reference.py:57](../../scripts/generate_function_reference.py#L57)

```python
function_entry(path: Path, name: str, node: ast.AST) -> str
```

Renderize objetivo, assinatura e mecanismos locais de uma definição.

Exige docstring; extrai parâmetros, retornos, yields, raises e chamadas
diretamente do AST. Não infere pureza, tipos ausentes nem exceções de
bibliotecas. Retorna Markdown com link para a implementação correspondente.

**Entradas e tipos declarados**

- `path: Path`
- `name: str`
- `node: ast.AST`

**Retornos/yields explícitos**

- `'\n'.join(lines)`

**Exceções lançadas explicitamente**

- `ValueError(f'Função sem docstring: {path}:{node.lineno}: {name}')`

**Colaboradores chamados diretamente**

- `ast.get_docstring`
- `ValueError`
- `ast.unparse`
- `list`
- `local_nodes`
- `isinstance`
- `arguments.append`
- `path.relative_to(ROOT).as_posix`
- `path.relative_to`
- `code_list`
- `'\n'.join`

### `build_reference`

[Implementação: scripts/generate_function_reference.py:92](../../scripts/generate_function_reference.py#L92)

```python
build_reference() -> dict[str, str]
```

Construa os documentos determinísticos e o índice de cobertura funcional.

Lê todos os .py próprios nos diretórios declarados, excluindo testes e
caches. Cada módulo recebe uma seção com todas as definições. Retorna
nome de arquivo para conteúdo; docstring ausente interrompe a geração.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `documents`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sorted`
- `(ROOT / root).rglob`
- `{'tests', '__pycache__'}.intersection`
- `ast.parse`
- `path.read_text`
- `str`
- `list`
- `function_nodes`
- `path.relative_to(ROOT).as_posix`
- `path.relative_to`
- `ast.get_docstring`
- `function_entry`
- `'\n'.join(entries).rstrip`
- `'\n'.join`
- `index.append`
- `len`

### `main`

[Implementação: scripts/generate_function_reference.py:129](../../scripts/generate_function_reference.py#L129)

```python
main(argv: list[str] | None=None) -> int
```

Grave a referência funcional ou valide se os arquivos estão atualizados.

Interpreta --check, gera o conteúdo em memória e compara com os destinos.
Sem --check, cria o diretório e grava UTF-8; com --check, retorna 1 quando
há divergência e 0 quando todos os documentos coincidem. Não importa MAGI.

**Entradas e tipos declarados**

- `argv: list[str] | None`

**Retornos/yields explícitos**

- `1`
- `0`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `argparse.ArgumentParser`
- `parser.add_argument`
- `parser.parse_args`
- `build_reference`
- `OUTPUT.mkdir`
- `documents.items`
- `path.exists`
- `path.read_text`
- `stale.append`
- `path.write_text`
- `print`
- `', '.join`
