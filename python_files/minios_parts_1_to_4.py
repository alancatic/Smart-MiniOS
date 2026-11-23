# Part 1 quoted by AI for reference:
# Process Scheduling & Monitoring manages process execution order using
# scheduling algorithms and flags suspicious CPU/memory-heavy behavior.

from collections import deque
from minios_memory_backend import Process, UserProcess, SystemProcess, MemoryManager


def clone_processes(process_list):
    cloned = []
    for process in process_list:
        cloned.append({
            "pid": process.process_id,
            "name": process.name,
            "priority": process.priority,
            "arrival_time": process.arrival_time,
            "burst_time": process.burst_time,
            "remaining_time": process.burst_time,
            "memory_usage": process.memory_usage,
            "cpu_usage": process.cpu_usage,
            "disk_usage": process.disk_usage,
            "user_role": process.user_role,
            "process_type": process.get_process_type(),
            "completion_time": 0,
            "turnaround_time": 0,
            "waiting_time": 0
        })
    return cloned


def finalize_process_metrics(process_record):
    process_record["turnaround_time"] = (
        process_record["completion_time"] - process_record["arrival_time"]
    )
    process_record["waiting_time"] = (
        process_record["turnaround_time"] - process_record["burst_time"]
    )


def priority_round_robin(process_list, quantum=1):
    processes = clone_processes(process_list)
    total_processes = len(processes)

    priority_queues = {}
    for process in processes:
        priority_queues.setdefault(process["priority"], deque())

    time = 0
    completed = 0
    arrived = set()

    while completed < total_processes:
        for index, process in enumerate(processes):
            if index not in arrived and process["arrival_time"] <= time:
                priority_queues[process["priority"]].append(index)
                arrived.add(index)

        ready_priorities = sorted(
            [priority for priority, queue in priority_queues.items() if queue]
        )

        if not ready_priorities:
            time += 1
            continue

        current_priority = ready_priorities[0]
        current_index = priority_queues[current_priority].popleft()
        current_process = processes[current_index]

        cpu_time = min(quantum, current_process["remaining_time"])
        current_process["remaining_time"] -= cpu_time
        time += cpu_time

        for index, process in enumerate(processes):
            if index not in arrived and process["arrival_time"] <= time:
                priority_queues[process["priority"]].append(index)
                arrived.add(index)

        if current_process["remaining_time"] == 0:
            current_process["completion_time"] = time
            finalize_process_metrics(current_process)
            completed += 1
        else:
            priority_queues[current_priority].append(current_index)

    return processes


def sjf_priority(process_list):
    processes = clone_processes(process_list)
    total_processes = len(processes)

    time = 0
    completed = 0
    finished = [False] * total_processes

    while completed < total_processes:
        ready_indices = []
        for index, process in enumerate(processes):
            if not finished[index] and process["arrival_time"] <= time:
                ready_indices.append(index)

        if not ready_indices:
            time += 1
            continue

        ready_indices.sort(
            key=lambda index: (
                processes[index]["burst_time"],
                processes[index]["priority"],
                processes[index]["arrival_time"]
            )
        )

        current_index = ready_indices[0]
        current_process = processes[current_index]

        time += current_process["burst_time"]
        current_process["remaining_time"] = 0
        current_process["completion_time"] = time
        finalize_process_metrics(current_process)

        finished[current_index] = True
        completed += 1

    return processes


def fcfs_priority(process_list):
    processes = clone_processes(process_list)

    processes.sort(
        key=lambda process: (
            process["priority"],
            process["arrival_time"]
        )
    )

    time = 0
    for process in processes:
        if time < process["arrival_time"]:
            time = process["arrival_time"]

        time += process["burst_time"]
        process["remaining_time"] = 0
        process["completion_time"] = time
        finalize_process_metrics(process)

    return processes


def detect_cpu_hogs(process_list, burst_threshold=12):
    if not process_list:
        return []

    average_burst_time = sum(process.burst_time for process in process_list) / len(process_list)
    suspicious = []

    for process in process_list:
        if (
            process.burst_time > average_burst_time * 1.5 or
            process.burst_time > burst_threshold
        ):
            suspicious.append({
                "pid": process.process_id,
                "name": process.name,
                "burst_time": process.burst_time,
                "reason": "Suspicious CPU hog"
            })

    return suspicious


def detect_memory_hogs(process_list, total_memory=1000):
    if not process_list:
        return []

    average_memory_usage = sum(process.memory_usage for process in process_list) / len(process_list)
    suspicious = []

    for process in process_list:
        if (
            process.memory_usage > total_memory * 0.30 or
            process.memory_usage > average_memory_usage * 2
        ):
            suspicious.append({
                "pid": process.process_id,
                "name": process.name,
                "memory_usage": process.memory_usage,
                "reason": "Suspicious memory hog"
            })

    return suspicious


# Part 3 quoted by AI for reference:
# Deadlock & Resource Contention tracks resource requests, blocked processes,
# detects wait cycles, and resolves deadlocks by removing a victim process.

class Resource:
    def __init__(self, resource_name):
        self.resource_name = resource_name
        self.held_by = None


class ResourceRequest:
    def __init__(self, request_id, process_id, resource_name):
        self.request_id = request_id
        self.process_id = process_id
        self.resource_name = resource_name


class DeadlockResourceSystem:
    # Paging:
    # Physical memory is divided into fixed-size frames
    # Then, a process is divided into fixed-size pages
    
    # Segmentation:
    # Memory is divided into variable-sized logical
    # segments instead of fixed pages.
    def __init__(self):
        self.processes = []
        self.resources = []
        self.requests = []

        self.allocations = []
        self.blocked_requests = []
        self.security_alerts = []
        self.wait_for_graph = {}

    def add_process(self, process):
        if self.find_process(process.process_id) is None:
            self.processes.append(process)

    def add_resource(self, resource):
        if self.find_resource(resource.resource_name) is None:
            self.resources.append(resource)

    def add_request(self, request):
        self.requests.append(request)

    def find_process(self, process_id):
        for process in self.processes:
            if process.process_id == process_id:
                return process
        return None

    def find_resource(self, resource_name):
        for resource in self.resources:
            if resource.resource_name == resource_name:
                return resource
        return None

    def request_resource(self, request):
        current_process = self.find_process(request.process_id)
        current_resource = self.find_resource(request.resource_name)

        if current_process is None or current_resource is None:
            return False, "Invalid process or resource"

        if current_resource.held_by is None:
            current_resource.held_by = current_process.process_id

            self.allocations.append({
                "request_id": request.request_id,
                "pid": current_process.process_id,
                "process_name": current_process.name,
                "role": current_process.user_role,
                "resource_name": current_resource.resource_name,
                "status": "ALLOCATED"
            })
            return True, "ALLOCATED"

        blocking_pid = current_resource.held_by
        blocking_process = self.find_process(blocking_pid)

        self.blocked_requests.append({
            "request_id": request.request_id,
            "blocked_pid": current_process.process_id,
            "blocked_process_name": current_process.name,
            "resource_name": current_resource.resource_name,
            "blocking_pid": blocking_pid,
            "blocking_process_name": blocking_process.name if blocking_process else "Unknown",
            "blocking_process_role": blocking_process.user_role if blocking_process else "Unknown",
            "status": "BLOCKED"
        })

        if current_process.process_id not in self.wait_for_graph:
            self.wait_for_graph[current_process.process_id] = []

        self.wait_for_graph[current_process.process_id].append(blocking_pid)

        if blocking_process is not None and self.is_suspicious_process(blocking_process):
            self.security_alerts.append({
                "request_id": request.request_id,
                "blocked_pid": current_process.process_id,
                "blocked_process_name": current_process.name,
                "blocking_pid": blocking_process.process_id,
                "blocking_process_name": blocking_process.name,
                "resource_name": current_resource.resource_name,
                "reason": "suspicious process is blocking a resource"
            })

        return False, "BLOCKED"

    def is_suspicious_process(self, process):
        return process.user_role.lower() == "guest"

    def detect_deadlock(self):
        visited = []
        recursion_stack = []

        for pid in self.wait_for_graph:
            if pid not in visited:
                cycle = self.depth_first_search(pid, visited, recursion_stack)
                if cycle is not None:
                    return cycle
        return None

    def depth_first_search(self, pid, visited, recursion_stack):
        visited.append(pid)
        recursion_stack.append(pid)

        if pid in self.wait_for_graph:
            for neighbor in self.wait_for_graph[pid]:
                if neighbor not in visited:
                    cycle = self.depth_first_search(neighbor, visited, recursion_stack)
                    if cycle is not None:
                        return cycle
                elif neighbor in recursion_stack:
                    start_index = recursion_stack.index(neighbor)
                    return recursion_stack[start_index:]

        recursion_stack.remove(pid)
        return None

    def resolve_deadlock(self, cycle):
        if cycle is None:
            return None

        victim_pid = self.choose_victim_process(cycle)
        victim_process = self.find_process(victim_pid)

        if victim_process is None:
            return None

        for resource in self.resources:
            if resource.held_by == victim_pid:
                resource.held_by = None

        self.wait_for_graph.pop(victim_pid, None)
        for pid in list(self.wait_for_graph.keys()):
            self.wait_for_graph[pid] = [n for n in self.wait_for_graph[pid] if n != victim_pid]

        return victim_pid

    def choose_victim_process(self, cycle):
        for pid in cycle:
            process = self.find_process(pid)
            if process is not None and self.is_suspicious_process(process):
                return pid
        return cycle[-1]


# Part 4 quoted by AI for reference:
# Disk Scheduling & Access Control checks whether processes can read/write files
# and records denied requests as suspicious security activity.

class SecureFile:
    def __init__(self, file_name, cylinder, read_roles, write_roles):
        self.file_name = file_name
        self.cylinder = cylinder
        self.read_roles = read_roles
        self.write_roles = write_roles


class AccessRequest:
    def __init__(self, request_id, process_id, file_name, action):
        self.request_id = request_id
        self.process_id = process_id
        self.file_name = file_name
        self.action = action


class AccessControlSystem:
    def __init__(self):
        self.processes = []
        self.files = []
        self.requests = []
        self.allowed_requests = []
        self.security_alerts = []
        self.denied_count = {}

    def add_process(self, process):
        if self.find_process(process.process_id) is None:
            self.processes.append(process)

    def add_file(self, secure_file):
        if self.find_file(secure_file.file_name) is None:
            self.files.append(secure_file)

    def add_request(self, request):
        self.requests.append(request)

    def find_process(self, process_id):
        for process in self.processes:
            if process.process_id == process_id:
                return process
        return None

    def find_file(self, file_name):
        for secure_file in self.files:
            if secure_file.file_name == file_name:
                return secure_file
        return None

    def evaluate_request(self, request):
        current_process = self.find_process(request.process_id)
        current_file = self.find_file(request.file_name)

        if current_process is None:
            return False, "process was not found"

        if current_file is None:
            return False, "file was not found"

        access_allowed = False
        reason = ""

        if request.action == "read":
            if current_process.user_role in current_file.read_roles:
                access_allowed = True
            else:
                reason = "role not allowed to read file"
        elif request.action == "write":
            if current_process.user_role in current_file.write_roles:
                access_allowed = True
            else:
                reason = "role not allowed to write file"
        else:
            reason = "invalid action"

        if access_allowed:
            row = {
                "request_id": request.request_id,
                "process_id": current_process.process_id,
                "process_name": current_process.name,
                "process_type": current_process.get_process_type(),
                "priority": current_process.priority,
                "burst_time": current_process.burst_time,
                "arrival_time": current_process.arrival_time,
                "user_role": current_process.user_role,
                "file_name": current_file.file_name,
                "cylinder": current_file.cylinder,
                "action": request.action,
                "status": "ALLOWED"
            }
            self.allowed_requests.append(row)
            return True, "ALLOWED"

        row = {
            "request_id": request.request_id,
            "process_id": current_process.process_id,
            "process_name": current_process.name,
            "process_type": current_process.get_process_type(),
            "user_role": current_process.user_role,
            "file_name": current_file.file_name,
            "action": request.action,
            "status": "DENIED",
            "reason": reason
        }
        self.security_alerts.append(row)

        if current_process.process_id not in self.denied_count:
            self.denied_count[current_process.process_id] = 0
        self.denied_count[current_process.process_id] += 1

        return False, reason
