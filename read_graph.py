# Import modules
import networkx as nx
from networkx.readwrite import json_graph
import json
import matplotlib.pyplot as plt
from pyvis.network import Network
import networkx as nx

# Load the JSON file into a dictionary
with open('graph.json', 'r') as f:
    data = json.load(f)

# Convert the dictionary into a networkx graph
G = json_graph.node_link_graph(data)

print(G.nodes)
print(G.edges)

# Draw the graph
nx.draw_networkx(G, with_labels=True)
plt.show()