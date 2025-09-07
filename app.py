import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Simulated example data for demonstration
disease_data = {
    "Parkinson's Disease": {
        "proteins": ["SNCA", "LRRK2", "PINK1"],
        "metabolites": ["Dopamine", "Alpha-synuclein", "Uric acid"],
        "pathways": ["Dopaminergic synapse", "Oxidative phosphorylation"]
    },
    "Renal Cancer": {
        "proteins": ["VHL", "HIF1A", "VEGFA"],
        "metabolites": ["Succinate", "Fumarate", "Glutamine"],
        "pathways": ["HIF-1 signaling", "Metabolic reprogramming"]
    },
    "Type 2 Diabetes": {
        "proteins": ["INS", "IRS1", "GLUT4"],
        "metabolites": ["Glucose", "Insulin", "Lactate"],
        "pathways": ["Insulin signaling", "Glycolysis"]
    }
}

# Streamlit UI
st.title("Multi-Omics Disease Explorer")
st.markdown("Explore relationships between proteins, metabolites, and pathways for selected diseases.")

# Disease selection
selected_disease = st.selectbox("Select a disease", list(disease_data.keys()))

# Search box for filtering nodes
search_term = st.text_input("Search for a specific protein/metabolite/pathway")

# Get data for selected disease
data = disease_data[selected_disease]
proteins = data["proteins"]
metabolites = data["metabolites"]
pathways = data["pathways"]

# Filter nodes if search term is provided
def filter_nodes(nodes):
    return [node for node in nodes if search_term.lower() in node.lower()]

if search_term:
    proteins = filter_nodes(proteins)
    metabolites = filter_nodes(metabolites)
    pathways = filter_nodes(pathways)

# Create network graph using Plotly
nodes = proteins + metabolites + pathways
node_types = ['Protein'] * len(proteins) + ['Metabolite'] * len(metabolites) + ['Pathway'] * len(pathways)
node_colors = ['skyblue'] * len(proteins) + ['lightgreen'] * len(metabolites) + ['orange'] * len(pathways)

# Create node positions in circular layout
import numpy as np
angle = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
x = np.cos(angle)
y = np.sin(angle)

# Create edges between proteins-metabolites and proteins-pathways
edges = []
for i, source in enumerate(nodes):
    for j, target in enumerate(nodes):
        if source != target:
            if (source in proteins and target in metabolites) or (source in proteins and target in pathways):
                edges.append((i, j))

# Create Plotly figure
fig = go.Figure()

# Add edges
for i, j in edges:
    fig.add_trace(go.Scatter(
        x=[x[i], x[j]],
        y=[y[i], y[j]],
        mode='lines',
        line=dict(color='gray', width=1),
        hoverinfo='none'
    ))

# Add nodes
fig.add_trace(go.Scatter(
    x=x,
    y=y,
    mode='markers+text',
    marker=dict(size=20, color=node_colors),
    text=nodes,
    textposition='top center',
    hovertext=node_types,
    hoverinfo='text'
))

fig.update_layout(
    title=f"Network Graph for {selected_disease}",
    showlegend=False,
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False),
    height=600
)

# Display graph
st.plotly_chart(fig, use_container_width=True)

