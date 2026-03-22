from shiny import App, ui, render, reactive, req
from shinywidgets import output_widget, render_widget, render_plotly
from shinywidgets import render_altair
import altair as alt
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
    llm_client = clt.ChatOllama(model="qwen3.5")
    ACTIVE_MODEL = "Local: Ollama (Qwen 3.5)"
    
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
app_ui = ui.page_fluid(
    ui.navset_tab(
        # --- Tab 1: Main Dashboard ---
        ui.nav_panel(
            "Main Dashboard",
            ui.h2(
                "Superstore Dashboard", 
                style="background-color: #2c4750; color: white; padding: 15px; border-radius: 5px;"
            ),
            ui.accordion(
                ui.accordion_panel(
                    "Click to learn more about this dashboard.",
                    ui.card(
                        ui.markdown(dashboard_description)
                    ),
                ),
                open=False
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_checkbox_group(
                        "category",
                        "Select Categories:",
                        choices=[], # Will be populated by the server
                    ),
                    ui.input_selectize(
                        "group_cols",
                        "Group Sales By (Select multiple):",
                        choices={
                            "category": "Category",
                            "sub_category": "Sub-Category",
                            "region": "Region",
                            "state": "State"
                        },
                        multiple=True,
                        selected=["category"]
                    )
                ),
                ui.navset_tab(
                    ui.nav_panel(
                        "Sales Table",
                        ui.output_data_frame("dynamic_table")
                    )
                ),
            ),
        ),

        # --- Tab 2: Query with Chat ---
        # ui.nav_panel(
        #     "Query with Chat",
        #     # Show actived model name into the header!
        #     ui.h2(f"AI-Powered Data Filtering (Powered by {ACTIVE_MODEL})"),
        #     ui.layout_sidebar(
        #         qc.sidebar() if qc else ui.sidebar(
        #             ui.card(
        #                 ui.card_header("LLM Not Configured"),
        #                 ui.p("To use the Query with Chat feature, configure an LLM client in your .env file:"),
        #                 ui.tags.ul(
        #                     ui.tags.li("Set ANTHROPIC_API_KEY for Claude"),
        #                     ui.tags.li("Set GITHUB_TOKEN for GitHub Models"),
        #                     ui.tags.li("Set USE_LOCAL_LLM=true for Ollama"),
        #                 ),
        #             )
        #         ),
        #         ui.layout_column_wrap(
        #             ui.card(
        #                 ui.card_header(
        #                     ui.output_text("chat_title"),
        #                     ui.download_button("download_chat_data", "Download CSV", class_="btn-success btn-sm") if qc else ui.div(),
        #                         class_="d-flex justify-content-between align-items-center"
        #                 ),
        #                 ui.output_data_frame("chat_tbl"),
        #             ),
        #             # ui.layout_column_wrap(
        #             #     ui.card(
        #             #         ui.card_header("Literacy Rate Scatterplot (Filtered)"),
        #             #         output_widget("chat_scatter"),
        #             #     ),
        #             #     ui.card(
        #             #         ui.card_header("Avg Education Level by Region (Filtered)"),
        #             #         output_widget("chat_bar"),
        #             #     ),
        #             #     width=1/2
        #             # ),
        #             width=1,
        #             heights_equal="row"
        #         ),
        #         # Set layout to a fixed height,
        #         height="80vh" 
        #     ),
        # ),
    ),
)

# ==========================================
#   SERVER LOGIC
# ==========================================
def server(input, output, session):    

    # ----------------------------------------
    # TAB 1 LOGIC (Main Dashboard)
    # ----------------------------------------
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
        # Require that categories are selected before proceeding
        req(input.category())
        return ss_data[ss_data["category"].isin(input.category())]

    @reactive.calc
    def dynamic_sales_agg():
        df = filtered_data()
        
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

    # @output
    # @render.table
    # def table():
    #     return filtered_data()


    # @reactive.Calc
    # def filtered_table():
    #     """Apply region filters at the database level using ibis.
        
    #     Returns an ibis table expression (lazy - not executed until .execute() is called).
    #     All filtering happens before data enters memory.
        
    #     Returns
    #     -------
    #     ibis.Table
    #         Lazy ibis table expression with filters applied
    #     """
    #     table = ss_data
        
    #     selected_regions = input.input_region()
    #     if selected_regions:
    #         table = table.filter(table["Region"].isin(selected_regions))
    #     else:
    #         table = table.filter(table["Region"] == "__NO_MATCH__")
    
    #     return table

    ### ----------------------------------------
    ### TAB 2 LOGIC (QueryChat)
    ### ----------------------------------------
    # @reactive.calc
    # def table_height():
    #     if qc is not None:
    #         n_rows = len(qc_vals.df())
    #         return f"{min(40 + n_rows * 30, 800)}px"
    #     else:
    #         return "250px" # Fallback height if LLM is disabled

    # if qc is not None:
    #     qc_vals = qc.server()

    #     @render.text
    #     def chat_title():
    #         return qc_vals.title() or "Superstore Dataset"

    #     @output
    #     @render.data_frame
    #     def chat_tbl():
    #         d = qc_vals.df()

    #         # Drop the unwanted index column
            
    #         # Define categorical columns
    #         cat_cols = ["state", "region", "city"]
            
    #         # Grab all the remaining numerical columns
    #         num_cols = [c for c in d.columns if c not in cat_cols]
            
    #         # Combine the lists to create final display order
    #         final_order = cat_cols + num_cols

    #         # Apply the order to the dataframe
    #         valid_cols = [c for c in final_order if c in d.columns]
            
    #         return render.DataGrid(
    #             d[valid_cols], 
    #             selection_mode="rows", 
    #             height=table_height()
    #         )
    # else:
    #     # Placeholder functions when QueryChat is not available
    #     @render.text
    #     def chat_title():
    #         return "LLM Not Configured"

    #     @output
    #     @render.data_frame
    #     def chat_tbl():
    #         return render.DataGrid(
    #             pd.DataFrame({"Message": ["Configure an LLM client to use this feature"]}),
    #             height=table_height()
    #         )

    # if qc is not None:
    #     @render.download(filename="supserstore_filtered.csv")
    #     def download_chat_data():
    #         yield qc_vals.df().to_csv(index=False).encode("utf-8")


app = App(app_ui, server)
