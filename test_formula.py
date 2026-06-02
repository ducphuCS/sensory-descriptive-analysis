import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

# Create dummy data with a column name containing a dot
df = pd.DataFrame({
    'object_name': ['A', 'A', 'B', 'B', 'C', 'C'],
    'subject_id': ['S1', 'S2', 'S1', 'S2', 'S1', 'S2'],
    'M.khoi': [3, 3, 1, 1, 2, 2]
})

print("Dummy DataFrame:")
print(df)

try:
    print("\nAttempting OLS with Q('M.khoi') ~ object_name...")
    model = ols("Q('M.khoi') ~ object_name", data=df).fit()
    print("OLS fit successful!")
    anova_table = anova_lm(model, typ=2)
    print("\nANOVA Table:")
    print(anova_table)
    print("\nANOVA Table columns:", anova_table.columns.tolist())
    print("ANOVA Table index:", anova_table.index.tolist())
    
    # Try to access Pr(>F)
    try:
        print("\nTrying to access 'Pr(>F)':")
        print(anova_table.loc["object_name", "Pr(>F)"])
    except Exception as e:
        print(f"Failed to access 'Pr(>F)': {e}")

    # Try to access PR(>F)
    try:
        print("\nTrying to access 'PR(>F)':")
        print(anova_table.loc["object_name", "PR(>F)"])
    except Exception as e:
        print(f"Failed to access 'PR(>F)': {e}")

except Exception as e:
    print(f"\nOLS fit failed with error: {e}")
