# **Superstore Retail Analytics**

This dashboard explores **retail sales and profitability** across different geographic regions using the classic Superstore dataset. It allows users to compare patterns in **revenue, profit margins, and discounting strategies** across product categories and customer segments. It addresses the challenge of making sense of complex transactional data by providing an interactive visualization tool that enables users to:

- Explore sales and profit metrics across various regions and states
- Compare product category performance and identify key profitability drivers
- Analyze the impact of discounts on the overall bottom line
- Make data-driven decisions to optimize retail pricing and operations

#### How to use this dashboard

**Global filters (left sidebar)**
- Select one or more regions, customer segments, or date ranges to update all charts, the map, and the data table.

**Overview tab**
- Explore a **geographic map of sales and profit** by selecting different metrics.
- KPI cards summarize the total revenue, overall profit margin, and total order volume for the selected filters.

**Profit & Discount tab**
- Compare category and sub-category patterns in:
  - total sales vs. net profit
  - the effect of discount rates on profitability (highlighting loss-leading items)
  - purchasing trends between Consumer, Corporate, and Home Office segments
- Click bars or scatterplot points to update the filter selection.

**Data Table tab**
- Inspect the filtered **transaction-level dataset**.
- Choose which variables to display using the feature selector.

**Query with Chat**:
- Supports Anthropic, local Ollama, or GitHub-backed LLM; 
- Anthropic by default on Posit Connect, and optional setup via `.env` if you run the app locally.
- Use natural language to explore the dataset with an AI assistant.
- Ask questions like *"Show me the sub-categories in the West region with negative profit"* to filter and visualize the data interactively.

## Limitations for this data set

- This data is a fictional, static snapshot of retail operations (typically spanning a fixed 4-year period), so it does not reflect real-time live business transactions.
- The dataset lacks granular cost-of-goods-sold (COGS), marketing spend, or internal operational expenses, so profit calculations are strictly limited to the provided revenue and discount fields.
- Geographic data is restricted primarily to North America (United States and Canada), meaning it cannot be used for broader global or international comparisons.

**Original data can be accessed via this [link to Kaggle](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final).**