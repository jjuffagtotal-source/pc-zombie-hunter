"""Teste da skill Context Sanitizer Oracle.

Uso: python teste_skill.py [arquivo.py]
(sem argumento, sanitiza o próprio sanitizer.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sanitizer import ALERTA, check_dependency, sanitize_code

alvo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sanitizer.py"

print("=" * 60)
print(f"1) SANITIZAÇÃO: {alvo}")
print("=" * 60)
original = alvo.read_text(encoding="utf-8")
esqueleto = sanitize_code(alvo)
print(esqueleto)
economia = len(original) - len(esqueleto)
print("-" * 60)
print(f"Original:   {len(original):>8,} caracteres")
print(f"Sanitizado: {len(esqueleto):>8,} caracteres")
print(f"Economia:   {economia:>8,} caracteres ({economia / len(original):.1%})")
print(f"Tokens (~4 chars/token): ~{len(original) // 4:,} -> ~{len(esqueleto) // 4:,}")

print()
print("=" * 60)
print("2) ORÁCULO DE DEPENDÊNCIAS")
print("=" * 60)
real = check_dependency("requests")
falso = check_dependency("requests-fake-xyz")
print(f"requests          -> {real['message']}")
print(f"requests-fake-xyz -> {falso['message']}")

ok = real["exists"] is True and falso["exists"] is False and falso["message"] == ALERTA
print()
print("RESULTADO:", "PASSOU" if ok else "FALHOU (veja mensagens acima; erro de rede?)")
sys.exit(0 if ok else 1)
