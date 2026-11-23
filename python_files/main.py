# main.py

import os
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_DIR, "csv_files")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "outputs")

from dashboard import Dashboard
from security import SecuritySession
from ml        import ml_recommend
from disk      import prepare_disk_input, run_disk_scheduling, save_disk_output
from pages     import run_pages
from memory    import init_memory, allocate_memory, get_ram
from deadlock  import check_deadlock
from scheduler import Scheduler


def _rename_for_ml(data):
    return data.rename(columns={
        "BurstTime":     "Burst Time",
        "ProcessNumber": "Process Number",
        "ArrivalTime":   "Request Number",
    })


def _parse_resources(resource_str):
    counts = [0, 0, 0, 0]
    for ch in str(resource_str).upper():
        if   ch == "A": counts[0] += 1
        elif ch == "B": counts[1] += 1
        elif ch == "C": counts[2] += 1
        elif ch == "D": counts[3] += 1
    return counts


def _build_deadlock_inputs(data):
    processes  = data["ProcessNumber"].tolist()
    max_demand = [_parse_resources(r) for r in data["Resources"].tolist()]
    allocation = [row[:] for row in max_demand]
    return processes, [0, 0, 0, 0], max_demand, allocation


def _to_scheduler_list(data, algo):
    uses_priority = "Priority" in algo
    rows = []
    for _, row in data.iterrows():
        if uses_priority:
            rows.append({
                "Process Number": int(row["ProcessNumber"]),
                "Burst Time":     int(row["BurstTime"]),
                "Request Number": int(row["ArrivalTime"]),
                "Priority":       int(row["Priority"]),
            })
        else:
            rows.append({
                "ProcessNumber": int(row["ProcessNumber"]),
                "BurstTime":     int(row["BurstTime"]),
                "Arrival":       int(row["ArrivalTime"]),
            })
    return rows


def _save(df, filename):
    df.to_csv(os.path.join(OUTPUT_DIR, filename), index=False)


def run_simulation(app, data, memory_config):
    """Run one workload. This is called again whenever the user starts a new run."""
    app.show_output_tab()

    # ML
    ml = ml_recommend(_rename_for_ml(data), memory_config["priority"])
    disk_algo,     disk_reason  = ml["disk"]
    schedule_algo, _            = ml["scheduler"]
    mem_algo                    = ml["memory"]
    app.set_ml_results(disk_algo, schedule_algo, mem_algo, "FIFO")

    # DISK
    os.chdir(OUTPUT_DIR)
    disk_result     = run_disk_scheduling(
                        prepare_disk_input(data),
                        disk_algo,
                        memory_config.get("disk", 50),
                        disk_reason)
    disk_ordered_df = save_disk_output(data, disk_result)
    app.set_disk_result(disk_result, disk_ordered_df)

    # PAGES
    pages_result = run_pages(disk_ordered_df, "FIFO",
                                memory_config.get("frame_size", 3))
    app.set_pages_result(pages_result)

    # MEMORY
    memory     = init_memory(memory_config.get("ram", 1024))
    last_index = 0
    overflow   = []
    for _, row in disk_ordered_df.iterrows():
        success, last_index = allocate_memory(
            memory,
            {"ProcessNumber": int(row["ProcessNumber"]),
                "Size":          int(row["Size"])},
            mem_algo, last_index)
        if not success:
            overflow.append(int(row["ProcessNumber"]))

    ram_ids  = get_ram(memory)
    in_ram   = disk_ordered_df[disk_ordered_df["ProcessNumber"].isin(ram_ids)].copy()
    in_queue = disk_ordered_df[disk_ordered_df["ProcessNumber"].isin(overflow)].copy()
    app.set_memory_result(memory, in_ram, in_queue)
    app.security_session = SecuritySession(data, memory, OUTPUT_DIR)
    app.reset_security_session()

    _save(pd.DataFrame([
        {"Start": b["start"], "Size": b["size"],
            "Status": "FREE" if b["free"] else "P" + str(b["process"])}
        for b in memory
    ]), "memory_output.csv")

    # DEADLOCK
    deadlock_result = check_deadlock(*_build_deadlock_inputs(in_ram))
    app.set_deadlock_result(deadlock_result)
    _save(pd.DataFrame({
        "Deadlock":     [deadlock_result["deadlock"]],
        "SafeSequence": [str(deadlock_result["safe_sequence"])]
    }), "deadlock_output.csv")

    if deadlock_result["deadlock"]:
        return

    # SCHEDULING
    safe_data = in_ram[in_ram["ProcessNumber"].isin(
                    deadlock_result["safe_sequence"])].copy()
    schedule = Scheduler(
        _to_scheduler_list(safe_data, schedule_algo),
        _to_scheduler_list(in_queue,  schedule_algo),
        schedule_algo, memory_config["quantum"])
    app.set_schedule_result(schedule, schedule_algo)
    _save(schedule, "schedule_output.csv")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app = Dashboard()
    app.set_input_dir(INPUT_DIR)
    app.set_output_dir(OUTPUT_DIR)
    app.set_simulation_callback(lambda data, memory_config: run_simulation(
        app, data, memory_config))
    app.wait_for_close()


if __name__ == "__main__":
    main()
