#!/usr/bin/env python

import json
import psutil
import subprocess
import time
import os

from psutil._common import bytes2human

def get_process_info(process):
    total_memory = process.memory_info().rss
    children = process.children(recursive=True)
    for child in children:
        total_memory += child.memory_info().rss
    return psutil.cpu_percent() * psutil.cpu_count(), total_memory

def monitor(executable_path, executable_args, measure_interval=1.0, print_interval=1.0, output_path="output.json"):
    process = subprocess.Popen([executable_path, *executable_args])
    p = psutil.Process(process.pid)
    start_time = time.time()

    cpu_usage = []
    memory_usage = []
    timestamps = []


    last_print_time = start_time
   
    try:
        while process.poll() is None:
            cpu_percent, memory_rss = get_process_info(p)
            cpu_usage.append(cpu_percent)
            memory_usage.append(memory_rss)
            
            current_time = time.time()
            timestamps.append(current_time - start_time)
            
            if current_time - last_print_time >= print_interval:
                print(f"CPU: {cpu_percent}%, Memory: {bytes2human(memory_rss)}")
                last_print_time = current_time
            
            t2 = time.time()
            time.sleep(measure_interval - (t2 - current_time))
    except Exception as e:
        print(e)
        process.terminate()

    end_time = time.time()
    duration = end_time - start_time

    data = {
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "timestamps": timestamps,
        "duration": duration,
        "start_time": start_time,
    }

    with open(output_path, "w") as f:
        json.dump(data, f)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor the CPU and memory usage of a process.")
    
    parser.add_argument("executable", help="The path to the executable to run and monitor.")

    parser.add_argument("executable_args", nargs=argparse.REMAINDER, help="The arguments to pass to the executable. (default: None)")

    parser.add_argument("-i", "--measure-interval", type=float, default=1.0,
                        help="The interval between measurements in seconds (default: 1.0).")
    
    parser.add_argument("-p", "--print-interval", type=float, default=1.0,
                        help="The interval between prints in seconds (default: 1.0).")
    
    parser.add_argument("-o", "--output-path", default="metrics.json",
                        help="The path to the output JSON file (default: metrics.json).")
    
    args = parser.parse_args()

    print(args)

    monitor(args.executable,
            args.executable_args,
            measure_interval=args.measure_interval,
            print_interval=args.print_interval,
            output_path=args.output_path)
    