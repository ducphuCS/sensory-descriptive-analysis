import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set basic page layout
st.set_page_config(
    page_title="Sensory Geometric Means Dashboard",
    page_icon="📊",
    layout="wide"
)

# Configuration constants
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api")
THRESHOLDS_RAW = os.getenv("SIGNIFICANCE_THRESHOLDS", "0.15,0.4,0.7")
THRESHOLDS = [float(t.strip()) for t in THRESHOLDS_RAW.split(",")]

# Helper functions to fetch data
def fetch_products():
    try:
        response = requests.get(f"{API_URL}/products")
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to the FastAPI backend at '{API_URL}'. Please run the app using 'uv run python main.py'.")
    return []

def fetch_gmeans(product):
    try:
        response = requests.get(f"{API_URL}/gmeans", params={"product": product})
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def fetch_pca():
    try:
        response = requests.get(f"{API_URL}/pca")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

st.title("Descriptive Sensory Analysis Dashboard")

# Create tabs
tab1, tab2 = st.tabs(["📊 Geometric Means (Dravnieks Score)", "📈 PCA Analysis (Arithmetic Means)"])

with tab1:
    st.write("This tab ranks sensory attributes by their Dravnieks modified frequency geometric mean index.")
    
    # Fetch products for selectbox
    products = fetch_products()
    
    if products:
        # Add an option to view overall (all products)
        options = ["all"] + products
        format_labels = {
            "all": "Overall (All Products)",
            **{p: p for p in products}
        }
        
        # Filter selection
        selected_option = st.selectbox(
            "Select Product Filter:",
            options=options,
            format_func=lambda x: format_labels[x],
            key="gmean_filter"
        )
        
        # Fetch geometric means data based on selection
        gmeans_data = fetch_gmeans(selected_option)
        
        if gmeans_data:
            df = pd.DataFrame(gmeans_data)
            
            # Split layout into columns for chart and table
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"Attribute Ranking: {format_labels[selected_option]}")
                
                # Render clean bar chart using Plotly
                fig = px.bar(
                    df,
                    x='geometric_mean',
                    y='attribute',
                    orientation='h',
                    labels={'geometric_mean': 'Standard Geometric Mean', 'attribute': 'Sensory Attribute'},
                    category_orders={"attribute": list(df['attribute'])[::-1]}, # maintain descending order
                    color_discrete_sequence=['#4b6584'] # simple muted slate-blue
                )
                
                # Add vertical threshold lines
                colors = ["#eb3b5a", "#fa8231", "#20bf6b"] # Red, Orange, Green
                for i, threshold in enumerate(THRESHOLDS):
                    color = colors[i % len(colors)]
                    fig.add_vline(
                        x=threshold, 
                        line_width=1.5, 
                        line_dash="dash", 
                        line_color=color, 
                        annotation_text=f"Threshold {threshold:.2f}", 
                        annotation_position="top right"
                    )
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=650
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("Data List")
                # Format display value
                df_display = df.copy()
                df_display['geometric_mean'] = df_display['geometric_mean'].round(4)
                st.dataframe(df_display, use_container_width=True, height=650, hide_index=True)
    else:
        st.info("Waiting for the backend server to become responsive...")

with tab2:
    st.write("This tab shows the Principal Component Analysis (PCA) of sensory attributes calculated from product-level arithmetic means.")
    
    pca_data = fetch_pca()
    if pca_data:
        df_prod = pd.DataFrame(pca_data["products"])
        df_attr = pd.DataFrame(pca_data["attributes"])
        ev = pca_data["explained_variance"]
        
        st.subheader("Sensory Space Mapping (PC1 vs PC2)")
        st.write(f"The first two principal components explain **{(ev[0] + ev[1])*100:.1f}%** of total variance (PC1: **{ev[0]*100:.1f}%**, PC2: **{ev[1]*100:.1f}%**).")
        
        col_p, col_a = st.columns(2)
        
        with col_p:
            st.write("### Product Map (Scores)")
            fig_prod = px.scatter(
                df_prod,
                x='pc1',
                y='pc2',
                text='product_name',
                labels={'pc1': f'PC1 ({ev[0]*100:.1f}%)', 'pc2': f'PC2 ({ev[1]*100:.1f}%)'},
                title="Product Positioning in PCA Space"
            )
            fig_prod.update_traces(textposition='top center', marker=dict(size=12, color='#4b6584'))
            fig_prod.update_layout(
                height=550,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            # Add grid line helpers
            fig_prod.add_hline(y=0, line_width=1, line_color="#d1d8e0", line_dash="dash")
            fig_prod.add_vline(x=0, line_width=1, line_color="#d1d8e0", line_dash="dash")
            
            st.plotly_chart(fig_prod, use_container_width=True)
            
        with col_a:
            st.write("### Attribute Map (Loadings)")
            fig_attr = px.scatter(
                df_attr,
                x='pc1',
                y='pc2',
                text='attribute',
                labels={'pc1': f'PC1 ({ev[0]*100:.1f}%)', 'pc2': f'PC2 ({ev[1]*100:.1f}%)'},
                title="Attribute Vector Loading Map"
            )
            fig_attr.update_traces(textposition='top center', marker=dict(size=8, color='#eb3b5a'))
            
            # Draw vectors from origin to loadings
            for _, row in df_attr.iterrows():
                fig_attr.add_shape(
                    type="line",
                    x0=0, y0=0,
                    x1=row['pc1'], y1=row['pc2'],
                    line=dict(color="#eb3b5a", width=1, dash="solid")
                )
                
            fig_attr.update_layout(
                height=550,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            # Add grid line helpers
            fig_attr.add_hline(y=0, line_width=1, line_color="#d1d8e0", line_dash="dash")
            fig_attr.add_vline(x=0, line_width=1, line_color="#d1d8e0", line_dash="dash")
            
            st.plotly_chart(fig_attr, use_container_width=True)
    else:
        st.info("Loading PCA mapping data from backend...")
