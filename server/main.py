from concurrent import futures
import logging
import grpc
import time
import numpy as np

#The server
import protofile_pb2
import protofile_pb2_grpc


import numpy as np
from math import *

class ComputeFunctionServicer(protofile_pb2_grpc.ComputeFunctionServicer):

    def __init__(self):
        pass

    #function to compute z with data from request sent by client
    def z_function(self, X, Y, t):
        #here our function z=cos(x).sin(y)
        return np.cos(X) * np.sin(Y)+t*np.cos(X)

    #The role of this function is to return z to the client,
    #rememebr it's the function prior definded in the protofile
    def compute(self, request, context):
        print('Server called, Data received from client :')
        print("Time :",request.time)
        print("Steps :", request.steps)
        print("x_min :", request.x_min)
        print("x_max :", request.x_max)
        print("y_min :", request.y_min)
        print("y_max :", request.y_max)
        x=np.linspace(request.x_min, request.x_max, 120)
        y=np.linspace(request.y_min, request.y_max, 120)


        #We compute the interval of time
        #p.s after how many seconds the server must return new data
        interval = int(request.time / request.steps)
        steps=request.steps

        self.X, self.Y = np.meshgrid(x,y)


        i=1
        #we send data as server-streaming depending on steps sent by client
        while i<=request.steps:
            response = protofile_pb2.DataResponse()
            z = self.z_function(self.X, self.Y, i*interval)
            x = self.X.tolist()
            y = self.Y.tolist()
            z = z.tolist()


            for xarr in x[:int(120*i/steps)]:
                xr = protofile_pb2.xarray()
                xr.x.extend(xarr[:int(120*i/steps)])
                response.x.extend([xr])

            for yarr in y[:int(120*i/steps)]:
                yr = protofile_pb2.yarray()
                yr.y.extend(yarr[:int(120*i/steps)])
                response.y.extend([yr])

            for zarr in z[:int(120*i/steps)]:
                zr = protofile_pb2.zarray()
                zr.z.extend(zarr[:int(120*i/steps)])
                response.z.extend([zr])
            if i>0:
                time.sleep(interval)
            #The response is sent as a generator (generator in python is an iterator that's consumed only once)
            yield response
            print('Z ', i,'sent to client after ',interval, 'secs ')
            i+=1



# Create a server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

protofile_pb2_grpc.add_ComputeFunctionServicer_to_server(ComputeFunctionServicer(), server)

print('Starting server. Listening on port 5000 - Streaming ')

#We attribute the port to the server
server.add_insecure_port('[::]:5000')
#We start the server
server.start()

try:
    while True:
        time.sleep(86400)
except:
    server.stop(0)

