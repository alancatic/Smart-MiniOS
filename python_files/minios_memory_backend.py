from abc import ABC, abstractmethod

# Part 2 quoted by AI for reference:
# Paging splits memory into fixed-size pages/frames and uses a page table to map them.
# Segmentation splits memory into variable-size logical segments (like code/data/stack) using a base and limit.


class Process(ABC):
    def __init__(
        self,
        name: str,
        process_id: int,
        priority: int,
        burst_time: int,
        arrival_time: int,
        user_role: str,
        memory_required: int = 0,
        memory_usage: int = 0,
        cpu_usage: int = 0,
        disk_usage: int = 0
    ):
        self._name = name
        self._process_id = process_id
        self._priority = priority
        self._burst_time = burst_time
        self._arrival_time = arrival_time
        self._user_role = user_role

        self._memory_required = memory_required
        self._memory_usage = memory_usage
        self._cpu_usage = cpu_usage
        self._disk_usage = disk_usage

        self._page_table = {}
        self._allocated_frames = []
        self._number_of_pages = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def process_id(self) -> int:
        return self._process_id

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def burst_time(self) -> int:
        return self._burst_time

    @property
    def arrival_time(self) -> int:
        return self._arrival_time

    @property
    def user_role(self) -> str:
        return self._user_role

    @property
    def memory_required(self) -> int:
        return self._memory_required

    @property
    def memory_usage(self) -> int:
        return self._memory_usage

    @property
    def cpu_usage(self) -> int:
        return self._cpu_usage

    @property
    def disk_usage(self) -> int:
        return self._disk_usage

    @property
    def page_table(self) -> dict:
        return self._page_table

    @property
    def allocated_frames(self) -> list:
        return self._allocated_frames

    @property
    def number_of_pages(self) -> int:
        return self._number_of_pages

    @number_of_pages.setter
    def number_of_pages(self, value: int) -> None:
        self._number_of_pages = value

    def add_page_mapping(self, page_number: int, frame_number: int) -> None:
        self._page_table[page_number] = frame_number
        self._allocated_frames.append(frame_number)

    def clear_memory_mappings(self) -> None:
        self._page_table = {}
        self._allocated_frames = []
        self._number_of_pages = 0

    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_process_type(self) -> str:
        raise NotImplementedError


class UserProcess(Process):
    def execute(self) -> None:
        print(f"Executing user process {self.name} with PID {self.process_id}")

    def get_process_type(self) -> str:
        return "User Process"


class SystemProcess(Process):
    def execute(self) -> None:
        print(f"Executing system process {self.name} with PID {self.process_id}")

    def get_process_type(self) -> str:
        return "System Process"


class MemoryManager:
    """
    Part 2 implements both views:
    - Paging: fixed-size pages mapped to fixed-size frames
    - Segmentation: variable-size logical segments with base + limit
    """

    def __init__(self, total_memory: int, frame_size: int):
        self.total_memory = total_memory
        self.frame_size = frame_size
        self.total_number_of_frames = total_memory // frame_size

        self.frame_table = []
        for current_frame_integer in range(self.total_number_of_frames):
            self.frame_table.append({
                "frame_number": current_frame_integer,
                "is_free": True,
                "owner_process_id": None
            })

        self.process_list = []
        self.alert_list = []

        # Simple segmentation view
        self.segment_table = []
        self.next_segment_base = 0

    def add_process(self, process: Process):
        if self.find_process_by_id(process.process_id) is None:
            self.process_list.append(process)

    def find_process_by_id(self, process_id: int):
        for current_process in self.process_list:
            if current_process.process_id == process_id:
                return current_process
        return None

    # ---------------- Paging ----------------
    def allocate_memory(self, process_id: int):
        current_process = self.find_process_by_id(process_id)

        if current_process is None:
            self.alert_list.append("ERROR: Process not found.")
            return False

        if current_process.allocated_frames:
            self.alert_list.append(f"WARNING: Process {current_process.name} already has allocated memory.")
            return False

        pages_needed = current_process.memory_required // self.frame_size
        if current_process.memory_required % self.frame_size != 0:
            pages_needed += 1

        free_frame_list = []
        for current_frame_integer in range(len(self.frame_table)):
            if self.frame_table[current_frame_integer]["is_free"]:
                free_frame_list.append(current_frame_integer)

        if len(free_frame_list) < pages_needed:
            self.alert_list.append("ERROR: Not enough free frames.")
            return False

        current_process.number_of_pages = pages_needed

        for current_page_integer in range(pages_needed):
            current_frame_integer = free_frame_list[current_page_integer]
            self.frame_table[current_frame_integer]["is_free"] = False
            self.frame_table[current_frame_integer]["owner_process_id"] = current_process.process_id
            current_process.add_page_mapping(current_page_integer, current_frame_integer)

        self.alert_list.append(f"INFO: Paging allocation completed for process {current_process.name}.")
        return True

    def deallocate_memory(self, process_id: int):
        current_process = self.find_process_by_id(process_id)

        if current_process is None:
            self.alert_list.append("ERROR: Process not found.")
            return False

        if not current_process.allocated_frames:
            self.alert_list.append(f"WARNING: Process {current_process.name} has no allocated memory.")
            return False

        for current_frame_integer in current_process.allocated_frames:
            self.frame_table[current_frame_integer]["is_free"] = True
            self.frame_table[current_frame_integer]["owner_process_id"] = None

        current_process.clear_memory_mappings()
        self.alert_list.append(f"INFO: Paging deallocation completed for process {current_process.name}.")
        return True

    def access_memory(self, requesting_process_id: int, target_process_id: int, logical_address: int):
        requesting_process = self.find_process_by_id(requesting_process_id)
        target_process = self.find_process_by_id(target_process_id)

        if requesting_process is None or target_process is None:
            self.alert_list.append("ERROR: Process not found.")
            return False

        if logical_address < 0 or logical_address >= target_process.memory_required:
            self.alert_list.append("SEGMENTATION FAULT: Invalid paging address.")
            return False

        page_number = logical_address // self.frame_size

        if page_number not in target_process.page_table:
            self.alert_list.append("UNAUTHORIZED ACCESS: Page not allocated.")
            return False

        if requesting_process_id != target_process_id:
            self.alert_list.append(
                f"UNAUTHORIZED ACCESS: Process {requesting_process.name} tried to access memory of process {target_process.name}."
            )
            return False

        frame_number = target_process.page_table[page_number]
        self.alert_list.append(
            f"ACCESS GRANTED: Process {requesting_process.name} accessed paging frame {frame_number}."
        )
        return True

    # ---------------- Segmentation ----------------
    def allocate_segments(self, process_id: int):
        current_process = self.find_process_by_id(process_id)
        if current_process is None:
            self.alert_list.append("ERROR: Process not found.")
            return False

        existing = [row for row in self.segment_table if row["owner_process_id"] == process_id]
        if existing:
            self.alert_list.append(f"WARNING: Process {current_process.name} already has segments allocated.")
            return False

        total = max(current_process.memory_required, 24)
        code_size = max(8, total // 3)
        data_size = max(8, total // 3)
        stack_size = max(8, total - code_size - data_size)
        segment_specs = [("code", code_size), ("data", data_size), ("stack", stack_size)]

        for segment_name, limit in segment_specs:
            self.segment_table.append({
                "owner_process_id": current_process.process_id,
                "owner_name": current_process.name,
                "segment_name": segment_name,
                "base": self.next_segment_base,
                "limit": limit
            })
            self.next_segment_base += limit

        self.alert_list.append(f"INFO: Segmentation allocation completed for process {current_process.name}.")
        return True

    def deallocate_segments(self, process_id: int):
        current_process = self.find_process_by_id(process_id)
        if current_process is None:
            self.alert_list.append("ERROR: Process not found.")
            return False

        before = len(self.segment_table)
        self.segment_table = [row for row in self.segment_table if row["owner_process_id"] != process_id]
        if len(self.segment_table) == before:
            self.alert_list.append(f"WARNING: Process {current_process.name} has no segments allocated.")
            return False

        self.alert_list.append(f"INFO: Segmentation deallocation completed for process {current_process.name}.")
        return True

    def access_segment(self, requesting_process_id: int, target_process_id: int, segment_name: str, offset: int):
        requesting_process = self.find_process_by_id(requesting_process_id)
        target_process = self.find_process_by_id(target_process_id)

        if requesting_process is None or target_process is None:
            self.alert_list.append("ERROR: Process not found.")
            return False

        target_segment = None
        for row in self.segment_table:
            if row["owner_process_id"] == target_process_id and row["segment_name"] == segment_name:
                target_segment = row
                break

        if target_segment is None:
            self.alert_list.append("SEGMENTATION FAULT: Segment not allocated.")
            return False

        if requesting_process_id != target_process_id:
            self.alert_list.append(
                f"UNAUTHORIZED ACCESS: Process {requesting_process.name} tried to access segment {segment_name} of process {target_process.name}."
            )
            return False

        if offset < 0 or offset >= target_segment["limit"]:
            self.alert_list.append("SEGMENTATION FAULT: Offset exceeds segment limit.")
            return False

        physical_address = target_segment["base"] + offset
        self.alert_list.append(
            f"ACCESS GRANTED: Process {requesting_process.name} accessed segment {segment_name} at physical address {physical_address}."
        )
        return True

    def get_frame_rows(self):
        return self.frame_table

    def get_process_rows(self):
        rows = []
        for current_process in self.process_list:
            rows.append({
                "process_id": current_process.process_id,
                "name": current_process.name,
                "memory_required": current_process.memory_required,
                "memory_usage": current_process.memory_usage,
                "cpu_usage": current_process.cpu_usage,
                "disk_usage": current_process.disk_usage,
                "allocated_frames": list(current_process.allocated_frames),
                "page_table": dict(current_process.page_table),
            })
        return rows

    def get_segment_rows(self):
        return self.segment_table
