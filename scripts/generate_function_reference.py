"""Gere referências funcionais por AST sem importar nem executar as simulações.

O inventário inclui funções, métodos e funções locais de source, MAGI,
projects e scripts. Docstrings são o contrato humano; assinaturas, retornos,
exceções explícitas e colaboradores são extraídos mecanicamente do código.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "referencia_funcoes"
ROOTS = ("source", "MAGI", "projects", "scripts")
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def function_nodes(tree: ast.AST, prefix: str = "") -> Iterator[tuple[str, ast.AST]]:
    """Liste definições com nome qualificado, incluindo funções locais.

    Percorre a árvore sintática, acrescenta classes/funções ao prefixo e
    produz pares (nome, nó). Não resolve imports nem invoca o código lido.
    """
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, (*FUNCTIONS, ast.ClassDef)):
            qualified = prefix + child.name
            if isinstance(child, FUNCTIONS):
                yield qualified, child
            yield from function_nodes(child, qualified + ".")
        else:
            yield from function_nodes(child, prefix)


def local_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """Percorra instruções de uma função sem atribuir a ela corpos de funções locais.

    Inclui o nó raiz e seus descendentes executáveis; corpos de definições
    aninhadas são documentados nas próprias entradas. Retorna um iterador AST.
    """
    yield node
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, (*FUNCTIONS, ast.ClassDef, ast.Lambda)):
            yield from local_nodes(child)


def code_list(values: list[str]) -> str:
    """Formate expressões sintáticas como itens Markdown sem interpretá-las.

    Elimina repetições mantendo ordem e escapa crases no texto. Lista vazia
    recebe uma indicação explícita de ausência de ocorrência local.
    """
    return "\n".join("- `" + value.replace("`", "\\`") + "`" for value in dict.fromkeys(values)) or "- Nenhuma ocorrência explícita no corpo local."


def function_entry(path: Path, name: str, node: ast.AST) -> str:
    """Renderize objetivo, assinatura e mecanismos locais de uma definição.

    Exige docstring; extrai parâmetros, retornos, yields, raises e chamadas
    diretamente do AST. Não infere pureza, tipos ausentes nem exceções de
    bibliotecas. Retorna Markdown com link para a implementação correspondente.
    """
    doc = ast.get_docstring(node)
    if not doc:
        raise ValueError(f"Função sem docstring: {path}:{node.lineno}: {name}")
    result_type = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    signature = f"{name}({ast.unparse(node.args)}){result_type}"
    body = list(local_nodes(node))
    returned = [ast.unparse(item.value) if item.value is not None else "None"
                for item in body if isinstance(item, (ast.Return, ast.Yield, ast.YieldFrom))]
    raised = [ast.unparse(item.exc) if item.exc else "raise (propaga a exceção ativa)"
              for item in body if isinstance(item, ast.Raise)]
    calls = [ast.unparse(item.func) for item in body if isinstance(item, ast.Call)]
    parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    arguments = [f"{arg.arg}: {ast.unparse(arg.annotation) if arg.annotation else 'tipo não anotado; ver contrato acima'}"
                 for arg in parameters if arg.arg not in {"self", "cls"}]
    if node.args.vararg:
        arguments.append("*" + node.args.vararg.arg + ": argumentos posicionais adicionais")
    if node.args.kwarg:
        arguments.append("**" + node.args.kwarg.arg + ": argumentos nomeados adicionais")
    relative = path.relative_to(ROOT).as_posix()
    lines = [f"### `{name}`", "", f"[Implementação: {relative}:{node.lineno}](../../{relative}#L{node.lineno})", "",
             "```python", signature, "```", "", doc, "", "**Entradas e tipos declarados**", "", code_list(arguments), "",
             "**Retornos/yields explícitos**", "", code_list(returned), "", "**Exceções lançadas explicitamente**", "", code_list(raised), "",
             "**Colaboradores chamados diretamente**", "", code_list(calls), ""]
    if not returned:
        lines += ["Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).", ""]
    return "\n".join(lines)


def build_reference() -> dict[str, str]:
    """Construa os documentos determinísticos e o índice de cobertura funcional.

    Lê todos os .py próprios nos diretórios declarados, excluindo testes e
    caches. Cada módulo recebe uma seção com todas as definições. Retorna
    nome de arquivo para conteúdo; docstring ausente interrompe a geração.
    """
    documents = {}
    index = ["# Referência funcional do Antares Flight Dynamics", "",
             "Inventário gerado por `scripts/generate_function_reference.py`, sem executar os módulos.", "",
             "Cada entrada reúne objetivo/mecanismo da docstring, assinatura, parâmetros, expressões de retorno, exceções explícitas e colaboradores locais.", "",
             "Os nomes de chamadas não constituem um grafo de dependências resolvido. Exceções de bibliotecas e efeitos externos transitivos podem existir mesmo sem `raise` local. Tipos não anotados não são inferidos. `self` e `cls` representam a instância/classe da seção.", "",
             "Escopo: funções próprias de execução e ferramentas; dependências, testes, caches e cópias de build não fazem parte desta referência de API. A verificação dos testes é registrada no relatório de revisão.", "",
             "| Grupo | Módulos Python | Definições documentadas | Referência |", "| --- | ---: | ---: | --- |"]
    for root in ROOTS:
        entries = [f"# Funções de {root}", "", "[Índice e convenções](README.md)", ""]
        paths = [p for p in sorted((ROOT / root).rglob("*.py"))
                 if not {"tests", "__pycache__"}.intersection(p.parts)]
        count = 0
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            functions = list(function_nodes(tree))
            entries += [f"## `{path.relative_to(ROOT).as_posix()}`", ""]
            if ast.get_docstring(tree):
                entries += [ast.get_docstring(tree), ""]
            if not functions:
                entries += ["Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.", ""]
            for name, node in functions:
                entries += [function_entry(path, name, node)]
                count += 1
        documents[root + ".md"] = "\n".join(entries).rstrip() + "\n"
        index.append(f"| {root} | {len(paths)} | {count} | [{root}]({root}.md) |")
    index += ["", "Para atualizar: `.venv/bin/python scripts/generate_function_reference.py`.", "Para verificar sem gravar: acrescente `--check`.", ""]
    documents["README.md"] = "\n".join(index)
    return documents


def main(argv: list[str] | None = None) -> int:
    """Grave a referência funcional ou valide se os arquivos estão atualizados.

    Interpreta --check, gera o conteúdo em memória e compara com os destinos.
    Sem --check, cria o diretório e grava UTF-8; com --check, retorna 1 quando
    há divergência e 0 quando todos os documentos coincidem. Não importa MAGI.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verificar sem gravar")
    args = parser.parse_args(argv)
    documents = build_reference()
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    stale = []
    for name, content in documents.items():
        path = OUTPUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            path.write_text(content, encoding="utf-8")
    if stale:
        print("Referência desatualizada: " + ", ".join(stale))
        return 1
    print("Referência funcional verificada." if args.check else "Referência funcional gerada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
