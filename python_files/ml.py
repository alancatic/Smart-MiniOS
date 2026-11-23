import statistics
import random
import pandas as pd
 
 
def ml_recommend(source, priority):
    if isinstance(source, str):
        data = pd.read_csv(source)
    else:
        data = source
 
    return {
        "disk":      pick_disk(data),
        "scheduler": pick_scheduler(data, priority),
        "memory":    pick_memory(data),
        "pages":     pick_pages(data),
    }

def stats(data):
    n          = len(data)
    bursts     = data["Burst Time"].tolist()
    priorities = data["Priority"].tolist()
    sizes      = data["Size"].tolist()
    locations  = data["Location"].tolist()
 
    return {
        "n_processes":     n,
        "burst_variance":  statistics.variance(bursts) if n > 1 else 0,
        "priority_spread": max(priorities) - min(priorities),
        "total_memory":     sum(sizes),
        "disk_spread":      (max(locations) - min(locations)) if len(locations) > 1 else 0,
    }

def pick_scheduler(data, priority):
    f  = stats(data)
    v  = f["burst_variance"]
    n  = f["n_processes"]


    # --- Step 1: Pick base algorithm ---
    if v > 10 and n < 8:
        algo = "SJF"
        reason = f"High variance ({v:.1f}) and manageable process count → SJF"

    elif n > 8:
        algo = "RoundRobin"
        reason = f"{n} processes → Round Robin ensures fairness"

    else:
        algo = "FCFS"
        reason = "Low complexity workload → FCFS is sufficient"


    # --- Step 2: priority  ---
    if f["priority_spread"] >= 4:
        if random.random() < 0.5:  # 50% chance
            priority = True
            reason += " and the wide priority spread → Priority scheduling is beneficial."
    
    if priority:
        algo += "_Priority"

    return algo, reason

def pick_memory(data):
    f  = stats(data)
    n = f["n_processes"]
    total = f["total_memory"]
 
    if n <= 3:
        return "FirstFit"
    if total > 500:
        return "BestFit"
    if n > 10:
        return "NextFit"
    return "FirstFit"

def pick_pages(data):
    f  = stats(data)
    n = f["n_processes"]
    v = f["burst_variance"]
 
    if n <= 4:
        return "Optimal"
    if v > 15:
        return "LRU"
    return "FIFO"

def pick_disk(data):
    f  = stats(data)
    spread = f["disk_spread"]      # 0–199
    n = f["n_processes"]

    # -------------------------
    # VERY SMALL CASE
    # -------------------------
    if n <= 3 and spread < 30:
        return ("FCFS", f"Very small workload (n={n}, spread={spread}) → FCFS is sufficient")

    # -------------------------
    # SMALL BUT SCATTERED
    # -------------------------
    if n <= 5 and spread >= 30:
        return ("SSTF", f"Few requests but spread out ({spread}) → SSTF reduces movement")

    # -------------------------
    # MEDIUM CASE (MOST COMMON)
    # -------------------------
    if 5 < n <= 15:
        if spread < 50:
            return ("FCFS", f"Moderate processes (n={n}) but clustered ({spread}) → FCFS is efficient")
        elif spread < 120:
            return ("SSTF", f"Moderate workload (n={n}, spread={spread}) → SSTF minimizes seek time")
        else:
            return ("SCAN", f"Wide spread ({spread}) with moderate load → SCAN avoids long jumps")

    # -------------------------
    # LARGE WORKLOAD
    # -------------------------
    if n > 15:
        if spread < 60:
            return ("SSTF", f"Many processes (n={n}) but clustered → SSTF is optimal")
        else:
            return ("SCAN", f"Heavy workload (n={n}, spread={spread}) → SCAN handles full-disk traversal well")

    # fallback
    return ("FCFS", f"Default case (n={n}, spread={spread})")