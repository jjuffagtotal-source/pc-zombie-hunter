"""Context Sanitizer Oracle.

- sanitize_code: reduz um arquivo Python ao seu "esqueleto" (imports + assinaturas).
- check_dependency: confirma em registro oficial se um pacote existe de verdade.

Uso via CLI:
    python sanitizer.py sanitize <arquivo.py>
    python sanitizer.py check <pacote> [--ecosystem pypi|npm]
"""

import ast
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

REGISTRIES = {
    "pypi": "https://pypi.org/pypi/{name}/json",
    "npm": "https://registry.npmjs.org/{name}",
}
ALERTA = "ALERTA: Pacote inexistente, não invente!"


class _Skeletonizer(ast.NodeTransformer):
    """Troca o corpo de funções por `...`, preservando docstring curta (1a linha)."""

    def _strip(self, node):
        body = []
        doc = ast.get_docstring(node)
        if doc:
            body.append(ast.Expr(ast.Constant(doc.strip().splitlines()[0])))
        body.append(ast.Expr(ast.Constant(...)))
        node.body = body
        return node

    def visit_FunctionDef(self, node):
        return self._strip(node)

    def visit_AsyncFunctionDef(self, node):
        return self._strip(node)

    def visit_ClassDef(self, node):
        # Mantém só métodos, classes aninhadas e atributos anotados (ex.: dataclasses).
        keep = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.AnnAssign)
        doc = ast.get_docstring(node)
        members = [self.visit(n) for n in node.body if isinstance(n, keep)]
        body = [ast.Expr(ast.Constant(doc.strip().splitlines()[0]))] if doc else []
        node.body = body + members or [ast.Expr(ast.Constant(...))]
        return node


def sanitize_code(file_path):
    """Retorna apenas imports e assinaturas de funções/classes de um arquivo Python."""
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    keep = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    tree.body = [_Skeletonizer().visit(n) for n in tree.body if isinstance(n, keep)]
    return ast.unparse(ast.fix_missing_locations(tree))


def check_dependency(package_name, ecosystem="pypi"):
    """Consulta o registro oficial e diz se o pacote existe e qual a última versão."""
    ecosystem = ecosystem.lower()
    if ecosystem not in REGISTRIES:
        raise ValueError(f"Ecossistema não suportado: {ecosystem} (use: {', '.join(REGISTRIES)})")

    url = REGISTRIES[ecosystem].format(name=urllib.parse.quote(package_name.strip(), safe="@"))
    req = urllib.request.Request(url, headers={"User-Agent": "Context-Sanitizer-Oracle/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"exists": False, "package": package_name, "ecosystem": ecosystem, "message": ALERTA}
        return {"exists": None, "package": package_name, "ecosystem": ecosystem,
                "message": f"ERRO: registro respondeu HTTP {e.code}; não foi possível verificar."}
    except (urllib.error.URLError, TimeoutError) as e:
        # Falha de rede NÃO significa que o pacote não existe.
        return {"exists": None, "package": package_name, "ecosystem": ecosystem,
                "message": f"ERRO: sem acesso ao registro ({e}); não foi possível verificar."}

    if ecosystem == "pypi":
        version = data["info"]["version"]
    else:
        version = data.get("dist-tags", {}).get("latest")
    return {"exists": True, "package": package_name, "ecosystem": ecosystem,
            "latest_version": version, "message": f"OK: {package_name} existe (última versão: {version})"}


def _main(argv):
    if len(argv) >= 2 and argv[0] == "sanitize":
        for path in argv[1:]:
            print(f"# ===== {path} =====")
            print(sanitize_code(path))
        return 0
    if len(argv) >= 2 and argv[0] == "check":
        ecosystem = "pypi"
        if "--ecosystem" in argv:
            i = argv.index("--ecosystem")
            ecosystem = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
        results = [check_dependency(p, ecosystem) for p in argv[1:]]
        for r in results:
            print(r["message"])
        return 1 if any(r["exists"] is False for r in results) else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
