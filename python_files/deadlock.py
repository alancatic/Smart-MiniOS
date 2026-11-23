# deadlock

# need matrix
def calculate_need(max_demand, allocation):
    need = []

    for i in range(len(max_demand)):
        row = []
        for j in range(len(max_demand[0])):
            row.append(max_demand[i][j] - allocation[i][j])
        need.append(row)

    return need


# deadlock detection
def check_deadlock(processes, available, max_demand, allocation):

    n = len(processes)
    m = len(available)

    need = calculate_need(max_demand, allocation)

    work = available.copy()
    finish = [False] * n
    safe_sequence = []

    while len(safe_sequence) < n:
        found = False

        for i in range(n):
            if not finish[i]:

                # check if process can run
                can_run = True
                for j in range(m):
                    if need[i][j] > work[j]:
                        can_run = False
                        break

                if can_run:
                    # release resources after finishing
                    for j in range(m):
                        work[j] += allocation[i][j]

                    safe_sequence.append(processes[i])
                    finish[i] = True
                    found = True

        if not found:
            return {
                "deadlock": True,
                "safe_sequence": []
            }

    return {
        "deadlock": False,
        "safe_sequence": safe_sequence
    }


# deadlock prevention
def request_resources(process_id, request, available, max_demand, allocation, processes):

    m = len(available)

    # Step 1: Check request <= need
    for j in range(m):
        if request[j] > (max_demand[process_id][j] - allocation[process_id][j]):
            return {
                "granted": False,
                "reason": "Request exceeds maximum need"
            }

    # Step 2: Check request <= available
    for j in range(m):
        if request[j] > available[j]:
            return {
                "granted": False,
                "reason": "Resources not available"
            }

    # Step 3: Allocate
    for j in range(m):
        available[j] -= request[j]
        allocation[process_id][j] += request[j]

    # Step 4: Check if system is safe
    result = detect_deadlock(processes, available, max_demand, allocation)

    if not result["deadlock"]:
        return {
            "granted": True,
            "safe_sequence": result["safe_sequence"]
        }
    else:
        # rollback
        for j in range(m):
            available[j] += request[j]
            allocation[process_id][j] -= request[j]

        return {
            "granted": False,
            "reason": "Would cause deadlock"
        }


def run_deadlock(processes, available, max_demand, allocation):

    result = detect_deadlock(processes, available, max_demand, allocation)

    print("\n=== DEADLOCK CHECK ===")

    if result["deadlock"]:
        print("DEADLOCK DETECTED")
    else:
        print("System is SAFE")
        print("Safe sequence:", result["safe_sequence"])

    return result
