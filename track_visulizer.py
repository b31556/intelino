import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend like 'Agg'
import matplotlib.pyplot as plt

from PIL import Image
import io
import json
# Example data

data={}
inn = {}
with open("map.json") as f:
    red=json.load(f)
    for i in red:
        inn[(i[0],i[1],i[2] if i[2] == "-" else int(i[2]))] = red[i]
for i in inn:
    key=inn[i]
    mi=[]
    for o in inn:
        if inn[o] == key:
            mi.append(o)

    data[key]=mi


# Create graph
G = nx.Graph()
for key in data.keys():
    G.add_edge(data[key][0][0:2], data[key][1][0:2])

# Generate a plot using matplotlib
plt.figure(figsize=(10, 8))
pos = nx.spring_layout(G)  # Set layout for node positioning

def draw_map():
    data={}
    inn = {}
    with open("map.json") as f:
        red=json.load(f)
        for i in red:
            inn[(i[0],i[1],i[2] if i[2] == "-" else int(i[2]))] = red[i]
    for i in inn:
        key=inn[i]
        mi=[]
        for o in inn:
            if inn[o] == key:
                mi.append(o)

        data[key]=mi


    # Create graph
    G = nx.Graph()
    for key in data.keys():
        G.add_edge(data[key][0][0:2], data[key][1][0:2])

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)  # Set layout for node positioning
    
    edgecolors=["black" for i in range(len(data))]

    edgelist=[str(i) for i in range(len(data))]

    # Assuming edge_labels is a list, convert it to a dictionary with appropriate keys
    edge_labels_dict = {edge: label for edge, label in zip(G.edges(), edgelist)}

    # Draw the graph
    nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=5, font_weight="bold", edge_color=edgecolors)

    # Draw edge labels
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_dict, font_size=5)

    # Save the plot to a BytesIO buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")  # Save figure as PNG
    buffer.seek(0)

    # Convert the buffer to a PIL Image
    img = Image.open(buffer)

    return img


def prepare_map(trains,_):
    edgecolors=["black" for i in range(len(data))]
    for tcol,tra in trains.items():
        edgecolors[tra]=(tcol[0]/255,tcol[1]/255,tcol[2]/255)

    edgelist=[str(i) for i in range(len(data))]

    # Assuming edge_labels is a list, convert it to a dictionary with appropriate keys
    edge_labels_dict = {edge: label for edge, label in zip(G.edges(), edgelist)}

    # Draw the graph
    nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=5, font_weight="bold", edge_color=edgecolors)

    # Draw edge labels
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_dict, font_size=5)

    # Save the plot to a BytesIO buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")  # Save figure as PNG
    buffer.seek(0)

    # Convert the buffer to a PIL Image
    img = Image.open(buffer)

    return img


plt.close()
