import sys
import os
import serial
import threading
import socket
import logging
import signal

log = logging.getLogger('serial2tcp')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)


class Redirector:
    def __init__(self, serial, socket):
        self.serial = serial
        self.socket = socket

    def shortcut(self):
        """connect the serial port to the tcp port by copying everything
           from one side to the other"""
        self.alive = True
        self.thread_read = threading.Thread(target=self.reader)
        self.thread_read.setDaemon(1)
        self.thread_read.start()
        self.writer()

    def reader(self):
        """loop forever and copy serial->socket"""
        while self.alive:
            try:
                #read one, blocking
                data = self.serial.read(1)
                #look if there is more
                n = self.serial.inWaiting()
                if n:
                    #and get as much as possible
                    data = data + self.serial.read(n)
                if data:
                    #send it over TCP
                    self.socket.sendall(data)
            except socket.error as msg:
                log.error(msg)
                #probably got disconnected
                break
        self.alive = False

    def writer(self):
        """loop forever and copy socket->serial"""
        while self.alive:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                self.serial.write(data)  # get a bunch of bytes and send them
            except socket.error as msg:
                log.error(repr(msg))
                break
            except Exception as e:
                log.critical(repr(e))
                break

        self.alive = False
        self.thread_read.join()

    def stop(self):
        """Stop copying"""
        if self.alive:
            self.alive = False
            self.thread_read.join()

if __name__ == '__main__':
    from optparse import OptionParser
    ser = serial.Serial()

    descr = 'WARNING: You have to allow connections only from the addresses' \
            'in the "--allow-list" option. e.g.' \
            '--allow-list="10.0.0.1, 172.16.0.1, 192.168.0.1"\n' \
            'NOTICE: This service supports only ' \
            'one tcp connection per instance.'

    usage = "USAGE: %prog [options]\n\nSimple Serial to Network (TCP/IP)" \
            "redirector."

    parser = OptionParser(usage=usage, version='%prog 0.5', description=descr)
    parser.add_option("-p", "--port", dest="serial",
                      help="Serial port, a number, defualt = 'COM5'", type=str, default='COM5')
    parser.add_option("-b", "--baud", dest="baudrate",
                      help="Baudrate, default 115200", default=115200, type=int)
    parser.add_option("-r", "--rtscts", dest="rtscts",
                      help="Enable RTS/CTS flow control (default off)", action='store_true', default=False)
    parser.add_option("-x", "--xonxoff", dest="xonxoff",
                      help="Enable software flow control (default off)", action='store_true', default=False)
    parser.add_option("-P", "--localport", dest="port",
                      help="TCP/IP port on which to run the server (default 8282)", type=int, default=8282)
    parser.add_option("-l", "--listen", dest="listen",
                      help="Listen address on which to run the server (default '0.0.0.0')", type=str, default='0.0.0.0')
    parser.add_option(
        '--access-list', dest='acl', type=str, default="192.168.7.220",
        help="List of IP addresses e.g '127.0.0.1, 192.168.0.2'")

    (options, args) = parser.parse_args()

    ser.port = options.serial
    ser.baudrate = options.baudrate
    ser.rtscts = options.rtscts
    ser.xonxoff = options.xonxoff

    access_list = set([ip.strip(" ") for ip in options.acl.split(',')])

    #required so that the reader thread can exit
    ser.timeout = 1

    log.info("TCP/IP to Serial redirector (Ctrl-C to quit)")

    try:
        ser.open()
    except serial.SerialException as e:
        log.fatal("Could not open serial port %s: %s" % (ser.portstr, e))
        sys.exit(1)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((options.listen, options.port))
    srv.listen(1)

    def signal_handler(signal, frame):
        try:
            srv.close()
        except Exception as e:
            log.warning(repr(e))
        finally:
            sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while 1:
        try:
            log.info("Waiting for connection...")
            connection, addr = srv.accept()
            address, port = addr
            log.info('Connecting with tcp://{0}:{1}'.format(address, port))
            if address in access_list:
                #enter console->serial loop
                r = Redirector(ser, connection)
                r.shortcut()
            else:
                log.error('Address {0} not in access list.'.format(address))
        except socket.error as msg:
            log.error(msg)
        finally:
            try:
                connection.close()
                log.info('Disconnecting')
            except NameError:
                pass
            except Exception as e:
                log.warning(repr(e))







#"""
#tsb.py -- A telnet <-> serial port bridge
#Copyright (C) 2005 Eli Fulkerson
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#----------------------------------------------------------------------
#Other license terms may be negotiable.  Contact the author if you would
#like copy that is licensed differently.
#Additionally, this script requires the use of "pyserial", which is licensed
#separately by its author.  This library can be found at http://pyserial.sourceforge.net/
#Contact information (as well as this script) lives at http://www.elifulkerson.com
#"""

## standard libraries
#from socket import *
#from select import *
#from string import *
#import sys
#from getopt import getopt, GetoptError

## nonstandard library
#import serial

#"""
#print usage, then exit
#"""
#def usage():
#    usagestring = """Usage: tsb [OPTIONS]
#Creates a TCP<->Serial port bridge, which allows a telnet client to
#cross over a Serial port.
#Serial Options:
#   -p, --port     :  Specify the desired serial port.
#                     (0 for COM1, 1 for COM2 etc)
#   -r, --baudrate :  Specify baudrate
#   -s, --bytesize :  Specify bytesize
#   -y, --parity   :  Specify parity options
#   -b, --stopbits :  Specify number of stopbits
#   -t, --timeout  :  Specify timeout
#   -f, --flow     :  Specify flow-control options
   
#TCP Options:
#   -l, --listen   :  Specify a TCP port to listen on
#General Options:
#   -h, --help     :  Display this help messsage
#"""
#    print usagestring
#    sys.exit(0)



#"""
#Function cleans up telnet's output for input into the serial port.
#Telnet is fancier than serial, so we have to strip some things out.
#"""
#def cleanup_for_serial(text):
#    """
#    chr(255) is the "we are negotiating" leading bit.  If it is the first bit in
#    a packet, we do not want to send it on to the serial port
#    """
#    if ord(text[:1]) == 255:
#        return ""

#    """
#    For some reason, windows likes to send "cr/lf" when you send a "cr".
#    Strip that so we don't get a double prompt.\
#    """
#    text = replace(text, chr(13) + chr(10), chr(13))

    
#    return text


#class Connection:
#    "A connection is a class that forwards requests between TCP and Serial"
#    def __init__(self, socket, com):
#        self.socket = socket
#        self.com = com

#    def fileno(self):
#        "Required, look it up"
#        return self.socket.fileno()

#    def init_tcp(self):
#        "Set up the TCP connection and do telnet negotiation"

#        "telnet negotiation:  we don't want linemode"
#        "      COMMAND,   DONT,      linemode"
#        data = chr(255) + chr(254) + chr(34)
#        self.socket.send(data)

#        "telnet negotation:  we don't want local echo"
#        "      COMMAND,   DONT,      echo"
#        data = chr(255) + chr(254) + chr(1)
#        self.socket.send(data)

#        "send the header"
#        self.socket.send("************************************************\r\n")
#        self.socket.send("Telnet <--> Serial Bridge by Eli Fulkerson\r\n")
#        self.socket.send("http://www.elifulkerson.com for updates       \r\n")
#        self.socket.send("\r\n")
#        self.socket.send("This program uses non-standard python libraries:\r\n")
#        self.socket.send("   - pyserial by Chris Liechti\r\n")
#        self.socket.send("   - pywin32 by Mark Hammond (et al)\r\n")
#        self.socket.send("\r\n")
#        self.socket.send("************************************************\r\n")

#        self.socket.send("\r\n")
#        self.socket.send("You are now connected to %s.\r\n" % self.com.portstr)
        


#    def recv_tcp(self):
#        "Receive some data from the telnet client"
#        data =  self.socket.recv(1024)
#        return data

#    def send_tcp(self, data):
#        "Send some data out to the telnet client"
#        self.socket.send(data)

#    def recv_serial(self):
#        "Recieve some data from the serial port"
#        data = self.com.read(self.com.inWaiting() )
#        return data

#    def send_serial(self,data):
#        "Send some data out to the serial port"
#        data = cleanup_for_serial(data)

#        try:
#            if ord(data) == 3:
#                self.com.sendbreak()
#		return
#        except:
#            pass


#        self.com.write(data)

    

#class Handler:
#    def __init__(self):
#        global LISTEN
#        global com
        
#        self.clist = [ ]
#        self.tcpconnected = False
#        self.serialconnected = False

#        self.start_new_listener()
        
#        print "TCP to Serial bridge is up: telnet to localhost:%s to access %s." % (LISTEN, com.portstr)
#        print "(Control-C to exit)"

#    def start_new_listener(self):
#        self.listener = socket(AF_INET, SOCK_STREAM)
#        self.listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#        self.listener.bind(('', LISTEN))
#        self.listener.listen(32)

#    def run(self):
#        """
#        yes, this was originally going to be multi-user, I don't feel like changing it
#        now though.  We shall loop.
#        """
#        for conn in self.clist[:]:
#            if conn.com.isOpen():
#                "pull data from serial and send it to tcp if possible"
#                data = conn.recv_serial()
#                if not data:
#                    pass
#                else:
#                    conn.send_tcp(data)

#        ready = self.clist[:]

#        if self.listener:
#            ready.append(self.listener)
            
#        ready = select(ready, [], [], 0.1)[0]
#        for conn in ready:
#            if conn is self.listener:
#                socket, address = self.listener.accept()


#                global com

#                try:
#                    com.close()
#                    com.open()
#                except serial.SerialException:
#                    print "Error opening serial port.  Is it in use?"
#                    sys.exit(1)
                
                
#                conn = Connection(socket, com)
#                self.clist.append(conn)

#                "set up our initial telnet environment"
#                conn.init_tcp()

#                "we don't need to listen anymore"
#                self.listener = None

#            else:
#                "pull some data from tcp and send it to serial, if possible."
#                data = conn.recv_tcp()
#                if not data:
#                    print "TCP connection closed."
#                    self.clist.remove(conn)
#                    self.start_new_listener()

                    
#                else:
#                    conn.send_serial(data)

        
#def main(argv=None):

#    "Pull in our arguments if we were not spoonfed some"
#    if argv is None:
#        argv = sys.argv

#    "Parse our arguments"
#    try:
#        options, args = getopt(argv[1:], "p:r:s:y:b:t:f:l:h", ["port=", "baudrate=", "bytesize=", "parity=", "stopbits=", "timeout=", "flow=", "listen=", "help"])
#    except GetoptError:
#        usage()
#        return    

#    global LISTEN  # int, the TCP port to listen on
#    global com     # the serial connection itself


#    "first, loop through and open the right port"
#    got_a_serial_port = False
#    for o,a in options:
#        if o in ("-p", "--port"):
#            a = int(a)
#            try:
#                com = serial.Serial(a)
#                #print "Serial port opened: %s" % (com.portstr)
#                got_a_serial_port = True
#            except:
#                print "Couldn't open serial port: %s" % (a)
#                print "This should be a numerical value.  0 == COM1, 1 == COM2, etc"
#                sys.exit(1)
#        if o in ("-h", "--help"):
#            usage()
#            return

#    if not got_a_serial_port:
#        # we don't have a port.  Fine, use the default.
#        try:
#            com = serial.Serial("COM5")
#            #print "Serial port opened: %s" % (com.portstr)
#        except:
#            print "Couldn't open serial port: %s" % (0)
#            sys.exit(1)


#    # sensible defaults
#    com.baudrate = 115200
#    com.timeout = 0
#    com.bytesize = serial.EIGHTBITS
#    com.parity = serial.PARITY_NONE
#    com.stopbits = serial.STOPBITS_ONE
#    com.xonxoff = 0
#    com.rtscts = 0
#    LISTEN = 8282      

#    # now loop through the other options   
#    for o,a in options:
        
#        if o in ("-l", "--listen"):
#            a = int(a)
#            if a < 1 or a > 65535:
#                print "Invalid listening (tcp) port.  Valid ports are 1-65535"
#                sys.exit(1)
#            else:
#                LISTEN = a
            
#        if o in ("-r", "--baudrate"):
#            a = int(a)
#            if a in com.BAUDRATES:
#                #print "Setting baudrate to %s." % (a)
#                com.baudrate = a
#            else:
#                print "Valid baudrates are:", com.BAUDRATES
#                sys.exit(1)

#        if o in ("-s", "--bytesize"):
#            a = int(a)
#            if a in com.BYTESIZES:
#                #print "Setting bytesize to %s." % (a)
#                com.bytesize = a
#            else:
#                print "Valid bytesizes are:", com.BYTESIZES
#                sys.exit(1)

#        if o in ("-y", "--parity"):
#            if a in com.PARITIES:
#                #print "Setting parity to %s." % (a)
#                com.parity = a
#            else:
#                print "Valid parities are:", com.PARITIES
#                sys.exit(1)

#        if o in ("-b", "--stopbits"):
#            a = float(a)
#            if a in com.STOPBITS:
#                #print "Setting stopbits to %s." % (a)
#                com.stopbits = a
#            else:
#                print "Valid stopbits are:", com.STOPBITS
#                sys.exit(1)

#        if o in ("-t", "--timeout"):
#            a = int(a)
#            if a < 0 or a > 100:
#                print "Valid timesouts are 0-100."
#                sys.exit(1)
#            else:
#                com.timeout = a

#        if o in ("-f", "--flow"):
#            FLOWS = ("xonxoff", "rtscts", "none")
#            if a in FLOWS:
#                #print "Setting flow control to %s" % (a)

#                if a == "xonxoff":
#                    com.xonxoff = True
#                if a == "rtscts":
#                    com.rtscts = True
#            else:
#                print "Valid flow-controls are:", FLOWS
#                sys.exit(1)
#    # print out com's statistics
#    print "------------------------"
#    print "Serial Port Information:"
#    print "------------------------"
#    print "port:     %s" % com.portstr
#    print "baudrate: %s" % com.baudrate
#    print "bytesize: %s" % com.bytesize
#    print "parity:   %s" % com.parity
#    print "stopbits: %s" % com.stopbits
#    print "timeout:  %s" % com.timeout
#    print "xonxoff:  %s" % com.xonxoff
#    print "rtscts:   %s" % com.rtscts
#    print ""
#    print "------------------------"
#    print "TCP/IP Port Information:"
#    print "------------------------"
#    print "host:     %s" % "localhost"
#    print "port:     %s" % LISTEN
#    print ""


#    # start up our run loop    
#    connections = Handler()
#    while 1:
#        connections.run()


#if __name__== "__main__":
#    try:
#        main()
#    except KeyboardInterrupt:
#        print "Keyboard Interrupt"



















#from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
#from datetime import datetime, date
#import _thread
#import time
#import serial
#import _thread

#class ThreadedTCPServer(ThreadingMixIn, TCPServer):
#    pass

#class COMTCPProxyServerHandler(BaseRequestHandler):
#    def handle(self):
#        self.callback(self.server, self.request, self.client_address)

#class COMTCPProxyServer():
#    handler = COMTCPProxyServerHandler
#    data = {}

#    def __init__(self):
#        self.handler.callback = self.callback

#    def callback(self, server, request, client_address):              
#        print(f"""CONNECTED LISTENER {client_address}""")
#        print(datetime.now())

#        while True:
#            try:
#                buf = request.recv(256)
#            except:
#                break
            
#            if not buf: 
#                break
            
#            #print(buf)

#            #print(f"""-----------------------------""")

#            #print(f"""request.recv(1024*8*4)""")        
#            #print(datetime.now())
     
#            #_thread.start_new_thread(do_upd_loop, (buf, request))

#            #ser = serial.serial_for_url(SERIALPORT, do_not_open=True)
            
#            message = do(buf)

#            #ser = serial.Serial(SERIALPORT, baudrate=BAUDRATE)

#            #ser.baudrate = BAUDRATE 
            
#            #while True:
#            #    try:
#            #        ser.open()
                    
#            #        print(f"""ser.open()""")        
#            #        print(datetime.now())
                    
#            #        break
#            #    except serial.SerialException as e:
#            #        print(str(e))

#            #    time.sleep(0.01)
        
#            #res = ser.write(buf)  

#            ##print(f"""res = ser.write(buf)""")        
#            ##print(datetime.now())

#            #time.sleep(0.001)

#            ##message = ser.read(ser.inWaiting())

#            #message = ser.read_until()


#            #print(message)
            
#            #print(f"""message = ser.read(ser.inWaiting())""")        
#            #print(datetime.now())
            
#            request.sendall(message)

#            #print(f"""request.sendall(message)""")        
#            #print(datetime.now())

#            #ser.close()

#            #print(f"""ser.close()""")        
#            #print(datetime.now())

#        print(f"""DISCONNECTED LISTENER {client_address}""")

#def do(buf):
#    res = ser.write(buf)  

#            #print(f"""res = ser.write(buf)""")        
#            #print(datetime.now())

#    time.sleep(0.01)

#    message = ser.read(ser.inWaiting())

#    #message = ser.read_until()


#    #print(message)

#    return message
 
#def do_upd_loop(buf, request):
#    ser = serial.serial_for_url(SERIALPORT, do_not_open=True)

#    ser.baudrate = BAUDRATE 

#    while True:
#        try:
#            ser.open()
                    
#            print(f"""ser.open()""")        
#            print(datetime.now())
                    
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




#TCP_IP = '0.0.0.0'
#TCP_PORT = 8282
#SERIALPORT = 'COM5'
#BAUDRATE = 115200


#ser = serial.Serial(SERIALPORT, baudrate=BAUDRATE)


#if __name__ == '__main__':
#    ones_serv = COMTCPProxyServer()
#    server = ThreadedTCPServer((TCP_IP, TCP_PORT), COMTCPProxyServerHandler)
    
#    print('starting ones socket server '+str(TCP_IP)+':'+str(TCP_PORT)+' (use <Ctrl-C> to stop)')

#    server.serve_forever()
    
