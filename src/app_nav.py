from shiny import App, ui, render, reactive, req
from shinywidgets import output_widget, render_widget, render_plotly
from shinywidgets import render_altair
import altair as alt
from vega_datasets import data
import os
from pathlib import Path
import pandas as pd
import numpy as np

import chatlas as clt
from dotenv import load_dotenv
from querychat import QueryChat

# Read data
from data_loader import ss_data, min_date, max_date


# anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# ==========================================
#   SETUP & DATA LOADING
# ==========================================
# Initialize the correct Chatlas Client inside the server so it's safe for multi-users
# Note: QueryChat requires a valid client, so we'll skip QueryChat initialization if no API key is available
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

if os.environ.get("USE_LOCAL_LLM", "False").lower() == "true":
    llm_client = clt.ChatOllama(model="llama3.1:8b")
    ACTIVE_MODEL = "Local: Ollama (llama 3.1 8B)"
    
elif os.environ.get("GITHUB_TOKEN"):
    llm_client = clt.ChatGithub(model="gpt-4o-mini")
    ACTIVE_MODEL = "Cloud: GitHub (GPT-4o-Mini)"
    
# elif os.environ.get("ANTHROPIC_API_KEY"):
#     llm_client = clt.ChatAnthropic(model="claude-haiku-4-5-20251001") 
#     ACTIVE_MODEL = "Cloud: Anthropic (Claude Haiku 4.5)"

else:
    llm_client = None
    ACTIVE_MODEL = "NONE (No API keys or Local LLM found)"

# Print in terminal to see LLM successfully loaded
print(f"\n---> LLM Status: {ACTIVE_MODEL} <---\n")

# QueryChat Setup
# Read greeting
greeting_path = Path(__file__).parent / "ai_greeting.md"
GREETING = greeting_path.read_text(encoding="utf-8")

# Read data description
data_desc_path = Path(__file__).parent / "ai_data_desc.md"
DATA_DESC = data_desc_path.read_text(encoding="utf-8")

# Add drop-down dashboard description
dashboard_desc_path = Path(__file__).parent / "dashboard_description.md"
dashboard_description = dashboard_desc_path.read_text(encoding="utf-8")

# Only initialize QueryChat if we have a valid LLM client
if llm_client is not None:
    qc = QueryChat(
        ss_data.copy(),
        "superstore",
        greeting=GREETING,
        data_description=DATA_DESC,
        client=llm_client,
    )
else:
    # Create a minimal placeholder - QueryChat tab won't work but app will load
    qc = None
    print("⚠️  Warning: QueryChat disabled - no LLM client configured")


# ==========================================
#   UI DEFINITION
# ==========================================
# Replace your current app_ui with this:
app_ui = ui.page_navbar(
    ui.nav_spacer(),
    # --- Tab 1: Main Dashboard ---
    ui.nav_panel(
        "Main Dashboard",
        ui.layout_sidebar(
            ui.sidebar(
                ui.tags.style("""
                    /* 1. Shrink the main "Filters" heading */
                    #filters-heading { font-size: 1.25rem; font-weight: bold; }
                    
                    /* 2. Shrink ALL input labels (Date Range, Group By, Category) */
                    .form-label, .control-label { font-size: 0.85rem; font-weight: 500; }
                    
                    /* 3. Shrink the Date Range input boxes */

                    
                    /* 4. Shrink the Selectize dropdown box and its popup menu */
                    .selectize-input { font-size: 0.85rem; min-height: 30px; }
                    .selectize-dropdown { font-size: 0.85rem; }
                    
                    /* 5. Shrink the Checkbox list text */
                    .form-check-label { font-size: 0.85rem; }
                """),
                ui.div(
                    ui.h4("Filters", id="filters-heading"),
                    ui.hr(),
                ),
                ui.input_date_range(
                    "daterange1",
                    "Order Date Range",
                    start=min_date,
                    end=max_date,
                    min=min_date,
                    max=max_date,
                    format="yyyy-mm",
                    startview="year",
                ),
                ui.input_selectize(
                    "group_cols",
                    "Group Sales By (Select multiple):",
                    choices={
                        "region": "Region",
                        "state": "State",                        
                        "segment": "Segment",
                        "category": "Category",
                        "sub_category": "Sub-Category",
                    },
                    multiple=True,
                    selected=["region"]
                ),
                ui.input_checkbox_group(
                    "category",
                    "Filter by Category:",
                    choices=[]
                )
            ),
            ui.navset_tab(
                ui.nav_panel(
                    "Aggregated View",
                    ui.accordion(
                        ui.accordion_panel(
                            "Click to learn more about this dashboard.",
                            ui.card(
                                ui.markdown(dashboard_description)
                            ),
                        ),
                        open=False
                    ),
                    ui.div(
                        {"class": "fixed-main-header"},
                        # KPI and Summary
                        ui.layout_columns(
                            ui.value_box(
                                "Total Sales",
                                ui.div(
                                    ui.output_text("total_sales_agg"),
                                    ui.div(
                                        {"style": "font-size:12px; color:gray;"},
                                        ui.output_ui("total_sales_change"),
                                    ),
                                ),
                            ),
                            ui.value_box(
                                "Total Profits",
                                ui.div(
                                    ui.output_text("total_profit_agg"),
                                    ui.div(
                                        {"style": "font-size:12px; color:gray;"},
                                        ui.output_ui("total_profit_change"),
                                    ),
                                ),
                            ),
                            ui.value_box(
                                "Total Orders",
                                ui.div(
                                    ui.output_text("total_order_agg"),
                                    ui.div(
                                        {"style": "font-size:12px;"},
                                        ui.output_text("total_order_change"),
                                    ),
                                ),
                                # theme="bg-success text-white",
                            ),
                            ui.value_box(
                                "Highest Avg Sales State",
                                ui.div(
                                    ui.output_text("kpi_max_state"),
                                    ui.div(
                                        {"style": "font-size:12px;"},
                                        ui.output_text("kpi_max_note"),
                                    ),
                                ),
                                # theme="bg-danger text-white",
                            ),
                            # ADDED: KPI — MOST COMMON CRIME
                            ui.card(
                                ui.h5("Most Sold Product"), ui.output_text("kpi_most_common")
                            ),
                        ),
                    ),
                    ui.hr(),
                    ui.card(
                        ui.h5("Sales Map"),
                        output_widget("map_chart")
                    ),
                    ui.hr(),
                    ui.layout_columns(
                        ui.column(
                            12,
                            ui.card(
                                ui.card_header("Visual Sales Breakdown"),
                                output_widget("sales_chart") # Notice we use output_widget for Altair!
                            ),
                        ),
                        # ui.column(
                        #     12,
                        #     ui.card(
                        #         ui.card_header("Visual Sales Breakdown"),
                        #         output_widget("sales_chart") # Notice we use output_widget for Altair!
                        #     ),
                        # ),
                    ),
                ),
                ui.nav_panel(
                    "Raw Data View",
                    ui.card(
                        ui.card_header("Aggregated Data Table"),
                        ui.p("Inspect the underlying filtered data before aggregation.", class_="text-muted mt-2"),
                        ui.output_data_frame("raw_data_table"), # <-- NEW UNIQUE ID!
                        class_="mt-3"
                    ),
                ),
            ),
        ),
    ),

    # --- Tab 2: Query with Chat ---
    ui.nav_panel(
        "Query with Chat",
        ui.layout_sidebar(
            qc.sidebar() if qc else ui.sidebar(
                ui.card(
                    ui.card_header("LLM Not Configured"),
                    ui.p("To use the Query with Chat feature, configure an LLM client in your .env file:"),
                    ui.tags.ul(
                        ui.tags.li("Set ANTHROPIC_API_KEY for Claude"),
                        ui.tags.li("Set GITHUB_TOKEN for GitHub Models"),
                        ui.tags.li("Set USE_LOCAL_LLM=true for Ollama"),
                    ),
                )
            ),
            # Show actived model name into the header!
            ui.h2(
                f"AI-Powered Data Filtering (Powered by {ACTIVE_MODEL})",
                class_="fs-6 mt-3 mb-4",
            ),
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header(
                        ui.output_text("chat_title"),
                        ui.download_button("download_chat_data", "Download CSV", class_="btn-success btn-sm") if qc else ui.div(),
                            class_="d-flex justify-content-between align-items-center"
                    ),
                    ui.output_data_frame("chat_tbl"),
                ),
                width=1,
                heights_equal="row"
            ),
            # Set layout to a fixed height,
            height="80vh" 
        )
    ),

    # --- Global Navbar Settings ---
    title="Superstore Dashboard",
    position="fixed-top",
    bg="#2c4750",  # Your custom Hex code
    inverse=True,  # Makes the text light to contrast the dark background
    footer=ui.tags.div(
        ui.p("2026 William Song | System Status: Online"),
        style="padding: 10px; text-align: center; font-size: 0.8em;"
    )
)

# ==========================================
#   SERVER LOGIC
# ==========================================
def server(input, output, session):    

    # ----------------------------------------
    # TAB 1 LOGIC (Main Dashboard)
    # ----------------------------------------
    @reactive.calc
    def cleaned_data():
        ss_data_clean = ss_data.copy().drop(columns=['row_id', 'ship_date', 'ship_mode', 'customer_name'])
        cat_cols = ss_data_clean.select_dtypes(include=['object', 'category']).columns.tolist()
        # if want to exclude specific column
        # cat_cols = [col for col in cat_cols if col not in ['order_id', 'customer_id', 'product_id']]

        return ss_data_clean, cat_cols
    
    @reactive.effect
    def update_categories():
        # Populate the checkbox choices on startup
        categories = sorted(ss_data["category"].unique())
        ui.update_checkbox_group(
            "category",
            choices=categories,
            selected=categories
        )

    @reactive.calc
    def filtered_data():
        df, cat_cols = cleaned_data()
        # Require that categories are selected before proceeding
        req(input.category(), input.daterange1())

        start_date, end_date = input.daterange1()

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        mask = (
            df["category"].isin(input.category()) & 
            (df['order_date'] >= start_date) & 
            (df['order_date'] <= end_date)
        )
        return df[mask]

    @output
    @render.text
    def total_sales_agg():
        df = filtered_data().copy()
        sales_total_agg = df['sales'].sum()

        return f"{sales_total_agg:,}"
    
    @output
    @render.ui
    def total_sales_change():
        df = filtered_data().copy()
        sales_total_change = df['sales'].sum()

        
        return f"{sales_total_change:,}"

    @output
    @render.text
    def total_profit_agg():
        df = filtered_data().copy()
        profit_total_agg = df['profit'].sum()

        return f"{profit_total_agg:,}"
    
    @output
    @render.ui
    def total_profit_change():
        df = filtered_data().copy()
        profit_total_change = df['profit'].sum()

        
        return f"{profit_total_change:,}"
    
    @output
    @render.text
    def total_order_agg():
        df = filtered_data().copy()
        if 'order_id' in df.columns:
            order_total_agg = df['order_id'].nunique()
        else:
            order_total_agg = len(df)

        return f"{order_total_agg:,}"
    
    @output
    @render.text
    def total_order_change():
        df = filtered_data().copy()
        if 'order_id' in df.columns:
            order_total_change = df['order_id'].nunique()
        else:
            order_total_change = len(df)

        
        return f"{order_total_change:,}"

    @reactive.calc
    def dynamic_sales_agg():
        df = filtered_data().copy()
        
        # Ensure it's a list (it usually is from input_selectize with multiple=True)
        cols_to_group = list(input.group_cols())
        
        if not cols_to_group:
            return pd.DataFrame({"Global Total Sales": [df['sales'].sum()]})
            
        agg_df = df.groupby(cols_to_group, as_index=False)['sales'].sum()
        agg_df = agg_df.sort_values('sales', ascending=False)
        
        return agg_df

    @output
    @render.data_frame
    def dynamic_table():
        df = dynamic_sales_agg()
        display_df = df.copy()
        
        if 'sales' in display_df.columns:
            display_df['sales'] = display_df['sales'].apply(lambda x: f"${x:,.2f}")

        elif 'Global Total Sales' in display_df.columns:
            display_df['Global Total Sales'] = display_df['Global Total Sales'].apply(lambda x: f"${x:,.2f}")

        return render.DataGrid(display_df)

    @output
    @render.data_frame
    def raw_data_table():
        d = ss_data.copy()
        return render.DataGrid(d)

    @output
    @render_altair
    def map_chart():
        df = filtered_data().copy()
        
        # Handle empty data case
        if df.empty:
            return alt.Chart(pd.DataFrame({'msg': ['No data available']})) \
                      .mark_text(size=16, color='gray') \
                      .encode(text='msg:N') \
                      .properties(height=400)

        # 2. Aggregate sales strictly by state
        state_sales = df.groupby('state', as_index=False)['sales'].sum()

        # 3. Map state names to FIPS ID codes for the geographic plot
        state_fips = {
            'Alabama': 1, 'Alaska': 2, 'Arizona': 4, 'Arkansas': 5, 'California': 6,
            'Colorado': 8, 'Connecticut': 9, 'Delaware': 10, 'District of Columbia': 11,
            'Florida': 12, 'Georgia': 13, 'Hawaii': 15, 'Idaho': 16, 'Illinois': 17,
            'Indiana': 18, 'Iowa': 19, 'Kansas': 20, 'Kentucky': 21, 'Louisiana': 22,
            'Maine': 23, 'Maryland': 24, 'Massachusetts': 25, 'Michigan': 26,
            'Minnesota': 27, 'Mississippi': 28, 'Missouri': 29, 'Montana': 30,
            'Nebraska': 31, 'Nevada': 32, 'New Hampshire': 33, 'New Jersey': 34,
            'New Mexico': 35, 'New York': 36, 'North Carolina': 37, 'North Dakota': 38,
            'Ohio': 39, 'Oklahoma': 40, 'Oregon': 41, 'Pennsylvania': 42, 'Rhode Island': 44,
            'South Carolina': 45, 'South Dakota': 46, 'Tennessee': 47, 'Texas': 48,
            'Utah': 49, 'Vermont': 50, 'Virginia': 51, 'Washington': 53, 'West Virginia': 54,
            'Wisconsin': 55, 'Wyoming': 56
        }
        
        # Apply the mapping
        state_sales['id'] = state_sales['state'].map(state_fips)
        state_sales = state_sales.dropna(subset=['id'])

        # 4. Load the Altair US map geometry
        states_topo = alt.topo_feature(data.us_10m.url, 'states')

        # 5. Build the map
        chart = alt.Chart(states_topo).mark_geoshape(
            stroke='white',     # Adds a clean white border between states
            strokeWidth=0.5
        ).encode(
            color=alt.Color(
                'sales:Q', 
                title='Total Sales (USD)', 
                scale=alt.Scale(scheme='tealblues') # Matches your dashboard's color scheme
            ),
            tooltip=[
                alt.Tooltip('state:N', title='State'),
                alt.Tooltip('sales:Q', title='Total Sales', format='$,.2f')
            ]
        ).transform_lookup(
            lookup='id',
            from_=alt.LookupData(state_sales, 'id', ['sales', 'state'])
        ).project(
            type='albersUsa' # Automatically moves AK and HI to the bottom left
        ).properties(
            height=400
        )

        return chart


    @output
    @render_altair
    def sales_chart():
        # 1. Fetch the raw, unformatted numbers from your reactive calculation
        df = dynamic_sales_agg().copy()
        
        # 2. Handle the edge case: If no grouping is selected, show a message instead of a broken chart
        if 'Global Total Sales' in df.columns:
            return alt.Chart(pd.DataFrame({'msg': ['Please select at least one group to display the chart.']})) \
                      .mark_text(size=16, color='gray') \
                      .encode(text='msg:N') \
                      .properties(height=100)

        # 3. Figure out which columns the user selected to group by
        # (Everything except the 'sales' column)
        group_cols = [col for col in df.columns if col != 'sales']
        
        # 4. The Trick: If they picked multiple columns, combine them into one string for the Y-axis
        if len(group_cols) > 1:
            # Creates labels like "Furniture - West"
            df['Chart_Label'] = df[group_cols].astype(str).agg(' - '.join, axis=1)
            y_axis_col = 'Chart_Label:N'
            y_axis_title = " + ".join([c.replace('_', ' ').title() for c in group_cols])
        else:
            y_axis_col = f"{group_cols[0]}:N"
            y_axis_title = group_cols[0].replace('_', ' ').title()

        # 5. Build the Altair Bar Chart
        chart = alt.Chart(df).mark_bar(color="#2c4750").encode(
            x=alt.X('sales:Q', title='Total Sales (USD)', axis=alt.Axis(format='$,.0f')),
            y=alt.Y(y_axis_col, sort='-x', title=y_axis_title), # sort='-x' orders bars from longest to shortest
            tooltip=[
                alt.Tooltip(c, type='nominal') for c in group_cols
            ] + [
                alt.Tooltip('sales:Q', title='Sales', format='$,.2f')
            ]
        ).properties(
            height=alt.Step(30) # Dynamic height based on the number of bars!
        ).interactive()
        
        return chart



    ### ----------------------------------------
    ### TAB 2 LOGIC (QueryChat)
    ### ----------------------------------------
    @reactive.calc
    def table_height():
        if qc is not None:
            n_rows = len(qc_vals.df())
            return f"{min(40 + n_rows * 30, 800)}px"
        else:
            return "250px" # Fallback height if LLM is disabled

    if qc is not None:
        qc_vals = qc.server()

        @render.text
        def chat_title():
            return qc_vals.title() or "Superstore Dataset"

        @output
        @render.data_frame
        def chat_tbl():
            d = qc_vals.df()

            # Drop the unwanted index column
            
            # Define categorical columns
            cat_cols = ["state", "region", "city"]
            
            # Grab all the remaining numerical columns
            num_cols = [c for c in d.columns if c not in cat_cols]
            
            # Combine the lists to create final display order
            final_order = cat_cols + num_cols

            # Apply the order to the dataframe
            valid_cols = [c for c in final_order if c in d.columns]
            
            return render.DataGrid(
                d[valid_cols], 
                selection_mode="rows", 
                height=table_height()
            )
    else:
        # Placeholder functions when QueryChat is not available
        @render.text
        def chat_title():
            return "LLM Not Configured"

        @output
        @render.data_frame
        def chat_tbl():
            return render.DataGrid(
                pd.DataFrame({"Message": ["Configure an LLM client to use this feature"]}),
                height=table_height()
            )

    if qc is not None:
        @render.download(filename="supserstore_filtered.csv")
        def download_chat_data():
            yield qc_vals.df().to_csv(index=False).encode("utf-8")


app = App(app_ui, server)
