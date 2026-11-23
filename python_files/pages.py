# pages.py

from collections import deque
import pandas as pd


# ====================================================
# FIFO PAGE REPLACEMENT
# ====================================================

def fifo_replacement(pages, size):

    memory = deque()

    faults = 0
    hits = 0

    results = []

    for page in pages:

        # PAGE HIT
        if page in memory:

            hits += 1

            fault = False

        # PAGE FAULT
        else:

            faults += 1

            fault = True

            # remove oldest page if full
            if len(memory) == size:
                memory.popleft()

            memory.append(page)

        # save current state
        results.append({
            "Page": page,
            "Memory": list(memory),
            "Fault": fault
        })

    output_df = pd.DataFrame(results)

    return {
        "results": output_df,
        "faults": faults,
        "hits": hits,
        "hit_rate": round(hits / len(pages), 2),
        "fault_rate": round(faults / len(pages), 2)
    }


# ====================================================
# MAIN PAGE MODULE
# ====================================================

def run_pages(data, algorithm="FIFO", frame_size=3):

    # extract page requests from incoming CSV/dataframe
    pages = data["Location"].tolist()

    # choose algorithm
    if algorithm == "FIFO":

        result = fifo_replacement(pages, frame_size)

    elif algorithm == "LRU":

        result = lru_replacement(pages, frame_size)

    elif algorithm == "Optimal":

        result = optimal_replacement(pages, frame_size)

    else:

        print("Unknown page replacement algorithm")
        return None

    # create NEW output csv
    result["results"].to_csv("pages_output.csv", index=False)

    print("\n=== PAGE REPLACEMENT RESULTS ===")
    print("Algorithm:", algorithm)

    print(result["results"])

    print("\nPage Faults:", result["faults"])
    print("Hits:", result["hits"])
    print("Hit Rate:", result["hit_rate"])
    print("Fault Rate:", result["fault_rate"])

    print("\nSaved output to pages_output.csv")

    return result

