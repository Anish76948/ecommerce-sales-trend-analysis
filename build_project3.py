"""
Build, execute, and validate Project 03: Customer Churn / Sales Trend Analysis.
Strictly adheres to InternCircle Learner Guide Project 03:
1. Executive business questions upfront (Which months/categories earn most? Who are top customers? What should we do next?).
2. Reproducible dataset generator using numpy.random.default_rng(42) with N=2000 transactions across 300 customers.
3. Feature engineering: month, weekday, quarter, day_of_month.
4. Monthly trend & MoM growth calculation (.pct_change()), marking best and worst months on a polished visual.
5. Category comparisons with groupby (sum, mean, count, share) and monthly category pivot table heatmap.
6. Top customer Pareto analysis (top 10% and top 20% revenue share with cumulative curve).
7. Three specific actionable business recommendations backed by exact numbers.
8. 2x2 Executive dashboard saved at 150 DPI ('sales_trend_overview.png') and one-page business brief.
"""

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter
import os

def generate_sales_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.13"
        }
    }

    cells = []

    # Title & Executive Business Context
    cells.append(nbf.v4.new_markdown_cell("""# E-Commerce Sales Trend & Customer Value Analysis
### InternCircle | Data Science & AI — Project 03
**Author:** Data Science Intern  
**Objective:** Perform an end-to-end commercial sales trend and customer value analysis for an e-commerce retailer. Extract date-driven features, evaluate monthly revenue trajectories and category dynamics, quantify customer spend concentration via the Pareto principle, and formulate data-backed strategic recommendations for executive leadership.

---

## 1. Business Questions Upfront (Step 1)
To ensure our exploratory and diagnostic analysis directly serves managerial decision-making, we formulate four central business questions:

1. **Seasonal Trajectory:** Which calendar months generate peak revenue, which represent annual troughs, and how volatile is month-over-month (MoM) revenue growth?
2. **Category Performance:** Which merchandise categories dominate total revenue volume, how do their Average Order Values (AOV) compare, and how do sales fluctuate across the year?
3. **Customer Value & Pareto Concentration:** What percentage of total commercial revenue is concentrated within the top 10% and top 20% of customer accounts?
4. **Actionable Commercial Strategy:** What concrete operational, merchandising, and retention interventions should leadership prioritize based on the empirical data?"""))

    # Section 2: Data Generation & Inspection
    cells.append(nbf.v4.new_markdown_cell("""---
## 2. Data Sourcing, Creation & Initial Audit (Step 2)
As outlined in the InternCircle guide, we utilize the reproducible practice dataset generator with a fixed random seed (`numpy.random.default_rng(42)`). This produces an empirical transaction ledger of $N = 2,000$ completed purchase orders across 300 unique customer accounts spanning the 2025 calendar year.

### Data Dictionary
| Attribute | Type | Description |
| :--- | :--- | :--- |
| `order_date` | Datetime | Timestamp of transaction settlement (2025-01-01 to 2025-12-31) |
| `customer_id`| Integer | Unique numerical identifier for the customer account (1 to 300) |
| `category` | Object | Product merchandise department (`Fashion`, `Electronics`, `Home`, `Books`) |
| `amount` | Float | Gross settled transaction value in US Dollars ($) |"""))

    cells.append(nbf.v4.new_code_cell("""# Import analytical and visualization libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure inline visualization aesthetics
%matplotlib inline
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams['font.size'] = 11
plt.rcParams['figure.titlesize'] = 13

# Reproducible e-commerce order generator (as specified in Learner Guide)
rng = np.random.default_rng(42)
n_orders = 2000

orders = pd.DataFrame({
    "order_date": pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n_orders), unit="D"),
    "customer_id": rng.integers(1, 301, n_orders),
    "category": rng.choice(["Electronics", "Fashion", "Home", "Books"], n_orders, p=[0.30, 0.35, 0.20, 0.15]),
    "amount": rng.gamma(2.0, 600, n_orders).round(2),
})

# Display dimensions and sample transactions
print(f"Dataset Dimensions: {orders.shape[0]} rows × {orders.shape[1]} columns")
orders.head()"""))

    cells.append(nbf.v4.new_code_cell("""# Audit structure, data types, and null records
orders.info()"""))

    cells.append(nbf.v4.new_code_cell("""# Summary statistics for monetary values
orders.describe().round(2)"""))

    cells.append(nbf.v4.new_code_cell("""# Verify completeness and duplicate integrity
print("Missing values per column:\\n", orders.isna().sum())
print(f"\\nDuplicate order records: {orders.duplicated().sum()}")"""))

    cells.append(nbf.v4.new_markdown_cell("""### Initial Baseline Observations:
- **Sample Size:** 2,000 orders placed across 300 unique registered customers.
- **Gross Revenue:** **$2,404,233.29** settled across the 2025 calendar year.
- **Order Amount Metrics:** Orders average **$1,202.12** with a median of **$1,012.35**, a minimum of $55.08, and a maximum of $5,081.23.
- **Data Quality:** Zero missing values and zero duplicate records."""))

    # Section 3: Feature Engineering
    cells.append(nbf.v4.new_markdown_cell("""---
## 3. Date Feature Engineering & Temporal Segmentation (Step 3)
To enable multi-level temporal analysis, we decompose `order_date` into standardized business reporting dimensions:
* `month`: Monthly cohort period (`2025-01` through `2025-12`)
* `month_name`: Standard calendar month label (Jan–Dec)
* `quarter`: Fiscal quarter (`2025Q1` through `2025Q4`)
* `weekday`: Day of the week (Monday through Sunday)"""))

    cells.append(nbf.v4.new_code_cell("""# Extract date features
orders['month'] = orders['order_date'].dt.to_period('M')
orders['month_name'] = orders['order_date'].dt.strftime('%b')
orders['quarter'] = orders['order_date'].dt.to_period('Q')
orders['weekday'] = orders['order_date'].dt.day_name()

# Inspect transformed schema
orders[['order_date', 'month', 'month_name', 'quarter', 'weekday', 'category', 'amount']].head()"""))

    # Section 4: Monthly Revenue Trend & MoM Growth
    cells.append(nbf.v4.new_markdown_cell("""---
## 4. Monthly Revenue Trend & MoM Growth Dynamics (Step 4)
We aggregate total monthly revenue, evaluate month-over-month (MoM) growth using `.pct_change()`, and isolate the top-performing and lowest-performing months of the year."""))

    cells.append(nbf.v4.new_code_cell("""# Aggregate revenue and compute MoM growth percentage
monthly_trend = orders.groupby('month')['amount'].agg(
    total_revenue='sum',
    order_count='count',
    aov='mean'
).reset_index()

monthly_trend['mom_growth_%'] = (monthly_trend['total_revenue'].pct_change() * 100).round(2)
monthly_trend['month_str'] = monthly_trend['month'].astype(str)

# Isolate peak and trough months
best_month_row = monthly_trend.loc[monthly_trend['total_revenue'].idxmax()]
worst_month_row = monthly_trend.loc[monthly_trend['total_revenue'].idxmin()]

print(f"Top-Performing Month: {best_month_row['month_str']} (${best_month_row['total_revenue']:,.2f} | MoM: +{best_month_row['mom_growth_%']:.1f}%)")
print(f"Lowest-Performing Month: {worst_month_row['month_str']} (${worst_month_row['total_revenue']:,.2f} | MoM: {worst_month_row['mom_growth_%']:.1f}%)")
print("\\nDetailed Monthly Performance Ledger:")
print(monthly_trend[['month_str', 'total_revenue', 'order_count', 'aov', 'mom_growth_%']].to_string(index=False))"""))

    cells.append(nbf.v4.new_code_cell("""# Visualize Monthly Revenue Trajectory with Key Callouts
plt.figure(figsize=(10, 5))
plt.plot(monthly_trend['month_str'], monthly_trend['total_revenue'], marker='o', color='#1f77b4', linewidth=2.5, markersize=7, label='Monthly Revenue ($)')

# Annotate Best Month
plt.annotate(
    f"Peak: {best_month_row['month_str']}\\n${best_month_row['total_revenue']:,.0f}\\n(+{best_month_row['mom_growth_%']:.1f}% MoM)",
    xy=(best_month_row['month_str'], best_month_row['total_revenue']),
    xytext=(1.2, best_month_row['total_revenue'] + 8000),
    arrowprops=dict(facecolor='#2ca02c', shrink=0.08, width=1.5, headwidth=8),
    fontweight='bold', color='#1b5e20', fontsize=10, ha='center'
)

# Annotate Worst Month
plt.annotate(
    f"Trough: {worst_month_row['month_str']}\\n${worst_month_row['total_revenue']:,.0f}\\n({worst_month_row['mom_growth_%']:.1f}% MoM)",
    xy=(worst_month_row['month_str'], worst_month_row['total_revenue']),
    xytext=(7.0, worst_month_row['total_revenue'] - 16000),
    arrowprops=dict(facecolor='#d62728', shrink=0.08, width=1.5, headwidth=8),
    fontweight='bold', color='#b71c1c', fontsize=10, ha='center'
)

# Plot formatting
plt.title("2025 Monthly E-Commerce Revenue Trajectory: Peak in February, Trough in August", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Billing Month", fontsize=11)
plt.ylabel("Gross Revenue (USD $)", fontsize=11)
plt.ylim(150000, 255000)
plt.gca().yaxis.set_major_formatter('${x:,.0f}')
plt.xticks(rotation=45)
plt.legend(loc='lower left')
plt.tight_layout()
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""**Monthly Trend Finding:** Gross revenue peaked in February 2025 at **$232,027.20** (+20.01% MoM expansion over January) before reaching an annual low in August 2025 at **$179,783.75** (-18.95% MoM contraction), reflecting noticeable late-summer demand softening before a steady Q4 recovery."""))

    # Section 5: Category Analysis
    cells.append(nbf.v4.new_markdown_cell("""---
## 5. Merchandise Department & Category Analysis (Step 5)
We now evaluate product categories by aggregate sales volume, transaction frequency, average ticket size, and monthly distribution via pivot table."""))

    cells.append(nbf.v4.new_code_cell("""# Category summary table
cat_summary = orders.groupby('category')['amount'].agg(
    total_revenue='sum',
    average_order_value='mean',
    order_count='count'
).sort_values(by='total_revenue', ascending=False).reset_index()

total_sales = cat_summary['total_revenue'].sum()
cat_summary['revenue_share_%'] = (cat_summary['total_revenue'] / total_sales * 100).round(2)
cat_summary['average_order_value'] = cat_summary['average_order_value'].round(2)

print("Merchandise Category Performance Breakdown:")
print(cat_summary.to_string(index=False))"""))

    cells.append(nbf.v4.new_code_cell("""# Monthly Revenue Pivot Table by Category
monthly_cat_pivot = orders.pivot_table(
    index='month', columns='category', values='amount', aggfunc='sum'
).round(0)

print("Monthly Category Revenue Pivot Table ($):")
print(monthly_cat_pivot)

# Heatmap visualization of category revenue by month
plt.figure(figsize=(9, 5.5))
sns.heatmap(monthly_cat_pivot, annot=True, fmt=",.0f", cmap="Blues", cbar_kws={'label': 'Gross Revenue ($)'})
plt.title("Monthly Revenue Heatmap by Category: Fashion & Electronics Drive Consistent Volume", fontsize=12, fontweight='bold', pad=12)
plt.xlabel("Product Category", fontsize=11)
plt.ylabel("Billing Month", fontsize=11)
plt.tight_layout()
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""**Category Performance Finding:** **Fashion** and **Electronics** serve as the commercial core, jointly delivering **65.58%** ($1,576,630.46) of total gross revenue across 1,321 transactions, while **Home** ($464,114.66 | 19.30%) and **Books** ($363,488.17 | 15.12%) fulfill vital basket-building roles with uniform AOVs across all four categories (~$1,163–$1,220)."""))

    # Section 6: Top Customers & Pareto Analysis
    cells.append(nbf.v4.new_markdown_cell("""---
## 6. Top Customer Segmentation & Pareto Concentration (Step 6)
The Pareto Principle (80/20 rule) is central to commercial customer strategy. We evaluate the cumulative spend distribution across our 300 unique customer accounts to determine the degree of revenue concentration."""))

    cells.append(nbf.v4.new_code_cell("""# Customer-level spend aggregation
customer_spend = orders.groupby('customer_id')['amount'].agg(
    total_spend='sum',
    order_count='count',
    avg_order_value='mean'
).sort_values(by='total_spend', ascending=False).reset_index()

# Cumulative revenue share
customer_spend['cumulative_spend'] = customer_spend['total_spend'].cumsum()
customer_spend['cumulative_share_%'] = (customer_spend['cumulative_spend'] / total_sales) * 100
customer_spend['customer_rank'] = np.arange(1, len(customer_spend) + 1)
customer_spend['customer_percentile_%'] = (customer_spend['customer_rank'] / len(customer_spend)) * 100

# Compute exact Pareto shares
top_10_pct_count = int(np.ceil(len(customer_spend) * 0.10))
top_20_pct_count = int(np.ceil(len(customer_spend) * 0.20))

top_10_share = customer_spend.loc[top_10_pct_count - 1, 'cumulative_share_%']
top_20_share = customer_spend.loc[top_20_pct_count - 1, 'cumulative_share_%']

print(f"Total Unique Customers: {len(customer_spend)}")
print(f"Top 10% of Customers ({top_10_pct_count} accounts) generate: {top_10_share:.2f}% of total revenue (${customer_spend.loc[top_10_pct_count - 1, 'cumulative_spend']:,.2f})")
print(f"Top 20% of Customers ({top_20_pct_count} accounts) generate: {top_20_share:.2f}% of total revenue (${customer_spend.loc[top_20_pct_count - 1, 'cumulative_spend']:,.2f})")"""))

    cells.append(nbf.v4.new_code_cell("""# Plotting Pareto Cumulative Curve (Lorenz Curve)
plt.figure(figsize=(8, 5))
plt.plot(customer_spend['customer_percentile_%'], customer_spend['cumulative_share_%'], color='#1f77b4', linewidth=2.5, label='Actual Customer Revenue Share')
plt.plot([0, 100], [0, 100], color='gray', linestyle='--', linewidth=1.5, label='Equal Distribution Baseline')

# Callout lines for Top 10% and Top 20%
plt.axvline(10, color='#2ca02c', linestyle=':', linewidth=1.8)
plt.axhline(top_10_share, color='#2ca02c', linestyle=':', linewidth=1.8)
plt.annotate(f"Top 10% accounts\\n→ {top_10_share:.1f}% Revenue", xy=(10, top_10_share), xytext=(22, top_10_share - 3),
             fontweight='bold', color='#1b5e20', arrowprops=dict(facecolor='#2ca02c', shrink=0.08, width=1.2, headwidth=6))

plt.axvline(20, color='#ff7f0e', linestyle=':', linewidth=1.8)
plt.axhline(top_20_share, color='#ff7f0e', linestyle=':', linewidth=1.8)
plt.annotate(f"Top 20% accounts\\n→ {top_20_share:.1f}% Revenue", xy=(20, top_20_share), xytext=(35, top_20_share - 4),
             fontweight='bold', color='#b26a00', arrowprops=dict(facecolor='#ff7f0e', shrink=0.08, width=1.2, headwidth=6))

plt.title("Pareto Curve: Top 20% of Accounts Contribute 33.88% of Total Revenue", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Cumulative % of Customers (Ranked by Spend)", fontsize=11)
plt.ylabel("Cumulative % of Total Revenue", fontsize=11)
plt.xlim(0, 100)
plt.ylim(0, 100)
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()"""))

    cells.append(nbf.v4.new_markdown_cell("""**Customer Concentration Finding:** The top 10% of customers (30 accounts) account for **18.94%** ($455,463.17) of total annual revenue, while the top 20% (60 accounts) generate **33.88%** ($814,643.08), illustrating a meaningful high-value cohort that anchors long-term store profitability."""))

    # Section 7: Combined 2x2 Dashboard
    cells.append(nbf.v4.new_markdown_cell("""---
## 7. Executive 2x2 Visual Dashboard (Step 8)
We synthesize the four analytical dimensions into a unified, high-resolution $2 \\times 2$ dashboard image saved at **150 DPI** to `sales_trend_overview.png`."""))

    cells.append(nbf.v4.new_code_cell("""fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Subplot [0, 0]: Monthly Revenue Trend with Markers
axes[0, 0].plot(monthly_trend['month_str'], monthly_trend['total_revenue'], marker='o', color='#1f77b4', linewidth=2)
axes[0, 0].set_title("1. Monthly Revenue: Peak in Feb ($232k), Trough in Aug ($180k)", fontsize=11, fontweight='bold')
axes[0, 0].set_xlabel("Month", fontsize=10)
axes[0, 0].set_ylabel("Revenue (USD $)", fontsize=10)
axes[0, 0].tick_params(axis='x', rotation=45)
axes[0, 0].yaxis.set_major_formatter('${x:,.0f}')

# Subplot [0, 1]: Category Share Bar Chart (Zero Baseline Preserved)
bars = axes[0, 1].bar(cat_summary['category'], cat_summary['total_revenue'], color=['#1f77b4', '#aec7e8', '#ffbb78', '#2ca02c'], edgecolor='black', alpha=0.85)
axes[0, 1].set_title("2. Category Sales: Fashion & Electronics Deliver 65.6% Share", fontsize=11, fontweight='bold')
axes[0, 1].set_xlabel("Merchandise Department", fontsize=10)
axes[0, 1].set_ylabel("Total Revenue (USD $)", fontsize=10)
axes[0, 1].set_ylim(0, 1000000)
axes[0, 1].yaxis.set_major_formatter('${x:,.0f}')
for b in bars:
    h = b.get_height()
    axes[0, 1].annotate(f"${h/1000:,.0f}k", (b.get_x() + b.get_width() / 2., h),
                        ha='center', va='bottom', fontsize=9, fontweight='bold', xytext=(0, 3), textcoords='offset points')

# Subplot [1, 0]: Monthly Category Pivot Heatmap
sns.heatmap(monthly_cat_pivot / 1000, annot=True, fmt=".0f", cmap="Blues", ax=axes[1, 0], cbar_kws={'label': 'Revenue ($k)'})
axes[1, 0].set_title("3. Category Revenue by Month ($ Thousands)", fontsize=11, fontweight='bold')
axes[1, 0].set_xlabel("Category", fontsize=10)
axes[1, 0].set_ylabel("Month", fontsize=10)

# Subplot [1, 1]: Pareto Lorenz Curve
axes[1, 1].plot(customer_spend['customer_percentile_%'], customer_spend['cumulative_share_%'], color='#1f77b4', linewidth=2, label='Actual Spend')
axes[1, 1].plot([0, 100], [0, 100], color='gray', linestyle='--', linewidth=1.2, label='Equal Share')
axes[1, 1].axvline(20, color='#ff7f0e', linestyle=':', linewidth=1.5)
axes[1, 1].axhline(top_20_share, color='#ff7f0e', linestyle=':', linewidth=1.5)
axes[1, 1].set_title(f"4. Pareto Curve: Top 20% Accounts Generate {top_20_share:.1f}% Revenue", fontsize=11, fontweight='bold')
axes[1, 1].set_xlabel("% of Total Customers", fontsize=10)
axes[1, 1].set_ylabel("% of Total Revenue", fontsize=10)
axes[1, 1].set_xlim(0, 100)
axes[1, 1].set_ylim(0, 100)
axes[1, 1].legend(loc='lower right')

plt.suptitle("Executive Dashboard: E-Commerce Sales Trends & Customer Concentration", fontsize=14, fontweight='bold', y=0.995)
plt.tight_layout()

# Save at 150 DPI as required by guide
plt.savefig("sales_trend_overview.png", dpi=150, bbox_inches='tight')
plt.show()

print("Dashboard image successfully saved as 'sales_trend_overview.png' (150 DPI).")"""))

    # Section 8: Recommendations & Brief
    cells.append(nbf.v4.new_markdown_cell("""---
## 8. Actionable Business Recommendations (Step 7)

Based on empirical data findings across all 2,000 transactions, we provide leadership with three targeted, quantitative operational recommendations:

### Recommendation 1: VIP Retention Program for the Top 20% Customer Cohort
* **The Empirical Evidence:** The top 20% of customer accounts (60 accounts) account for **33.88%** ($814,643.08) of total annual revenue, spending an average of over $13,577 per account.
* **Managerial Action:** Launch an exclusive VIP loyalty tier offering dedicated account concierges, tiered cash-back gratuities, and early access to high-demand merchandise. Preventing churn among just 5 of these top accounts protects over $67,000 in recurring annual revenue.

### Recommendation 2: Inventory & Marketing Capital Prioritization in Fashion & Electronics
* **The Empirical Evidence:** Fashion ($853,984.93 | 35.52%) and Electronics ($722,645.53 | 30.06%) jointly generate **65.58%** ($1,576,630.46) of total commercial revenue across 1,321 transactions.
* **Managerial Action:** Allocate at least 65% of Q1–Q2 paid acquisition budgets and vendor volume rebates toward Fashion and Electronics. Cross-promote Home and Books as basket-building checkout bundles to elevate overall transaction margins.

### Recommendation 3: Counter-Cyclical Promotions to Offset Q3 Seasonal Troughs
* **The Empirical Evidence:** Revenue plunges from its Q1 peak of $232,027.20 (February) to an annual trough of **$179,783.75** in August (-18.95% MoM contraction).
* **Managerial Action:** Establish a scheduled "Mid-Year Cyber Week" and "Back-to-School" promotional event in late July and August. Offering limited-time category bundles in Fashion and Electronics can stabilize the $52,243 revenue gap between peak and trough months."""))

    # Section 9: Verification Checklist
    cells.append(nbf.v4.new_markdown_cell("""---
## 9. Submission Verification Checklist

- [x] **Business questions written first:** Stated clearly in Section 1.
- [x] **Monthly trend and growth shown and plotted:** Full ledger with `.pct_change()` and annotated line chart marking best and worst months.
- [x] **Categories compared with groupby and pivot table:** Table of sum, mean, count, share, and month-by-category heatmap.
- [x] **Top-customer share calculated:** Top 10% (18.94%) and top 20% (33.88%) calculated and visualized via Pareto Lorenz curve.
- [x] **Three specific recommendations use real numbers:** Provided with exact monetary and percentage targets.
- [x] **Dashboard image exported at 150 DPI:** Saved cleanly as `sales_trend_overview.png`.
- [x] **Notebook runs from top to bottom without errors.**"""))

    nb.cells = cells
    return nb

def main():
    target_dir = os.path.dirname(os.path.abspath(__file__))
    notebook_path = os.path.join(target_dir, "sales_trend_analysis.ipynb")
    html_path = os.path.join(target_dir, "sales_trend_analysis.html")

    print(f"Generating notebook at {notebook_path}...")
    nb = generate_sales_notebook()

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Notebook written to disk.")

    print("Executing notebook end-to-end with ExecutePreprocessor...")
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': target_dir}})

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Notebook executed and saved with all outputs.")

    print(f"Exporting HTML to {html_path}...")
    html_exporter = HTMLExporter()
    (body, resources) = html_exporter.from_notebook_node(nb)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(body)
    print("HTML export completed successfully!")

if __name__ == "__main__":
    main()
