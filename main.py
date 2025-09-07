import streamlit as st
import pandas as pd
import requests
import networkx as nx
from pyvis.network import Network
import tempfile
import os
from fpdf import FPDF

# Function to query RaMP API for pathways related to analyte
def query_ramp(analyte_id, analyte_type):
    url = "https://ramp-api-url/query"  # Replace with actual RaMP API endpoint
    payload = {
        "analyte_id": analyte_id,
        "analyte_type": analyte_type
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

# Function to perform enrichment analysis (mock implementation)
def enrichment_analysis(pathways):
    enriched = []
    for pathway in pathways:
        enriched.append({
            "Pathway": pathway["name"],
            "Score": round(pathway["relevance_score"] * 1.5, 2),
            "Source": pathway["source"]
        })
    return enriched

# Function to create network graph
def create_network_graph(enriched_pathways, analyte_id):
    G = nx.Graph()
    G.add_node(analyte_id, label="Analyte", color="red")
    for pathway in enriched_pathways:
        G.add_node(pathway["Pathway"], label="Pathway", color="blue")
        G.add_edge(analyte_id, pathway["Pathway"])
    return G

# Function to save results as CSV
def save_csv(enriched_pathways):
    df = pd.DataFrame(enriched_pathways)
    csv_path = os.path.join(tempfile.gettempdir(), "enrichment_results.csv")
    df.to_csv(csv_path, index=False)
    return csv_path

# Function to save results as PDF
def save_pdf(enriched_pathways):
    pdf_path = os.path.join(tempfile.gettempdir(), "enrichment_results.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Enrichment Analysis Results", ln=True, align='C')
    for pathway in enriched_pathways:
        line = f"{pathway['Pathway']} | Score: {pathway['Score']} | Source: {pathway['Source']}"
        pdf.cell(200, 10, txt=line, ln=True)
    pdf.output(pdf_path)
    return pdf_path

# Streamlit UI
st.title("Multi-Omic Pathway Analysis using RaMP")

analyte_id = st.text_input("Enter Analyte ID (e.g., UniProt or HMDB ID):")
analyte_type = st.selectbox("Select Analyte Type:", ["protein", "metabolite"])

if st.button("Analyze"):
    st.info("Querying RaMP database...")
    pathways = query_ramp(analyte_id, analyte_type)
    if pathways:
        st.success(f"Found {len(pathways)} pathways related to {analyte_id}")
        enriched_pathways = enrichment_analysis(pathways)
        df = pd.DataFrame(enriched_pathways)
        st.dataframe(df)

        # Create and display network graph
        G = create_network_graph(enriched_pathways, analyte_id)
        net = Network(notebook=False)
        net.from_nx(G)
        graph_path = os.path.join(tempfile.gettempdir(), "network_graph.html")
        net.save_graph(graph_path)
        st.components.v1.html(open(graph_path, 'r').read(), height=500)

        # Download options
        csv_file = save_csv(enriched_pathways)
        pdf_file = save_pdf(enriched_pathways)
        st.download_button("Download CSV", open(csv_file, "rb"), file_name="enrichment_results.csv")
        st.download_button("Download PDF", open(pdf_file, "rb"), file_name="enrichment_results.pdf")
    else:
        st.error("No pathways found or error querying RaMP API.")

