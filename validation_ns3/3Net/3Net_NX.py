import networkx as nx
import matplotlib.pyplot as plt

# *************************
#           Graph
#
#       A-----------B
#       |           |
#       |           |
#       |           |
#       D-----------C
#
# *************************

# *************************
#           Graph
#
#       A-----------C
#         \       /
#           \  /
#             B
#
# *************************

# initialize latencies for edges (links)
weights = [
    ("A", "B", 100),
    ("B", "C", 100),
    ("A", "C", 300)
]

# create Graph
G = nx.Graph()
G.add_weighted_edges_from(weights)

path = nx.dijkstra_path(G, "A", "C", weight="weight")
dist = nx.dijkstra_path_length(G, "A", "C", weight="weight")

print(path, dist)

nx.draw(G, with_labels=True)
plt.show()

print('Ok!')