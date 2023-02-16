#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 22 12:14:39 2022

@author: levi

"""
import numpy as np
import random as rd
import sys

from PyQt5.QtGui import QColor,QPainter, QFontDatabase, QPen, QFont, QBrush
from PyQt5.QtCore import QObject, Qt, QPropertyAnimation, QPoint,\
    QRect, QPointF,pyqtProperty,QEasingCurve
from PyQt5.QtWidgets import QMainWindow, QGridLayout,QLabel,\
    QPushButton,QWidget,QApplication
from PyQt5.QtMultimedia import QSound


OFFSET = 15
SIZE_C = 52
SIZE = 9*SIZE_C


class Grid_Model(QObject):
    def __init__(self):
        super().__init__()
        self.mat = np.zeros([9,9], dtype = bool)
        self.color = QColor(0x5193ea)
        self.colorFade = QColor(0x5193ea)
        self.colorHint = QColor(0x72756b)
        self.colorResult = self.colorHint.lighter(180) # QColor(0xb5eb49)
        
        self.matFade = np.full((9,9),False, dtype = bool) # même chose
        self.matHint = np.full((9,9),False, dtype = bool)
        self.matResult = np.full((9,9),False, dtype = bool)
        
    def set_(self, x_p, y_n):
        self.mat[y_n, x_p] = True
    
    def is_set(self, x_p, y_n):
        return self.mat[y_n, x_p]
    
    def reset_mat(self):
        self.mat = np.zeros([9,9], dtype = bool)
    
    def display(self, painter):
     
        for i in range(9):
            for j in range(9):
                if (self.mat[i,j] or self.matHint[i,j]):
                    r = SIZE_C * np.array([j,i,1,1])
                    color = self.color
                    if self.matHint[i,j]:
                        color = self.colorHint
                    if self.matResult[i,j]:
                        color = self.colorResult
                    if self.matFade[i,j]:
                        color = self.colorFade
                        
                    painter.fillRect(r[0],r[1],r[2],r[3],color)
                            
    def _set_Fade(self,fade):
        self.colorFade = fade
          
    fade = pyqtProperty(QColor, fset = _set_Fade)
    
    #necessaire pour les tests, a supprimer
    def fill_random(self):
        for i in range(9):
            for j in range(9):
                if rd.randint(1,10)>6:
                    self.mat[i,j]=True

        for i in range(8):
            self.mat[i,0]=True
        self.mat[8,0]=False
        
        L,C,Cr = self.evaluate()
        self.remove(L, C, Cr)
            
    
    def admissible(self, block, att_x, att_y):
        res = True
        if not (att_x % SIZE_C == 0 and att_y % SIZE_C == 0):
            print("erreur")
        else:
            for rect in block.list_rect:
                x_rect, y_rect = att_x + rect[0], att_y + rect[1]
                x_p, y_n = x_rect//SIZE_C, y_rect//SIZE_C
                if (x_p > 8 or y_n > 8 or x_p<0 or y_n<0):
                    res=False
                    break
                if (self.is_set(x_p,y_n)):
                    res=False
                    break
        return res
    
    
    def color_hint(self, block, att_x, att_y,value):
        self.matHint = np.full((9,9),False, dtype = bool)
        self.matResult = np.full((9,9),False, dtype = bool)
        for rect in block.list_rect:
            x_rect, y_rect = att_x + rect[0], att_y + rect[1]
            x_p, y_n = x_rect//SIZE_C, y_rect//SIZE_C
            if not (x_p > 8 or y_n > 8 or x_p<0 or y_n<0):
                self.matHint[y_n, x_p] = value
        
        if (value):
            lignes, colonnes, carres = self.destructible(block, att_x, att_y)
            for i in range(9):
                for l in lignes:
                    self.matResult[l,i]=True
                for c in colonnes:
                    self.matResult[i,c]=True
                for cr in carres:
                   n = 3*(cr//3) + (i//3)
                   p = 3*(cr % 3) + (i % 3)
                   self.matResult[n,p]=True
                   
                   
    def destructible(self, block, att_x, att_y):
        lignes, colonnes, carres = set({}), set({}), set({})
        lignes_r, colonnes_r, carres_r = set({}), set({}), set({})
        
        mat_test = self.mat.copy()
        
        for rect in block.list_rect:
            x_rect, y_rect = att_x + rect[0], att_y + rect[1]
            x_p, y_n = x_rect//SIZE_C, y_rect//SIZE_C
            if not (x_p > 8 or y_n > 8 or x_p<0 or y_n<0):
                mat_test[y_n,x_p] = True
                lignes.add(y_n)
                colonnes.add(x_p)
                i_carre  = 3*(y_n//3)+(x_p//3)
                carres.add(i_carre)
                
        for l in lignes:
            is_l_complete = True
            for i in range(9):
                is_l_complete = is_l_complete and mat_test[l, i]
            if (is_l_complete): lignes_r.add(l)
                
        for c in colonnes:
            is_c_complete = True
            for i in range(9):
                is_c_complete = is_c_complete and mat_test[i, c]
            if (is_c_complete): colonnes_r.add(c)
        
        for cr in carres:
            is_cr_complete = True
            for i in range(9):
                n = 3*(cr//3) + (i//3)
                p = 3*(cr % 3) + (i % 3)
                is_cr_complete = is_cr_complete and mat_test[n, p] 
            if (is_cr_complete): carres_r.add(cr) 
                
        return lignes_r, colonnes_r, carres_r

            

    # recherche s'il existe au moins une position dans la grille pour inserer le bloc
    def inserable(self,block):
        found = False
        for n in range(9):
            for p in range(9):
                res = True
                for c in block.list_case:
                    if (n + c[1]>8 or p + c[0]>8):
                        res = False
                    else:
                        res = res and not self.mat[n + c[1],p + c[0]]
                    if (not res):
                        break
                if (res):
                    found = True
                    break
            if (found):
                break             
        return found
                        
    
    
    def admit(self,block,att_x,att_y):
        for rect in block.list_rect:
            x_rect, y_rect = att_x + rect[0], att_y + rect[1]
            x_p, y_n = x_rect//SIZE_C, y_rect//SIZE_C
            self.set_(x_p, y_n)
        
        
    
    def evaluate(self):
        suppr_lignes, suppr_colonnes, suppr_carres = [], [], []
        for i in range(9):
            is_Li_complete = True
            is_Ci_complete = True
            is_CRi_complete = True
            for j in range(9):
                is_Li_complete = is_Li_complete and self.is_set(j, i)
                is_Ci_complete = is_Ci_complete and self.is_set(i, j)
                n = 3*(i//3) + (j//3)
                p = 3*(i % 3) + (j % 3)
                is_CRi_complete = is_CRi_complete and self.is_set(p,n)
                
            if (is_Li_complete): suppr_lignes  +=[i]
            if (is_Ci_complete): suppr_colonnes+=[i]
            if (is_CRi_complete): suppr_carres +=[i]
                    
        return suppr_lignes,suppr_colonnes, suppr_carres
                
    
    def remove(self,lignes, colonnes, carres):
        nb_set_0 = sum(sum(self.mat))
        for j in range(9):     
            for i in lignes:
                self.mat[i,j] = False
            for i in colonnes:
                self.mat[j,i] = False
            for i in carres:
                n = 3*(i//3) + (j//3)
                p = 3*(i % 3) + (j % 3)
                self.mat[n,p] = False
                
        nb_set_1 = sum(sum(self.mat))
        return 2*(nb_set_0 - nb_set_1)

    def ChangeColor(self,lignes, colonnes, carres):
        for j in range(9):     
            for i in lignes:
                self.matFade[i,j] = True
            for i in colonnes:
                self.matFade[j,i] = True
            for i in carres:
                n = 3*(i//3) + (j//3)
                p = 3*(i % 3) + (j % 3)
                self.matFade[n,p] = True
                
    def resetColor(self):
        self.matFade = np.full((9,9),False, dtype = bool)
        
                
class block(QObject):
    def __init__(self,x,y,id):
        super().__init__()
        self.init_pos(x, y)
        self.list_rect = []
        self.list_case = [] # coord coins sup gauche de chaque carré dans le modèle
        self.color = QColor(0x5a98e8)
        self.id = id
        self.onFocus = False
        self.inserable = True
        self.resize_factor = .65    
        
    def set_pos(self,x,y):
        self.x = x
        self.y = y
        
    def init_pos(self,x,y):
        self.set_pos(x,y)
        self.pos_0 = QPointF(x,y)
        
                    
    def _set_pos(self, pos):
        self.set_pos(int(pos.x()),int(pos.y()))

    pos = pyqtProperty(QPointF, fset=_set_pos)        
    
        
    def set_case(self, list_case):
        self.list_case=list_case
        
        
    def update_inserabilite(self,value):
        self.inserable = value
        if (value):
            self.color = QColor(0x407be3)
        else:
            self.color = QColor(0x9598c5)
            
            
    def build_rect(self, size):
        arr1,arr2 = self.list_case, [[1,1] for k in range(len(self.list_case))]
        rect_0 = size * np.concatenate([arr1,arr2],axis=1)
        self.list_rect = list(rect_0) 
        return self.list_rect
                    
        
    def add_rect(self,rect):
        self.list_rect += [rect]
                               
    #rectangle x, y, largeur, longueur
    def display(self,painter):
        if (self.onFocus or self.y<SIZE):
            factor = 1
        else:
            factor = self.resize_factor
        
        size = int(SIZE_C * factor)
        self.build_rect(size)
        
        painter.setRenderHint(QPainter.Antialiasing) 
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        for rect in self.list_rect:
            x0,y0 = self.x + rect[0], self.y + rect[1]
            x1,y1 = rect[2], rect[3] 
      
            Rect = QRect(x0,y0,x1,y1)
            painter.fillRect(x0,y0,x1,y1, self.color)
            painter.drawRect(Rect)
                            
            
    def is_clicked(self,pos_x,pos_y):
        res = False
        for rect  in self.list_rect:
            x0,y0 = self.x + rect[0], self.y + rect[1]
            x1,y1 = self.x + rect[2]+rect[0], self.y + rect[1] + rect[3] 
            if (pos_x>x0 and pos_x<x1 and pos_y>y0 and pos_y < y1):
                res = True
                break
        return res
    
    def center_on_pos(self,pos_x, pos_y): 
        cases = self.list_case
        cases_x = [case[0] for case in cases]
        cases_y = [case[1] for case in cases]
        Lx = max(cases_x) - min(cases_x) + 1 
        Ly = max(cases_y) - min(cases_y) + 1 
        self.x = pos_x - (Lx*SIZE_C)//2
        self.y = pos_y - (Ly*SIZE_C)//2
        
        
             
    def build_random(self):
        P1 = [[0,0], [1,0], [2,0], [3,0]]
        P2 = [[0,0], [0,1], [0,2]]
        P3 = [[0,0], [1,0], [2,0],[3,0]]
        P4 = [[0,0], [0,1], [0,2],[0,3]]
        P5 = [[0,0], [1,0], [0,1], [0,2], [0,3]]
        P6 = [[0,0], [1,0], [2,0], [1,1]]
        P7 = [[0,0], [0,1], [1,0], [2,0], [3,0]]
        P8 = [[0,0]]
        P9 = [[0,0],[1,1]]
        P10 = [[0,0],[1,1],[2,2]]
        P11 = [[1,0], [1,1], [1,2], [0,1]]
        P12 = [[0,0], [1,0],[0,1],[1,1]]
        L = [P1,P2,P3, P4,P5,P6, P7,P8,P9,P10,P11,P12]
        d = rd.randint(0,len(L)-1)
        
        self.list_case = L[d]
        self.build_rect(SIZE_C)      
        
               
class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('Working on a PyQT5 Puzzle game implementation')
        self.setStyleSheet("QMainWindow {background: 'white';}");

        self.width, self.height = SIZE+2*OFFSET, int(SIZE*1.5)+2*OFFSET
        screen = QApplication.primaryScreen()        
        x0 = screen.availableSize().width()//2 - self.width//2
        y0 = screen.availableSize().height()//10
        self.setGeometry(x0, y0, self.width, self.height) 
        self.setFixedSize(self.width, self.height)
        
        self.init_widgets()
        
        self.Model = Grid_Model()
        self.init_sounds()
        self.init_game()  
        self.init_animations()
        self.show()
       
    def _set_Fade_factor(self,factor):
        self.colorFade = QColor(80, 90, 255, factor)
          
    fade_factor = pyqtProperty(int, fset = _set_Fade_factor)
       
    
    def init_widgets(self):
        layout = QGridLayout()
        
        font_path = "./fonts/maldini/MaldiniBold-OVZO6.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.font2 = QFontDatabase.applicationFontFamilies(font_id)[0] 
        
        self.label_score=QLabel()
        self.label_score.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        self.label_score.setFont(QFont(self.font2,SIZE_C//3))

        self.label_end = QLabel()
        self.label_end.setFont(QFont(self.font2,4*SIZE_C//5))
        self.label_end.setAlignment(Qt.AlignCenter)
        qss = "QLabel { color : white; }"
        self.label_end.setStyleSheet(qss)

        self.button = QPushButton("Restart")
        self.button2 = QPushButton("Exit")
        
        for b in (self.button,self.button2):
            b.setFixedHeight(SIZE//6)
            b.setFont(QFont(self.font2,30))
             
            qss = "QPushButton {color:blue; \
                background-color: white;  \
                border: 1px solid black;\
                border-radius: 7px;} \
                QPushButton:pressed {background-color: rgb(192,192,192);}"
            b.setStyleSheet(qss)
        
        layout.addWidget(self.label_score,5,0,1,2)
        layout.addWidget(self.label_end,3,0,1,2) # 1 ligne, deux colonnes
        layout.addWidget(self.button, 5, 0)
        layout.addWidget(self.button2,5, 1)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def init_sounds(self):
        self.s_destruction = QSound("./sounds/destruction1.wav")
        self.s_game_over = QSound("./sounds/game_over.wav")
        self.s_insertion = QSound("./sounds/insertion.wav")
        self.s_retour = QSound("./sounds/retour.wav")
            
    def init_game(self):
        self.over = False
        self.label_score.setVisible(True)
        self.label_end.setVisible(False)
        self.button.setVisible(False)
        self.button2.setVisible(False)
        self.button2.clicked.connect(self.close)
        self.button.clicked.connect(self.init_game) # necessaire cause init
        
        self.Model.reset_mat()
       # self.Model.fill_random()
        self.covering_rect = QRect(-OFFSET,-OFFSET,self.width+OFFSET, self.height+OFFSET)
        
        self.generate_3b()
        self.state = 0
        self.mouse_prev_x, self.mouse_prev_y = 0, 0  
        self.score = 0      
        self.update_label()
        self.animation_running = False
        self.anim_retour_debug = False
        self.update()
        
        
    
    def disp_game_over(self):
        self.label_score.setVisible(False)
        self.label_end.setVisible(True)
        self.label_end.setText("Game Completed \n"+str(self.score))
        self.button.setVisible(True)
        self.button2.setVisible(True)
                
        
    
    def init_animations(self):
        self.anim_col = QPropertyAnimation(self.Model, b'fade')
        self.anim_col.setStartValue(self.Model.color)
        self.anim_col.setEndValue(QColor(255,255,255))
        self.anim_col.setLoopCount(1)
        self.anim_col.setDuration(750)
        self.anim_col.valueChanged.connect(self.update)
        self.anim_col.finished.connect(self.anim_col_finished)
                
        self.anim_end = QPropertyAnimation(self, b'fade_factor')
        self.anim_end.setStartValue(0)
        self.anim_end.setEndValue(210)
        self.anim_end.setLoopCount(1)
        self.anim_end.setDuration(1200)
        self.anim_end.valueChanged.connect(self.update)
        self.anim_end.finished.connect(self.disp_game_over) # Modifier
    
 
    def set_3b_pos(self):
        Lx = [0,0,0]
        for i in range(3):
            cases = self.blocks[i].list_case
            cases_x = [case[0] for case in cases]
            Lx[i] = max(cases_x) - min(cases_x) + 1 
        factor = .5
        f2 = .5 * SIZE_C*factor
        w = self.width-2*OFFSET
        x = [0,0,0]
        x[0] = int(w/6 - Lx[0]*f2)
        x[1]  = int(w/2 - Lx[1]*f2)
        x[2] = int(5/6*w - Lx[2]*f2)

        for i in range(3):
            self.blocks[i].resize_factor = factor
            self.blocks[i].init_pos(x[i], int(SIZE*1.1))
        
        
    def generate_3b(self):
        self.blocks = (block(0,0,0),block(0,0,1),block(0,0,2))
        for i in range(3):
            self.blocks[i].build_random()
            ins = self.Model.inserable(self.blocks[i])
            self.blocks[i].update_inserabilite(ins)
            
        self.set_3b_pos()  
        self.block_disp = [True,True,True]
        self.block = self.blocks[0]
        self.check_game_over()
      
        
    def start_anim_retour(self):
        Q_start = QPointF(self.block.x, self.block.y)
        if (Q_start!=self.block.pos_0):
            self.anim_ret = QPropertyAnimation(self.block, b'pos')
            self.anim_ret.setStartValue(Q_start)
            self.anim_ret.setEndValue(self.block.pos_0)
            self.anim_ret.setEasingCurve(QEasingCurve.InOutCubic)
            vec = (Q_start - self.block.pos_0)
            dist = np.sqrt(vec.x()*vec.x() + vec.y()*vec.y())
            duration = int((dist*450)/SIZE)
            self.anim_ret.setDuration(duration)
            self.animation_running=True
            self.anim_retour_debug = True
            
            self.anim_ret.start()
            self.anim_ret.valueChanged.connect(self.update)
            
            def finished_ret():
                self.animation_running=False
                self.anim_retour_debug = False
                
            self.anim_ret.finished.connect(finished_ret)
        
        
    def mousePressEvent(self,event):      
        if self.state == 0 and not self.animation_running:
            pos = event.pos()-QPoint(OFFSET,OFFSET)
            pos_x, pos_y = pos.x(), pos.y()
            self.mouse_prev_x, self.mouse_prev_y = pos_x, pos_y
            
            is_b0_c = self.blocks[0].is_clicked(pos_x, pos_y)
            is_b1_c = self.blocks[1].is_clicked(pos_x, pos_y)
            is_b2_c = self.blocks[2].is_clicked(pos_x, pos_y)
            
            if  is_b0_c or is_b1_c or is_b2_c:
                 i = [is_b0_c,is_b1_c,is_b2_c].index(True)
                 if (self.blocks[i].inserable and self.block_disp[i]):                 
                     self.block = self.blocks[i]
                     self.block.center_on_pos(pos_x,pos_y)
                     self.block.onFocus = True
                     self.state = 1
            
    def mouseMoveEvent(self, event):
        if self.state == 1 and not self.animation_running:
            pos = event.pos()-QPoint(OFFSET,OFFSET)
            pos_x, pos_y = pos.x(), pos.y()
            dx,dy = pos_x - self.mouse_prev_x , pos_y - self.mouse_prev_y
            self.mouse_prev_x, self.mouse_prev_y = pos_x, pos_y
            self.block.set_pos(self.block.x + dx, self.block.y + dy)
            self.process_block_hint()
            self.update()
     
        
    def process_block_hint(self):
        treshhold = .5
        x0, y0 = self.block.x, self.block.y
        x_close_m, y_close_m = SIZE_C*int(np.round(x0/SIZE_C)), SIZE_C*int(np.round(y0/SIZE_C))
        d1, d2  = abs(x0 - x_close_m)/SIZE_C, abs(y0 - y_close_m)/SIZE_C
 
        value = False
        x_correct, y_correct = x_close_m, y_close_m
        if (d1*d1 + d2*d2 < treshhold * treshhold): 
            value = self.Model.admissible(self.block, x_correct, y_correct)
        self.Model.color_hint(self.block, x_correct, y_correct, value)
        
        

    def process_block_pos(self):
        treshhold = .5
        x0, y0 = self.block.x, self.block.y
        x_close_m, y_close_m = SIZE_C*int(np.round(x0/SIZE_C)), SIZE_C*int(np.round(y0/SIZE_C))
        d1, d2  = abs(x0 - x_close_m)/SIZE_C, abs(y0 - y_close_m)/SIZE_C
 
        admitted = False
        
        if (d1*d1 + d2*d2 < treshhold * treshhold):           
            x_correct, y_correct = x_close_m, y_close_m
             
            if self.Model.admissible(self.block, x_correct, y_correct):
                self.block.x, self.block.y = x_correct, y_correct
                self.Model.admit(self.block, x_correct, y_correct)
                self.block_disp[self.block.id] = False
                self.score += self.block.list_case.__len__()
                self.update_label()
                admitted = True
                self.s_insertion.play()
                
                for i in range(3):
                    if self.block_disp[i]:                        
                        ins = self.Model.inserable(self.blocks[i])
                        self.blocks[i].update_inserabilite(ins)
            

        if (not admitted):
            self.start_anim_retour()
            self.s_retour.play()
                                 
    def mouseReleaseEvent(self,event):
        if self.state==1 and not self.animation_running:
            self.block.onFocus = False
            self.state = 0
            self.process_block_pos()
            self.Model.matHint = np.full((9,9),False, dtype = bool)
            self.update() 
            L,C,Cr = self.Model.evaluate()
            if (len(L)+len(C)+len(Cr) > 0):
                self.Model.ChangeColor(L, C, Cr)
                self.animation_running = True
                self.anim_col.start()
                self.s_destruction.play()
            else:
                self.check_game_over()
                
                if (sum(self.block_disp)==0):
                    self.generate_3b()
            
         
    def anim_col_finished(self):
        self.animation_running = False
        L,C,Cr = self.Model.evaluate()  
        gain = self.Model.remove(L, C, Cr)
        
        for i in range(3):
            if self.block_disp[i]:                        
                ins = self.Model.inserable(self.blocks[i])
                self.blocks[i].update_inserabilite(ins)
        
        if (sum(self.block_disp)==0):
            self.generate_3b()
            
        self.score += gain
        self.Model.resetColor()
        self.update()
        self.update_label()
        self.check_game_over()
        
          
    def check_game_over(self):
        g_continue = False 
        for i in range(3):
            if self.block_disp[i]:                        
                g_continue = g_continue or self.blocks[i].inserable                
        if (not g_continue and sum(self.block_disp)!=0):
            self.over=True
            self.anim_end.start()
            self.s_game_over.play()
            
        
    def update_label(self):
        s = ""
        s+= str(self.score)
        s+= (" "*20)
        s+=  str(int(100*sum(sum(self.Model.mat)/81)))
        s+="%"
        self.label_score.setText(s)
        
        
        
    def drawGrid(self, painter):
        
        H,W = SIZE, SIZE
        painter.setPen(QPen(Qt.blue, 5, Qt.SolidLine))
        painter.drawLine(0,H//3,W,H//3)
        painter.drawLine(0,2*H//3,W,2*H//3)
        painter.drawLine(W//3,0,W//3,H) 
        painter.drawLine(2*W//3,0,2*W//3,H) 
        
        painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        for i in (1,2,4,5,7,8):
            painter.drawLine(0,i*H//9,W,i*H//9)
            painter.drawLine(i*W//9,0,i*W//9,H)
            
        painter.setPen(QPen(Qt.black, 6, Qt.SolidLine))  
        painter.drawLine(0,0,W,0)
        painter.drawLine(0,H,W,H)
        painter.drawLine(0,0,0,H)
        painter.drawLine(W,0,W,H)
        

    def drawDebugValues(self,painter):
        H,W = SIZE, SIZE
        c1, c2, c3 = Qt.green, Qt.green, Qt.green
        if (self.animation_running): c1 = Qt.red
        if (self.state==1): c2 = Qt.red
        if (self.anim_retour_debug): c3 = Qt.red

        painter.setPen(QPen(Qt.green, 0, Qt.SolidLine)) 
        painter.setBrush(c1)
        painter.drawEllipse(QPoint(int(W*.95),int(H*1.35)), 10, 10)
        painter.setBrush(c2)
        painter.drawEllipse(QPoint(int(W*.95),int(H*1.4)), 10, 10)
        painter.setBrush(c3)
        painter.drawEllipse(QPoint(int(W*.95),int(H*1.45)), 10, 10)  
        
                   
    def paintEvent(self, event): 
        self.painter = QPainter(self)
        self.painter.translate(QPoint(OFFSET,OFFSET))
        
        self.Model.display(self.painter)
        for i in range(3):
            if (self.block_disp[i]):    
                self.blocks[i].display(self.painter)
               
                
        self.drawGrid(self.painter)
        self.drawDebugValues(self.painter)
              
        if self.over:
            self.painter.fillRect(self.covering_rect, QBrush(self.colorFade));
        self.painter.end()
            
       
app=0 # necessaire crash
app = QApplication([])
app.setStyle('Fusion')
dow = Window()
sys.exit(app.exec_())

