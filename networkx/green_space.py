import numpy as np
import pandas as pd
import networkx as nx
import json
import time
import math
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,LinearSegmentedColormap
from scipy.spatial import cKDTree

DATA_BUS_STOPS = "./data/bus-stops.csv"
DATA_BUS_SEQUENCES = "./data/bus-sequences.csv"
DATA_LONDON = "./data/londonUTLA_full.csv"
DATA_POPULATION = "./data/LSOA_(Dec_2011)_Population_Weighted_Centroids_in_England_and_Wales.csv"
DATA_GREEN_SPACE = "./data/green_space.csv"

WALKING_SPEED = 1 # m/s
BUS_SPEED = 4 # m/s
K = 5

breakdown = []

# 1. Import dataset
breakdown.append(time.time())
bus_stops = pd.read_csv(DATA_BUS_STOPS, header=0, dtype={'Location_Easting': float, 'Location_Northing': float})
routes = pd.read_csv(DATA_BUS_SEQUENCES, header=0, dtype={'Location_Easting': float, 'Location_Northing': float})
population = pd.read_csv(DATA_POPULATION, header=0, dtype={'X': float, 'Y': float})
councils = pd.read_csv(DATA_LONDON, header=0)
df_green_space = pd.read_csv(DATA_GREEN_SPACE, header=0, index_col=0)



# 2. Preprocess
breakdown.append(time.time())
bus_stops = bus_stops[['Stop_Code_LBSL', 'Location_Easting', 'Location_Northing']]
bus_stops.columns = ['id', 'x', 'y']

routes = routes[['Route', 'Run', 'Sequence', 'Stop_Code_LBSL', 'Location_Easting', 'Location_Northing']]
routes.columns = ['id', 'run', 'seq', 'stop', 'x', 'y']

councils = set(councils['LAName'])

population.columns = ['x', 'y', 'oid', 'lsoa', 'council', 'gid']
population['council'] = population['council'].str[:-5]
population = population[population['council'].isin(councils)]

df_green_space = df_green_space[df_green_space['LSOA_Code'].isin(population['lsoa'])].reset_index(drop=True)

bus_stops_pos = dict(zip(bus_stops['id'].values, bus_stops[['x', 'y']].itertuples(index=False)))
population_pos = dict(zip(population['lsoa'].values, population[['x', 'y']].itertuples(index=False)))
pos = {**bus_stops_pos, **population_pos}

# build KNN from bus stops
kdtree = cKDTree(bus_stops[['x', 'y']])

# find top K nearest bus stops for each population
stops_distance, nearest_stops = kdtree.query(population[['x', 'y']], k=K)

# 3. Building Graph
breakdown.append(time.time())
Graph = nx.DiGraph()
Graph.add_nodes_from(bus_stops['id'].values, type='stop')
Graph.add_nodes_from(population['lsoa'].values, type='population')

# Add bus routes as edges
for route in routes.groupby(['id', 'run']):
    stops = route[1][['stop', 'x', 'y']]
    x1, x2 = stops['x'].values[:-1], stops['x'].values[1:]
    y1, y2 = stops['y'].values[:-1], stops['y'].values[1:]
    d = ((x1-x2)**2 + (y1-y2)**2)**0.5
    edges = zip(stops['stop'].values[:-1], stops['stop'].values[1:], d / BUS_SPEED)
    Graph.add_weighted_edges_from(edges)

# Add edges between population and nearest bus stops
for lsoa, stops, dis in zip(population['lsoa'].values, nearest_stops, stops_distance):
    near_stops = bus_stops['id'].iloc[stops]
    in_edges = zip([lsoa]*len(stops), near_stops, dis / WALKING_SPEED)
    out_edges = zip(near_stops, [lsoa]*len(stops), dis / WALKING_SPEED)
    Graph.add_weighted_edges_from(in_edges)
    Graph.add_weighted_edges_from(out_edges)
    

# 4. Caculation
breakdown.append(time.time())
# for all population that GSDI_AvgArea <= 2 and GSDI_Access <= 2, find the shortest path to the nearest population that GSDI_AvgArea is 4
large_green_space = set(df_green_space[df_green_space['GSDI_AvgArea'] == 4]['LSOA_Code'].values)
reachbility = {}
for i, row in df_green_space.iterrows():
    if i % 100 == 0:
        print(i, flush=True)
    lsoa = row['LSOA_Code']
    pcnt_goaccess = row['Pcnt_PopArea_With_GOSpace_Access']
    area = row['Area']
    if row['GSDI_AvgArea'] > 2 or row['GSDI_Access'] > 2:
        reachbility[lsoa] = 300 * pcnt_goaccess + area**0.5
        continue
    distance, path = nx.single_source_dijkstra(Graph, source=lsoa, weight='weight', cutoff=5000)
    dis_to_green = [dis for lsoa, dis in distance.items() if lsoa in large_green_space]
    if len(dis_to_green) == 0:
        reachbility[lsoa] = math.inf
    reachbility[lsoa] = min(dis_to_green)


# 5. Plot
breakdown.append(time.time())
plt.hist(reachbility.values(), bins=100)
plt.savefig('distribution.png', dpi=300, bbox_inches='tight')

# plot hot spot map by reachbility
nodes = population['lsoa']
m = max(reachbility.values()) + 10
hot_spot_size = [ 0.1 if math.isinf(reachbility[lsoa]) else (m - reachbility[lsoa]) / 3000 for lsoa in nodes ]
# print(hot_spot_size)
plt.figure(figsize = (10,10))
nx.draw_networkx_nodes(Graph, nodelist=nodes, pos=pos, node_size=hot_spot_size, node_color='#66CC66')
plt.savefig('hot_spot.png', dpi=300, bbox_inches='tight')


NODE_SIZE = 0.1
EDGE_WIDTH = 0.1
BASE_COLORS = ['#990000', '#EE2C2C', '#EE5C42', '#FF7256', '#FF9966',
          '#FFB90F', '#CDCD00', '#999900', '#66CC66', '#00CC66',
          '#20B2AA', '#0099FF', '#0066FF', '#6600FF', '#B23AEE',
          '#FF3366',]
colors = LinearSegmentedColormap.from_list('chaos', BASE_COLORS, len(councils))

plt.figure(figsize = (10,10))
nodes = bus_stops['id'].values
# print(list(nodes))
nx.draw_networkx_nodes(Graph, nodelist=nodes, pos=pos, node_size=NODE_SIZE, node_color='lightgray', label='Bus Stops')
Graph.edges()
nx.draw_networkx_edges(Graph, pos=pos, width=EDGE_WIDTH, edge_color='lightgray', arrows=False, label='Bus Routes')    # 添加arrows后，时间增长两个数量级

councils_colors = {council: colors(i) for i, council in enumerate(councils)}
population_by_council = population.groupby('council')
for council, populations in population_by_council:
    nx.draw_networkx_nodes(Graph, pos=pos, nodelist=populations['lsoa'], node_size=NODE_SIZE, node_color=[councils_colors[council]], label=council)

plt.legend(loc='upper left', bbox_to_anchor=(1, 1), markerscale=10)
plt.savefig('draw.png', format='png', dpi=1000, bbox_inches='tight')


with open('breakdown.json', 'w') as f:
    json.dump(breakdown, f)