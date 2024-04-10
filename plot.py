import json
import numpy as np
import matplotlib.pyplot as plt
import os

def plot_breakdown(dir1: str, dir2: str):
    with open(f'{dir1}/metrics.json', 'r') as f:
        m1 = json.load(f)
    with open(f'{dir2}/metrics.json', 'r') as f:
        m2 = json.load(f)

    with open(f'{dir1}/breakdown.json', 'r') as f:
        brk1 = json.load(f)
    with open(f'{dir2}/breakdown.json', 'r') as f:
        brk2 = json.load(f)

    names = ['Mathematica', 'NetworkX']

    dur1 = m1['duration']
    dur2 = m2['duration']

    st1 = m1['start_time']
    st2 = m2['start_time']

    ts1 = [st1, *brk1, st1 + dur1]
    ts2 = [st2, *brk2, st2 + dur2]
    ts1 = [y - x for x, y in zip(ts1, ts1[1:])]
    ts2 = [y - x for x, y in zip(ts2, ts2[1:])]

    labels = ['Initialization', 'Data Import', 'Preprocess', 'Building Graph', 'Calculation', 'Visualization']
    height = 0.25
    y = [1, 2]
    acc = np.zeros(2)

    fig, ax = plt.subplots(layout='constrained')

    for label, d1, d2 in zip(labels, ts1, ts2):
        rects = ax.barh(y, [d1, d2], height, left=acc, label=label)
        # if d1 > 50 and d2 > 50:
        #     ax.bar_label(rects, label_type='center', fmt="{:.2f}")
        acc += [d1, d2]
    
    ax.bar_label(rects, labels=[f"{acc[0]:.2f}",f"{acc[1]:.2f}"], label_type='edge')
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('Time (s)')
    ax.set_title('Breakdown of Execution Time', fontsize=16)
    ax.set_yticks(y, names, fontsize=12, rotation=90, va="center")
    ax.legend(loc='upper center', ncols=3)
    ax.set_ylim(0.5, 3)
    ax.set_xlim(0, 600)

    fig.savefig('breakdown.pdf', dpi=300, bbox_inches='tight')


def plot_data(ax, timestamps, cpu_usage, memory_usage):
    color = "tab:red"
    # ax.set_xlabel("Time (s)")
    ax.set_ylabel("CPU Usage (%)", color=color)
    ax.plot(timestamps, cpu_usage, color=color)
    ax.tick_params(axis="y", labelcolor=color)

    ax2 = ax.twinx()
    
    color = "tab:blue"
    ax2.set_ylabel("Memory Usage (MB)", color=color)
    ax2.plot(timestamps, memory_usage, color=color)
    ax2.tick_params(axis="y", labelcolor=color)


def plot_metrics(dirs: list[str]):
    labels = ['Mathematica', 'NetworkX']
    fig, axes = plt.subplots(2, 1, layout='constrained')
    for dir, label, ax in zip(dirs, labels, axes):
        with open(os.path.join(dir, 'metrics.json'), 'r') as f:
            data = json.load(f)
        ts = data['timestamps']
        mu = [x / (1024 * 1024) for x in data['memory_usage']]
        cu = data['cpu_usage']
        ax.set_title(label)
        plot_data(ax, ts, cu, mu)
    ax.set_xlabel("Time (s)")
    fig.savefig('metrics.pdf', dpi=300, bbox_inches='tight')



def plot_related(labels, baseline, others):
    bname, bdata = baseline
    bdata = np.array(bdata)
    n = len(bdata)
    ngroups = len(others) + 1

    width = 1
    gw = width * (ngroups + 1)
    offset = - (gw - width) / 2 + width / 2

    x = np.arange(n) * gw

    fig, ax = plt.subplots(layout='constrained')
    
    rects = ax.bar(x + offset, 1, width, label=bname)
    ax.bar_label(rects, labels=[f"{x:.2f}" for x in bdata], label_type='edge', fontsize=8)
    for name, data in others:
        offset += width 
        data = np.array(data)
        rects = ax.bar(x + offset, data / bdata, width, label=name)
        ax.bar_label(rects, labels=[f"{x:.2f}" for x in data], label_type='edge', fontsize=8)

    ax.set_title('Relative Execution Time', fontsize=16)
    ax.set_xticks(x, labels, rotation=45)
    ax.set_yscale('log')
    ax.set_ylabel('Relative Time')
    ax.set_yticks([1, 5, 10, 50, 100], ['1x', '5x', '10x', '50x', '100x'])
    ax.legend()

    fig.savefig('relative.pdf', dpi=300, bbox_inches='tight')





dirs = ['./networkx/', './mathematica/']
names = ['NetworkX', 'Mathematica']
labels = ['Initialization', 'Data Import', 'Preprocess', 'Building Graph', 'Calculation', 'Visualization', 'Total']
breakdowns = []

for name, dir in zip(names, dirs):
    with open(f'{dir}/metrics.json', 'r') as f:
        m = json.load(f)
    with open(f'{dir}/breakdown.json', 'r') as f:
        brk = json.load(f)
    dur = m['duration']
    st = m['start_time']
    ts = [st, *brk, st + dur]
    ts = [y - x for x, y in zip(ts, ts[1:])]
    ts.append(dur)
    breakdowns.append((name, ts))

plot_breakdown('./mathematica/', './networkx/')
plot_metrics(['./mathematica/', './networkx/'])
plot_related(labels, breakdowns[0], breakdowns[1:])