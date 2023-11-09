docker run mbed "cert_req_ca_list=/ra-tls-secret-prov/ssl/ca.crt"

 ./ssl_server2 cert_req_ca_list=/ra-tls-secret-prov/ssl/ca.crt server_port=4434
./ssl_client2 server_addr=verifierbymr.eastus2.cloudapp.azure.com ca_file=/ca.crt server_port=4434


./ssl_server2 server_port=4434