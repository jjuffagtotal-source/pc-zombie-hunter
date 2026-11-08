import sys, math, random, time, threading, queue
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
    QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget, QProgressBar)

# --- SISTEMA DE SOM ---
try:
    import winsound
    class SomThread(threading.Thread):
        def __init__(self):
            super().__init__()
            self.fila = queue.Queue()
            self.daemon = True
        def tocar(self, freq, dur):
            if self.fila.qsize() > 2: return 
            self.fila.put((freq, dur))
        def run(self):
            while True:
                f, d = self.fila.get()
                try: winsound.Beep(f, d)
                except: pass
    som = SomThread()
    som.start()
except ImportError:
    class SomFake:
        def tocar(self, f, d): pass
    som = SomFake()

# --- CLASSES DO JOGO ---
class Enemy:
    def __init__(self, t, x, y, v, ond=False, chefe=False):
        self.t=t; self.x=x; self.y_b=y; self.y=y; self.v=v; self.ond=ond; self.chefe=chefe; self.fase=0
        self.l = 90 if chefe else 30
        self.a = 120 if chefe else (50 if t=="zumbi" else 40)
        self.hp = 5 if chefe else 1
    def upd(self, dt):
        self.x -= self.v * dt
        if self.t=="fantasma" and self.ond: 
            self.fase += dt*6
            self.y = self.y_b + math.sin(self.fase)*25
    def r(self): return QRect(int(self.x), int(self.y), self.l, self.a)

class Shot:
    def __init__(self, x, y): 
        self.x=x; self.y=y; self.v=1200
    def upd(self, dt): 
        self.x += self.v * dt
    def r(self): return QRect(int(self.x)-4, int(self.y)-4, 8, 8)

class Game(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.on=False; self.over=False; self.px=80; self.py=0; self.vy=0; self.pul=True; self.pts=0
        self.vidas=3; self.inv=0.0
        self.ens=[]; self.shots=[]; self.ts=0; self.lvl=1; self.als=0; self.mun=0
        self.transicao_timer=0.0; self.transicao_texto=""
        self.tm=QTimer(self); self.tm.timeout.connect(self.tick); self.tm.start(16)
    
    def reset(self):
        self.on=True; self.over=False; self.pts=0; self.ens=[]; self.shots=[]; self.py=self.height()-90; self.vy=0; self.lvl=1; self.vidas=3; self.inv=0; self.lvl_init(); self.setFocus()
    
    def lvl_init(self):
        self.ens=[]; self.shots=[]; self.ts=0
        if self.lvl == 1: self.als = 50; self.mun = 80
        elif self.lvl == 2: self.als = 100; self.mun = 120
        elif self.lvl == 3: self.als = 150; self.mun = 160
        else: self.als = 200; self.mun = 200
    
    def prox_fase(self):
        self.lvl+=1; self.pts+=50; self.lvl_init()

    def transicao(self, texto, fim=None):
        self.transicao_timer = 2.0
        self.transicao_texto = texto
        self.fim_transicao = fim

    def tick(self):
        # Lógica da Transição
        if self.transicao_timer > 0:
            self.transicao_timer -= 0.016
            if self.transicao_timer <= 0 and self.fim_transicao:
                self.fim_transicao()
                self.fim_transicao = None
                self.setFocus()
            self.update()
            return 

        if not self.on or self.over: return
        dt=0.016
        if self.inv > 0: self.inv -= dt
        
        self.vy+=1800*dt; self.py+=self.vy*dt
        if self.py>=self.height()-90: self.py=self.height()-90; self.vy=0; self.pul=True
        
        if self.als>0:
            self.ts+=dt
            if self.ts>1.2:
                self.ts=0; self.als-=1
                t="zumbi" if (self.lvl==1 or random.random()>0.5) else "fantasma"
                self.ens.append(Enemy(t, self.width(), self.height()-130 if t=="fantasma" else self.height()-90, 180, self.lvl>1))
        elif not self.ens: 
            som.tocar(600, 100); som.tocar(800, 150) 
            self.transicao(f"FASE {self.lvl} CONCLUÍDA!", self.prox_fase)
            return
        
        pr = QRect(self.px, int(self.py), 30, 50)
        for e in list(self.ens):
            e.upd(dt)
            # COLISÃO COM O JOGADOR
            if pr.intersects(e.r()):
                if self.inv <= 0:
                    self.vidas -= 1
                    self.inv = 2.0 
                    som.tocar(200, 300) 
                    if self.vidas <= 0:
                        self.over=True
                        som.tocar(100, 500)
                    if not e.chefe:
                        if e in self.ens: self.ens.remove(e)
                    else:
                        e.x += 250 
            
            # PUNIÇÃO DO FANTASMA: Se passar e sair da tela
            if e.x < -50:
                if e.t == "fantasma" and not e.chefe:
                    self.mun -= 1 # Perde 1 tiro
                    if self.mun < 0: self.mun = 0
                    som.tocar(300, 100)
                if e in self.ens: self.ens.remove(e)
        
        for s in list(self.shots):
            s.upd(dt)
            if s.x>self.width(): self.shots.remove(s); continue
            for e in list(self.ens):
                if s.r().intersects(e.r()):
                    if s in self.shots: self.shots.remove(s)
                    e.hp -= 1
                    som.tocar(1000, 50)
                    if e.hp <= 0:
                        if e in self.ens: self.ens.remove(e)
                        self.pts += 10 if not e.chefe else 100
                        if e.chefe: 
                            som.tocar(800, 100); som.tocar(1200, 200)
                            self.transicao("AMEAÇA ELIMINADA!\nSISTEMA SEGURO")
                    break
        self.update()
    
    def chefe(self): 
        if not self.on:
            self.reset()
        self.ens.append(Enemy("zumbi", self.width(), self.height()-140, 80, False, True))
        som.tocar(150, 400)
    
    def keyPressEvent(self, ev):
        if self.transicao_timer > 0: return 
        if ev.key()==Qt.Key_Space:
            if self.over: self.reset()
            elif self.on and self.pul: 
                self.vy=-650; self.pul=False
                som.tocar(600, 50)
        elif ev.key()==Qt.Key_M and self.on and not self.over:
            if self.mun>0: 
                self.mun-=1
                self.shots.append(Shot(self.px+30, self.py+15))
                som.tocar(1200, 20) 
    
    def paintEvent(self, ev):
        p=QPainter(self); W=self.width(); H=self.height(); c=H-40
        p.fillRect(0,0,W,H,QColor(15,15,30)); p.fillRect(0,H//2,W,H//2,QColor(40,20,60)); p.fillRect(0,c,W,40,QColor(30,30,40))
        
        # Jogador
        if not (self.inv > 0 and int(self.inv * 10) % 2 == 0):
            p.fillRect(self.px,int(self.py),30,50,QColor(220,60,60)) 
            p.fillRect(self.px+30,int(self.py)+12,15,6,QColor(200,200,200))
            p.setBrush(QColor(20,20,20))
            p.drawRect(self.px+4, int(self.py)+6, 6, 6)
            p.drawRect(self.px+20, int(self.py)+6, 6, 6)
        
        # Tiros
        p.setBrush(QColor(255,255,100)); p.setPen(Qt.NoPen)
        for s in self.shots: p.drawEllipse(int(s.x)-4,int(s.y)-4,8,8)
        
        # Inimigos
        for e in self.ens:
            if e.chefe: self.desenha_chefe(p, e)
            elif e.t == "zumbi": self.desenha_zumbi(p, e)
            else: self.desenha_fantasma(p, e)
            
            if e.chefe and e.hp < 5:
                p.setBrush(QColor(255,0,0))
                p.drawRect(int(e.x), int(e.y)-10, int(90 * (e.hp/5)), 5)
        
        p.setPen(QColor(255,255,255)); p.setFont(QFont("Consolas",12))
        p.drawText(20,30,f"FASE {self.lvl} | PONTOS: {self.pts} | ALVOS: {self.als+len(self.ens)} | TIROS: {self.mun}")
        p.drawText(20,50,f"VIDAS: {'❤' * self.vidas}{'♡' * (3-self.vidas)}")

        if self.transicao_timer > 0:
            p.fillRect(0,0,W,H,QColor(0,0,0,180))
            p.setPen(QColor(255,255,100)); p.setFont(QFont("Consolas",24, QFont.Bold))
            p.drawText(self.rect(), Qt.AlignCenter, self.transicao_texto)
        
        if self.over: 
            p.setPen(QColor(255,60,60)); p.setFont(QFont("Consolas",20, QFont.Bold))
            p.drawText(self.rect(), Qt.AlignCenter, "SISTEMA INFECTADO!\n(ESPACO PARA REINICIAR)")

    def desenha_zumbi(self, p, e):
        x, y = int(e.x), int(e.y)
        # Corpo verde
        p.setBrush(QColor(80, 200, 80)); p.setPen(Qt.NoPen)
        p.drawRect(x, y, 30, 50)
        # Braços
        p.drawRect(x-5, y+15, 10, 8)
        p.drawRect(x+25, y+15, 10, 8)
        # Olhos vermelhos
        p.setBrush(QColor(255, 0, 0))
        p.drawRect(x+5, y+8, 6, 6)
        p.drawRect(x+20, y+8, 6, 6)
        # Boca
        p.setBrush(QColor(30, 30, 30))
        p.drawRect(x+8, y+35, 14, 5)

    def desenha_fantasma(self, p, e):
        x, y = int(e.x), int(e.y)
        # Corpo azul translúcido
        p.setBrush(QColor(160, 200, 255, 150)); p.setPen(Qt.NoPen)
        # Cabeça e tronco
        p.drawEllipse(x, y, 30, 40)
        # Cauda ondulada (3 pontas)
        p.drawEllipse(x, y+25, 10, 20)
        p.drawEllipse(x+10, y+30, 10, 20)
        p.drawEllipse(x+20, y+25, 10, 20)
        # Olhos
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(x+6, y+12, 6, 8)
        p.drawEllipse(x+18, y+12, 6, 8)
        p.setBrush(QColor(0, 0, 0))
        p.drawEllipse(x+8, y+14, 2, 4)
        p.drawEllipse(x+20, y+14, 2, 4)

    def desenha_chefe(self, p, e):
        x, y = int(e.x), int(e.y)
        # Corpo escuro
        p.setBrush(QColor(150, 20, 20)); p.setPen(Qt.NoPen)
        p.drawRect(x, y, 90, 120)
        # Chifres
        p.setBrush(QColor(40, 40, 40))
        p.drawRect(x+10, y-15, 10, 20)
        p.drawRect(x+70, y-15, 10, 20)
        p.drawRect(x+20, y-5, 8, 10)
        p.drawRect(x+62, y-5, 8, 10)
        # Olhos amarelos
        p.setBrush(QColor(255, 255, 0))
        p.drawRect(x+15, y+20, 15, 15)
        p.drawRect(x+60, y+20, 15, 15)
        p.setBrush(QColor(0, 0, 0))
        p.drawRect(x+20, y+25, 5, 5)
        p.drawRect(x+65, y+25, 5, 5)
        # Boca cheia de dentes
        p.setBrush(QColor(30, 0, 0))
        p.drawRect(x+15, y+70, 60, 30)
        p.setBrush(QColor(255, 255, 255))
        for i in range(15, 75, 10):
            p.drawRect(x+i, y+70, 5, 10) # Dentes de cima
            p.drawRect(x+i+2, y+90, 5, 10) # Dentes de baixo

class MenuScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("PC ZOMBIE HUNTER")
        title.setStyleSheet("font-size: 40px; font-weight: bold; color: #7ef29d; font-family: Consolas;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Mantenha seu PC limpo enquanto luta pela sobrevivência.")
        subtitle.setStyleSheet("font-size: 14px; color: #a0a0c0; font-family: Consolas; margin-bottom: 30px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        btn_jogar = QPushButton("JOGAR AGORA")
        btn_jogar.setFixedSize(250, 50)
        btn_jogar.setStyleSheet("background-color: #2a7a4a; color: white; font-size: 16px; font-weight: bold; border-radius: 5px;")
        btn_jogar.clicked.connect(self.main_window.iniciar_jogo)
        layout.addWidget(btn_jogar, alignment=Qt.AlignCenter)
        
        btn_limpar = QPushButton("LIMPEZA PESADA + JOGAR")
        btn_limpar.setFixedSize(250, 50)
        btn_limpar.setStyleSheet("background-color: #2a4a7a; color: white; font-size: 16px; border-radius: 5px; margin-top: 10px;")
        btn_limpar.clicked.connect(self.main_window.limpeza_rapida_menu)
        layout.addWidget(btn_limpar, alignment=Qt.AlignCenter)

class GameScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        top_bar = QFrame()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet("background-color: #12121c; border-bottom: 2px solid #333355;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_status = QLabel("Status do Sistema: Aguardando...")
        self.lbl_status.setStyleSheet("color: #e0e0f0; font-family: Consolas; font-weight: bold;")
        top_layout.addWidget(self.lbl_status)
        
        self.progress = QProgressBar()
        self.progress.setFixedWidth(200)
        self.progress.setValue(0)
        self.progress.setStyleSheet("QProgressBar { border: 1px solid #555; border-radius: 3px; text-align: center; color: white; } QProgressBar::chunk { background-color: #7ef29d; }")
        top_layout.addWidget(self.progress)
        
        btn_limpar = QPushButton("LIMPAR AGORA")
        btn_limpar.setStyleSheet("background-color: #7a2a2a; color: white; font-weight: bold; padding: 5px;")
        btn_limpar.setFocusPolicy(Qt.NoFocus) # IMPEDE DE ROUBAR O FOCO DO TECLADO
        btn_limpar.clicked.connect(self.main_window.iniciar_limpeza_no_jogo)
        top_layout.addWidget(btn_limpar)
        
        layout.addWidget(top_bar)
        
        self.game = Game()
        layout.addWidget(self.game, 1)
        
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(30)
        bottom_bar.setStyleSheet("background-color: #12121c;")
        bot_layout = QHBoxLayout(bottom_bar)
        btn_voltar = QPushButton("Voltar ao Menu")
        btn_voltar.setStyleSheet("color: #aaa; background: none; border: none; text-decoration: underline;")
        btn_voltar.clicked.connect(self.main_window.voltar_menu)
        bot_layout.addWidget(btn_voltar, alignment=Qt.AlignRight)
        layout.addWidget(bottom_bar)

class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC Zombie Hunter")
        self.resize(960, 600)
        self.setStyleSheet("background-color: #0a0a10;")
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.menu_screen = MenuScreen(self)
        self.game_screen = GameScreen(self)
        
        self.stack.addWidget(self.menu_screen)
        self.stack.addWidget(self.game_screen)
        
    def iniciar_jogo(self):
        self.stack.setCurrentWidget(self.game_screen)
        self.game_screen.game.reset()
        
    def voltar_menu(self):
        self.game_screen.game.on = False 
        self.stack.setCurrentWidget(self.menu_screen)
        
    def iniciar_limpeza_no_jogo(self):
        if not self.game_screen.game.on:
            self.game_screen.game.reset()
            
        self.game_screen.lbl_status.setText("Status: Limpando...")
        self.game_screen.progress.setValue(0)
        
        self.progresso_visual = 0
        self.timer_barra = QTimer(self)
        self.timer_barra.timeout.connect(self.animar_barra)
        self.timer_barra.start(100)
        
        self.game_screen.game.chefe()

    def animar_barra(self):
        if self.progresso_visual < 100:
            self.progresso_visual += 2
            self.game_screen.progress.setValue(self.progresso_visual)
            self.game_screen.lbl_status.setText("Status: Limpando...")
        else:
            self.timer_barra.stop()
            self.game_screen.lbl_status.setText("Status: Sistema Limpo e Otimizado!")
        
    def limpeza_rapida_menu(self):
        self.stack.setCurrentWidget(self.game_screen)
        self.game_screen.game.reset()
        self.iniciar_limpeza_no_jogo()

if __name__=="__main__":
    app=QApplication(sys.argv)
    w=Janela()
    w.show()
    sys.exit(app.exec())