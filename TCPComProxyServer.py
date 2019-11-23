from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
from datetime import datetime, date
import _thread
import time
#import serial
import _thread
import socket

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass

class COMTCPProxyServerHandler(BaseRequestHandler):
    def handle(self):
        self.callback(self.server, self.request, self.client_address)

class COMTCPProxyServer():
    handler = COMTCPProxyServerHandler
    data = {}

    def __init__(self):
        self.handler.callback = self.callback

    def callback(self, server, request, client_address):              
        print(f"""CONNECTED LISTENER {client_address}""")
        print(datetime.now())

        #buf = None

        #buf = bytearray(8192)
        #view = memoryview(buf)

        while True:
            try:
                buf = request.recv(4096)
            except:
                break
            
            if not buf: 
                break
            
            print(buf)

            #print(f"""-----------------------------""")

            #print(f"""request.recv(1024*8*4)""")        
            #print(datetime.now())
     
            #_thread.start_new_thread(do_upd_loop, (buf, request))

            #ser = serial.serial_for_url(SERIALPORT, do_not_open=True)
            
            #message = do(buf)

            #ser = serial.Serial(SERIALPORT, baudrate=BAUDRATE)

            #ser.baudrate = BAUDRATE 
            
            #while True:
            #    try:
            #        ser.open()
                    
            #        print(f"""ser.open()""")        
            #        print(datetime.now())
                    
            #        break
            #    except serial.SerialException as e:
            #        print(str(e))

            #    time.sleep(0.01)
        
            #ser = serial.Serial(SERIALPORT, baudrate=BAUDRATE)

            #res = ser.write(buf[0:res])  

            sock.sendall(buf)

            resp = sock.recv(4096)

            ##print(f"""res = ser.write(buf)""")        
            ##print(datetime.now())

            #time.sleep(0.001)

            #message = ser.read(ser.inWaiting())

            #message = ser.read_until()
            


            #print(message)
            #print(f"""message = ser.read(ser.inWaiting())""")        
            #print(datetime.now())
            
            request.sendall(resp)

            #print(f"""request.sendall(message)""")        
            #print(datetime.now())

            #ser.close()

            #print(f"""ser.close()""")        
            #print(datetime.now())

        print(f"""DISCONNECTED LISTENER {client_address}""")

def do(buf):
    res = ser.write(buf)  

            #print(f"""res = ser.write(buf)""")        
            #print(datetime.now())

    time.sleep(0.01)

    message = ser.read(ser.inWaiting())

    #message = ser.read_until()


    #print(message)

    return message
 
#def do_upd_loop(buf, request):
#    ser = serial.serial_for_url(SERIALPORT, do_not_open=True)

#    ser.baudrate = BAUDRATE 

#    while True:
#        try:
#            ser.open()
                    
#            #print(f"""ser.open()""")        
#            #print(datetime.now())
                    
#            break
#        except serial.SerialException as e:
#            print(str(e))

#            time.sleep(0.001)
        
#    res = ser.write(buf)  

#    print(f"""res = ser.write(buf)""")        
#    print(datetime.now())

#    #time.sleep(0.01)

#    message = ser.read(ser.inWaiting())
            
#    print(f"""message = ser.read(ser.inWaiting())""")        
#    print(datetime.now())
            
#    request.sendall(message)

#    print(f"""request.sendall(message)""")        
#    print(datetime.now())

#    ser.close()

#    print(f"""ser.close()""")        
#    print(datetime.now())




TCP_IP = '0.0.0.0'
TCP_PORT = 8284
#SERIALPORT = 'COM5'
#BAUDRATE = 115200

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('192.168.7.220', 8282)
print('connecting to {} port {}'.format(*server_address))
sock.connect(server_address)


#ser = serial.Serial(SERIALPORT, baudrate=BAUDRATE)


if __name__ == '__main__':
    ones_serv = COMTCPProxyServer()
    server = ThreadedTCPServer((TCP_IP, TCP_PORT), COMTCPProxyServerHandler)
    
    print('starting ones socket server '+str(TCP_IP)+':'+str(TCP_PORT)+' (use <Ctrl-C> to stop)')

    server.serve_forever()
    
