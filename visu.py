import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import networkx as nx
import requests
import plotly.colors

# Define the server URL
SERVER_URL = "http://127.0.0.1:5080"

# Fetch and build the static graph
graph_response = requests.get(f"{SERVER_URL}/graph").json()
graph = nx.Graph()
for node, neighbors in graph_response.items():
    for neighbor in neighbors:
        if neighbor is not None:
            graph.add_edge(node, neighbor)

# Calculate node positions using spring layout
node_positions = nx.spring_layout(graph)

# Fetch train IDs and assign unique colors
train_response = requests.get(f"{SERVER_URL}/get_trains").json()
train_ids = train_response["trains"]
train_colors = {
    train_id: plotly.colors.qualitative.Plotly[i % len(plotly.colors.qualitative.Plotly)]
    for i, train_id in enumerate(train_ids)
}

# Initialize the Dash application
app = dash.Dash(__name__)

# Define the application layout
app.layout = html.Div([
    # Sidebar with train selection checklist
    html.Div([
        html.H3("Select Trains"),
        dcc.Checklist(
            id='train-checklist',
            options=[{'label': tid, 'value': tid} for tid in train_ids],
            value=[],
            style={'margin': '10px'}
        ),
    ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'top'}),
    
    # Main graph display area with update interval
    html.Div([
        dcc.Graph(id='graph'),
        dcc.Interval(id='interval-component', interval=5000, n_intervals=0)  # Refresh every 5 seconds
    ], style={'width': '80%', 'display': 'inline-block'})
])

# Callback function to update the graph dynamically
@app.callback(
    Output('graph', 'figure'),
    [Input('train-checklist', 'value'), Input('interval-component', 'n_intervals')]
)
def update_graph(selected_trains, n_intervals):
    traces = []

    # Add static edges to the graph
    edge_x_coords = []
    edge_y_coords = []
    for edge in graph.edges():
        x0, y0 = node_positions[edge[0]]
        x1, y1 = node_positions[edge[1]]
        edge_x_coords.extend([x0, x1, None])
        edge_y_coords.extend([y0, y1, None])
    traces.append(go.Scatter(
        x=edge_x_coords,
        y=edge_y_coords,
        mode='lines',
        line=dict(color='gray', width=1),
        hoverinfo='none',
        name='Edges'
    ))

    # Add static nodes to the graph
    node_x_coords = [node_positions[node][0] for node in graph.nodes()]
    node_y_coords = [node_positions[node][1] for node in graph.nodes()]
    traces.append(go.Scatter(
        x=node_x_coords,
        y=node_y_coords,
        mode='markers',
        marker=dict(color='gray', size=5),
        hoverinfo='text',
        text=list(graph.nodes()),
        name='Nodes'
    ))

    # Add traces for each selected train
    for train_id in selected_trains:
        try:
            # Fetch train plan and position from the server
            train_data = requests.get(f"{SERVER_URL}/get_plan/{train_id}").json()
            plan = train_data.get('plan', [])
            position = train_data.get('position')
            color = train_colors[train_id]

            # Plot the train's route (semi-transparent line)
            if plan:
                route_x = [node_positions[node][0] for node in plan if node in node_positions]
                route_y = [node_positions[node][1] for node in plan if node in node_positions]
                traces.append(go.Scatter(
                    x=route_x,
                    y=route_y,
                    mode='lines',
                    line=dict(color=color, width=2),
                    opacity=0.5,  # Lighter appearance for the route
                    name=f"{train_id} Route",
                    showlegend=False
                ))

            # Plot the train's current position (opaque marker)
            if position and position in node_positions:
                pos_x, pos_y = node_positions[position]
                traces.append(go.Scatter(
                    x=[pos_x],
                    y=[pos_y],
                    mode='markers',
                    marker=dict(color=color, size=10),
                    name=train_id,
                    text=[train_id],
                    hoverinfo='text'
                ))
        except Exception as e:
            print(f"Failed to load data for train {train_id}: {e}")

    # Configure the figure layout
    figure = go.Figure(data=traces)
    figure.update_layout(
        showlegend=True,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )
    return figure

# Launch the Dash application
if __name__ == '__main__':
    app.run(debug=True)