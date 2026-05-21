import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PRODUCT_AMEANS_PATH = os.getenv("PRODUCT_AMEANS_PATH", "data/product_ameans.csv")
CORRELATION_PATH = os.getenv("ATTRIBUTE_CORRELATION_PATH", "data/attribute_correlation.csv")

def main():
    if not os.path.exists(PRODUCT_AMEANS_PATH):
        print(f"Error: {PRODUCT_AMEANS_PATH} not found. Please run 'backend/arithmetic_mean.py' first.")
        return

    print("Loading arithmetic means...")
    df = pd.read_csv(PRODUCT_AMEANS_PATH)
    metadata = ['object_code', 'object_name']
    attrs = [col for col in df.columns if col not in metadata]

    print("Calculating Pearson correlation matrix...")
    corr_df = df[attrs].corr(method="pearson").fillna(0)

    # Save to CSV (keeping the index as attribute names)
    corr_df.to_csv(CORRELATION_PATH, index=True)
    print(f"Saved correlation matrix to: {CORRELATION_PATH}")

if __name__ == '__main__':
    main()
