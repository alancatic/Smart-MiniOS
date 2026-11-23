import csv
from pathlib import Path
from minios_memory_backend import UserProcess, SystemProcess
from minios_parts_1_to_4 import (
    AccessControlSystem, AccessRequest, SecureFile, DeadlockResourceSystem,
    Resource, ResourceRequest, detect_cpu_hogs, detect_memory_hogs,
)


class SecuritySession:
    def __init__(self, data, memory, output_dir):
        self.memory = memory  # The same blocks displayed by Alan's Memory view.
        self.output_dir = Path(output_dir)
        self.events = []
        self.access = AccessControlSystem()
        self.resources = DeadlockResourceSystem()
        self.processes = []
        for _, row in data.iterrows():
            role = str(row.get('UserRole', 'user')).strip().lower()
            cls = SystemProcess if str(row.get('ProcessType', 'user')).lower() == 'system' else UserProcess
            process = cls(
                name=str(row.get('Name', 'P' + str(int(row['ProcessNumber'])))),
                process_id=int(row['ProcessNumber']), priority=int(row['Priority']),
                burst_time=int(row['BurstTime']), arrival_time=int(row['ArrivalTime']),
                user_role=role, memory_required=int(row['Size']), memory_usage=int(row['Size']),
            )
            self.processes.append(process)
            self.access.add_process(process)
            self.resources.add_process(process)
        for name in 'ABCD':
            self.resources.add_resource(Resource(name))
        # Simulated files only; these permissions never grant access to host files.
        self.access.add_file(SecureFile('public.txt', 10, ['guest', 'user', 'admin'], ['user', 'admin']))
        self.access.add_file(SecureFile('system.cfg', 50, ['admin'], ['admin']))
        self.access.add_file(SecureFile('shared.txt', 100, ['user', 'admin'], ['admin']))
        for alert in detect_cpu_hogs(self.processes) + detect_memory_hogs(
                self.processes, sum(b['size'] for b in memory)):
            self.record('monitor', alert['pid'], '', 'ALERT', alert['reason'])
        self.save()

    def record(self, kind, pid, target, status, reason):
        self.events.append(dict(Event=len(self.events) + 1, Kind=kind, Process=pid,
                                Target=target, Status=status, Reason=reason))
        self.save()

    def save(self):
        with (self.output_dir / 'security_output.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=['Event', 'Kind', 'Process', 'Target', 'Status', 'Reason'])
            writer.writeheader()
            writer.writerows(self.events)

    def file_request(self, pid, file_name, action):
        allowed, reason = self.access.evaluate_request(AccessRequest(len(self.events) + 1, pid, file_name, action))
        self.record('file', pid, file_name, 'ALLOWED' if allowed else 'DENIED', reason)
        return allowed

    def memory_request(self, pid, target, offset):
        block = next((b for b in self.memory if not b['free'] and b['process'] == target), None)
        if self.access.find_process(pid) is None:
            allowed, reason = False, 'Process was not found'
        elif block is None:
            allowed, reason = False, 'Target is not resident in RAM'
        elif pid != target:
            allowed, reason = False, 'Cross-process memory access'
        elif offset < 0 or offset >= block['size']:
            allowed, reason = False, 'Offset exceeds memory limit'
        else:
            allowed, reason = True, 'Physical address ' + str(block['start'] + offset)
        self.record('memory', pid, target, 'ALLOWED' if allowed else 'DENIED', reason)
        return allowed

    def resource_request(self, pid, name):
        resource = self.resources.find_resource(name)
        if resource is not None and resource.held_by == pid:
            allowed, reason = True, 'Already owned'
        else:
            allowed, reason = self.resources.request_resource(ResourceRequest(len(self.events) + 1, pid, name))
        self.record('resource', pid, name, 'ALLOWED' if allowed else 'BLOCKED', reason)
        if self.resources.security_alerts:
            alert = self.resources.security_alerts[-1]
            if alert['request_id'] == len(self.events):
                self.record('resource', pid, name, 'ALERT', alert['reason'])
        cycle = self.resources.detect_deadlock()
        if cycle:
            victim = self.resources.resolve_deadlock(cycle)
            self.record('resource', victim, str(cycle), 'RELEASED', 'Deadlock recovery: released victim resources')
        return allowed
