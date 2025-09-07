import streamlit as st
import requests
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import os
import fitz  # PyMuPDF
from io import BytesIO

# RaMP API endpoint
RAMP_API_URL = "https://rampdb.nih.gov/api/pathways-from-analytes"

# MetaboAnalyst mapping function
def map_common_name_to_hmdb(common_name):
    # MetaboAnalyst uses a web form, so we simulate a query via their conversion tool
    # This is a workaround using their web interface
    search_url = f"https://www.metaboanalyst.ca/resources/data/compound_name_mapping.csv"
    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content))
            match = df[df['Name'].str.lower() == common_name.lower()]
            if not match.empty:
                return match.iloc[0]['HMDB']
    except Exception as e:
        print(f"Error mapping name: {e}")
    return None

# Query RaMP API
def query_ramp_api(analyte_id, analyte_type):
    prefix = "hmdb" if analyte_type == "metabolite" else "uniprot"
    full_id = f"{prefix}:{analyte_id}"
    payload = {
        "input": [full_id],
        "type": "pathway"
    }
    try:
        response = requests.post(RAMP_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"API connection failed: {e}")
    return {}

# Generate network graph
def generate_network_graph(analyte_id, pathways):
    g = nx.Graph()
    g.add_node(analyte_id, label=analyte_id, color='red')
    for pw in pathways:
        pw_name = pw.get('name', 'Unknown')
        g.add_node(pw_name, label=pw_name, color='blue')
        g.add_edge(analyte_id, pw_name)
    return g

# Save network graph as HTML
def save_network_html(graph):
    net = Network(height="600px", width="100%", notebook=False)
    net.from_nx(graph)
    temp_dir = tempfile.mkdtemp()
    html_path = os.path.join(temp_dir, "network.html")
    net.save_graph(html_path)
    return html_path

# Save results to CSV
def save_results_csv(pathways):
    df = pd.DataFrame(pathways)
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "results.csv")
    df.to_csv(csv_path, index=False)
    return csv_path

# Save results to PDF
def save_results_pdf(pathways):
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "results.pdf")
    doc = fitz.open()
    page = doc.new_page()
    text = "Pathway Results:\n\n"
    for pw in pathways:
        text += f"- {pw.get('name', 'Unknown')} (Source: {pw.get('source', 'N/A')})\n"
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(pdf_path)
    return pdf_path

# Streamlit UI
st.title("Multi-Omic Pathway Explorer using RaMP")

st.markdown("""
Enter either an **Analyte ID** (e.g., UniProt ID like `P04637` or HMDB ID like `HMDB0000122`)  
or a **common name** (e.g., `Glucose`, `Lactic acid`).  
If you enter a common name, the system will automatically map it to the correct HMDB ID and analyte type.
""")

analyte_input = st.text_input("Enter Analyte ID or Common Name:")
analyte_type = st.selectbox("Select Analyte Type", ["protein", "metabolite"])

if st.button("Query Pathways"):
    if analyte_input:
        mapped_id = None
        if analyte_type == "metabolite" and not analyte_input.lower().startswith("hmdb"):
            mapped_id = map_common_name_to_hmdb(analyte_input)
            if mapped_id:
                st.success(f"Mapped '{analyte_input}' to HMDB ID: {mapped_id}")
                analyte_id = mapped_id
                analyte_type = "metabolite"
            else:
                st.error("Could not map common name to HMDB ID.")
                st.stop()
        else:
            analyte_id = analyte_input

        result = query_ramp_api(analyte_id, analyte_type)
        if result and isinstance(result, list) and len(result) > 0:
            st.success(f"Found {len(result)} pathways.")
            df = pd.DataFrame(result)
            st.dataframe(df)

            # Network graph
            graph = generate_network_graph(analyte_id, result)
            html_path = save_network_html(graph)
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=600)

            # Download buttons
            csv_path = save_results_csv(result)
            pdf_path = save_results_pdf(result)

            with open(csv_path, "rb") as f:
                st.download_button("Download CSV", f, file_name="results.csv")

            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="results.pdf")
        else:
            st.warning("No pathways found for the given analyte.")
    else:
        st.warning("Please enter an analyte ID or name.")

