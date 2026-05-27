import os
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api")

def main():
    try:
        print("Fetching PCA results from backend...")
        response = requests.get(f"{API_URL}/pca")
        if response.status_code != 200:
            print(f"Error: Backend API returned code {response.status_code}")
            return
        
        pca_data = response.json()
        df_attr = pd.DataFrame(pca_data["attributes"])
        ev = pca_data["explained_variance"]
        
        print("Generating loadings map figure...")
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
            height=600,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        fig_attr.add_hline(y=0, line_width=1, line_color="#d1d8e0", line_dash="dash")
        fig_attr.add_vline(x=0, line_width=1, line_color="#d1d8e0", line_dash="dash")
        
        os.makedirs("images", exist_ok=True)
        html_path = "images/pca_attribute_map.html"
        fig_attr.write_html(html_path)
        print(f"Successfully saved interactive HTML to: {html_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
