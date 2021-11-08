import sys
import threading

import tkinter as tk
from tkinter import *
import grpc
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import matplotlib;

import protofile_pb2, protofile_pb2_grpc

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

X = []
Y = []
Z = []
parts = None


def rungrpc(mytime, steps, x_min, x_max, y_min, y_max):
    print('Yeah !')
    global Z
    global parts
    channel = grpc.insecure_channel("localhost:5000")
    try:
        grpc.channel_ready_future(channel).result(timeout=10)
    except grpc.FutureTimeoutError:
        sys.exit('Error connecting to server')

    stub = protofile_pb2_grpc.ComputeFunctionStub(channel)
    request = protofile_pb2.DataRequest()
    request.x_min = x_min
    request.x_max = x_max
    request.y_min = y_min
    request.y_max = y_max
    request.time = mytime
    request.steps = steps

    parts = stub.compute(request)

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
   # print(a)
    print(Z)


class App:
    def __init__(self):
        root = tk.Tk()
        root.title("Our GRPC")
        canvas1 = tk.Canvas(root, width=300, height=600, bg='blue')

        canvas1.pack()

        label_x = tk.Label(root, text='X')
        label_y = tk.Label(root, text='Y')
        label_dt = tk.Label(root, text='Step')

        x_min = tk.Entry(root, width=16)
        x_max = tk.Entry(root, width=16)
        y_min = tk.Entry(root, width=16)
        y_max = tk.Entry(root, width=16)
        # z0 = tk.Entry (root,width=16)
        dt = tk.Entry(root, width=16)

        self.w2 = Scale(root, from_=0, to=120, tickinterval=5,
                        orient=HORIZONTAL, label='Time (sec)',
                        activebackground='blue',
                        length=1000)
        self.w2.set(0)
        self.w2.pack()

        canvas1.create_window(20, 160, window=label_x)
        canvas1.create_window(100, 160, window=x_min)
        canvas1.create_window(210, 160, window=x_max)
        canvas1.create_window(20, 200, window=label_y)
        canvas1.create_window(100, 200, window=y_min)
        canvas1.create_window(210, 200, window=y_max)
        # canvas1.create_window(100, 240, window=z0)
        canvas1.create_window(20, 240, window=label_dt)
        canvas1.create_window(100, 240, window=dt)
        button1 = tk.Button(text='Start', width=16)
        canvas1.create_window(100, 320, window=button1)
        # canvas1.create_rectangle(200, 100, 700, 500, fill="RED")

        canvas1.pack(side=tk.LEFT)

        def startDraw():
            print(x_min.get())
            # self.canvas.get_tk_widget().create_rectangle(200, 100, 700, 500, fill="BLUE")
            self.canvas.get_tk_widget().pack(side=tk.RIGHT)

        button1 = tk.Button(text='Start', width=16, command=startDraw)
        canvas1.create_window(100, 320, window=button1)


        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')

        grpcThread = threading.Thread(target=self.run)
        grpcThread.start()
        time.sleep(2)

        self.X, self.Y, self.Z = np.array(X), np.array(Y), np.array(Z)
        self.line = self.ax.plot_surface(self.X, self.Y, self.Z, rstride=1, cstride=1,
                                         cmap='winter', edgecolor='none')
        print(len(self.Z))
        print('Data Received')
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        # self.canvas.get_tk_widget().create_rectangle(200, 100, 700, 500, fill="BLUE")
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ani = None

        myThread = threading.Thread(target=self.animation)
        myThread.start()

        root.mainloop()

    def run(self):
        print('Calling gRPC')
        rungrpc(10, 10, -6, 6, -6, 6)

    def animation(self):
        # time.sleep(2)
        self.ani = animation.FuncAnimation(self.fig, self.data, fargs=(self.Z, self.line), interval=1000, blit=False)

    def data(self, i, z, line):
        # z = np.sin(x+y+i)
        # print('Checking for new data from the server :) ')
        # print('The length of Z: ',len(Z))
        time.sleep(4)
        # self.Z = np.cos(self.X) * np.sin(self.Y)
        try:

            self.Z = np.array(Z)
            self.ax.clear()
            print(len(self.Z))
            self.X = X
            self.Y = Y
            self.line = self.ax.plot_surface(self.X, self.Y, self.Z, cmap='summer')
            print('Data received')

            return self.line
        except:
            # self.ax.clear()
            print(len(self.Z))
            self.line = self.ax.plot_surface(self.X, self.Y, self.Z, cmap='spring')
            print('Data not received yet, Waiting ')
            return self.line
        # finally:
        #    return self.line,


if __name__ == '__main__':
    app = App()
    app.exec_()

    #rungrpc(10, 10, -6, 6, -6, 6)
