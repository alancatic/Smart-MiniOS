# dashboard.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os


COLOURS = [
    "#4C72B0","#DD8452","#55A868","#C44E52","#8172B2",
    "#937860","#DA8BC3","#8C8C8C","#CCB974","#64B5CD",
]

def _pc(pid):
    return COLOURS[(int(pid) - 1) % len(COLOURS)]


class Dashboard:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MiniOS Simulator")
        self.root.geometry("1200x700")

        # input state
        self.full_data     = None
        self.selected_data = None
        self.final_data    = None
        self.memory_config = {}
        self.input_dir     = None
        self.output_dir    = None

        # results injected by main.py
        self.ml_results      = None   # {disk, scheduler, memory, pages}
        self.disk_result     = None   # {order, movements, total, algorithm, reason}
        self.disk_ordered_df = None   # DataFrame ordered by disk visit
        self.pages_result    = None   # {results df, faults, hits, hit_rate, fault_rate}
        self.memory_state    = None   # list of memory blocks
        self.in_ram          = None   # DataFrame of processes in RAM
        self.in_queue        = None   # DataFrame of processes in queue
        self.deadlock_result = None   # {deadlock, safe_sequence}
        self.schedule_df     = None   # DataFrame from Scheduler
        self.schedule_algo   = None   # algo name string
        self.simulation_callback = None

        self._ready = None            # BooleanVar set in run()

        self.build_ui()
        from security_ui import install_security_tab
        install_security_tab(self)

    # ── UI BUILD ──────────────────────────────────────────────────────────────

    def build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        notebook = self.notebook
        notebook.pack(fill="both", expand=True)

        # ---- TAB 1: INPUT ----
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="Input")

        top = ttk.Frame(tab1)
        top.pack(pady=10)

        ttk.Button(top, text="Load CSV", command=self.load_csv).pack(side="left", padx=5)

        self.process_count_var = tk.StringVar(value="5")
        ttk.Combobox(top, textvariable=self.process_count_var, values=[str(i) for i in range(1, 51)], width=5).pack(side="left")

        ttk.Button(top, text="Select Processes", command=self.select_processes).pack(side="left", padx=5)

        ttk.Button(top, text="Start Simulation", command=self.finish).pack(side="left", padx=5)

        # Inputs
        mem_frame = ttk.Frame(tab1)
        mem_frame.pack(pady=5)

        self.ram_var        = tk.StringVar(value="1024")
        self.disk_head_var  = tk.StringVar(value="50")
        self.frame_size_var = tk.StringVar(value="3")
        self.quantum_var = tk.StringVar(value="3")
        self.priority_var = tk.BooleanVar()

        ttk.Label(mem_frame, text="RAM (KB)").pack(side="left")
        ttk.Entry(mem_frame, textvariable=self.ram_var, width=8).pack(side="left", padx=5)

        ttk.Label(mem_frame, text="Disk Head").pack(side="left")
        ttk.Entry(mem_frame, textvariable=self.disk_head_var, width=8).pack(side="left", padx=5)

        ttk.Label(mem_frame, text="Frame Size").pack(side="left")
        ttk.Entry(mem_frame, textvariable=self.frame_size_var, width=5).pack(side="left", padx=5)

        ttk.Label(mem_frame, text="Quantum").pack(side="left")
        ttk.Entry(mem_frame, textvariable=self.quantum_var, width=5).pack(side="left", padx=5)

        ttk.Checkbutton(mem_frame, text="Priority?", variable=self.priority_var).pack(side="left", padx=5)

        # Table
        cols = ["ProcessNumber", "BurstTime", "ArrivalTime", "Priority", "Size", "Location", "Resources", "UserRole", "Name"]
        self.tree = ttk.Treeview(tab1, columns=cols, show="headings")
        col_width = 1200 // len(cols)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=col_width, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # ---- TAB 2: OUTPUT ----
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="Output")

        btn_frame = ttk.Frame(tab2)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Disk",       command=self.show_disk).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Pages",      command=self.show_pages).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Memory",     command=self.show_memory).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Deadlock",   command=self.show_deadlock).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Scheduling", command=self.show_scheduling).pack(side="left", padx=5)

        # ML label — shows chosen algorithms
        self.ml_label = tk.Label(tab2, text="", fg="navy", justify="left", anchor="w")
        self.ml_label.pack(fill="x", padx=10)

        # Scrollable canvas for visuals
        canvas_frame = tk.Frame(tab2)
        canvas_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.disk_canvas = tk.Canvas(canvas_frame, height=220, bg="white")
        self.disk_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.disk_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.disk_canvas.configure(yscrollcommand=scrollbar.set)
        self.disk_canvas.bind("<MouseWheel>",
            lambda e: self.disk_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Info text
        self.info_label = tk.Label(tab2, text="", justify="left", anchor="w", wraplength=960)
        self.info_label.pack(fill="x", padx=10, pady=10)

        # Output table
        self.output_tree = ttk.Treeview(tab2, show="headings", height=8)
        out_scroll = ttk.Scrollbar(tab2, orient="vertical", command=self.output_tree.yview)
        self.output_tree.configure(yscrollcommand=out_scroll.set)
        self.output_tree.pack(fill="both", expand=True, padx=10)
        out_scroll.pack(side="right", fill="y")

    # ── INPUT HANDLERS ────────────────────────────────────────────────────────

    def load_csv(self):
        path = filedialog.askopenfilename(
            initialdir=self.input_dir,
            filetypes=[("CSV", "*.csv")])
        if path:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            df = df.rename(columns={
                "Process Number": "ProcessNumber",
                "Burst Time":     "BurstTime",
                "Request Number": "ArrivalTime",
            })
            self.full_data = df

    def select_processes(self):
        if self.full_data is None:
            messagebox.showwarning("Warning", "Please load a CSV first")
            return

        n = int(self.process_count_var.get())
        self.selected_data = self.full_data.sample(
            n=min(n, len(self.full_data))).reset_index(drop=True)

        for row in self.tree.get_children():
            self.tree.delete(row)
        for _, r in self.selected_data.iterrows():
            self.tree.insert("", "end", values=[r.get(c, "") for c in self.tree["columns"]])

    def finish(self):
        if self.selected_data is None:
            messagebox.showwarning("Warning", "No data selected")
            return

        self.final_data    = self.selected_data
        self.memory_config = {
            "ram":        int(self.ram_var.get()),
            "disk":       int(self.disk_head_var.get()),
            "frame_size": int(self.frame_size_var.get()),
            "quantum":    int(self.quantum_var.get()),
            "priority":    self.priority_var.get()
        }

        save_path = os.path.join(self.output_dir or os.getcwd(), "selected_processes.csv")
        self.final_data.to_csv(save_path, index=False)
        if self.simulation_callback is not None:
            self.simulation_callback(self.final_data.copy(), self.memory_config.copy())
        elif self._ready is not None:
            self._ready.set(True)

    def set_simulation_callback(self, callback):
        """Register the main simulation runner for the initial and later runs."""
        self.simulation_callback = callback

    def set_input_dir(self, path):
        self.input_dir = path

    def set_output_dir(self, path):
        self.output_dir = path

    # ── SETTERS (called by main.py after each module runs) ────────────────────

    def set_ml_results(self, disk_algo, schedule_algo, mem_algo, page_algo):
        self.ml_results = {
            "disk":      disk_algo,
            "scheduler": schedule_algo,
            "memory":    mem_algo,
            "pages":     page_algo,
        }
        self.ml_label.config(
            text=f"ML  →  Disk: {disk_algo}  |  CPU: {schedule_algo}"
                 f"  |  Memory: {mem_algo}  |  Pages: {page_algo}"
        )
        self.root.update()

    def set_disk_result(self, disk_result, disk_ordered_df):
        self.disk_result     = disk_result
        self.disk_ordered_df = disk_ordered_df
        self.show_disk()       # auto-display disk visual when results arrive
        self.root.update()

    def set_pages_result(self, pages_result):
        self.pages_result = pages_result
        self.root.update()

    def set_memory_result(self, memory_state, in_ram, in_queue):
        self.memory_state = memory_state
        self.in_ram       = in_ram
        self.in_queue     = in_queue
        self.root.update()

    def set_deadlock_result(self, deadlock_result):
        self.deadlock_result = deadlock_result
        self.root.update()

    def set_schedule_result(self, schedule_df, schedule_algo):
        self.schedule_df   = schedule_df
        self.schedule_algo = schedule_algo
        self.root.update()

    # ── RUN / CLOSE ───────────────────────────────────────────────────────────

    def run(self):
        self._ready = tk.BooleanVar(value=False)
        self.root.wait_variable(self._ready)
        return self.final_data, self.memory_config

    def show_output_tab(self):
        self.notebook.select(1)
        self.root.update()

    def show_error(self, message):
        self.info_label.config(text=f"ERROR — simulation stopped:\n{message}", fg="red")
        self.root.update()

    def wait_for_close(self):
        self.root.mainloop()

    # ── DISPLAY HELPERS ───────────────────────────────────────────────────────

    def _show_table(self, df):
        self.output_tree.delete(*self.output_tree.get_children())
        self.output_tree["columns"] = list(df.columns)
        for col in df.columns:
            self.output_tree.heading(col, text=col)
            self.output_tree.column(col, width=120, anchor="center")
        for _, row in df.iterrows():
            self.output_tree.insert("", "end", values=list(row))

    def _clear_canvas(self):
        self.disk_canvas.delete("all")

    # ── OUTPUT VIEWS ──────────────────────────────────────────────────────────

    def show_disk(self):
        self._clear_canvas()
        self.info_label.config(text="")

        if self.disk_result is None:
            self.info_label.config(text="Disk results not yet available.")
            return

        result = self.disk_result

        # Table: disk-ordered processes
        display_df = self.disk_ordered_df[["ProcessNumber", "Location"]].copy()
        self._show_table(display_df)

        self.info_label.config(text=(
            f"Algorithm: {result['algorithm']}  |  "
            f"Reason: {result['reason']}\n"
            f"Total Head Movement: {result['total']}  |  "
            f"Head Path: {result['order']}"
        ))

        self._draw_disk_path(result["order"])

    def show_pages(self):
        self._clear_canvas()

        if self.pages_result is None:
            self.info_label.config(text="Pages results not yet available.")
            return

        r  = self.pages_result
        df = r["results"]
        frame_size = max((len(m) for m in df["Memory"].tolist()), default=3)

        self.info_label.config(text=(
            f"Algorithm: FIFO  |  Faults: {r['faults']}  |  Hits: {r['hits']}  "
            f"|  Hit Rate: {r['hit_rate']}  |  Fault Rate: {r['fault_rate']}"
        ))

        cvs = self.disk_canvas
        cvs.update_idletasks()
        W     = max(cvs.winfo_width(), 700)
        total = r["hits"] + r["faults"]

        # Hit / fault bar
        BX=60; BY=14; BH=34; BW=W-100
        hit_w = int(BW * r["hits"] / total) if total else 0
        cvs.create_text(BX-4, BY+BH//2, text="Pages", anchor="e", font=("Arial",8,"bold"))
        cvs.create_rectangle(BX, BY, BX+hit_w, BY+BH, fill="#55A868", outline="")
        if hit_w > 28:
            cvs.create_text(BX+hit_w//2, BY+BH//2,
                text=f"Hits {r['hits']}", fill="white", font=("Arial",9,"bold"))
        fw = BW - hit_w
        cvs.create_rectangle(BX+hit_w, BY, BX+hit_w+fw, BY+BH, fill="#C44E52", outline="")
        if fw > 28:
            cvs.create_text(BX+hit_w+fw//2, BY+BH//2,
                text=f"Faults {r['faults']}", fill="white", font=("Arial",9,"bold"))

        # Page-frame grid
        CW=42; CH=26; PL=60; PT=68
        for ci, (_, row) in enumerate(df.iterrows()):
            col = "#C44E52" if row["Fault"] else "#444"
            cvs.create_text(PL+ci*CW+CW//2, PT-14, text=str(row["Page"]),
                font=("Arial",7), fill=col)
        for ri in range(frame_size):
            cvs.create_text(PL-6, PT+ri*CH+CH//2, text=f"F{ri}",
                anchor="e", font=("Arial",8))
        for ci, (_, row) in enumerate(df.iterrows()):
            mem = row["Memory"]
            for ri in range(frame_size):
                x1=PL+ci*CW; y1=PT+ri*CH; x2=x1+CW-2; y2=y1+CH-2
                if ri < len(mem):
                    cvs.create_rectangle(x1, y1, x2, y2,
                        fill=_pc(mem[ri]), outline="#fff", width=1)
                    cvs.create_text((x1+x2)//2, (y1+y2)//2, text=str(mem[ri]),
                        fill="white", font=("Arial",8,"bold"))
                else:
                    cvs.create_rectangle(x1, y1, x2, y2, fill="#e0e0e0", outline="#ccc")
            if row["Fault"]:
                cvs.create_rectangle(PL+ci*CW-1, PT-2,
                    PL+ci*CW+CW-3, PT+frame_size*CH, outline="#C44E52", width=2)

        cvs.configure(scrollregion=(0, 0, PL+len(df)*CW+20, PT+frame_size*CH+20))
        cvs.yview_moveto(0)

        tbl = r["results"].copy()
        tbl["Memory"] = tbl["Memory"].apply(str)
        self._show_table(tbl)

    def show_memory(self):
        self._clear_canvas()

        if self.memory_state is None:
            self.info_label.config(text="Memory results not yet available.")
            return

        ram_ids   = [b["process"] for b in self.memory_state if not b["free"]]
        queue_ids = self.in_queue["ProcessNumber"].tolist() if self.in_queue is not None else []
        algo      = self.ml_results["memory"] if self.ml_results else "-"

        self.info_label.config(text=(
            f"Algorithm: {algo}  |  "
            f"In RAM: {ram_ids}  |  "
            f"Queue: {queue_ids}"
        ))

        cvs = self.disk_canvas
        cvs.update_idletasks()
        W     = max(cvs.winfo_width(), 800)
        total = sum(b["size"] for b in self.memory_state)

        # RAM segmented bar
        BY=28; BH=55; PX=30; BW=W-2*PX
        cvs.create_text(PX, BY-14, text="RAM", anchor="w", font=("Arial",9,"bold"))
        x = PX
        for block in self.memory_state:
            w = max(int(BW * block["size"] / total), 2)
            if block["free"]:
                fill, label, tc = "#d0d0d0", "FREE", "#666"
            else:
                fill  = _pc(block["process"])
                label = f"P{block['process']}"
                tc    = "white"
            cvs.create_rectangle(x, BY, x+w, BY+BH, fill=fill, outline="#fff", width=1)
            if w > 22:
                cvs.create_text(x+w//2, BY+BH//2, text=label, fill=tc, font=("Arial",9,"bold"))
            if w > 38:
                cvs.create_text(x+w//2, BY+BH+12, text=str(block["size"]),
                    font=("Arial",7), fill="#555")
            x += w

        # Queue row
        QY = BY + BH + 38
        cvs.create_text(PX, QY+18, text="Queue:", anchor="w", font=("Arial",9,"bold"))
        qx = PX + 68
        if not queue_ids:
            cvs.create_text(qx, QY+18, text="empty", anchor="w", fill="#888", font=("Arial",9))
        else:
            for pid in queue_ids:
                cvs.create_rectangle(qx, QY+2, qx+50, QY+36, fill=_pc(pid), outline="#fff")
                cvs.create_text(qx+25, QY+18, text=f"P{pid}", fill="white", font=("Arial",9,"bold"))
                qx += 58

        cvs.configure(scrollregion=(0, 0, W, QY+52))
        cvs.yview_moveto(0)

        rows = [{"Start (KB)": b["start"], "Size (KB)": b["size"],
                 "Status": "FREE" if b["free"] else f"P{b['process']}"}
                for b in self.memory_state]
        self._show_table(pd.DataFrame(rows))

    def show_deadlock(self):
        self._clear_canvas()

        if self.deadlock_result is None:
            self.info_label.config(text="Deadlock results not yet available.")
            return

        r = self.deadlock_result

        if r["deadlock"]:
            status, colour = "DEADLOCK DETECTED", "red"
        else:
            status, colour = "System is SAFE", "#2a7a2a"

        seq     = r["safe_sequence"]
        seq_str = "  ->  ".join(str(p) for p in seq) or "N/A"
        self.info_label.config(text=f"{status}     Safe sequence: {seq_str}", fg=colour)

        cvs = self.disk_canvas
        if not seq:
            cvs.create_text(20, 40, text="No safe sequence — deadlock.",
                anchor="w", fill="red", font=("Arial",11))
            cvs.configure(scrollregion=(0, 0, 300, 80))
        else:
            BW=70; BH=40; PX=30; PY=40
            x = PX
            for i, pid in enumerate(seq):
                cvs.create_rectangle(x, PY, x+BW, PY+BH,
                    fill=_pc(pid), outline="#fff", width=2)
                cvs.create_text(x+BW//2, PY+BH//2, text=f"P{pid}",
                    fill="white", font=("Arial",11,"bold"))
                if i < len(seq)-1:
                    ax = x+BW+2
                    cvs.create_line(ax, PY+BH//2, ax+18, PY+BH//2,
                        arrow=tk.LAST, width=2, fill="#555")
                x += BW + 22
            cvs.configure(scrollregion=(0, 0, x+20, PY+BH+30))
            cvs.yview_moveto(0)

        self._show_table(pd.DataFrame({"Status": [status], "Safe Sequence": [seq_str]}))

    def show_scheduling(self):
        self._clear_canvas()

        if self.schedule_df is None:
            self.info_label.config(text="Scheduling results not yet available.")
            return

        df      = self.schedule_df
        avg_wait = df["Waiting"].mean()
        avg_tat  = df["Turnaround"].mean()
        self.info_label.config(
            text=f"Algorithm: {self.schedule_algo}  |  "
                 f"Avg Waiting: {avg_wait:.2f}  |  Avg Turnaround: {avg_tat:.2f}",
            fg="#333")

        cvs = self.disk_canvas
        cvs.update_idletasks()
        W = max(cvs.winfo_width(), 900)

        if "Start" not in df.columns:
            cvs.create_text(20, 30,
                text="Gantt not available for this algorithm (no Start column).",
                anchor="w", fill="#888")
            cvs.configure(scrollregion=(0, 0, 500, 60))
        else:
            procs = df["Process"].unique().tolist()
            max_t = int(df["Finish"].max())
            PL=70; PT=14; RH=28; BH=20; WU=W-PL-20

            def tx(t):
                return PL + int(t / max_t * WU) if max_t else PL

            row_map = {p: i for i, p in enumerate(procs)}
            for p, i in row_map.items():
                cvs.create_text(PL-6, PT+i*RH+RH//2, text=f"P{p}",
                    anchor="e", font=("Arial",8,"bold"))

            ax_y = PT + len(procs)*RH + 8
            cvs.create_line(PL, ax_y, W-20, ax_y, fill="#999")
            for t in range(0, max_t+1, max(1, max_t//12)):
                x = tx(t)
                cvs.create_line(x, ax_y, x, ax_y+4, fill="#999")
                cvs.create_text(x, ax_y+12, text=str(t), font=("Arial",7), fill="#555")

            for _, row in df.iterrows():
                pid = row["Process"]
                ri  = row_map[pid]
                y1  = PT + ri*RH + (RH-BH)//2
                x1  = tx(int(row["Start"]))
                x2  = tx(int(row["Finish"]))
                cvs.create_rectangle(x1, y1, x2, y1+BH,
                    fill=_pc(pid), outline="#fff", width=1)
                if x2-x1 > 14:
                    cvs.create_text((x1+x2)//2, y1+BH//2, text=f"P{pid}",
                        fill="white", font=("Arial",7,"bold"))

            # Waiting / turnaround bars below Gantt
            BY2   = ax_y + 28
            max_v = max(df[["Waiting","Turnaround"]].max().tolist() + [1])
            def bw(v): return max(2, int(v / max_v * (W-PL-60)))

            cvs.create_rectangle(PL,    BY2+2, PL+12,  BY2+11, fill="#4C72B0", outline="")
            cvs.create_text(PL+16,  BY2+6, text="Waiting",    anchor="w", font=("Arial",7))
            cvs.create_rectangle(PL+80, BY2+2, PL+92,  BY2+11, fill="#DD8452", outline="")
            cvs.create_text(PL+96,  BY2+6, text="Turnaround", anchor="w", font=("Arial",7))

            for i, (_, row) in enumerate(df.iterrows()):
                pid = row["Process"]
                yw  = BY2 + 18 + i*26
                cvs.create_text(PL-6, yw+5, text=f"P{pid}", anchor="e", font=("Arial",8))
                ww = bw(row["Waiting"])
                cvs.create_rectangle(PL, yw, PL+ww, yw+9, fill="#4C72B0", outline="")
                cvs.create_text(PL+ww+3, yw+4, text=str(int(row["Waiting"])),
                    anchor="w", font=("Arial",7), fill="#333")
                tw = bw(row["Turnaround"])
                cvs.create_rectangle(PL, yw+11, PL+tw, yw+20, fill="#DD8452", outline="")
                cvs.create_text(PL+tw+3, yw+15, text=str(int(row["Turnaround"])),
                    anchor="w", font=("Arial",7), fill="#333")

            cvs.configure(scrollregion=(0, 0, W, BY2+18+len(df)*26+20))
            cvs.yview_moveto(0)

        self._show_table(df)

    # ── DISK GRAPH ────────────────────────────────────────────────────────────

    def _draw_disk_path(self, order):
        self.disk_canvas.delete("all")
        if not order:
            return

        self.disk_canvas.update_idletasks()
        width    = max(self.disk_canvas.winfo_width(), 200)
        max_disk = 199

        def scale(x):
            return int((x / max_disk) * (width - 40)) + 20

        # Axis
        axis_y = 20
        self.disk_canvas.create_line(20, axis_y, width - 20, axis_y)
        for tick in [0, 50, 100, 150, 199]:
            x = scale(tick)
            self.disk_canvas.create_line(x, axis_y - 5, x, axis_y + 5)
            self.disk_canvas.create_text(x, axis_y + 15, text=str(tick))

        step    = 35
        start_y = 55
        x_prev  = scale(order[0])
        y_prev  = start_y

        self.disk_canvas.create_oval(
            x_prev-4, y_prev-4, x_prev+4, y_prev+4, fill="blue")
        self.disk_canvas.create_text(
            x_prev, y_prev - 10, text=str(order[0]), font=("Arial", 8))

        for i in range(1, len(order)):
            x_curr = scale(order[i])
            y_curr = start_y + i * step
            self.disk_canvas.create_line(
                x_prev, y_prev, x_curr, y_curr, arrow=tk.LAST, width=2)
            self.disk_canvas.create_oval(
                x_curr-4, y_curr-4, x_curr+4, y_curr+4, fill="blue")
            self.disk_canvas.create_text(
                x_curr, y_curr - 10, text=str(order[i]), font=("Arial", 8))
            x_prev, y_prev = x_curr, y_curr

        # Final point in red
        self.disk_canvas.create_oval(
            x_prev-5, y_prev-5, x_prev+5, y_prev+5, fill="red")

        self.disk_canvas.update_idletasks()
        bbox = self.disk_canvas.bbox("all")
        if bbox:
            self.disk_canvas.configure(scrollregion=bbox)
            self.disk_canvas.yview_moveto(0)
