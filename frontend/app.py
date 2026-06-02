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

def fetch_correlation():
    try:
        response = requests.get(f"{API_URL}/correlation")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def fetch_replicated_analysis():
    try:
        response = requests.get(f"{API_URL}/replicated-analysis")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

st.title("Descriptive Sensory Analysis Dashboard")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Geometric Means (Dravnieks Score)", 
    "📈 PCA Analysis (Arithmetic Means)",
    "🔗 Attribute Correlation",
    "🔍 Replicated analysis"
])

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
            try:
                os.makedirs("images", exist_ok=True)
                fig_attr.write_html("images/pca_attribute_map.html")
            except Exception as e:
                print(f"Warning: Could not save loadings chart HTML: {e}")
    else:
        st.info("Loading PCA mapping data from backend...")

with tab3:
    st.write("This tab shows the correlation between different sensory attributes based on product-level arithmetic means.")
    
    corr_data = fetch_correlation()
    if corr_data:
        attrs = corr_data["attributes"]
        matrix = corr_data["matrix"]
        
        df_corr = pd.DataFrame(matrix, index=attrs, columns=attrs)
        
        st.subheader("Correlation Heatmap")
        
        fig_heat = px.imshow(
            df_corr,
            x=attrs,
            y=attrs,
            color_continuous_scale="RdBu_r",
            zmin=-1.0,
            zmax=1.0,
            labels=dict(color="Correlation (r)"),
            title="Pearson Correlation Matrix of Sensory Attributes"
        )
        fig_heat.update_layout(
            height=700,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Explore Single Attribute Correlation")
        
        selected_attr = st.selectbox(
            "Select an attribute to inspect:",
            options=attrs,
            key="corr_inspect_select"
        )
        
        if selected_attr:
            # Get correlations for this attribute
            corr_series = df_corr[selected_attr].drop(selected_attr).sort_values(ascending=False)
            df_single_corr = pd.DataFrame({
                "attribute": corr_series.index,
                "correlation": corr_series.values
            })
            
            col_chart, col_data = st.columns([3, 1])
            
            with col_chart:
                fig_single = px.bar(
                    df_single_corr,
                    x="correlation",
                    y="attribute",
                    orientation="h",
                    category_orders={"attribute": list(df_single_corr["attribute"])[::-1]},
                    color="correlation",
                    color_continuous_scale="RdBu_r",
                    range_color=[-1, 1],
                    labels={"correlation": "Pearson Correlation (r)", "attribute": "Sensory Attribute"},
                    title=f"Correlation of other attributes with '{selected_attr}'"
                )
                fig_single.update_layout(
                    height=600,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_single, use_container_width=True)
                
            with col_data:
                st.write("**Correlation Coefficients**")
                df_display_single = df_single_corr.copy()
                df_display_single["correlation"] = df_display_single["correlation"].round(4)
                st.dataframe(df_display_single, use_container_width=True, height=550, hide_index=True)
    else:
        st.info("Loading correlation data from backend...")

with tab4:
    st.write("This tab provides analysis of discriminating power, repeatability, and usage rates of sensory attributes, as well as panelist performance.")
    
    replicated_data = fetch_replicated_analysis()
    if replicated_data:
        # 1. Summary Table
        st.subheader("Descriptor Summary Analysis")
        if "summary_table" in replicated_data and replicated_data["summary_table"]:
            df_sum = pd.DataFrame(replicated_data["summary_table"])
            
            col_sum, col_bubble = st.columns([1, 1])
            
            with col_sum:
                st.write("### Decision Table")
                st.dataframe(df_sum, use_container_width=True, height=600)
                
            with col_bubble:
                st.write("### Discriminating Power vs Repeatability")
                # Bubble plot
                fig_bubble = px.scatter(
                    df_sum,
                    x="Repeatability_r",
                    y="F_product",
                    size="UsageRate",
                    color="Decision",
                    text="Descriptor",
                    labels={
                        "Repeatability_r": "Repeatability r (Rep1 vs Rep2)",
                        "F_product": "F-ratio (Product effect)",
                        "UsageRate": "Usage Rate"
                    },
                    color_discrete_map={
                        "GIU": "#2E7D32",
                        "LOAI": "#C62828",
                        "XEM LAI": "#F57F17",
                        "XEM LAI (usage thap)": "#6A1B9A",
                        "XEM LAI (F thap)": "#E65100"
                    }
                )
                fig_bubble.update_traces(textposition='top center')
                
                # Add threshold lines (approximate median for F-product as in R script)
                f_median = df_sum["F_product"].median()
                fig_bubble.add_hline(y=f_median, line_width=1.5, line_dash="dash", line_color="gray")
                fig_bubble.add_vline(x=0.6, line_width=1.5, line_dash="dash", line_color="gray")
                
                fig_bubble.update_layout(height=600, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_bubble, use_container_width=True)

            st.markdown("---")
            
            # 2. Descriptor Correlation Heatmap
            st.subheader("Descriptor Correlation Heatmap")
            if "descriptor_correlation_matrix" in replicated_data:
                matrix_data = replicated_data["descriptor_correlation_matrix"]
                attrs_corr = matrix_data["attributes"]
                matrix_vals = matrix_data["matrix"]
                
                if attrs_corr and matrix_vals:
                    df_corr_heatmap = pd.DataFrame(matrix_vals, index=attrs_corr, columns=attrs_corr)
                    fig_heat_rep = px.imshow(
                        df_corr_heatmap,
                        color_continuous_scale="RdBu_r",
                        zmin=-1.0,
                        zmax=1.0,
                        labels=dict(color="Correlation (r)"),
                        title="Attribute Correlation Matrix"
                    )
                    fig_heat_rep.update_layout(height=600, margin=dict(l=40, r=40, t=40, b=40))
                    st.plotly_chart(fig_heat_rep, use_container_width=True)
                else:
                    st.info("No correlation data available for descriptors.")
            
            st.markdown("---")
            
            # 3. Panelist Performance
            st.subheader("Panelist Performance")
            if "panelist_performance" in replicated_data and replicated_data["panelist_performance"]:
                df_panel = pd.DataFrame(replicated_data["panelist_performance"])
                st.write("### Median Agreement with Panel (r)")
                st.dataframe(df_panel.sort_values("median_agreement", ascending=False), use_container_width=True, hide_index=True)
                
                # Simple bar chart for agreement
                fig_panel = px.bar(
                    df_panel,
                    x="panelist",
                    y="median_agreement",
                    labels={"panelist": "Panelist", "median_agreement": "Median Agreement (r)"},
                    title="Panelist Agreement Score"
                )
                fig_panel.update_layout(height=400)
                st.plotly_chart(fig_panel, use_container_width=True)
            else:
                st.info("No panelist performance data available.")
                
        else:
            st.info("No replicated analysis data available.")
    else:
        st.info("Loading replicated analysis data from backend...")
