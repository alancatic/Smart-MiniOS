from collections import deque
import pandas as pd


def Scheduler(ram_processes, queue_processes, schedule_algo, quantum=3):

    print ("ram processes")
    print (ram_processes)
    print ("queue processes")
    print (queue_processes)
    

    if schedule_algo == "FCFS":
        return fcfs(ram_processes, queue_processes)

    elif schedule_algo == "SJF":
        return sjf(ram_processes, queue_processes)

    elif schedule_algo == "RoundRobin":
        return round_robin(ram_processes, queue_processes, quantum)

    elif schedule_algo == "FCFS_Priority":
        return priority_fcfs(ram_processes, queue_processes)

    elif schedule_algo == "SJF_Priority":
        return priority_sjf(ram_processes, queue_processes)

    elif schedule_algo == "RoundRobin_Priority":
        return priority_round_robin(ram_processes, queue_processes, quantum)

    else:
        raise ValueError(f"Unknown scheduling algorithm: {schedule_algo}")


# ---------------- FCFS ----------------
# Output columns: Process, Start, Finish, Waiting, Turnaround
def fcfs(ram, queue):
    time = 0
    results = []

    while len(ram) > 0:
        p = ram.pop(0)

        start      = time
        finish     = start + p["BurstTime"]
        waiting    = start - p.get("ArrivalTime", 0)
        turnaround = finish - p.get("ArrivalTime", 0)

        results.append({
            "Process":    p["ProcessNumber"],
            "Start":      start,
            "Finish":     finish,
            "Waiting":    waiting,
            "Turnaround": turnaround,
        })

        time = finish

        if len(queue) > 0:
            ram.append(queue.pop(0))

    return pd.DataFrame(results)


# ---------------- SJF ----------------
# Output columns: Process, Start, Finish, Waiting, Turnaround
def sjf(ram, queue):
    time    = 0
    results = []

    while len(ram) > 0 or len(queue) > 0:
        idx      = -1
        shortest = -1

        # find shortest ready job in RAM
        for i in range(len(ram)):
            p = ram[i]
            if p.get("ArrivalTime", 0) <= time and p["BurstTime"] > 0:
                ram[i]["State"] = "Ready"
                if shortest == -1 or p["BurstTime"] < shortest:
                    shortest = p["BurstTime"]
                    idx = i

        # nothing ready, advance time
        if idx == -1:
            time += 1
            continue

        p          = ram[idx]
        arrival    = p.get("ArrivalTime", 0)
        start      = time                       
        finish     = start + p["BurstTime"]
        waiting    = start - arrival
        turnaround = finish - arrival

        results.append({
            "Process":    p["ProcessNumber"],
            "Start":      start,               
            "Finish":     finish,
            "Waiting":    waiting,
            "Turnaround": turnaround,
        })

        time = finish
        p["State"] = "Completed"

        ram.pop(idx)
        if len(queue) > 0:
            ram.append(queue.pop(0))

    return pd.DataFrame(results)


# ---------------- ROUND ROBIN ----------------
# Output columns: Process, Start, Finish, Waiting, Turnaround
def round_robin(ram, queue, quantum):
    ram = deque(ram)
    queue = list(queue)  
    time = 0

    # Initialize tracking dictionaries
    remaining = {p["ProcessNumber"]: p["BurstTime"] for p in ram}
    arrival   = {p["ProcessNumber"]: p.get("Arrival", 0) for p in ram}

    results = []

    while len(ram) > 0 or len(queue) > 0:
        # Add newly arrived processes to RAM
        arrived = [p for p in queue if p.get("Arrival", 0) <= time]
        for p in arrived:
            queue.remove(p)
            ram.append(p)
            remaining[p["ProcessNumber"]] = p["BurstTime"]
            arrival[p["ProcessNumber"]]   = p.get("Arrival", 0)

        # If no process is ready, advance time
        if not ram:
            time += 1
            continue

        # Get next process
        p   = ram.popleft()
        pid = p["ProcessNumber"]

        start    = time
        run_time = min(remaining[pid], quantum)

        time += run_time
        remaining[pid] -= run_time

        results.append({
            "Process":    pid,
            "Start":      start,
            "Finish":     time,
            "Waiting":    start - arrival[pid],
            "Turnaround": time  - arrival[pid],
        })

        # Add any processes that arrived during execution window
        arrived = [p for p in queue if p.get("Arrival", 0) <= time]
        for p in arrived:
            queue.remove(p)
            ram.append(p)
            remaining[p["ProcessNumber"]] = p["BurstTime"]
            arrival[p["ProcessNumber"]]   = p.get("Arrival", 0)

        # Requeue if not finished
        if remaining[pid] > 0:
            ram.append(p)

    return pd.DataFrame(results)


# ---------------- PRIORITY FCFS ----------------
# Output columns: Process, Priority, Start, Finish, Waiting, Turnaround
def priority_fcfs(ram, queue):
    time    = 0
    results = []

    queues, priority_levels = build_priority_queues(ram)

    while has_work(queues, priority_levels):
        for level in priority_levels:
            priority_queue = queues[level]

            if len(priority_queue) == 0:
                continue

            process = priority_queue.popleft()

            arrival = process["ArrivalTime"]
            if time < arrival:
                time = arrival

            start      = time
            finish     = start + process["BurstTime"]
            waiting    = start - arrival
            turnaround = finish - arrival

            results.append({
                "Process":    process["ProcessNumber"],
                "Priority":   level,
                "Start":      start,
                "Finish":     finish,
                "Waiting":    waiting,
                "Turnaround": turnaround,
            })

            time = finish

            if len(queue) > 0:
                new_process     = queue.pop(0)
                priority_levels = add_to_queues(new_process, queues, priority_levels)

            break  # restart at highest priority

    return pd.DataFrame(results)


# ---------------- PRIORITY SJF ----------------
# Output columns: Process, Priority, Start, Finish, Waiting, Turnaround
def priority_sjf(ram, queue):
    time    = 0
    results = []

    queues, priority_levels = build_priority_queues(ram)

    while has_work(queues, priority_levels):
        for level in priority_levels:
            priority_queue = queues[level]

            if len(priority_queue) == 0:
                continue

            # pick shortest burst in this priority band
            shortest = min(priority_queue, key=lambda p: p["BurstTime"])  
            priority_queue.remove(shortest)

            arrival = shortest["ArrivalTime"] 
            if time < arrival:
                time = arrival

            start      = time
            finish     = start + shortest["BurstTime"]
            waiting    = start - arrival
            turnaround = finish - arrival

            results.append({
                "Process":    shortest["ProcessNumber"], 
                "Priority":   level,
                "Start":      start,
                "Finish":     finish,
                "Waiting":    waiting,
                "Turnaround": turnaround,
            })

            time = finish

            if len(queue) > 0:
                new_process     = queue.pop(0)
                priority_levels = add_to_queues(new_process, queues, priority_levels)

            break  # restart at highest priority

    return pd.DataFrame(results)


# ---------------- PRIORITY ROUND ROBIN ----------------
# Output columns: Process, Priority, Start, Finish, Waiting, Turnaround
from collections import deque
import pandas as pd

def priority_round_robin(ram, queue, quantum):
    time    = 0
    results = []

    queues, priority_levels = build_priority_queues(ram)
    queue = list(queue)

    while has_work(queues, priority_levels) or len(queue) > 0:

        arrived = [p for p in queue if p.get("ArrivalTime", 0) <= time]
        for p in arrived:
            queue.remove(p)
            priority_levels = add_to_queues(p, queues, priority_levels)

        # If nothing is ready, advance time
        if not has_work(queues, priority_levels):
            time += 1
            continue

        for level in priority_levels:
            priority_queue = queues[level]

            if len(priority_queue) == 0:
                continue

            process = priority_queue.popleft()

            arrival = process["ArrivalTime"]
            if time < arrival:
                time = arrival

            start    = time
            run_time = min(process["BurstTime"], quantum)
            finish   = start + run_time
            time     = finish

            process["BurstTime"] -= run_time

            results.append({
                "Process":    process["ProcessNumber"],
                "Priority":   level,
                "Start":      start,
                "Finish":     finish,
                "Waiting":    start  - arrival,
                "Turnaround": finish - arrival,
            })

            # add process
            arrived = [p for p in queue if p.get("ArrivalTime", 0) <= time]
            for p in arrived:
                queue.remove(p)
                priority_levels = add_to_queues(p, queues, priority_levels)

            if process["BurstTime"] > 0:
                priority_queue.append(process)

            break  # restart from highest priority

    return pd.DataFrame(results)


# ---------------- HELPERS ----------------

def build_priority_queues(ram):
    levels = []

    for p in ram:
        level = p["Priority"]
        if level not in levels:
            levels.append(level)

    levels = sort_desc(levels)

    queues = {level: deque() for level in levels}

    for p in ram:
        process = {
            "ProcessNumber": p["Process Number"],
            "BurstTime":     p["Burst Time"],
            "Priority":      p["Priority"],
            "ArrivalTime":   p.get("Request Number", 0),
        }
        queues[p["Priority"]].append(process)

    return queues, levels


def add_to_queues(process, queues, priority_levels):
    level = process["Priority"]

    normalized = {
        "ProcessNumber": process.get("ProcessNumber", process.get("Process Number")),
        "BurstTime":     process.get("BurstTime", process.get("Burst Time")),
        "Priority":      process["Priority"],
        "ArrivalTime":   process.get("ArrivalTime", process.get("Request Number", 0)),
    }

    if level not in queues:
        queues[level] = deque()
        priority_levels.append(level)
        priority_levels = sort_desc(priority_levels)

    queues[level].append(normalized)
    return priority_levels


def sort_desc(priority_levels):
    levels = list(priority_levels)
    for i in range(len(levels)):
        for j in range(i + 1, len(levels)):
            if levels[j] > levels[i]:
                levels[i], levels[j] = levels[j], levels[i]
    return levels


def has_work(queues, priority_levels):
    return any(len(queues[level]) > 0 for level in priority_levels)