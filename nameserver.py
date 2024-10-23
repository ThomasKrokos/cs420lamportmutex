import Pyro5.nameserver
# RUN THIS FILE FIRST
# Creates pyro name server that allows for easier rmi lookup
if __name__ == "__main__": 
    print("Starting Pyro5 Name Server...")
    Pyro5.nameserver.start_ns_loop()