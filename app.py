import streamlit as st
import polars as pl
import io
import zipfile
import re

# Page Config
st.set_page_config(page_title="Ultra-Fast CSV Splitter", page_icon="⚡", layout="wide")

# --- SIDEBAR PRIVACY NOTICE ---
with st.sidebar:
    st.header("🔒 Privacy & Security")
    st.info("Your data is processed in-memory using Polars (Rust-backed) and is **not stored**.")

st.caption("by Asrol")
st.title("⚡ Ultra-Fast CSV Splitter (Polars Edition)")
st.markdown("Optimized for large files. Process 600MB+ in seconds without external servers.")
st.divider()

def clean_filename(name):
    """Removes invalid characters for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "-", str(name)).strip()

# 1. File Uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    # 2. Read Data with Polars (Much faster than pd.read_csv)
    # We wrap this in a cache so it doesn't re-read on every button click
    @st.cache_data
    def load_data(file):
        return pl.read_csv(file)

    try:
        df = load_data(uploaded_file)
        
        st.subheader("👀 Data Preview")
        st.dataframe(df.head(5).to_pandas(), use_container_width=True)
        
        # 3. Dynamic Selection Controls
        st.divider()
        col1, col2 = st.columns(2)
        all_columns = df.columns
        
        with col1:
            split_column = st.selectbox("1. Which column determines the split?", options=all_columns)
        
        with col2:
            exclude_cols = st.multiselect(
                "2. Columns to EXCLUDE", 
                options=[c for c in all_columns if c != split_column]
            )
        
        # 4. Processing Logic
        if st.button("🚀 Fast Generate & Download"):
            with st.spinner("Polars is multi-threading your data..."):
                zip_buffer = io.BytesIO()
                
                # Drop columns efficiently
                processed_df = df.drop(exclude_cols)
                
                # Polars 'partition_by' is significantly faster than a Python for-loop
                # It splits the dataframe into a list of dataframes in one go
                partitions = processed_df.partition_by(split_column, as_dict=True)
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for value, group_df in partitions.items():
                        # value is a tuple because partition_by supports multiple columns
                        file_label = str(value[0]) if isinstance(value, tuple) else str(value)
                        
                        # Convert to CSV bytes directly from Polars
                        csv_bytes = group_df.write_csv().encode('utf-8')
                        
                        file_name = f"{clean_filename(file_label)}.csv"
                        zip_file.writestr(file_name, csv_bytes)

                st.success(f"✅ Created {len(partitions)} files instantly!")
                
                st.download_button(
                    label="📥 Download ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=f"Split_by_{split_column}.zip",
                    mime="application/zip"
                )

    except Exception as e:
        st.error(f"Error loading file: {e}")

# --- FOOTER ---
st.divider()
st.caption("Privacy Guarantee: We don't store your data. All processing happens live.")
