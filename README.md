# HAproxy + LetsEncrypt + SQRL

(the SQRL part doesn't work at all yet, but I'll finish that one day)

Eventually I want to do something smart to automatically generate haproxy.cfg so that i can do cool stuff with autoscaling, but I don't need that right now. Hard coded works fine.

I also want to get it so that deploys aren't needed. It would be better to modify the haproxy config in the container and then reload. I think I'll want my own script that reads a consul cluster or something like that to get fqdn to server mappings. ZeroTier should make it really easy for all the systems to communicate with eachother.


# Adding a new domain

1. Setup a docker container
    * if its a simple static site, add it to the same docker-compose group as haproxy
    * if it is a more complicated application, give it its own file

2. add the domain to domain2backend.map

3. add a new backend for the domain to haproxy.cfg

4. Deploy with something like `docker-compose up -d`

5. `docker-compose exec -e EMAIL=root@example.com haproxy-ssl certbot-haproxy.py`

6. uncomment port 443 and the path to the new ssl certs and the security settings in haproxy.cfg

7. Deploy again `docker-compose up -d`
