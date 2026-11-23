# disk.py

import pandas as pd
import os


def prepare_disk_input(data):
    disk_df = data.copy()
    disk_df = disk_df[["ProcessNumber", "Location"]]
    disk_df = disk_df.rename(columns={"Location": "DiskRequest"})

    path = os.path.join(os.getcwd(), "disk_input.csv")
    disk_df.to_csv(path, index=False)

    return disk_df


def run_disk_scheduling(data, algo, head=50, reason=""):

    requests = data["DiskRequest"].tolist()

    if algo == "FCFS":
        result = fcfs(requests, head)
    elif algo == "SSTF":
        result = sstf(requests, head)
    elif algo == "SCAN":
        result = scan(requests, head)
    else:
        return None

    result["algorithm"] = algo
    result["reason"] = reason

    return result


def fcfs(req, head):
    order = [head] + req
    moves, total = [], 0
    for i in range(len(order)-1):
        m = abs(order[i+1]-order[i])
        moves.append(m)
        total += m
    return {"order": order, "movements": moves, "total": total}


def sstf(req, head):
    rem = req.copy()
    order = [head]
    moves, total = [], 0
    cur = head

    while rem:
        nxt = min(rem, key=lambda x: abs(x-cur))
        m = abs(cur-nxt)
        moves.append(m)
        total += m
        cur = nxt
        order.append(cur)
        rem.remove(nxt)

    return {"order": order, "movements": moves, "total": total}


def scan(req, head):
    left = sorted([r for r in req if r < head])
    right = sorted([r for r in req if r >= head])

    order = [head] + left[::-1] + right
    moves, total = [], 0

    for i in range(len(order)-1):
        m = abs(order[i+1]-order[i])
        moves.append(m)
        total += m

    return {"order": order, "movements": moves, "total": total}


def save_disk_output(original_data, disk_result):
    order = disk_result["order"][1:]

    df = original_data.copy()
    ordered_rows = []

    for loc in order:
        match = df[df["Location"] == loc]

        # FIX: include ALL matches (not just one)
        for _, row in match.iterrows():
            ordered_rows.append(row)

        df = df.drop(match.index)

    output_df = pd.DataFrame(ordered_rows)

    path = os.path.join(os.getcwd(), "disk_output.csv")
    output_df.to_csv(path, index=False)

    return output_df