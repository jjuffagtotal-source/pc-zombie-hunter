---
name: context-sanitizer-oracle
description: Economiza contexto e evita alucinação de dependências. Use ANTES de ler arquivos Python grandes inteiros (gera só imports + assinaturas de funções/classes) e SEMPRE antes de sugerir, instalar ou adicionar um pacote pip/npm em requirements.txt, pyproject.toml ou package.json (confirma no PyPI/npm que o pacote existe e qual a última versão).
---

# Context Sanitizer Oracle

Duas ferramentas, expostas pelo script `sanitizer.py` desta pasta
(`~/.claude/skills/Context_Sanitizer_Oracle/sanitizer.py`). Só usa a biblioteca padrão do Python 3.9+.

## Ferramenta 1 — `sanitize`: esqueleto do código

Quando precisar entender a *estrutura* de um arquivo Python (o que ele importa, quais
funções/classes expõe e com quais parâmetros), rode isto em vez de ler o arquivo inteiro:

```bash
python ~/.claude/skills/Context_Sanitizer_Oracle/sanitizer.py sanitize caminho/arquivo.py [outro.py ...]
```

Saída: imports, decorators, assinaturas (com type hints e defaults), a primeira linha de cada
docstring, e o corpo trocado por `...`.

Regras:
- Use o esqueleto para mapear o código e escolher o que ler. Para **editar** uma função,
  leia o trecho real dela com a ferramenta Read — nunca edite com base no esqueleto.
- Variáveis/constantes no nível do módulo não aparecem; se importarem, leia o arquivo.
- Só funciona para `.py`. Erro de sintaxe no arquivo = leia normalmente.

## Ferramenta 2 — `check`: oráculo de dependências

Antes de recomendar `pip install X`, `npm install X` ou escrever `import X` de um pacote
de terceiros que você não viu no projeto, verifique:

```bash
python ~/.claude/skills/Context_Sanitizer_Oracle/sanitizer.py check requests httpx
python ~/.claude/skills/Context_Sanitizer_Oracle/sanitizer.py check lodash --ecosystem npm
```

Interpretação:
- `OK: <pacote> existe (última versão: X)` → pode usar; prefira fixar versão compatível.
- `ALERTA: Pacote inexistente, não invente!` → **não** sugira o pacote. Procure o nome
  correto ou uma alternativa real, e verifique de novo.
- `ERRO: ...` → não foi possível verificar (rede/registro). Diga isso ao usuário; não
  afirme que o pacote existe nem que não existe.

Exit code: `1` se algum pacote não existe, `0` caso contrário.

Atenção: no PyPI o nome de instalação pode diferir do nome de import
(`pip install beautifulsoup4` → `import bs4`). Verifique o nome de **instalação**.

## Uso como biblioteca

```python
from sanitizer import sanitize_code, check_dependency
print(sanitize_code("app.py"))
check_dependency("requests")  # {'exists': True, 'latest_version': '...', ...}
```
