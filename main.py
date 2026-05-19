import pandas as pd
import numpy as np

def gmean_standard(x):
    v = x.dropna()
    if len(v) == 0 or (v < 0).any(): 
        return np.nan
    return 0.0 if (v == 0).any() else np.exp(np.log(v).mean())

def main():
    df = pd.read_csv('data.csv').dropna(how='all')
    
    metadata = ['subject_id', 'object_code', 'object_name', 'replicate', 'Comment']
    attrs = [col for col in df.columns if col not in metadata]
    
    df[attrs] = df[attrs].apply(pd.to_numeric, errors='coerce')
    df['object_code'] = df['object_code'].astype(int)
    
    result = df.groupby(['object_code', 'object_name'])[attrs].agg(gmean_standard).reset_index()
    result.to_csv('product_gmeans_standard.csv', index=False)

if __name__ == '__main__':
    main()
