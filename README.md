# Descriptive Sensory Data - Geometric Means

This project contains a Python script to calculate the product-level geometric means of sensory attributes from panelist data.

## Usage

Ensure you have `uv` installed, then run:

```bash
uv run python main.py
```

This will load the raw sensory ratings from `data.csv`, clean empty rows, compute the standard geometric mean for each sensory attribute per product, and save the results to `product_gmeans_standard.csv`.

## Approaches to Geometric Mean in Sensory Evaluation

When calculating the geometric mean of sensory ratings, the presence of zero scores (i.e., when a panelist did not detect an attribute) can be handled in different ways. Below are the three approaches considered:

### 1. Standard Geometric Mean (Currently Implemented)
* **Formula**: $\left(\prod_{i=1}^n x_i\right)^{\frac{1}{n}}$ or $\exp\left(\frac{1}{n}\sum_{i=1}^n \ln(x_i)\right)$
* **Handling of Zeros**: If any rating is `0`, the resulting geometric mean is `0.0`.
* **Note**: This is the default mathematical definition. It is highly sensitive to zero ratings, meaning even if most panelists detect a strong sensation, a single panelist rating it `0` will force the product's overall attribute score to `0.0`.

### 2. Shifted Geometric Mean (+1 Shift)
* **Formula**: $\exp\left(\frac{1}{n}\sum_{i=1}^n \ln(x_i + 1)\right) - 1$
* **Handling of Zeros**: Avoids the logarithm of zero by shifting all values up by 1 before calculating the geometric mean, then subtracting 1 at the end to restore the original scale.
* **Note**: Commonly used on fixed intensity scales (e.g., 0-10) to prevent zero-out effects while keeping the boundaries of the scale intact.

### 3. Non-Zero Geometric Mean (Zero-Ignored)
* **Formula**: Geometric mean calculated only on values where $x_i > 0$.
* **Handling of Zeros**: Ignores zero ratings. If all ratings are 0, returns `0.0`.
* **Note**: Captures the average intensity rating specifically among the subset of panelists who successfully perceived the attribute.
