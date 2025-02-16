import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image
import io

# Example data
data = {
    0: (("B", "W", 0), ("B", "R", 1)),
    1: (("B", "W", 1), ("R", "B", 0)),
    2: (("R", "Y", 0), ("B", "R", 0)),
    3: (("R", "Y", 1), ("B", "Y", 0)),
    4: (("B", "Y", 1), ("B", "G", 1)),
    5: (("B", "G", 0), ("R", "M", 0)),
    6: (("R", "M", 1), ("B", "M", 1)),
    7: (("B", "W", "-"), ("B", "M", 0)),
    8: (("B", "M", "-"), ("B", "R", "-")),
    9: (("R", "B", 1), ("B", "G", "-")),
    10: (("R", "M", "-"), ("B", "Y", "-")),
    11: (("R", "Y", "-"), ("R", "B", "-"))
}

# Create graph
G = nx.Graph()
for key in data.keys():
    G.add_edge(data[key][0][0:2], data[key][1][0:2])

# Generate a plot using matplotlib
plt.figure(figsize=(10, 8))
pos = nx.spring_layout(G)  # Set layout for node positioning

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
