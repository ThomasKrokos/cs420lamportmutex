import Pyro5.api
import time
import Pyro5.server
# RUN THIS FILE AFTER nameserver.py

@Pyro5.server.expose
@Pyro5.server.behavior(instance_mode="single")
class Process(object):
    def __init__(self, pid, num_process, mutexmanager):
        print(f"created process{pid}")
        self.pid = pid  # Process ID
        self.request_queue = []  # Queue of requests (sorted by clock, pid)
        self.local_clock = 0  # Logical clock
        self.replies_received = []  # List of processes that have replied
        self.process_num = num_process
        self.has_critical_section = False  # Indicator of critical section access
        self.mutex_manager = mutexmanager  # Shared MutexManager instance

    def set_mutex_manager(self, mutex_manager):
        self._mutex_manager = mutex_manager
        
    def request_critical_section(self):
        self.local_clock += 1
        self.request_queue.append((self.local_clock, self.pid))
        self.request_queue.sort()  # Sorts by (clock, pid) to ensure top of queue is next request up
        self.mutex_manager.request(self.local_clock, self.pid)

    def release_critical_section(self):
        if self.has_critical_section:
            print(f"Process{self.pid} releasing from the critical section\n")
            self.mutex_manager.release(self.pid)
            self.has_critical_section = False
            self.replies_received = []
            self.receive_release(self.pid)
        else:
            print(f"process{self.pid} does not have access to the critical section, unable to give it up\n")

    def receive_request(self, clock, request_pid):
        # Update the logical clock and add the request to the queue
        print(f"process{request_pid}'s request received by process{self.pid} and local clock is {self.local_clock}\n")
        self.local_clock = max(self.local_clock, clock) + 1
        print(f"process{self.pid}'s local clock is now {self.local_clock}\n")
        self.request_queue.append((clock, request_pid))
        self.request_queue.sort()  # Sort by (clock, pid)

        # If the request is at the top of the queue, send a reply
        if self.request_queue[0] == (clock, request_pid):
            self.mutex_manager.reply(self.pid, request_pid)

    def receive_release(self, released_pid):
        if self.request_queue:
            self.request_queue.pop(0)  # Remove the top request from the queue
            if self.request_queue and self.request_queue[0][1] != self.pid:
                next_request = self.request_queue[0]
                print(f"after receiving process{released_pid}'s release broadcast, process{self.pid} is replying to process{next_request[1]}'s request\n")
                self.mutex_manager.reply(self.pid, next_request[1])

    def receive_reply(self, reply_pid):
        self.replies_received.append(reply_pid)
        print(f"Process{self.pid} received a reply from Process{reply_pid} for their critical access request.\n")
        if len(self.replies_received) == self.process_num - 1:
            # Received all necessary replies, process can now enter the critical section
            self.access_critical_section()

    def access_critical_section(self):
        self.has_critical_section = True
        replies_list = ', '.join([f'Process{pid}' for pid in self.replies_received])
        print(f"{replies_list} have all replied to Process{self.pid}'s request.\n")
        print(f"Process{self.pid} is now entering the critical section.\n")
        # time.sleep(1)  # Simulate doing something in the critical section
        # print(f"Process{self.pid} finished its work in the critical section")
        # self.release_critical_section() <-- optional code for auto release instead of manual release

    def get_pid(self):
        return self.pid
    def has_critical_access(self):
        return self.has_critical_access


@Pyro5.server.expose
class Process0(Process):
    def __init__(self, mutexmanager):
        super().__init__(0,3, mutexmanager)

@Pyro5.server.expose
class Process1(Process):
    def __init__(self, mutexmanager):
        super().__init__(1,3, mutexmanager)

@Pyro5.server.expose
class Process2(Process):
    def __init__(self, mutexmanager):
        super().__init__(2,3, mutexmanager)

@Pyro5.server.expose
@Pyro5.server.behavior(instance_mode="single")
class MutexManager(object):
    def __init__(self, process_num):
        self.process_num = process_num

    def request(self, clock, pid):
        print(f"Broadcasting process{pid}'s request for the critical section their clock is at {clock}.\n")
        # Broadcast request to all processes via Pyro name server lookup
        for i in range(self.process_num):
            if i != pid:
                process_uri = f"PYRONAME:process.{i}"
                process = Pyro5.api.Proxy(process_uri)
                process.receive_request(clock, pid)            

    def release(self, pid):
        
        print(f"Process{pid} asks mutexmanager to broadcast release.\n")
        # Broadcast release to all processes
        for i in range(self.process_num):
            if i != pid:
                process_uri = f"PYRONAME:process.{i}"
                process = Pyro5.api.Proxy(process_uri)
                process.receive_release(pid)

    def reply(self, pid, to_pid):
        print(f"Process{pid} is sending back a reply to Process{to_pid}.\n")
        process_uri = f"PYRONAME:process.{to_pid}"
        process = Pyro5.api.Proxy(process_uri)
        process.receive_reply(pid)



if __name__ == "__main__":
    print("please run nameserver.py first")
    mutex_manager = MutexManager(3)

    print("Registering processes and mutex manager with pyro...")
    daemon = Pyro5.server.Daemon()         
    ns = Pyro5.api.locate_ns()             
    uri = daemon.register(MutexManager)   # register the process as a Pyro object
    ns.register(f"mutexmanager", uri) 
    print(f"registered mutexmanager")
    
    urip0 = daemon.register(Process0(mutex_manager))   # register the process as a Pyro object
    ns.register(f"process.0", urip0) 
    print(f"registered process0")

    urip1 = daemon.register(Process1(mutex_manager))   # register the process as a Pyro object
    ns.register(f"process.1", urip1) 
    print(f"registered process1")
    
    urip2 = daemon.register(Process2(mutex_manager))   # register the process as a Pyro object
    ns.register(f"process.2", urip2) 
    print(f"registered process2")
    
    print("Server is ready.")
    daemon.requestLoop()
    
    