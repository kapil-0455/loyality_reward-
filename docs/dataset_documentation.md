# Dataset & Feature Engineering Documentation

## 1. Primary Dataset: UCI Online Retail II
- **Source:** [UCI Machine Learning Repository - Online Retail II](https://archive.ics.uci.edu/dataset/502/online_retail%2Bii)
- **Domain:** Non-store online retail transactions for a UK-based registered giftware retailer.
- **Timeframe:** 01/12/2009 to 09/12/2011.
- **Raw Location:** `data/raw/online_retail_II.xlsx`

### Raw Dataset Attributes
| Field | Data Type | Description |
|---|---|---|
| `Invoice` | String | 6-digit transaction identifier. Prefixed with 'C' for cancellations. |
| `StockCode` | String | Distinct 5-digit product code. |
| `Description` | String | Item name. |
| `Quantity` | Integer | Product units per invoice line. Negative values indicate returns. |
| `InvoiceDate` | Datetime | Invoice generation timestamp. |
| `Price` | Float | Unit price in Sterling (£). |
| `Customer ID` | Float/Int | 5-digit unique customer identifier. Missing for guest checkouts. |
| `Country` | String | Customer country of residence. |

---

## 2. Data Cleaning & Transformation Pipeline
1. **Missing Customer ID Handling:** Records with `Customer ID = NaN` represent unregistered guest visitors. They are excluded from the loyalty profile calculation but retained for product demand benchmarking.
2. **Cancellations & Returns:** Invoices starting with `C` or records with `Quantity <= 0` or `Price <= 0` are excluded from gross purchase value and RFM frequency computations.
3. **Reference Evaluation Date:** A fixed anchor date of `2011-12-10` is used for historical consistency (one day post-dataset completion date).

---

## 3. Customer RFM Feature Engineering
From qualifying transaction records, three core analytical features are computed per customer:

- **Recency ($R$):** $R = \text{Anchor Date} - \max(\text{InvoiceDate})$ (Days since most recent qualifying purchase).
- **Frequency ($F$):** $F = \text{Count}(\text{Distinct Invoices})$ (Number of unique qualifying transactions).
- **Monetary ($M$):** $M = \sum (\text{Quantity} \times \text{Price})$ (Gross lifetime purchase expenditure).

### K-Means Customer Clustering
- **Features Scaled:** Log-transformed and standardized using `StandardScaler`.
- **Optimal Clusters ($k=2$):**
  - **Cluster 1 (High-Value Champions):** Recency $\approx 51$ days, Frequency $\approx 12.6$ purchases, Monetary $\approx \$6,520$.
  - **Cluster 0 (At-Risk / Occasional):** Recency $\approx 301$ days, Frequency $\approx 2.1$ purchases, Monetary $\approx \$611$.

Processed dataset saved at: `data/processed/customer_rfm_segments.csv`.

---

## 4. Synthetic Loyalty & Operational Schema
Because UCI Online Retail II does not contain points ledgers or live stock tracking, synthetic records are generated to complete the loyalty lifecycle:

1. **`CustomerLoyaltyProfile`:**
   - `customer_id` (PK, matches UCI ID)
   - `loyalty_tier` (Bronze, Silver, Gold, Platinum based on RFM percentiles)
   - `points_balance` (Synthetic opening points balance)
   - `profile_status` (`active` / `inactive`)

2. **`RewardCatalogue`:**
   - 20 synthetic rewards across vouchers, physical products, and seasonal perks.
   - Includes `points_required`, `eligible_tiers`, `valid_from`, `valid_until`, `minimum_purchase_value`.

3. **`ProductInventory`:**
   - 30 tracked stock SKUs.
   - Includes `on_hand_stock`, `reserved_stock`, `available_stock`, `reorder_level`.

4. **`CampaignBudget`:**
   - 5 active campaigns (`CAMP-001` to `CAMP-005`).
   - Tracks `budget_limit`, `committed_amount`, `approved_amount`.

5. **`RewardLedger` & `RewardApproval`:**
   - Immutable financial audit log with `idempotency_key` and timestamped point debits.

