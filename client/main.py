import threading
import tkinter as tk
from tkinter import *

import grpc
import matplotlib;
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

import protofile_pb2
import protofile_pb2_grpc

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

#Here we create global variables that will be used in the entire program
X = []
Y = []
Z = []
parts = None
#storeData will store all data from the server,
# #so that we can go back and forth
storedData = []


#This function will send request to the server
def rungrpc( x_min, x_max, y_min, y_max, steps, mytime):
    print('Yeah ! Connecting to the server baby !')
    global storedData
    global Z
    global parts
    #We create a channel, that will listen to the server port
    channel = grpc.insecure_channel("localhost:5000")
    try:
        #the client can wait for about 10 seconds before existing if the server is not responding
        grpc.channel_ready_future(channel).result(timeout=10)
    except grpc.FutureTimeoutError:
        sys.exit('Error connecting to server')
    # Create a client
    stub = protofile_pb2_grpc.ComputeFunctionStub(channel)
    #We instanciate the request object
    request = protofile_pb2.DataRequest()
    request.x_min = x_min
    request.x_max = x_max
    request.y_min = y_min
    request.y_max = y_max
    request.time = mytime
    request.steps = steps
    #Sending the request
    parts = stub.compute(request)
    #We get the response (remember, the response is a generator)
    a = next(parts)

    for elt in a.z:
        i = [i for i in elt.z]
        Z.extend([i])
    for elt in a.x:
        i = [i for i in elt.x]
        X.extend([i])
    for elt in a.y:
        i = [i for i in elt.y]
        Y.extend([i])

    ### storing data
    data=[]
    data.append(X)
    data.append(Y)
    data.append(Z)
    storedData.append(data)


   # print(Z[0])
   # print(a)
    #print(Z)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Our GRPC")
        self.ax=None
        self.canvas=None
        self.time_array=[]##
        canvas1 = tk.Canvas(self.root, width=300, height=600, bg='grey')

        canvas1.pack()

        label_x = tk.Label(self.root, text='X')
        label_y = tk.Label(self.root, text='Y')
        label_dt = tk.Label(self.root, text='Step')

        self.x_min = tk.Entry(self.root, width=16)
        self.x_max = tk.Entry(self.root, width=16)
        self.y_min = tk.Entry(self.root, width=16)
        self.y_max = tk.Entry(self.root, width=16)
        # z0 = tk.Entry (root,width=16)
        self.dt = tk.Entry(self.root, width=16)


        self.x_min_value=None
        self.x_max_value=None
        self.y_min_value=None
        self.y_max_value=None
        self.step_value=None
        self.time_value=None
        self.interval=None

        #The scale will allow to choose a time range
        self.w2 = Scale(self.root, from_=0, to=120, tickinterval=5,
                        orient=HORIZONTAL, label='Time (sec)',
                        activebackground='blue',
                        length=1000)



        #self.w2.set(0)
        self.w2.pack()

        canvas1.create_window(20, 160, window=label_x)
        canvas1.create_window(100, 160, window=self.x_min)
        canvas1.create_window(210, 160, window=self.x_max)
        canvas1.create_window(20, 200, window=label_y)
        canvas1.create_window(100, 200, window=self.y_min)
        canvas1.create_window(210, 200, window=self.y_max)
        # canvas1.create_window(100, 240, window=z0)
        canvas1.create_window(20, 240, window=label_dt)
        canvas1.create_window(100, 240, window=self.dt)
        #button1 = tk.Button(text='Start', width=16)
        #canvas1.create_window(100, 320, window=button1)

        canvas1.pack(side=tk.LEFT)

        self.line=None
        #the start button, once, pressed, will start the startProcess
        self.button1 = tk.Button(text='Start', width=16, command=self.startProcess)
        canvas1.create_window(100, 320, window=self.button1)

        self.fig = plt.figure()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        self.ani = None
        #this thread will allow us to run the animation method in a different a thread, independently from the main
        self.myThread = threading.Thread(target=self.animation, daemon=True)

        self.root.mainloop()

    def startProcess(self):
        #the first draw
        self.startDraw()
        time.sleep(1)
        #then, we launch the thread for animation
        self.myThread.start()
        ##self.animation()

    def startDraw(self):
        print('Initialization...')
        self.x_min_value=float(self.x_min.get())
        self.x_max_value=float(self.x_max.get())
        self.y_min_value=float(self.y_min.get())
        self.y_max_value=float(self.y_max.get())
        self.step_value=int(self.dt.get())
        self.time_value=int(self.w2.get())
        self.interval=int(self.time_value/self.step_value)

        self.w2.set(0)
        #We get the first data from the server
        rungrpc(
            self.x_min_value, self.x_max_value, self.y_min_value,
            self.y_max_value, self.step_value, self.time_value
        )
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.X, self.Y, self.Z = np.array(X), np.array(Y), np.array(Z)

        # self.canvas.get_tk_widget().create_rectangle(200, 100, 700, 500, fill="BLUE")
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


        self.button1.destroy()
        #self.canvas.get_tk_widget().pack(side=tk.RIGHT)

        #the plot
        self.line = self.ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                                         cmap='winter', edgecolor='none')
        return self.line

    def animation(self):
        #for animation, it will try to recreate a new plot each 1 second
        self.ani = animation.FuncAnimation(self.fig, self.data, fargs=(self.Z, self.line), interval=self.interval*1000, blit=False)


    def data(self, i, z, line):
        #if there are new data from this function will plot a new graph
        self.w2.set(self.w2.get()+self.interval if self.w2.get()!=self.time_value else self.w2.get())
        time=[i for i in range(self.w2.get()-self.interval+1, self.w2.get()+1)]
        self.time_array.append(time)
        #Once the time's passed, the animation will be stopped immediately
        if (self.w2.get()>=self.time_value):
            print("!!! No more data from the server. Animation to be stopped. !!!")
            self.ani.event_source.stop()
            #print(self.time_array)
            #And the scale will be bound to the updateValue method, so that we can go and fourth
            self.w2.bind("<ButtonRelease-1>", self.updateValue)
        else:
            print('Checking new data from the server')
            try:
                a = next(parts)
                X,Y,Z=[],[],[]
                for elt in a.z:
                    i = [i for i in elt.z]
                    Z.extend([i])
                for elt in a.x:
                    i = [i for i in elt.x]
                    X.extend([i])
                for elt in a.y:
                    i = [i for i in elt.y]
                    Y.extend([i])
                data = []
                data.append(X)
                data.append(Y)
                data.append(Z)
                storedData.append(data)
                self.X, self.Y, self.Z = np.array(X), np.array(Y), np.array(Z)
                self.line = self.ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                                                 cmap='winter', edgecolor='none')
                return self.line
            except:
                self.line = self.ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                                                 cmap='winter', edgecolor='none')
                return self.line

    #This function will help us to go back and forth
    #by changing the time value on scale
    def updateValue(self, event):
        i=None
        index=int(self.w2.get())

        for arr in self.time_array:
            if index in arr:
                i=self.time_array.index(arr)
                break
        if index==0:
            i=0
        #if i==None:
        #    i=0

        self.ax.clear()
        self.canvas.get_tk_widget().destroy()
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas=FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.NONE, expand=1)
        try:
            self.X, self.Y, self.Z = np.array(storedData[i][0]), np.array(storedData[i][1]), np.array(storedData[i][2])
            self.line = self.ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                                            cmap='winter', edgecolor='none')

            return self.line,
        except:
            #self.X, self.Y, self.Z=np.array([0]),np.array([0]),np.array([0])
            self.X, self.Y, self.Z = np.array(storedData[self.step_value-1][0]), np.array(storedData[self.step_value-1][1]), np.array(storedData[self.step_value-1][2])
            self.line = self.ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                                             cmap='winter', edgecolor='none')

            return self.line,


if __name__ == '__main__':
    app = App()
    app.exec_()

    #rungrpc(10, 10, -6, 6, -6, 6)
