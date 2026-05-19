import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
DATA_CSV_PATH = os.getenv("DATA_CSV_PATH", "data/data.csv")
PRODUCT_GMEANS_PATH = os.getenv("PRODUCT_GMEANS_PATH", "data/product_gmeans_standard.csv")
OVERALL_GMEANS_PATH = os.getenv("OVERALL_GMEANS_PATH", "data/overall_gmeans_standard.csv")
INTENSITY_SCALE_MAX = float(os.getenv("INTENSITY_SCALE_MAX", "10.0"))
METADATA_COLUMNS = os.getenv("METADATA_COLUMNS", "subject_id,object_code,object_name,replicate,Comment").split(",")

def gmean_standard(x):
    """
    Calculates the geometric mean of frequency and intensity (Dravnieks Score / Index).
    It integrates both the frequency of citation and the relative intensity.
    If there are any negative values, returns NaN.
    """
    v = x.dropna()
    if len(v) == 0 or (v < 0).any(): 
        return np.nan

    def citation_freq(val):
        # Scalar: Proportion of panelists who cited the attribute (score >= 1)
        return (val >= 1).sum() / len(val)
    
    def relative_intensity(val):
        # Scalar: Average intensity score scaled relative to the maximum of the scale (INTENSITY_SCALE_MAX)
        return val.mean() / INTENSITY_SCALE_MAX
        
    return np.sqrt(citation_freq(v) * relative_intensity(v))

def main():
    if not os.path.exists(DATA_CSV_PATH):
        print(f"Error: {DATA_CSV_PATH} not found.")
        return

    print("Loading data...")
    df = pd.read_csv(DATA_CSV_PATH).dropna(how='all')
    print(f"Loaded {len(df)} sensory evaluation rows.")

    attrs = [col for col in df.columns if col not in METADATA_COLUMNS]
    
    df[attrs] = df[attrs].apply(pd.to_numeric, errors='coerce')
    df['object_code'] = df['object_code'].astype(int)
    
    # 1. Calculate product-level Dravnieks modified frequency scores
    product_result = df.groupby(['object_code', 'object_name'])[attrs].agg(gmean_standard).reset_index()
    product_result.to_csv(PRODUCT_GMEANS_PATH, index=False)
    print(f"Saved product-level scores to: {PRODUCT_GMEANS_PATH}")

    # 2. Calculate overall scores for each attribute across all products
    overall_result = df[attrs].agg(gmean_standard).reset_index()
    overall_result.columns = ['attribute', 'geometric_mean']
    overall_result.to_csv(OVERALL_GMEANS_PATH, index=False)
    print(f"Saved overall scores to: {OVERALL_GMEANS_PATH}")

if __name__ == '__main__':
    main()
