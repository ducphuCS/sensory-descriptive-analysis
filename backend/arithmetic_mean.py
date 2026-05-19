import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
DATA_CSV_PATH = os.getenv("DATA_CSV_PATH", "data/data.csv")
PRODUCT_AMEANS_PATH = os.getenv("PRODUCT_AMEANS_PATH", "data/product_ameans.csv")
METADATA_COLUMNS = os.getenv("METADATA_COLUMNS", "subject_id,object_code,object_name,replicate,Comment").split(",")

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
    
    # Calculate product-level arithmetic means
    print("Calculating product-level arithmetic means...")
    result = df.groupby(['object_code', 'object_name'])[attrs].mean().reset_index()
    
    result.to_csv(PRODUCT_AMEANS_PATH, index=False)
    print(f"Saved product-level arithmetic means to: {PRODUCT_AMEANS_PATH}")

if __name__ == '__main__':
    main()
