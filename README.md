# Descriptive Sensory Data - Geometric Means

This project contains a Python script to calculate the product-level geometric means of sensory attributes from panelist data.

## Usage

Ensure you have `uv` installed, then run:

```bash
uv run python -m backend.geometric_mean
```

This will load the raw sensory ratings from `data/data.csv`, clean empty rows, compute the Dravnieks modified frequency index for each sensory attribute (both per product and overall), and save the results to `data/product_gmeans_standard.csv` and `data/overall_gmeans_standard.csv`.

To calculate the arithmetic means of attributes grouped by product, run:

```bash
uv run python -m backend.arithmetic_mean
```

This generates the arithmetic means and saves them to `data/product_ameans.csv`.

## Project Structure

The project follows a standard structured layout for web applications combining FastAPI and Streamlit:

```text
descriptive-sensory/
├── data/
│   ├── data.csv                      # Raw input sensory ratings
│   ├── product_gmeans_standard.csv   # Pre-calculated product scores
│   ├── overall_gmeans_standard.csv   # Pre-calculated overall scores
│   └── product_ameans.csv            # Pre-calculated product arithmetic means
├── backend/
│   ├── app.py                        # FastAPI backend server
│   ├── geometric_mean.py             # Geometric mean (Dravnieks Score) logic
│   └── arithmetic_mean.py            # Arithmetic mean calculation logic
├── frontend/
│   └── app.py                        # Streamlit frontend dashboard
├── main.py                           # App runner (launches both services)
├── pyproject.toml                    # Project configuration and packages
├── .env.example                      # Template for environment variables
└── README.md                         # Documentation
```

## Configuration

The application uses environment variables for configuration. You can copy the template `.env.example` file to `.env` to customize settings:

```bash
cp .env.example .env
```

### Configurable Environment Variables:
* **`INTENSITY_SCALE_MAX`**: The maximum value of the intensity scale (default: `10.0`).
* **`SIGNIFICANCE_THRESHOLDS`**: Comma-separated threshold values for the geometric mean bar chart (default: `0.15,0.4,0.7`).
* **`BACKEND_API_URL`**: The URL Streamlit uses to connect to the FastAPI backend (default: `http://127.0.0.1:8000/api`).
* **`BACKEND_HOST` / `BACKEND_PORT`**: Host and port bindings for FastAPI (default: `127.0.0.1:8000`).
* **`FRONTEND_HOST` / `FRONTEND_PORT`**: Host and port bindings for Streamlit (default: `127.0.0.1:8501`).
* **`DATA_CSV_PATH` / `PRODUCT_GMEANS_PATH` / `OVERALL_GMEANS_PATH` / `PRODUCT_AMEANS_PATH`**: Input and output file paths.
* **`METADATA_COLUMNS`**: Non-sensory descriptor columns to exclude from calculations (default: `subject_id,object_code,object_name,replicate,Comment`).







## Approaches to Geometric Mean in Sensory Evaluation

When calculating the geometric mean of sensory ratings, standard mathematical calculations can be problematic due to zero scores (which occur when a panelist does not perceive an attribute). To resolve this, the **Dravnieks modified frequency score** (index of significance) is used.

### Currently Implemented: Dravnieks Score (Geometric Mean of Citation Frequency & Intensity)
* **Formula**: $\sqrt{F \times I}$
* **Components**:
  * **$F$ (Citation Frequency)**: The proportion of panelists who perceived the attribute (rating $\ge 1$).
    $$F = \frac{\sum (x \ge 1)}{N}$$
  * **$I$ (Relative Intensity)**: The average intensity rating of the attribute scaled by the maximum value of the intensity scale ($10.0$ for this dataset).
    $$I = \frac{\bar{x}}{10.0}$$
* **Handling of Zeros**: A single zero rating does not zero out the entire score. The score is only zero if no panelist detected the attribute at all. This balances qualitative applicability (how many noticed it) and quantitative strength (how strong it was).

### Alternatives Considered:
1. **Standard Geometric Mean**: $\left(\prod x_i\right)^{1/n}$. Any $0.0$ score zeroes out the entire result. (Highly sensitive, not suitable for sensory data).
2. **Shifted Geometric Mean (+1 Shift)**: $\exp\left(\frac{1}{n}\sum \ln(x_i + 1)\right) - 1$. Prevents zeros but distorts mathematical scaling.
3. **Non-Zero Geometric Mean**: Geometric mean computed only on $x_i > 0$. Ignores panelists who did not perceive the attribute.

---

## Interactive Dashboard

The project includes an interactive dashboard featuring a **FastAPI backend** and a **Streamlit frontend**. 

The dashboard ranks sensory attributes based on their Dravnieks Score (modified frequency geometric mean index) across the entire dataset or filtered by a specific product.

### Features
* **Geometric Means Tab**:
  * **Ranking Chart**: A horizontal bar chart visualizing sensory attributes sorted in descending order of their Dravnieks Score, with vertical dashed lines representing the $0.15$, $0.4$, and $0.7$ thresholds.
  * **Product Filter**: Filter the calculations to focus on a single product or view the overall dataset summary.
  * **Data List**: A side-by-side table listing the attributes and their rounded Dravnieks values.
* **PCA Analysis Tab**:
  * **Product Map (Score Plot)**: Displays product positions in PCA space relative to PC1 and PC2, showing how similar or different their overall profiles are.
  * **Attribute Map (Loading Plot)**: Visualizes attribute correlation vectors, illustrating which sensory descriptors are pulling products in specific directions.
  * **Explained Variance**: Highlights the percentage of total variance captured by PC1 and PC2.


### Running the Dashboard

To start both the FastAPI backend and Streamlit frontend concurrently, run:

```bash
uv run python main.py
```


* **FastAPI Backend API**: runs at `http://127.0.0.1:8000`
* **Streamlit Dashboard**: runs at `http://127.0.0.1:8501`

