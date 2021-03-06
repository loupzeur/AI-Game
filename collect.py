import numpy as np
from numpy import argmax
from PIL import ImageGrab
import cv2
import time
import keyboard
import pickle
import sys
import os
from keras.models import load_model
import tensorflow as tf
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

config = {
    'reduce_x_factor': 0.25,
    'reduce_y_factor': 0.25,
    'capture_0x': 0,
    'capture_0y': 40,
    'capture_x_size': 1920,
    'capture_y_size': 1020,
    'default_path': 'data/',
    'req_shape': (245,480)
}

class RecordData:
    def __init__(self):
        self.path = config['default_path']
        self.data = {}
        self.printscreen = []
        self.last_time = time.time()
        self.last_key = {'key':0,'type':0}
        self.run_AI = False
        self.ctl_AI = False
        self.model = None

    def _capKey(self,e):
        if self.last_key['key']==e.name and self.last_key['type']==e.event_type :
            return
        if(self.printscreen.shape!=config['req_shape']):
            print('Failed shape : {} Required : {}'.format(self.printscreen.shape,config['req_shape']))
            return
        self.data[e.time]={'key':e.name,'type':e.event_type,'data':self.printscreen}
        self.last_key={'key':e.name,'type':e.event_type}
        print(self.last_key)

    def run(self): 
        if not self.run_AI:
            keyboard.hook(self._capKey)
        while(True):
            self.printscreen =  cv2.cvtColor( cv2.resize( np.array(ImageGrab.grab(bbox=(config['capture_0x'],config['capture_0y'],config['capture_x_size'],config['capture_y_size']))) ,(0,0),fx=config['reduce_x_factor'],fy=config['reduce_y_factor']) , cv2.COLOR_BGR2GRAY)
            self.last_time = time.time()
            if self.run_AI:
                self._screenToData(self.printscreen)
            cv2.imshow('window',self.printscreen)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break    
        if not self.run_AI:
            self.writeData(str(self.last_time))
    
    def writeData(self,file):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        fw = open(self.path+file, 'wb')
        pickle.dump(self.data, fw)
        fw.close()

    def loadData(self,file):
        fd = open(file, 'rb')
        dataset = pickle.load(fd)
        for z in dataset:
            cv2.putText(dataset[z]['data'], dataset[z]['key'], (230, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow('window',cv2.cvtColor(dataset[z]['data'], cv2.COLOR_BGR2RGB))
            time.sleep(.5)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

    def loadAI(self,path):
        self.run_AI = True
        self.model = load_model(path)
        keyboard.add_hotkey('ctrl + space',self._switchAICtl)

    def _switchAICtl(self):
        self.ctl_AI=not self.ctl_AI
        print('AI is {}'.format('Running' if self.ctl_AI else 'Stopped'))

    def _screenToData(self,data):
        if not self.ctl_AI:
            return
        if time.time() - self.last_time > 0.5:
            print('Delaying to avoid overflowing AI : {}'.format(time.time() - self.last_time))
            return
        X_tst = data.astype('float32') / 255.
        pred = self.model.predict([[X_tst]])
        self._returnKey(pred)

    def _returnKey(self,pred):
        key = {
            0: 'Nothing',
            1: 'space',
            2: 's',
            3: 'a',
            4: 'd',
            5: 'space',
            6: 's',
            7: 'a',
            8: 'd'
        }
        idx = argmax(pred)
        ret = key.get(argmax(pred),'Nothing')
        score = pred[0][idx]
        if score < 0.7:
            return

        #Breaking systems ... for drift
        if idx==2 and self.last_key!='s' :
            keyboard.press('s')
        elif idx == 6:
            keyboard.release('s')

        if ret != 'Nothing' and ret != 's' and (self.last_key!=ret or ret=='space'):
            keyboard.press_and_release(ret)
        self.last_key = ret
        print("Key : {:6} {}({}) Pred {:4} Delay : {:5}".format(retprintkey(ret),('Down' if idx<4 else 'Up  '),idx,score, time.time() - self.last_time))

def retprintkey(ret):
    if ret == 'space':
        return 'sprint'
    if ret == 's':
        return 'drift'
    return ret

if __name__ == "__main__":
    if len(sys.argv)==0:
        sys.exit()
    x=RecordData()
    if sys.argv[1]=='loadData' and len(sys.argv)==3:
        x.loadData(sys.argv[2])
    elif sys.argv[1]=='run':
        if len(sys.argv)==3:
            x.path=sys.argv[2]+'/'
        x.run()
    elif sys.argv[1]=='runai':
        if len(sys.argv)==3:
            x.loadAI(sys.argv[2])
        x.run()