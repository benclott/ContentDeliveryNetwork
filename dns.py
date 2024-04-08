#!/usr/bin/env python3

# The DNS server that will handle input of ports and ip addresses

import socket, struct, argparse, time, sys

# GLOBAL VARIABLES
cache = {}  # Cache with the following format {hostname: {expirationTime, ip}}
ttl = 300.0  # The time to live for cache entries

def dns_query(data, ip_address):
    tid = data[:2]
    flags = 0x8180  # Standard DNS response flags: response, recursion desired, recursion available
    questions = 1
    answers = 1
    authority_rrs = 0
    additional_rrs = 0
    dns_header = struct.pack("!HHHHHH", tid, flags, questions, answers, authority_rrs, additional_rrs)
    question_section = data[12:]
    answer_section = struct.pack("!HHHLH4s", 0xc00c, 1, 1, ttl, 4, socket.inet_aton(ip_address))
    return dns_header + question_section + answer_section


'''
Send responses

sock ip -> none
'''
def handle_connection(sock, ip_address):
    data, addr = sock.recvfrom(512)
    response = dns_query(data, ip_address)
    sock.sendto(response, addr)


'''
Run function => breaks down to call everything else 

1. initialize a socket for listening 
2. bind the socket using specified port range only 
3. Attempt to get an ip address for the given CDN
4. Handle all connections coming from that cdn

name port -> none
'''
def run(name, port):
    # Initialize the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the specified port
    sock.bind(('', port))
    
    # Resolve the IP address for the given CDN name
    try:
        ipAddress = getIp(name)
    except ValueError:
        ipAddress = socket.gethostbyname(name)
        update_cache(name, ipAddress)

    print(f"DNS server running on port {port}, directing to {ipAddress}")
    
    try:
        while True:
            handle_connection(sock, ipAddress)
    finally:
        sock.close()

'''
Get the ip address given the hostname

1. check if it has expired or isnt there
2. if it has then throw an error so that we can catch it above
3. otherwise get the ip address

name -> none
'''

def getIp(name):
    if name in cache and cache[name]['expireTime'] > time.time():
        return cache[name]['ip']
    else:
        raise ValueError("The cache entry is missing or expired.")

'''
Update the cache by updating the time and the ip address if it has changed
this will allow things to be maintained for longer if they are being used 

1. just reset the values in the hashmap

name ip -> none
'''

def update_cache(name, ip):
    cache[name] = {'ip': ip, 'expireTime': time.time() + ttl}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple DNS Server")
    parser.add_argument("-p", "--port", type=int, required=True, help="Port number the DNS server will listen on")
    parser.add_argument("-n", "--name", type=str, required=True, help="The CDN-specific name to resolve")
    args = parser.parse_args()

    if not (20090 <= args.port <= 20099):
        print("Please stay within our given port range")
        sys.exit(1) 

    run(args.name, args.port)
