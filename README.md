# 🧟 PC ZOMBIE HUNTER 🧟‍♂️

**PC Zombie Hunter** é um jogo arcade 2D estilo pixel art desenvolvido em Python (PySide6) que funciona como um otimizador e limpador de PC gamificado. 

Enquanto você se diverte destruindo zumbis e fantasmas, o programa executa uma limpeza real no seu Windows (arquivos TEMP, Lixeira, cache de DNS, etc.) em segundo plano.

## 🎮 Como Jogar
- **Mover:** O personagem se move automaticamente para frente.
- **Pular:** Barra de espaço (cuidado com os fantasmas que voam!).
- **Atirar:** Tecla **M** (você tem munição limitada!).
- **Vidas:** Você tem 3 vidas (corações). Se um inimigo encostar em você, perde uma vida.

## 🛠️ Funcionalidades
- Limpeza real de `%TEMP%`, `%TMP%` e Lixeira.
- Otimização de conexão (DNS Flush).
- Barra de progresso real de limpeza.
- Sistema de fases progressivas (mais inimigos e menos munição).
- **Batalha contra o Chefe (Zumbizão)** ao final da limpeza pesada.
- Efeitos sonoros nativos do Windows.

## 💻 Como Executar o Código Fonte
1. Clone o repositório.
2. Crie um ambiente virtual (`python -m venv .venv`).
3. Ative o ambiente (`\.venv\Scripts\activate`).
4. Instale as dependências: `pip install PySide6`.
5. Execute: `python main.py`.

## 📦 Executável (.EXE)
Para usuários que não têm Python instalado, você pode baixar a versão `.exe` gerada pelo PyInstaller. *(Você pode subir o .exe na aba "Releases" do GitHub).*

---
*Desenvolvido com muito código, café e zumbis.*
