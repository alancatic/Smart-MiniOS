import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd


def install_security_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text='Security')
    ttk.Label(tab, text='Run a simulation first. Requests below use its processes and RAM.\n'
              'File permissions and resource requests are simulated; results are saved to security_output.csv.').pack(pady=8)
    controls = ttk.Frame(tab)
    controls.pack(fill='x', padx=10)
    fields = {}
    for label, default in [('PID', '1'), ('Target PID', '1'), ('Offset (KB)', '0')]:
        ttk.Label(controls, text=label).pack(side='left')
        var = tk.StringVar(value=default)
        ttk.Entry(controls, textvariable=var, width=6).pack(side='left', padx=4)
        fields[label] = var
    file_var = tk.StringVar(value='public.txt')
    ttk.Combobox(controls, textvariable=file_var, values=['public.txt', 'system.cfg', 'shared.txt'], width=15, state='readonly').pack(side='left')
    resource_var = tk.StringVar(value='A')
    ttk.Combobox(controls, textvariable=resource_var, values=list('ABCD'), width=4, state='readonly').pack(side='left')
    info = ttk.Label(tab, text='No simulation yet.', wraplength=950)
    info.pack(fill='x', padx=10, pady=8)
    tree = ttk.Treeview(tab, columns=['Event', 'Kind', 'Process', 'Target', 'Status', 'Reason'], show='headings')
    for col in tree['columns']:
        tree.heading(col, text=col)
        tree.column(col, width=90 if col != 'Reason' else 320)
    scroll = ttk.Scrollbar(tab, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    buttons = ttk.Frame(tab)
    buttons.pack(fill='x', padx=10, pady=6)
    tree.pack(side='left', fill='both', expand=True)
    scroll.pack(side='right', fill='y')

    def refresh():
        session = getattr(app, 'security_session', None)
        if session is None:
            return
        info.config(text='Processes: ' + ', '.join(f'{p.process_id} ({p.user_role})' for p in session.processes)
                    + '\nFiles: public.txt: all read, user/admin write; system.cfg: admin only; shared.txt: user/admin read, admin write.')
        tree.delete(*tree.get_children())
        for event in session.events:
            tree.insert('', 'end', values=list(event.values()))

    def reset_session():
        """Replace the old audit table and PID defaults after a new workload runs."""
        session = getattr(app, 'security_session', None)
        if session and session.processes:
            first_pid = str(session.processes[0].process_id)
            fields['PID'].set(first_pid)
            fields['Target PID'].set(first_pid)
        fields['Offset (KB)'].set('0')
        refresh()

    def request(kind):
        session = getattr(app, 'security_session', None)
        if session is None:
            messagebox.showinfo('Security', 'Run a simulation first.')
            return
        try:
            pid = int(fields['PID'].get())
            if kind == 'memory':
                session.memory_request(pid, int(fields['Target PID'].get()), int(fields['Offset (KB)'].get()))
            elif kind == 'resource':
                session.resource_request(pid, resource_var.get())
            else:
                session.file_request(pid, file_var.get(), kind)
            refresh()
        except (ValueError, OSError) as exc:
            messagebox.showerror('Security', str(exc))

    for text, kind in [('Read file', 'read'), ('Write file', 'write'), ('Access memory', 'memory'), ('Request resource', 'resource')]:
        ttk.Button(buttons, text=text, command=lambda k=kind: request(k)).pack(side='left', padx=5)
    app.refresh_security = refresh
    app.reset_security_session = reset_session
