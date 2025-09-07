import streamlit as st
import requests
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import os
from fpdf import FPDF

# -------------------------------
# Configuration
# -------------------------------
RAMP_API_URLS = [
    "https://rampdb.nih.gov/api/query"
]

# -------------------------------
# Helper Functions
# -------------------------------

def map_common_name_to_hmdb(common_name):
    """Mock function to map common name to HMDB ID"""
    # In production, replace with actual lookup or API call
    mapping = {
        "glucose": "HMDB0000122",
        "lactic acid": "HMDB0000190",
        "citrate": "HMDB0000094"
    }
    return mapping.get(common_name.lower(), None)

def query_ramp_api(analyte_id, analyte_type):
    """Query RaMP API for pathway information"""
    prefix = "hmdb" if analyte_type == "metabolite" else "uniprot"
    full_id = f"{prefix}:{analyte_id}"
    payload = {
        "input": [full_id],
        "type": "pathway"
    }

    for url in RAMP_API_URLS:
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            continue
    return {}

def perform_enrichment(pathway_data):
    """Mock enrichment analysis"""
    enriched = []
    for entry in pathway_data:
        enriched.append({
            "pathway": entry.get("pathway_name", "Unknown"),
            "source": entry.get("source", "RaMP"),
            "score": round(1.0 / (1 + len(entry.get("analyte_list", []))), 4)
        })
    return pd.DataFrame(enriched)

def create_network_graph(analyte_id, pathway_df):
    """Create a network graph using pyvis"""
    net = Network(height="500px", width="100%", notebook=False)
    net.add_node(analyte_id, label=analyte_id, color="red")

    for _, row in pathway_df.iterrows():
        net.add_node(row["pathway"], label=row["pathway"], color="lightblue")
        net.add_edge(analyte_id, row["pathway"])

    temp_dir = tempfile.mkdtemp()
    html_path = os.path.join(temp_dir, "network.html")
    net.show(html_path)
    return html_path

def download_csv(df):
    return df.to_csv(index=False).encode("utf-8")

def download_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for i, row in df.iterrows():
        line = f"{row['pathway']} (Score: {row['score']})"
        pdf.cell(200, 10, txt=line, ln=True)
    temp_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(temp_path)
    return temp_path

# -------------------------------
# Streamlit App
# -------------------------------

st.title("Multi-Omic Pathway Explorer using RaMP")

analyte_input = st.text_input("Enter Analyte ID or Common Name (e.g., P04637 or Glucose):")
analyte_type = st.selectbox("Select Analyte Type", ["protein", "metabolite"])

if st.button("Query Pathways"):
    if not analyte_input:
        st.warning("Please enter an analyte ID or name.")
    else:
        analyte_id = analyte_input
        if not analyte_input.upper().startswith(("P", "Q", "HMDB")):
            mapped_id = map_common_name_to_hmdb(analyte_input)
            if mapped_id:
                analyte_id = mapped_id
                st.info(f"Mapped '{analyte_input}' to HMDB ID: {analyte_id}")
            else:
                st.error("Could not map common name to ID.")
                st.stop()

        data = query_ramp_api(analyte_id, analyte_type)
        if not data:
            st.error("No data returned from RaMP API.")
        else:
            df = perform_enrichment(data)
            st.subheader("Enriched Pathways")
            st.dataframe(df)

            # Download buttons
            st.download_button("Download CSV", download_csv(df), file_name="enriched_pathways.csv")
            pdf_path = download_pdf(df)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="enriched_pathways.pdf")

            # Network graph
            st.subheader("Pathway Network Graph")
            html_path = create_network_graph(analyte_id, df)
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
                st.components.v1.html(html_content, height=550, scrolling=True)

