# Comparing Tools for Analysing and Visualising London Citizens Access Green Spaces via Bus
This is the code part of my BSc final year project at King's College London. Please contact me if you're interested in the whole report.
- Research Problem: The ease of London citizens access green spaces via bus
- Tools: NetworkX, Mathematica
- Supervisor: Professor Nicolas S. Holliman
- Author: [Yichun Zhang](https://github.com/missyQWQ)

## Abstract

In the era of big data, data is growing in size and complexity. In order to meet the challenges of the era of big data, data visualization technology has become a powerful tool. Data visualization refers to the presentation of data in the form of charts or images so that people can visually see and understand trends, patterns, and anomalies in the data. Among them, the visualization of network data is important. Taking ”the ease of London citizens to access green spaces via bus” as the research problem, this project models and solves it from the perspective of graph theory. The algorithm is implemented in two common graph processing and visualization tools (NetworkX and Mathematica), and the performance of the two tools is also evaluated.

## Directory Structure

```bash
Project Directory
├── mathematica
│   ├── data
│   │   ├── (dataset files)
│   ├── green_space.nb
│   ├── green_space.wls
├── monitor.py
├── networkx
│   ├── data
│   │   ├── (dataset files)
│   ├── green_space.ipynb
│   ├── green_space.py
├── plot.py
└── readme.md
```

## Run Code and Collect Metrics

Run the following command in the project root directory to run the code for Mathematica and NetworkX respectively. After running, 3 PNG files will be generated in the mathematica and networkx directories respectively. These three images are the results of the code execution, that is, the visualization of the green space problem. In addition, two JSON files, metrics.json and breakdown.json, will be generated in both directories. The former is the CPU and memory usage information collected by the collector, and the latter is output by the program, which is the timestamp when each part of the program starts running.

```bash
# Run Mathematica
cd mathematica
python ../monitor.py wolframscript -file ./green_space.wls

# Run Networkx
cd ..
cd networkx
python ../monitor.py python ./green_space.py
```

## Plot 

After successfully generating the JSON files, you can use the following command in the project root directory to draw performance comparison graphs.

```bash
python ./plot.py
```
