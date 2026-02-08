import streamlit as st
import polars as pl
import io
import zipfile
import re

# Page Config
st.set_page_config(page_title="Ultra-Fast CSV Splitter", page_icon="⚡", layout="wide")

# --- SIDEBAR PRIVACY NOTICE ---
with st.sidebar:
    st.header("Privacy & Security")
    st.info("Your data is processed in-memory. **We don't store your data.**")

st.caption("by Asrol")
st.title(" CSV Splitter")
st.markdown("Optimized for speed. Pick your column, check the file count, and split.")
st.divider()

def clean_filename(name):
    """Removes invalid characters for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "-", str(name)).strip()

# 1. File Uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        # Polars read_csv is significantly faster for 600MB+ files
        return pl.read_csv(file)

    try:
        df = load_data(uploaded_file)
        
        st.subheader("👀 Data Preview")
        # Polars head(5) needs to be converted to pandas just for Streamlit display
        st.dataframe(df.head(5).to_pandas(), use_container_width=True)
        
        # 2. Dynamic Selection Controls
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
                options=[c for c in all_columns if c != split_column],
                help="Selected columns will be removed from all generated files."
            )
        
        # --- THE PREVIEW LOGIC ---
        if split_column:
            # Polars n_unique() is highly optimized
            num_unique = df[split_column].n_unique()
            cols_remaining = len(all_columns) - len(exclude_cols)
            
            st.info(f"Ready to create **{num_unique}** files. Columns being kept: **{cols_remaining}**")

            # 3. Processing Logic
            if st.button("🚀 Fast Generate & Download ZIP"):
                with st.spinner("Polars is multi-threading your data..."):
                    zip_buffer = io.BytesIO()
                    
                    # Drop excluded columns
                    processed_df = df.drop(exclude_cols)
                    
                    # Grouping data efficiently
                    partitions = processed_df.partition_by(split_column, as_dict=True)
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for value, group_df in partitions.items():
                            # Handle potential tuple return from partition_by
                            file_label = str(value[0]) if isinstance(value, tuple) else str(value)
                            
                            # Convert each group to CSV bytes
                            csv_bytes = group_df.write_csv().encode('utf-8')
                            
                            file_name = f"{clean_filename(file_label)}.csv"
                            zip_file.writestr(file_name, csv_bytes)

                    st.success(f"✅ Successfully created {len(partitions)} files!")
                    
                    # 4. Download Button
                    st.download_button(
                        label="📥 Download ZIP",
                        data=zip_buffer.getvalue(),
                        file_name=f"Split_by_{split_column}.zip",
                        mime="application/zip"
                    )

    except Exception as e:
        st.error(f"Error processing file: {e}")

# --- FOOTER ---
st.divider()
st.caption("Privacy Guarantee: We don't store your data. All processing happens live.")
