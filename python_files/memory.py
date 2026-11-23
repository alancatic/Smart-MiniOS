# memory.py

# INITIAL MEMORY STATE
def init_memory(total_memory):
    return [{
        "start": 0,
        "size": total_memory,
        "free": True,
        "process": None
    }]


# ALLOCATE MEMORY
def allocate_memory(memory, process, algo, last_index=0):
    size = process["Size"]

    if algo == "FirstFit":
        index = first_fit(memory, size)

    elif algo == "BestFit":
        index = best_fit(memory, size)

    elif algo == "WorstFit":
        index = worst_fit(memory, size)

    elif algo == "NextFit":
        index = next_fit(memory, size, last_index)

    else:
        print("Unknown memory algorithm")
        return False, last_index

    if index == -1:
        return False, last_index

    memory, new_last = place_process(memory, index, process, last_index)
    return True, new_last


# PLACE PROCESS INTO MEMORY
def place_process(memory, index, process, last_index):
    block = memory[index]
    size = process["Size"]

    allocated = {
        "start": block["start"],
        "size": size,
        "free": False,
        "process": process["ProcessNumber"]
    }

    remaining = block["size"] - size

    memory[index] = allocated

    if remaining > 0:
        memory.insert(index + 1, {
            "start": allocated["start"] + size,
            "size": remaining,
            "free": True,
            "process": None
        })

    return memory, index


# DEALLOCATE MEMORY
def deallocate_memory(memory, process_number):
    for i, block in enumerate(memory):
        if block["process"] == process_number:
            memory[i]["free"] = True
            memory[i]["process"] = None

            memory = merge_holes(memory)
            return memory

    return memory


# MERGE HOLES
def merge_holes(memory):
    merged = []

    for block in memory:
        if merged and block["free"] and merged[-1]["free"]:
            merged[-1]["size"] += block["size"]
        else:
            merged.append(block)

    return merged


# FIRST FIT
def first_fit(memory, size):
    for i, block in enumerate(memory):
        if block["free"] and block["size"] >= size:
            return i
    return -1


# BEST FIT
def best_fit(memory, size):
    best_index = -1
    best_size = float('inf')

    for i, block in enumerate(memory):
        if block["free"] and block["size"] >= size:
            if block["size"] < best_size:
                best_size = block["size"]
                best_index = i

    return best_index


# WORST FIT
def worst_fit(memory, size):
    worst_index = -1
    worst_size = -1

    for i, block in enumerate(memory):
        if block["free"] and block["size"] >= size:
            if block["size"] > worst_size:
                worst_size = block["size"]
                worst_index = i

    return worst_index

# NEXT FIT
def next_fit(memory, size, last_index):
    n = len(memory)

    for i in range(n):
        idx = (last_index + i) % n
        block = memory[idx]

        if block["free"] and block["size"] >= size:
            return idx

    return -1


# GET RAM PROCESSES
def get_ram(memory):
    return [b["process"] for b in memory if not b["free"]]



def print_memory(memory):
    print("\n=== MEMORY STATE ===")

    for block in memory:
        if block["free"]:
            print(f"[ FREE {block['size']} ]", end=" ")
        else:
            print(f"[ P{block['process']} {block['size']} ]", end=" ")

    print()
