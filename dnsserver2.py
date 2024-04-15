#!/usr/bin/env python3

# The DNS server that will handle input of ports and ip addresses

import socket, struct, argparse, time, sys, subprocess
from dnslib import DNSRecord, DNSHeader, DNSQuestion, RR, A, QTYPE

# GLOBAL VARIABLES
cache = {
    "cdn-http3.khoury.northeastern.edu" : {"ip": "45.33.55.171", "expirationTime": time.time()},
    "cdn-http16.khoury.northeastern.edu" : {"ip": "192.46.221.203", "expirationTime": time.time()},
    "cdn-http15.khoury.northeastern.edu" : {"ip": "192.53.123.145", "expirationTime": time.time()},
    "cdn-http7.khoury.northeastern.edu" : {"ip": "213.168.249.157", "expirationTime": time.time()},
    "cdn-http4.khoury.northeastern.edu" : {"ip": "170.187.142.220", "expirationTime": time.time()},
    "cdn-http11.khoury.northeastern.edu" : {"ip": "139.162.82.207", "expirationTime": time.time()},
}  # Cache with the following format {hostname: {expirationTime, ip}}
dn = "cdn-http3.khoury.northeastern.edu"
domain = "cs5700cdn.example.com"

class DnsServer:
    def __init__(self, port, cdnname):
        self.port = port
        self.name = domain
        self.cache = cache
        self.ttl = 300 # The time to live for cache entries

    def dns_query(self, data, ipAddress):
        # Parse the incoming query
        query = DNSRecord.parse(data)
        
        # Prepare a response based on the query
        response = query.reply()
        qtype = query.q.qtype
        qname = str(query.q.qname)
        
        if qtype == QTYPE.A: #Redundant Check 
            # Create an A record with the desired IP address
            a_record = RR(qname, QTYPE.A, rdata=A(ipAddress), ttl=300)
            
            # Add the A record to the response
            response.add_answer(a_record)
        
        print(response)
        return response.pack()



    '''
    Run function => breaks down to call everything else 
    ç
    1. initialize a socket for listening 
    2. bind the socket using specified port range only 
    3. Attempt to get an ip address for the given CDN
    4. Handle all connections coming from that cdn

    name port -> none
    '''
    def run(self, name, port):
        
        # Initialize the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', port)) # Bind the socket to the specified port
        print("Gets here")
        ipAddress = self.getIp(dn) #Get the ip from the cache or googles DNS
        self.update_cache(dn, ipAddress) #Change the time or ip if new 


        try: ##See if we can get data 
            while True:
                print(F"Waiting for Data...") 
                data, addr = sock.recvfrom(512) ##Get the data 
                print(f"Data is ... {data}")
                response = self.dns_query(data, ipAddress) # Create a dns query 
                try:
                    sock.sendto(response, addr)
                    print("Response sent successfully.")
                except Exception as e:
                    print(f"Error sending response: {e}")
        except KeyboardInterrupt:
            print("Shutting down the server...")
        finally:
            sock.close()
    '''
    Get the ip address given the hostname

    1. check if it has expired or isnt there
    2. if it has then throw an error so that we can catch it above
    3. otherwise get the ip address

    name -> none
    '''

    def getIp(self, name):
        print(name)
        if name in cache: #and cache[name]['expirationTime'] > time.time():
            print("HERE THO?")

            all_ip = [entry["ip"] for entry in cache.values()] # list of ips
            min_latency = float('inf') #set minimum to infinity
            best_ip = None

            for ip in all_ip: # Go through all ips
                latency = self.get_latency(ip) 
                if latency < min_latency:  # if we found the lowest
                    min_latency = latency
                    best_ip = ip # set it as the best one so far
            if best_ip is None:
                print('idk boss couldnt find an ip')
            
            return best_ip


            request = DNSRecord.question(name, 'A')
            packet = request.pack() #make it a sendable format
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)  #in case it can't find it
            address = ('8.8.8.8',  53)
            sock.sendto(packet,address)

            response, _  = sock.recvfrom(512)
            dnsr = DNSRecord.parse(response)

            for reply in dnsr.rr:
                if reply.rtype == QTYPE.A:
                    return  str(reply.rdata)

            raise Exception('Could not resolve IP Address for %s'%name)
        

    '''
        Get the latency for a server
        parse the output of ping to get the latency
    '''
    def get_latency(self, ip):
        try:
            # Ping the server
            resp = subprocess.run(['ping', '-c', '4', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if resp.returncode == 0: # on success
                output = resp.stdout.decode('utf-8') # decode output
                lines = output.split('\n')
                for line in lines:
                    if 'min/avg/max/mdev' in line: # last line of output
                        pingtime = line.split(' ')[3].split('/')[1]
                        return float(pingtime)
        except Exception as e:
            print(f'Error with latency. IP: {ip} \nError: {e}')

        return float('inf') # on error return infinity so that this ip is not selected

    '''
    Update the cache by updating the time and the ip address if it has changed
    this will allow things to be maintained for longer if they are being used 

    1. just reset the values in the hashmap

    name ip -> none
    '''

    def update_cache(self, name, ip):
        cache[name] = {'ip': ip, 'expireTime': time.time() + self.ttl}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple DNS Server")
    parser.add_argument("-p", "--port", type=int, required=True, help="Port number the DNS server will listen on")
    parser.add_argument("-n", "--name", type=str, required=True, help="The CDN-specific name to resolve")
    args = parser.parse_args()

    if not (20090 <= args.port <= 20099):
        print("Please stay within our given port range")
        sys.exit(1) 
    if args.name != "cs5700cdn.example.com":
        print("Wrong domain name idiot")
        sys.exit(1)

    server = DnsServer(args.name, args.port)
    server.run(args.name, args.port)