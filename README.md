## Overview

To begin, we started with the dns server. At first this server would create a DNS query




HTTP Server

The HTTP Server recieves requests for pages from the origin website. In order to return the content to the reqestor it either retrieves it from the origin server, or relays an already saved copy in the cache. It starts by accepting requests in a loop and extracting the path that the request wants. It then sends the path to the handle_request() method. Here, if that path is stored in our cache, it will return the content that is saved in the cache. If the path is not there, it then requests the origin server for the content. Each entry in the cache is time tracked from when it gets entered. The time to live is set to 300 seconds so if an entry has been in the cahce from over 300 seconds it gets reoved in the routine cache cleanup method call.

deployCDN

This script accepts the port origin and username and will then deploy our http server onto all of the CDN servers, it does this through scp copying the file onto the server and then giving it x permissions. Our DNS server will then pick the server with the lowest latency by pinging each one during run time. It will then route the requests through the server with the least round trip time which also increases the efficiency.

## Challenges

At first, we faced some conceptual challenges in terms of understanding all of the components and how the worked together. Once we got started on the DNS server and realized that it worked independently from the HTTP server it started to become more clear. We also struggled writing the scripts in python as it was hard to execute the individual files with the correct parameters. When we converted them to bash scripts we found it much easier to run the servers in unison and deploy them amongst all servers. One of the challenges we faced was performance. We decided to implement a shelf life to the items in the chache so that it does not fill up and then become useless, when the enteries expire they can get cleared out and more curernt entries can be saved. We also added gzip encoding to the items in the cache. This way they take up less space and more things can be cached which sigificantly improves the performance.