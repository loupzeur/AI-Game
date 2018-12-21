import numpy as np
from PIL import ImageGrab
import cv2
import time
import keyboard
import pickle
import sys

config = {
    'reduce_x_factor': 0.25,
    'reduce_y_factor': 0.25,
    'capture_0x': 0,
    'capture_0y': 40,
    'capture_x_size': 1920,
    'capture_y_size': 1020,
    'default_path': 'data/'
}

class RecordData:
    def __init__(self):
        self.path = config['default_path']
        self.data = {}
        self.printscreen = []
        self.last_time = time.time()
        self.last_key = {'key':0,'type':0}

    def _capKey(self,e):
        if self.last_key['key']==e.name and self.last_key['type']==e.event_type :
            return
        self.data[e.time]={'key':e.name,'type':e.event_type,'data':self.printscreen}
        self.last_key={'key':e.name,'type':e.event_type}

    def run(self): 
        keyboard.hook(self._capKey)
        while(True):
            self.printscreen =  cv2.resize( np.array(ImageGrab.grab(bbox=(config['capture_0x'],config['capture_0y'],config['capture_x_size'],config['capture_y_size']))) ,(0,0),fx=config['reduce_x_factor'],fy=config['reduce_y_factor'])
            self.last_time = time.time()
            cv2.imshow('window',cv2.cvtColor(self.printscreen, cv2.COLOR_BGR2GRAY))
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        self.writeData(str(self.last_time))
    
    def writeData(self,file):
        fw = open(self.path+file, 'wb')
        pickle.dump(self.data, fw)
        fw.close()

    def loadData(self,file):
        fd = open(file, 'rb')
        dataset = pickle.load(fd)
        for z in dataset:
            cv2.putText(dataset[z]['data'], dataset[z]['key'], (230, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow('window',cv2.cvtColor(dataset[z]['data'], cv2.COLOR_BGR2RGB))
            time.sleep(.5)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

if __name__ == "__main__":
    if len(sys.argv)==0:
        sys.exit()
    x=RecordData()
    if sys.argv[1]=='loadData' and len(sys.argv)==3:
        x.loadData(sys.argv[2])
    elif sys.argv[1]=='run':
        if len(sys.argv)==3:
            x.path=sys.argv[2]
        x.run()