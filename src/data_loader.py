import pandas as pd
from pathlib import Path

def load_superstore_data():
    # Resolve the file path (assumes this file is in the 'src' folder)
    file_path = Path(__file__).parent.parent / "data/sample_superstore.csv"
    
    # Read the data
    df = pd.read_csv(file_path, encoding="latin1")
    # .drop(columns=['Row ID', 'Ship Date', 'Ship Mode', 'Customer Name'])
    
    # Clean the column names
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    
    # Convert dates
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Extract min and max dates
    min_dt = df['order_date'].min().date()
    max_dt = df['order_date'].max().date()
    
    return df, min_dt, max_dt

# Run the function once when the module is imported
ss_data, min_date, max_date = load_superstore_data()