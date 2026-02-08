import streamlit as st
import polars as pl
import io
import zipfile
import re
import fastexcel

# Page Config
st.set_page_config(page_title="Universal Data Splitter", layout="wide")

# --- SIDEBAR PRIVACY NOTICE ---
with st.sidebar:
    st.header("Privacy and Security")
    st.info("Your data is processed in-memory using Polars. Data is not stored on our servers.")

st.caption("by Asrol")
st.title("Universal CSV and Excel Splitter")
st.markdown("Upload a file, select your preferences, and split by column with a full preview.")
st.divider()

def clean_filename(name):
    """Removes invalid characters for Windows/Mac filenames."""
    return re.sub(r'[\\/*?:"<>|]', "-", str(name)).strip()

# 1. File Uploader
uploaded_file = st.file_uploader("Upload your file (CSV or XLSX)", type=["csv", "xlsx"])

if uploaded_file is not None:
    df = None
    file_bytes = uploaded_file.getvalue() # Get raw bytes to avoid 'source must be string' error
    
    # --- HANDLING EXCEL SHEETS ---
    try:
        if uploaded_file.name.endswith('.xlsx'):
            # Use BytesIO to make the bytes readable like a file
            excel_info = fastexcel.read_excel(io.BytesIO(file_bytes))
            sheet_names = excel_info.sheet_names
            
            selected_sheet = st.selectbox(
                "Select the sheet to process:",
                options=sheet_names
            )
            
            if selected_sheet:
                # Read the specific sheet from bytes
                df = pl.read_excel(io.BytesIO(file_bytes), sheet_name=selected_sheet)
        else:
            # Direct load for CSV from bytes
            df = pl.read_csv(io.BytesIO(file_bytes))
            df.columns = [c.strip() for c in df.columns]

    except Exception as e:
        st.error(f"Error reading file: {e}")

    # --- DATA PREVIEW AND CONTROLS ---
    if df is not None:
        st.subheader("Data Preview")
        st.dataframe(df.head(5).to_pandas(), use_container_width=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        all_columns = df.columns
        
        with col1:
            split_column = st.selectbox(
                "1. Select the column to split by:", 
                options=all_columns,
                help="Every unique value in this column will create a separate file."
            )
        
        with col2:
            exclude_cols = st.multiselect(
                "2. Select columns to exclude (Optional):", 
                options=[c for c in all_columns if c != split_column]
            )
        
        # --- PREVIEW LOGIC ---
        if split_column:
            num_unique = df[split_column].n_unique()
            cols_remaining = len(all_columns) - len(exclude_cols)
            
            st.info(f"Ready to create {num_unique} files. Each file will contain {cols_remaining} columns.")

            # --- PROCESSING ---
            if st.button("Generate and Download ZIP"):
                with st.spinner("Processing data..."):
                    zip_buffer = io.BytesIO()
                    
                    # Drop excluded columns
                    processed_df = df.drop(exclude_cols)
                    
                    # High-speed partitioning
                    partitions = processed_df.partition_by(split_column, as_dict=True)
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for value, group_df in partitions.items():
                            file_label = str(value[0]) if isinstance(value, tuple) else str(value)
                            
                            csv_bytes = group_df.write_csv().encode('utf-8')
                            
                            file_name = f"{clean_filename(file_label)}.csv"
                            zip_file.writestr(file_name, csv_bytes)

                    st.success(f"Successfully created {len(partitions)} files.")
                    
                    st.download_button(
                        label="Download ZIP",
                        data=zip_buffer.getvalue(),
                        file_name=f"Split_{uploaded_file.name.replace('.xlsx', '').replace('.csv', '')}.zip",
                        mime="application/zip"
                    )

# --- FOOTER ---
st.divider()
st.caption("Privacy Guarantee: We do not store your data. All processing occurs in live memory.")
