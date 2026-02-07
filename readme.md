#  Universal CSV Splitter & Cleaner

This is a lightweight web application built with **Python** and **Streamlit** that allows you to break down large CSV files into multiple smaller files based on a specific column's values.

##  Features
- **Smart Splitting**: Choose any column from your CSV to group data into separate files.
- **Data Privacy**: Select specific columns to **exclude** from the output files (perfect for hiding internal data).
- **Large File Support**: Configured to handle file uploads up to **600MB**.
- **Instant ZIP**: Processes all files in-memory and provides a single ZIP download.
- **Data Preview**: View your data immediately after uploading to ensure everything looks correct.

##  How to Use
1. **Upload**: Drag and drop your `.csv` file into the uploader.
2. **Preview**: Check the data table to confirm the headers are correct.
3. **Configure**:
   - Select the **Split Column** (e.g., `Customer Name`).
   - (Optional) Choose columns to **Exclude** from the final reports.
4. **Generate**: Click the "Generate & Download" button.
5. **Download**: Once processed, click the button to save the `.zip` file to your computer.

##  Local Installation
If you want to run this locally on your own machine:

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
