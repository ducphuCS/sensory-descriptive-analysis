import os
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from typing import Dict, Any

# Use a specific env var for replicated analysis data, or fallback to the new data file
REPLICATED_DATA_CSV_PATH = os.getenv("REPLICATED_DATA_CSV_PATH", "data/replicated_data.csv")

def load_data():
    if not os.path.exists(REPLICATED_DATA_CSV_PATH):
        raise FileNotFoundError(f"Data file not found: {REPLICATED_DATA_CSV_PATH}")
    
    df = pd.read_csv(REPLICATED_DATA_CSV_PATH)
    # Remove rows that are all NaN
    df = df.dropna(how='all')
    # Clean up column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]
    return df

def calculate_replicated_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    # 1. Identify metadata and descriptor columns
    # We support both the original format and the new replicated format
    possible_metadata = [
        'subject_id', 'object_code', 'object_name', 'replicate',
        'Panelist', 'Product', 'Rep'
    ]
    
    existing_metadata = [c for c in possible_metadata if c in df.columns]
    
    # Descriptor columns are everything else that is numeric
    desc_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # IMPORTANT: Remove metadata columns from desc_cols even if they are numeric (like 'replicate' or 'Rep')
    desc_cols = [c for c in desc_cols if c not in existing_metadata]
    
    if not desc_cols:
        return {"error": "No descriptor columns found."}

    # Map columns to internal names for consistent processing if they use the new format
    rename_map = {}
    if 'Panelist' in df.columns:
        rename_map['Panelist'] = 'subject_id'
    if 'Product' in df.columns:
        rename_map['Product'] = 'object_name'
    if 'Rep' in df.columns:
        rename_map['Rep'] = 'replicate'
        
    if rename_map:
        df = df.rename(columns=rename_map)
        # Update existing_metadata with new names
        existing_metadata = [c for c in ['subject_id', 'object_code', 'object_name', 'replicate'] if c in df.columns]

    # 2. Usage Rate
    usage_rates = {}
    for col in desc_cols:
        usage_rates[col] = float(df[col].gt(0).mean())

    # 3. Discriminating Power (LMM)
    # We'll use Score ~ object_name + (1 | subject_id)
    lmm_results = []
    
    # Ensure object_name and subject_id are strings/categories for formula
    df_lmm = df.copy()
    df_lmm['object_name'] = df_lmm['object_name'].astype(str)
    df_lmm['subject_id'] = df_lmm['subject_id'].astype(str)

    for col in desc_cols:
        try:
            # Drop NaNs for this specific descriptor to avoid issues with formula
            sub_df = df_lmm[['object_name', 'subject_id', col]].dropna()
            
            if len(sub_df) < 5: # Not enough data to fit a model
                lmm_results.append({
                    "descriptor": col,
                    "f_product": 0.0,
                    "p_product": 1.0,
                    "eta2": 0.0,
                    "model": "too_few_data"
                })
                continue

            # Attempt OLS (as an approximation of LMM for stability in this implementation)
            from statsmodels.formula.api import ols
            from statsmodels.stats.anova import anova_lm
            ols_model = ols(f"Q('{col}') ~ object_name", sub_df).fit()
            anova_table = anova_lm(ols_model, typ=2)
            
            f_val = float(anova_table.loc["object_name", "F"])
            p_val = float(anova_table.loc["object_name", "PR(>F)"])
            ss_prod = float(anova_table.loc["object_name", "sum_sq"])
            ss_res = float(anova_table.loc["Residual", "sum_sq"])
            eta2 = ss_prod / (ss_prod + ss_res) if (ss_prod + ss_res) != 0 else 0
            
            lmm_results.append({
                "descriptor": col,
                "f_product": round(f_val, 2),
                "p_product": round(p_val, 4),
                "eta2": round(eta2, 4),
                "model": "ols"
            })
            
        except Exception as e:
            lmm_results.append({
                "descriptor": col,
                "f_product": 0.0,
                "p_product": 1.0,
                "eta2": 0.0,
                "model": f"error: {str(e)}"
            })

    # 4. Repeatability (Correlation between replicates)
    repeatability = {}
    if 'replicate' in df.columns and df['replicate'].nunique() > 1:
        # Pivot to wide format: subject_id, object_name, Rep1_Attr, Rep2_Attr, ...
        
        # Create a unique ID for each event
        df_rep = df.copy()
        df_rep['event_id'] = df_rep['subject_id'].astype(str) + "_" + df_rep['object_name'].astype(str)
        
        # Pivot
        rep_wide = df_rep.pivot_table(
            index=['event_id', 'subject_id', 'object_name'],
            columns='replicate',
            values=desc_cols,
            aggfunc='mean'
        )
        
        # Flatten columns (e.g., ('Mùi cỏ tươi', 1) -> 'Mùi cỏ tươi_1')
        rep_wide.columns = [f"{col}_{rep}" for col, rep in rep_wide.columns]
        rep_wide = rep_wide.reset_index()
        
        reps = sorted(df['replicate'].unique())
        for col in desc_cols:
            if len(reps) >= 2:
                col1 = f"{col}_{reps[0]}"
                col2 = f"{col}_{reps[1]}"
                if col1 in rep_wide.columns and col2 in rep_wide.columns:
                    valid_mask = rep_wide[col1].notna() & rep_wide[col2].notna()
                    if valid_mask.any():
                        r_val = rep_wide.loc[valid_mask, [col1, col2]].corr().iloc[0, 1]
                        repeatability[col] = round(float(r_val), 3) if not np.isnan(r_val) else 0.0
                    else:
                        repeatability[col] = 0.0
                else:
                    repeatability[col] = 0.0
            else:
                repeatability[col] = 0.0
    else:
        for col in desc_cols:
            repeatability[col] = 0.0

    # 5. Descriptor Correlation
    df_means = df.groupby(['subject_id', 'object_name'])[desc_cols].mean().reset_index()
    if len(df_means) > 1:
        corr_matrix = df_means[desc_cols].corr()
        corr_matrix_list = corr_matrix.values.tolist()
    else:
        corr_matrix_list = []

    # 6. Panelist Performance (Simplified)
    panelist_performance = []
    panelists = df['subject_id'].unique()
    
    if len(panelists) > 1:
        product_means = df.groupby('object_name')[desc_cols].mean().reset_index()
        
        for p in panelists:
            p_df = df[df['subject_id'] == p]
            if p_df.empty: continue
            
            p_prod_means = p_df.groupby('object_name')[desc_cols].mean().reset_index()
            merged = pd.merge(p_prod_means, product_means, on='object_name', suffixes=('_p', '_panel'))
            
            p_agrees = []
            for col in desc_cols:
                col_p = f"{col}_p"
                col_panel = f"{col}_panel"
                if col_p in merged.columns and col_panel in merged.columns:
                    valid = merged[col_p].notna() & merged[col_panel].notna()
                    if valid.sum() > 1:
                        r = merged.loc[valid, [col_p, col_panel]].corr().iloc[0, 1]
                        if not np.isnan(r):
                            p_agrees.append(r)
                        else:
                            p_agrees.append(0.0)
                    else:
                        p_agrees.append(0.0)
                else:
                    p_agrees.append(0.0)

            median_r = np.median(p_agrees) if p_agrees else 0.0
            panelist_performance.append({
                "panelist": p,
                "median_agreement": float(round(median_r, 3))
            })
    else:
        panelist_performance = []

    # 7. Summary Table & Decision Logic
    summary_table = []
    if lmm_results:
        # Calculate f_median for decision making
        valid_f_values = [res["f_product"] for res in lmm_results if res["model"] not in ["too_few_data", "error: *"]]
        f_median = np.median(valid_f_values) if valid_f_values else 0.0
        
        for res in lmm_results:
            desc = res["descriptor"]
            f_prod = res["f_product"]
            p_prod = res["p_product"]
            eta2 = res["eta2"]
            usage = usage_rates.get(desc, 0.0)
            repeat = repeatability.get(desc, 0.0)
            
            # Decision Logic
            # GIU (Keep): HIGH F AND OK Repeat AND OK Usage
            # LOAI (Discard): low F AND weak Repeat
            # XEM LAI (Review): others
            
            flag_disc = "HIGH" if f_prod >= f_median else "low"
            flag_repeat = "OK" if repeat >= 0.6 else "weak"
            flag_usage = "OK" if usage >= 0.35 else "low"
            
            if flag_disc == "HIGH" and flag_repeat == "OK" and flag_usage == "OK":
                decision = "GIU"
            elif flag_disc == "low" and flag_repeat == "weak":
                decision = "LOAI"
            elif flag_disc == "HIGH" and flag_usage == "low":
                decision = "XEM LAI (usage thap)"
            elif flag_disc == "low" and flag_repeat == "OK":
                decision = "XEM LAI (F thap)"
            else:
                decision = "XEM LAI"
                
            summary_table.append({
                "Descriptor": desc,
                "F_product": f_prod,
                "sig": "*" if p_prod < 0.05 else "",
                "eta2": eta2,
                "Repeatability_r": repeat,
                "UsageRate": usage,
                "Decision": decision
            })

    return {
        "usage_rates": usage_rates,
        "lmm_results": lmm_results,
        "repeatability": repeatability,
        "descriptor_correlation_matrix": {
            "attributes": desc_cols,
            "matrix": corr_matrix_list
        },
        "panelist_performance": panelist_performance,
        "summary_table": summary_table
    }

def get_replicated_analysis_data():
    try:
        df = load_data()
        return calculate_replicated_analysis(df)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}
