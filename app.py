import streamlit as st
import polars as pl
import io
import zipfile
import re
import fastexcel

# Page Config
st.set_page_config(page_title="Universal Data Splitter", page_icon="✂️", layout="wide")

# --- SIDEBAR PRIVACY NOTICE ---
with st.sidebar:
    st.header("🔒 Privacy & Security")
    st.info("Your data is processed in-memory. **We don't store your data.**")

st.caption("by Asrol")
st.title("Universal CSV & Excel Splitter")
st.markdown("Upload a **CSV** or **XLSX**, select your sheet, and split by column with a full preview.")
st.divider()

def clean_filename(name):
    """Removes invalid characters for Windows/Mac filenames."""
    return re.sub(r'[\\/*?:"<>|]', "-", str(name)).strip()

# 1. File Uploader
uploaded_file = st.file_uploader("Upload your file (CSV or XLSX)", type=["csv", "xlsx"])

if uploaded_file is not None:
    df = None
    
    # --- STEP A: LOAD DATA ---
    try:
        if uploaded_file.name.endswith('.xlsx'):
            # Peek at sheet names first
            excel_info = fastexcel.read_excel(uploaded_file)
            sheet_names = excel_info.sheet_names
            
            selected_sheet = st.selectbox(
                "Select the sheet you want to split:",
                options=sheet_names
            )
            
            if selected_sheet:
                df = pl.read_excel(uploaded_file, sheet_name=selected_sheet)
        else:
            # Direct load for CSV
            df = pl.read_csv(uploaded_file)
            df.columns = [c.strip() for c in df.columns]

    except Exception as e:
        st.error(f"Error reading file: {e}")

    # --- STEP B: PREVIEW & CONTROLS ---
    if df is not None:
        st.subheader("Data Preview")
        # Convert to Pandas only for the UI display
        st.dataframe(df.head(5).to_pandas(), use_container_width=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        all_columns = df.columns
        
        with col1:
            split_column = st.selectbox(
                "1. Which column determines the split?", 
                options=all_columns,
                help="Every unique value here creates a new file."
            )
        
        with col2:
            exclude_cols = st.multiselect(
                "2. Columns to EXCLUDE (Optional)", 
                options=[c for c in all_columns if c != split_column]
            )
        
        # --- STEP C: FILE COUNT PREVIEW ---
        if split_column:
            unique_values = df[split_column].dropna().unique().to_list()
            num_unique = len(unique_values)
            cols_remaining = len(all_columns) - len(exclude_cols)
            
            st.info(f" **Ready to create {num_unique} files.** Each file will contain **{cols_remaining}** columns.")

            # --- STEP D: PROCESSING ---
            if st.button(" Generate & Download ZIP"):
                with st.spinner("Polars is splitting and zipping your data..."):
                    zip_buffer = io.BytesIO()
                    
                    # Drop excluded columns
                    processed_df = df.drop(exclude_cols)
                    
                    # High-speed partitioning
                    partitions = processed_df.partition_by(split_column, as_dict=True)
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for value, group_df in partitions.items():
                            # Handle tuple values from partition_by
                            file_label = str(value[0]) if isinstance(value, tuple) else str(value)
                            
                            # Write to CSV bytes
                            csv_bytes = group_df.write_csv().encode('utf-8')
                            
                            file_name = f"{clean_filename(file_label)}.csv"
                            zip_file.writestr(file_name, csv_bytes)

                    st.success(f"✅ Successfully created {len(partitions)} files!")
                    
                    st.download_button(
                        label="📥 Download ZIP",
                        data=zip_buffer.getvalue(),
                        file_name=f"Split_{uploaded_file.name}.zip",
                        mime="application/zip"
                    )

# --- FOOTER ---
st.divider()
st.caption("Privacy Guarantee: We don't store your data. All processing happens in live memory.")
