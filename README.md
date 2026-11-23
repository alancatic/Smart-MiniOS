# Smart MiniOS Simulator

Smart MiniOS is an educational Python application that demonstrates operating-system concepts through a Tkinter dashboard. It combines CPU and disk scheduling, memory allocation, paging, deadlock analysis, and simulated security checks.

## Features

- CPU scheduling: FCFS, SJF, Round Robin, and priority variants
- Disk scheduling: FCFS, SSTF, and SCAN
- Memory allocation: First Fit, Best Fit, and Next Fit
- Paging simulation
- Deadlock analysis
- Simulated file-access and process-memory checks
- Rule-based algorithm recommendations

The dashboard calls the recommendation feature “ML,” but its recommendations are based on predefined rules. It does not train a machine-learning model.

## Requirements

- Python 3.13
- pandas, installed from `python_files/requirements.txt`
- A desktop environment that supports Tkinter

## Run on Windows

Open a terminal in the project folder and run:

```powershell
py -3.13 -m pip install -r python_files/requirements.txt
py -3.13 python_files/main.py
```

You can also double-click `START.bat`. The application opens a desktop window, so it does not run as a Tkinter dashboard inside Google Colab.

## Input data

The `csv_files` folder contains synthetic process data and a small security demonstration dataset. Use these files to load example workloads into the dashboard.

## Output files

The application writes simulation results to the `outputs` folder. These are generated files and do not need to be included in the repository.

## Scope

This is a classroom simulation. It does not boot an operating system, control real processes, enforce access to files on the computer, or provide real security monitoring.
