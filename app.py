import streamlit as st
import pandas as pd
import io
import zipfile
import re

# Page Config
st.set_page_config(page_title="Universal CSV Splitter", page_icon="✂️", layout="wide")

# --- HEADER SECTION ---
# This adds your name as a professional sub-header at the very top
st.caption("🚀 Developed by Asrol")

st.title("✂️ Universal CSV Splitter + Data Cleaner")
st.markdown("Upload any CSV, pick your split column, and remove any sensitive data before zipping.")
st.divider()

def clean_filename(name):
    """Removes invalid characters for Windows/Mac filenames."""
    return re.sub(r'[\\/*?:"<>|]', "-", str(name)).strip()

# 1. File Uploader
uploaded_file = st.file_uploader("Upload your CSV file (Max 600MB)", type="csv")

if uploaded_file is not None:
    # 2. Read Data
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    st.subheader("👀 Data Preview")
    st.dataframe(df.head(5), use_container_width=True)
    
    # 3. Dynamic Selection Controls
    st.divider()
    col1, col2 = st.columns(2)
    
    all_columns = df.columns.tolist()
    
    with col1:
        split_column = st.selectbox(
            "1. Which column determines the split?",
            options=all_columns,
            help="Every unique value here creates a new file."
        )
    
    with col2:
        exclude_cols = st.multiselect(
            "2. Columns to EXCLUDE (Optional)",
            options=[c for c in all_columns if c != split_column],
            help="Selected columns will be REMOVED from the final files."
        )
    
    if split_column:
        unique_values = df[split_column].dropna().unique()
        st.info(f"Ready to create **{len(unique_values)}** files. Columns being kept: **{len(all_columns) - len(exclude_cols)}**")

        # 4. Processing
        if st.button("🚀 Generate & Download ZIP"):
            with st.spinner("Cleaning data and zipping..."):
                zip_buffer = io.BytesIO()
                
                # Drop the excluded columns
                processed_df = df.drop(columns=exclude_cols)
                
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for value in unique_values:
                        filtered_data = processed_df[processed_df[split_column] == value]
                        csv_string = filtered_data.to_csv(index=False).encode('utf-8')
                        
                        file_name = f"{clean_filename(value)}.csv"
                        zip_file.writestr(file_name, csv_string)

                st.success("✅ Your files are ready!")
                
                # 5. Download Button
                st.download_button(
                    label="📥 Download ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=f"Cleaned_Split_by_{split_column}.zip",
                    mime="application/zip"
                )