import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv
from backend.replicated_analysis import get_replicated_analysis_data

# Load environment variables
load_dotenv()

app = FastAPI(title="Sensory Geometric Means API")

GMEANS_CSV_PATH = os.getenv("PRODUCT_GMEANS_PATH", "data/product_gmeans_standard.csv")
OVERALL_CSV_PATH = os.getenv("OVERALL_GMEANS_PATH", "data/overall_gmeans_standard.csv")
AMEANS_CSV_PATH = os.getenv("PRODUCT_AMEANS_PATH", "data/product_ameans.csv")
CORRELATION_CSV_PATH = os.getenv("ATTRIBUTE_CORRELATION_PATH", "data/attribute_correlation.csv")

def get_precalculated_gmeans():
    if not os.path.exists(GMEANS_CSV_PATH):
        raise HTTPException(
            status_code=500, 
            detail=f"Precalculated geometric means file '{GMEANS_CSV_PATH}' not found. Please run 'backend/geometric_mean.py' first."
        )
    
    df = pd.read_csv(GMEANS_CSV_PATH)
    metadata = ['object_code', 'object_name']
    attrs = [col for col in df.columns if col not in metadata]
    return df, attrs

def get_overall_gmeans():
    if not os.path.exists(OVERALL_CSV_PATH):
        raise HTTPException(
            status_code=500, 
            detail=f"Precalculated overall geometric means file '{OVERALL_CSV_PATH}' not found. Please run 'backend/geometric_mean.py' first."
        )
    return pd.read_csv(OVERALL_CSV_PATH)

@app.get("/api/products")
def get_products():
    df, _ = get_precalculated_gmeans()
    return sorted(df['object_name'].unique().tolist())

@app.get("/api/gmeans")
def get_geometric_means(product: str = "all"):
    if product != "all":
        df, attrs = get_precalculated_gmeans()
        # Get row for specific product
        prod_df = df[df['object_name'] == product]
        if prod_df.empty:
            raise HTTPException(status_code=404, detail="Product not found")
        
        result = []
        for attr in attrs:
            val = prod_df.iloc[0][attr]
            result.append({"attribute": attr, "geometric_mean": float(val)})
    else:
        # Load precalculated overall scores across all products
        df = get_overall_gmeans()
        result = df.to_dict(orient="records")
            
    # Sort descending by geometric mean value
    result.sort(key=lambda x: x["geometric_mean"], reverse=True)
    return result

@app.get("/api/pca")
def get_pca():
    if not os.path.exists(AMEANS_CSV_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"Arithmetic means file '{AMEANS_CSV_PATH}' not found. Please run 'backend/arithmetic_mean.py' first."
        )
    
    df = pd.read_csv(AMEANS_CSV_PATH)
    metadata = ['object_code', 'object_name']
    attrs = [col for col in df.columns if col not in metadata]
    
    # Scale attributes
    scaler = StandardScaler()
    X = scaler.fit_transform(df[attrs])
    
    # Perform PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    
    # Get scores (products)
    products_pca = []
    for i, row in df.iterrows():
        products_pca.append({
            "product_name": row["object_name"],
            "pc1": float(X_pca[i, 0]),
            "pc2": float(X_pca[i, 1])
        })
        
    # Get loadings (attributes)
    loadings = pca.components_
    attributes_pca = []
    for i, attr in enumerate(attrs):
        attributes_pca.append({
            "attribute": attr,
            "pc1": float(loadings[0, i]),
            "pc2": float(loadings[1, i])
        })
        
    # Explained variance ratios
    explained_variance = [float(v) for v in pca.explained_variance_ratio_]
    
    return {
        "products": products_pca,
        "attributes": attributes_pca,
        "explained_variance": explained_variance
    }

@app.get("/api/correlation")
def get_correlation():
    if not os.path.exists(CORRELATION_CSV_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"Precalculated correlation file '{CORRELATION_CSV_PATH}' not found. Please run 'backend/correlation.py' first."
        )
    
    # Load correlation CSV (keep index_col=0 to identify row names)
    corr_df = pd.read_csv(CORRELATION_CSV_PATH, index_col=0)
    attrs = corr_df.index.tolist()
    matrix = corr_df.values.tolist()
    
    return {
        "attributes": attrs,
        "matrix": matrix
    }

@app.get("/api/replicated-analysis")
def get_replicated_analysis():
    data = get_replicated_analysis_data()
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data
