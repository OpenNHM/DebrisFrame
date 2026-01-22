# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 13:11:54 2020

@author: cscheidl
"""
class MonteCarloSingleFlowPath():
    def __init__(self,raster,band2,position,temp_height):
        self.startrastercells=band2
        self.dem=raster
        self.startcell=position
        self.artificalheight=temp_height
        #self.articficalrasterheight=band2
    def NextStartCell(self):
        import numpy as np
        rowPosition = self.startcell[0]
        colPosition = self.startcell[1]
        #self.startrastercells[rowPosition,colPosition]=True
      # Adjacent cells positions
        adjacentBelow = rowPosition + 1
        adjacentUpper = rowPosition - 1
        adjacentLeft = colPosition - 1
        adjacentRight = colPosition + 1
           # Check if adjacent cells positions are out of raster positions limits
        if adjacentBelow < self.dem.height:
            if self.startrastercells[adjacentBelow,colPosition]==False:
               belowBound = True
            else:
               belowBound=False
        else: 
               belowBound = False
        if adjacentUpper >0:
            if self.startrastercells[adjacentUpper,colPosition]==False:
               upperBound = True
            else:
               upperBound = False
        else: 
                upperBound = False
        if adjacentLeft >0:
            if self.startrastercells[rowPosition,adjacentLeft]==False:
               leftBound = True
            else:
               leftBound = False
        else: 
                leftBound = False
        if adjacentRight < self.dem.width:
            if self.startrastercells[rowPosition,adjacentRight]==False:
               rightBound = True
            else:
               rightBound = False
        else: 
                rightBound = False
        if upperBound==True :
            diff1=self.dem.read(1)[rowPosition,colPosition] - self.dem.read(1)[adjacentUpper,colPosition]
            if (diff1+self.artificalheight)<=0: #or belowBound==False or leftBound==False or rightBound==False:
                diff1=0
                position1=[0,0]
            else:
                position1=[adjacentUpper,colPosition] 
                if diff1<0:
                   diff1=diff1 + self.artificalheight
                else:
                   diff1=diff1
        else:
            diff1=0
            position1=[0,0]
        if rightBound==True :
            diff2=self.dem.read(1)[rowPosition,colPosition] - self.dem.read(1)[rowPosition,adjacentRight]
            if (diff2+self.artificalheight)<=0: #or belowBound==False or leftBound==False or  rightBound==False:
                diff2=0
                position2=[0,0]
            else:
                position2=[rowPosition,adjacentRight]
                if diff2<0:
                   diff2=diff2 + self.artificalheight
                else:
                   diff2=diff2
        else:
            diff2=0
            position2=[0,0]
        if belowBound==True:
            diff3=self.dem.read(1)[rowPosition,colPosition] - self.dem.read(1)[adjacentBelow,colPosition]
            if (diff3+self.artificalheight)<=0: #or belowBound==False or  leftBound==False or rightBound==False:
                diff3=0
                position3=[0,0]
            else:
                position3=[adjacentBelow,colPosition]
                if diff3<0:
                   diff3=diff3 + self.artificalheight
                else:
                   diff3=diff3
        else:
            diff3=0
            position3=[0,0]
        if leftBound==True :
            diff4=self.dem.read(1)[rowPosition,colPosition] - self.dem.read(1)[rowPosition,adjacentLeft]
            if (diff4+self.artificalheight)<=0: #or  belowBound==False or  leftBound==False or rightBound==False:
                diff4=0
                position4=[0,0]
            else:
                position4=[rowPosition,adjacentLeft]
                if diff4<0:
                   diff4=diff4 + self.artificalheight
                else:
                   diff4=diff4
        else:
            diff4=0
            position4=[0,0]
        summe=diff1+diff2+diff3+diff4
        #print(summe)
        if summe==0:
            newcell=[0,0]
            #print('MIST!')
        else:
            valid_positions = []
            valid_probabilities = []

            if diff1 > 0:
                valid_positions.append(position1)
                valid_probabilities.append(diff1 / summe)
            if diff2 > 0:
                valid_positions.append(position2)
                valid_probabilities.append(diff2 / summe)
            if diff3 > 0:
                valid_positions.append(position3)
                valid_probabilities.append(diff3 / summe)
            if diff4 > 0:
                valid_positions.append(position4)
                valid_probabilities.append(diff4 / summe)
            # Normiere die Wahrscheinlichkeiten, um Rundungsfehler zu vermeiden
            valid_probabilities = np.array(valid_probabilities)
            valid_probabilities /= valid_probabilities.sum()
            # Konvertiere die Liste der gültigen Positionen in ein numpy-Array
            allpos = np.array(valid_positions)
            if len(allpos) > 0:  # Überprüfe, ob es gültige Zellen gibt
                newcell = allpos[np.random.choice(len(allpos), size=None, replace=True, p=valid_probabilities)]
            else:
                newcell = [0, 0]  # Fallback, falls keine gültigen Zellen vorhanden sind
          #prob=(diff1/summe,diff2/summe,diff3/summe,diff4/summe,0)
          #print(prob)
          #allpos=np.array([position1,position2,position3,position4,[0,0]])
          #print(allpos)
          #newcell = np.random.choice(len(allpos), size=None, replace=True, p=prob)
          #newcell=np.random.choice(allpos, size=None, replace=True, p=prob)  
        return newcell
