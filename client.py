from Pyro5.api import Proxy

# RUN THIS FILE AFTER server.py

if __name__ == "__main__":
    print("Pulling objects from pyro server \n")
    process0 = Proxy("PYRONAME:process.0")
    print(process0)
    process1 = Proxy("PYRONAME:process.1")
    print(process1)
    process2 = Proxy("PYRONAME:process.2")
    print(process2)
    mutexmanager = Proxy("PYRONAME:mutexmanager")
    print(mutexmanager)

    try:
        print("testing lamport mutex algo...")
        process0.set_mutex_manager(mutexmanager)
        process1.set_mutex_manager(mutexmanager)
        process2.set_mutex_manager(mutexmanager)
        process0.request_critical_section()
        process1.request_critical_section() 
        process2.request_critical_section() 
        process0.release_critical_section() # manually release critical section
        process0.request_critical_section()
        process1.release_critical_section() # manually release critical section
        process2.release_critical_section() # manually release critical section
        process0.release_critical_section() # manually release critical section
        
        # release one more time to check that no process is in the critical section
        
        process0.release_critical_section() # manually release critical section
        process1.release_critical_section() # manually release critical section
        process2.release_critical_section() # manually release critical section

        print("ending test of lamport mutex algo")
        
    except Exception as e:
        print(f"error: {e}")
    
