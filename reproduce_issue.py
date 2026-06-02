import pandas as pd
import numpy as np
import os
import sys

# Add current directory to sys.path to import backend
sys.path.append(os.getcwd())

from backend.replicated_analysis import load_data, calculate_replicated_analysis

def reproduce():
    df = load_data()
    print("Data loaded. Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    
    # Map columns as in the original code to see what happens
    rename_map = {}
    if 'Panelist' in df.columns:
        rename_map['Panelist'] = 'subject_id'
    if 'Product' in df.columns:
        rename_map['Product'] = 'object_name'
    if 'Rep' in df.columns:
        rename_map['Rep'] = 'replicate'
    
    if rename_map:
        df = df.rename(columns=rename_map)
        print("Columns after renaming:", df.columns.tolist())

    results = calculate_replicated_analysis(df)
    
    if "panelist_performance" in results:
        print("\nPanelist Performance Results:")
        for perf in results["panelist_performance"]:
            print(perf)
    else:
        print("No panelist performance in results.")

    print("\nDescriptor Summary Results (lmm_results):")
    if "lmm_results" in results:
        for res in results["lmm_results"]:
            print(res)
    else:
        print("lmm_results not found in results")

    print("\n--- Manual Debugging ---")
    panelists = df['subject_id'].unique()
    print("Panelists:", panelists)
    
    desc_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude metadata
    possible_metadata = ['subject_id', 'object_code', 'object_name', 'replicate']
    desc_cols = [c for c in desc_cols if c not in possible_metadata]
    print("Descriptor columns:", desc_cols)

    product_means = df.groupby('object_name')[desc_cols].mean().reset_index()
    print("\nProduct Means (first 5):")
    print(product_means.head())

    for p in panelists:
        print(f"\n--- Debugging Panelist: {p} ---")
        p_df = df[df['subject_id'] == p]
        if p_df.empty:
            print("Empty p_df")
            continue
        
        p_prod_means = p_df.groupby('object_name')[desc_cols].mean().reset_index()
        print(f"Panelist {p} product means (first 5):")
        print(p_prod_means.head())
        
        merged = pd.merge(p_prod_means, product_means, on='object_name', suffixes=('_p', '_panel'))
        print(f"Merged dataframe shape: {merged.shape}")
        if merged.empty:
            print("Merged dataframe is empty!")
            continue
        print("Merged dataframe (first 5):")
        print(merged.head())

        p_agrees = []
        for col in desc_cols:
            if col in merged.columns:
                col_p = f"{col}_p"
                col_panel = f"{col}_panel"
                if col_p in merged.columns and col_panel in merged.columns:
                    valid = merged[col_p].notna() & merged[col_panel].notna()
                    print(f"Descriptor '{col}': valid count = {valid.sum()}")
                    if valid.sum() > 1:
                        # Check for zero variance
                        var_p = merged.loc[valid, col_p].var()
                        var_panel = merged.loc[valid, col_panel].var()
                        print(f"  Variance - p: {var_p}, panel: {var_panel}")
                        
                        r = merged.loc[valid, [col_p, col_panel]].corr().iloc[0, 1]
                        print(f"  Correlation r: {r}")
                        if not np.isnan(r):
                            p_agrees.append(r)
                            print(f"  Appended {r} to p_agrees")
                        else:
                            print("  r is NaN, NOT appending")
                    else:
                        p_agrees.append(0.0)
                else:
                    print(f"  Column {col}_p or {col}_panel not in merged")
                    p_agrees.append(0.0)
            else:
                print(f"  Descriptor {col} not in merged")
                p_agrees.append(0.0)
        
        print(f"Final p_agrees for {p}: {p_agrees}")
        if p_agrees:
            print(f"Median agreement for {p}: {np.median(p_agrees)}")

if __name__ == "__main__":
    reproduce()
