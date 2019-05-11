import numpy as np
import cv2
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from PIL import Image,ImageTk
import os
import re
import subprocess

def numpy2tkImg(img_array):
    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    pil_img =  Image.fromarray(img_array)
    tk_img = ImageTk.PhotoImage(pil_img)
    return tk_img

def get_audio_duration(audioPath):
    # valid for any audio file accepted by ffprobe
    command = 'ffprobe -v error -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 "'+audioPath+'"'
    output = subprocess.getoutput(command)

    try:
        duration = float(output) #### get audio duration in seconds
    except:
        duration = -1
    
    return duration

def imgResize(img,outShape):
    #### resize and image keeping the aspect ratio to outShape (by padding after the resizing)
    orig_dims = np.array(img.shape[0:2])
    target_shape =  np.array(outShape)
    res_factor = np.min(target_shape / orig_dims)
    if res_factor < 1:
        interp_method = cv2.INTER_AREA
    else:
        interp_method = cv2.INTER_CUBIC
        
    img = cv2.resize(img,(0,0),fx = res_factor,fy = res_factor,interpolation = interp_method)
    outImg = np.zeros((outShape[0],outShape[1],3),dtype = img.dtype)
    
    diff = target_shape - img.shape[0:2]
    init_pos = diff // 2
    r1 = init_pos[0]
    r2 = init_pos[0] + img.shape[0]
    c1 = init_pos[1]
    c2 = init_pos[1] + img.shape[1]
    outImg[r1:r2,c1:c2,:] = img
    return outImg


class imageMontageMaker(tk.Tk):
    def __init__(self,initDir):
        super().__init__(None)
        self.initDir = initDir
        self.initialize()
        
    def initialize(self):
        self.grid()
        self.image = None
        
        self.labelImageSelection = tk.Label(self,text='IMAGES TO MOUNT')
        self.labelImageSelection.grid(row=0, column=0,rowspan = 1,columnspan = 2, sticky='NEWS',pady=(20,20))
        self.grid_rowconfigure(0,weight=1);self.grid_columnconfigure(0,weight=1)

        self.labelimageVisualizer = tk.Label(self,text='IMAGE VISUALIZER')
        self.labelimageVisualizer.grid(row=0, column=3,columnspan = 4, sticky='NEWS',pady=(20,20))
        self.grid_rowconfigure(0,weight=1);self.grid_columnconfigure(3,weight=1)

        self.imageSelectionBox = tk.Listbox(self, selectmode=tk.EXTENDED,exportselection=False)
        self.imageSelectionBox.bind('<<ListboxSelect>>', self.on_selection_changed)
        self.imageSelectionBox.grid(row = 1,column = 0,rowspan = 4,columnspan = 2,sticky='NEWS',padx = (30,15))
        self.grid_rowconfigure(1,weight=3);self.grid_columnconfigure(0,weight=2)

        self.imageVisualizer = tk.Canvas(self, width = 400, height = 400,background = 'black')
        self.imageVisualizer.grid(row = 1,column = 3,rowspan = 4,columnspan = 4,sticky='NEWS',padx = (30,30))
        self.imageVisualizer.bind('<Configure>',self.on_resize)
        self.grid_rowconfigure(1,weight=3);self.grid_columnconfigure(3,weight=2)

        self.addButton = tk.Button(self, text="+", command=self.on_add)
        self.addButton.grid(row=1, column=2, sticky='NEWS',padx=(30,15),pady=30)
        self.grid_rowconfigure(1,weight=1);self.grid_columnconfigure(2,weight=1)

        self.removeButton = tk.Button(self, text="-", command=self.on_remove)
        self.removeButton.grid(row=2, column=2, sticky='NEWS',padx=(30,15),pady=30)
        self.grid_rowconfigure(2,weight=1);self.grid_columnconfigure(2,weight=1)

        self.upButton = tk.Button(self, text="^", command=self.on_up)
        self.upButton.grid(row=3, column=2, sticky='NEWS',padx=(30,15),pady=30)
        self.grid_rowconfigure(3,weight=1);self.grid_columnconfigure(2,weight=1)

        self.downButton = tk.Button(self, text="v", command=self.on_down)
        self.downButton.grid(row=4, column=2, sticky='NEWS',padx=(30,15),pady=30)
        self.grid_rowconfigure(4,weight=1);self.grid_columnconfigure(2,weight=1)

        self.loadAudioButton = tk.Button(self, text="Select audio file", command=self.on_select_audio)
        self.loadAudioButton.grid(row = 5,column = 0,rowspan = 1,columnspan = 1,sticky='NEWS',padx = (30,15),pady = (30,15))
        self.grid_rowconfigure(5,weight=1);self.grid_columnconfigure(0,weight=1)

        self.clearAudioButton = tk.Button(self, text="Clear audio file", command=self.on_clear_audio)
        self.clearAudioButton.grid(row = 5,column = 1,rowspan = 1,columnspan = 1,sticky='NEWS',padx = (30,15),pady = (30,15))
        self.grid_rowconfigure(5,weight=1);self.grid_columnconfigure(1,weight=1)

        self.labelVideoWidth = tk.Label(self,text='Output video width (px.) -> ')
        self.labelVideoWidth.grid(row=5, column=3,columnspan = 1, sticky='EW',pady=(30,15),padx = (30,0))
        self.grid_rowconfigure(5,weight=1);self.grid_columnconfigure(3,weight=1)

        self.videoWidthInput = tk.Spinbox(self,from_=0,to = np.inf,width = 10)
        self.videoWidthInput.grid(row=5, column=4,columnspan = 1, sticky='NEWS',pady=(30,15),padx = (15,30))
        self.grid_rowconfigure(5,weight=1);self.grid_columnconfigure(4,weight=1)

        self.labelVideoHeight = tk.Label(self,text='Output video height (px.) -> ')
        self.labelVideoHeight.grid(row=5, column=5,columnspan = 1, sticky='EW',pady=(30,15))
        self.grid_rowconfigure(5,weight=1);self.grid_columnconfigure(5,weight=1)

        self.videoHeightInput = tk.Spinbox(self,from_=0,to = np.inf,width = 10)
        self.videoHeightInput.grid(row=5, column=6,columnspan = 1, sticky='NEWS',pady=(30,15),padx = (15,30))
        self.grid_rowconfigure(5,weight=1);self.grid_columnconfigure(6,weight=1)

        self.audioPathLabel = tk.Label(self,text='',background = 'white',foreground='black')
        self.audioPathLabel.grid(row=6, column = 0,rowspan = 1,columnspan = 2,sticky='NEWS',padx = (30,15),pady = (0,30))
        self.grid_rowconfigure(6,weight=1);self.grid_columnconfigure(0,weight=2)

        self.makeVideoButton = tk.Button(self, text="Make video montage", command=self.on_make_montage)
        self.makeVideoButton.grid(row=6, column = 3,rowspan = 1,columnspan = 4,sticky='NEWS',padx = (30,30),pady = (0,30))
        self.grid_rowconfigure(7,weight=1);self.grid_columnconfigure(3,weight=1)

        self.programLog = tk.Label(self,text='',background = 'black',foreground='yellow',anchor = 'nw')
        self.programLog.grid(row=7, column = 3,rowspan = 1,columnspan = 4,sticky='NEWS',padx = (30,30),pady = (30,30))
        self.grid_rowconfigure(7,weight=1);self.grid_columnconfigure(0,weight=1)


    def on_resize(self,event):
        if self.image is not None:
            self.assignImg(self.image)
    
    def on_selection_changed(self,event):
        idx = self.imageSelectionBox.curselection()[0]
        imgPath = self.imageSelectionBox.get(idx).split(' -> ')[1]
        img = cv2.imread(imgPath)
        if img is None:
            print('Error loading file: '+imgPath)
            img = np.zeros((100,100),dtype=np.uint8)
        self.assignImg(img)

    def imgFit(self,img,height,width):
        h,w = img.shape[0:2]
        aspectRatio = h/w
        if h >= w:
            nW = int(height / aspectRatio)
            if nW > width:
                nH = int(aspectRatio * width)
                nW = width
            else:
                nH = height   
        else:
            nH = int(aspectRatio * width)
            if nH > height:
                nW = int(height / aspectRatio)
                nH = height
            else:
                nW = width
        img = cv2.resize(img,(nW,nH),interpolation = cv2.INTER_LANCZOS4)
        return img

    def assignImg(self,img):   
        self.image = img
        panelWidth = self.imageVisualizer.winfo_width()
        panelHeight = self.imageVisualizer.winfo_height()
        fitImg = self.imgFit(img,panelHeight,panelWidth)
        tkimg = numpy2tkImg(fitImg)
        self.imageVisualizer.create_image(0, 0, image=tkimg, anchor='nw')
        self.imageVisualizer.image = tkimg

    def on_add(self):
        filepaths = tk.filedialog.askopenfilenames(title='Add image...',initialdir=self.initDir)
        for path in filepaths:
            nElems = self.imageSelectionBox.size()
            self.imageSelectionBox.insert(nElems,'%d -> %s' % (nElems,path))
        self.initDir = os.path.dirname(path)
        
    def on_remove(self):
        selectedElems = self.imageSelectionBox.curselection()
        if len(selectedElems) != 0:
            items = list(self.imageSelectionBox.get(0, tk.END))
            updatedItems = list()
            for j,elem in enumerate(items):
                if not j in selectedElems:
                    updatedItems.append(elem)
            
            self.setListbox(updatedItems)
            idx = max(selectedElems[0] - 1 ,0)
            self.imageSelectionBox.selection_set(idx)
            self.on_selection_changed(None)
        
    def on_up(self):
        selectedElem = self.imageSelectionBox.curselection()
        if len(selectedElem) == 1:
            selectedElem = selectedElem[0]
            if selectedElem != 0:
                items = list(self.imageSelectionBox.get(0, tk.END))
                updatedItems = items.copy()
                updatedItems[selectedElem] = items[selectedElem - 1]
                updatedItems[selectedElem - 1] = items[selectedElem]
                self.setListbox(updatedItems)
                self.imageSelectionBox.selection_set(selectedElem - 1)
                
    def on_down(self):
        selectedElem = self.imageSelectionBox.curselection()
        if len(selectedElem) == 1:
            selectedElem = selectedElem[0]
            nElems = self.imageSelectionBox.size()
            if selectedElem != nElems - 1:
                items = list(self.imageSelectionBox.get(0, tk.END))
                updatedItems = items.copy()
                updatedItems[selectedElem + 1] = items[selectedElem]
                updatedItems[selectedElem] = items[selectedElem +1]
                self.setListbox(updatedItems)
                self.imageSelectionBox.selection_set(selectedElem + 1)
    
    def on_select_audio(self):
        filepath = tk.filedialog.askopenfilename(title='Add audio file...',initialdir=self.initDir)
        self.audioPathLabel['text'] = filepath
        self.initDir = os.path.dirname(filepath)
    
    def on_clear_audio(self):
        self.audioPathLabel['text'] = ''

    def setListbox(self,elemList):
        self.imageSelectionBox.delete(0, tk.END)   
        for i,elem in enumerate(elemList):
            path = elem.split(' -> ')[1]
            self.imageSelectionBox.insert(i,'%d -> %s' % (i,path))

    def on_make_montage(self):
        self.programLog['text'] = '';self.update()
        items = list(self.imageSelectionBox.get(0, tk.END))
        audioPath = self.audioPathLabel['text']
        errMess = ''
        nImages = len(items)
        
        if nImages == 0:
            errMess += "- No input images specified!\n"

        if audioPath == '':
            errMess += "- No input audio file specified!\n"
        else:
            duration = get_audio_duration(audioPath)
            if duration == -1:
               errMess += "- Cannot load audio file: "+audioPath+" !\n"

        try:
            frame_width = int(self.videoWidthInput.get())
            frame_height = int(self.videoHeightInput.get())
            if frame_width<= 0 or frame_height <=0:
                errMess += "- Invalid output video dimensions %d x %d!\n" % (frame_width,frame_height)
        except:
            errMess += "- Invalid output video dimensions!\n"
        
        if errMess != '':
            tk.messagebox.showerror("Error", errMess)
        else:
            fps = nImages / duration
            outPath = tk.filedialog.asksaveasfilename(confirmoverwrite=False)     #### returns None is cancel button is pressed
            
            if outPath:

                if '.' in outPath: #### of outPath has an extension, remove it
                    outPath = outPath.split('.')[0]
                outPath += '.mp4' ## add mp4 extension

                tempVideoPath = os.path.join(os.path.dirname(outPath),'tempVid-aabifabifasopv.mp4')
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                videoWriter = cv2.VideoWriter(tempVideoPath,fourcc, fps = fps, frameSize=(frame_width,frame_height))
                L = self.imageSelectionBox.size()
                for k,elem in enumerate(items):
                    imgPath = elem.split(' -> ')[1]
                    self.programLog['text'] = 'Making video - Progress %.2f %' % (k/L*100);self.update()
                    try:
                        img = cv2.imread(imgPath)
                    except:
                        continue

                    in_frame = imgResize(img,(frame_height,frame_width))
                    videoWriter.write(in_frame)
            
            videoWriter.release()

            self.programLog['text'] = 'Adding audio track...';self.update()
            
            subprocess.call(['ffmpeg','-i',tempVideoPath,'-i',audioPath,'-codec','copy','-shortest',outPath])

            self.programLog['text'] = 'All done!!';self.update()
            os.remove(tempVideoPath)

if __name__ == "__main__":
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    app = imageMontageMaker(initDir = os.path.expanduser('~'))
    app.title("IMAGE MONTAGE MAKER")
    app.mainloop()
