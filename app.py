import streamlit as st
import polars as pl
import io
import zipfile
import re
import fastexcel  # Needed for sheet inspection

# Page Config
st.set_page_config(page_title="Universal Data Splitter", page_icon="✂️", layout="wide")

# --- SIDEBAR PRIVACY NOTICE ---
with st.sidebar:
    st.header("Privacy & Security")
    st.info("Your data is processed in-memory. **We don't store your data.**")

st.caption("by Asrol")
st.title("Universal CSV & Excel Splitter")
st.markdown("Upload a **CSV** or **XLSX**, select your sheet (for Excel), and split by column.")
st.divider()

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "-", str(name)).strip()

# 1. File Uploader
uploaded_file = st.file_uploader("Upload your file (CSV or XLSX)", type=["csv", "xlsx"])

if uploaded_file is not None:
    df = None
    
    # --- HANDLING EXCEL SHEETS ---
    if uploaded_file.name.endswith('.xlsx'):
        try:
            # Inspect the Excel file for sheet names
            excel_info = fastexcel.read_excel(uploaded_file)
            sheet_names = excel_info.sheet_names
            
            selected_sheet = st.selectbox(
                "📂 This Excel file has multiple sheets. Which one should we use?",
                options=sheet_names
            )
            
            if selected_sheet:
                df = pl.read_excel(uploaded_file, sheet_name=selected_sheet)
        except Exception as e:
            st.error(f"Could not read Excel sheets: {e}")
            
    # --- HANDLING CSV ---
    else:
        try:
            df = pl.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

    # 2. Data Processing (If file is successfully loaded)
    if df is not None:
        st.subheader(" Data Preview")
        st.dataframe(df.head(5).to_pandas(), use_container_width=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        all_columns = df.columns
        
        with col1:
            split_column = st.selectbox("1. Split by this column:", options=all_columns)
        
        with col2:
            exclude_cols = st.multiselect("2. Exclude these columns:", 
                                         options=[c for c in all_columns if c != split_column])
        
        if split_column:
            num_unique = df[split_column].n_unique()
            st.info(f"Ready to create **{num_unique}** files.")

            if st.button(" Process & Download ZIP"):
                with st.spinner("Processing..."):
                    zip_buffer = io.BytesIO()
                    processed_df = df.drop(exclude_cols)
                    
                    # Efficiently split data
                    partitions = processed_df.partition_by(split_column, as_dict=True)
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for value, group_df in partitions.items():
                            file_label = str(value[0]) if isinstance(value, tuple) else str(value)
                            
                            # Exporting each split as CSV (standard for portability)
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

st.divider()
st.caption("Privacy Guarantee: We don't store your data. All processing happens in live memory.")
