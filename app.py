import streamlit as st
import pandas as pd
import io
import requests

# --- Load Excel file from GitHub ---
@st.cache_data
def load_data():
    url = "https://github.com/manojcpatil-students/PRERNA/raw/main/SurveyData.xlsx"
    response = requests.get(url)
    return pd.read_excel(io.BytesIO(response.content))

df = load_data()

st.title("📊 Filter & Export Survey Data")

# --- Column filter selection ---
st.sidebar.header("🔍 Filter Criteria")
filter_column = st.sidebar.selectbox("Choose column to filter by", df.columns)

unique_values = df[filter_column].dropna().unique()
selected_values = st.sidebar.multiselect(f"Select value(s) from '{filter_column}'", unique_values)

# --- Column selection for export ---
st.sidebar.header("📁 Columns to Export")
selected_columns = st.sidebar.multiselect("Choose columns to include in Excel", df.columns, default=df.columns.tolist())

# --- Apply filters ---
if selected_values:
    filtered_df = df[df[filter_column].isin(selected_values)]
else:
    filtered_df = df.copy()

# --- Subset selected columns ---
export_df = filtered_df[selected_columns] if selected_columns else filtered_df

# --- Display table ---
st.write(f"### Showing {len(export_df)} records")
st.dataframe(export_df)

# --- Export as Excel ---
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='FilteredData')
    return output.getvalue()

excel_data = convert_df_to_excel(export_df)
st.download_button(
    label="📥 Download Filtered Data as Excel",
    data=excel_data,
    file_name="filtered_survey_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
