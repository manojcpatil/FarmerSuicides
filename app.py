import streamlit as st
import pandas as pd
import io
import requests

# --- Simple password protection for Streamlit Cloud ---
def login():
    st.markdown("## 🔒 Secure Access")
    password_input = st.text_input("Enter Password:", type="password")
    if password_input != st.secrets["password"]:
        st.warning("Invalid password")
        st.stop()

login()


# --- Load Excel file from GitHub ---
@st.cache_data
def load_data():
    url = "https://github.com/manojcpatil-students/PRERNA/raw/main/SurveyData.xlsx"
    response = requests.get(url)
    return pd.read_excel(io.BytesIO(response.content))

df = load_data()

st.title("📊 Record of Deceased Farmers with Codes")

# --- Mandatory columns (always included in export) ---
mandatory_columns = [
    "farmer_id", "Priority", "farmers_name_marathi",
    "village_marathi", "taluka_marathi", "informant_name", "informant_mobile"
]

# --- Sidebar filter options ---
st.sidebar.header("🔍 Primary Filter Criteria")
filter_column = st.sidebar.selectbox("Choose column to filter by", df.columns)

unique_values = df[filter_column].dropna().unique()
selected_values = st.sidebar.multiselect(f"Select value(s) from '{filter_column}'", unique_values)

# --- Additional filters: village and taluka ---
# st.sidebar.header("🏡 Additional Filters")
# village_values = df['village_marathi'].dropna().unique()
# selected_villages = st.sidebar.multiselect("Select village(s)", village_values)

taluka_values = df['taluka_marathi'].dropna().unique()
selected_talukas = st.sidebar.multiselect("Select taluka(s)", taluka_values)

# --- Search + checkbox for export column selection ---
st.sidebar.header("📁 Optional Columns to Export")
search_term = st.sidebar.text_input("🔎 Search optional columns", "")

optional_cols = [col for col in df.columns if col not in mandatory_columns]
matching_cols = [col for col in optional_cols if search_term.lower() in col.lower()]

selected_columns = []
for col in matching_cols:
    if st.sidebar.checkbox(col, value=False, key=col):  # Optional columns not selected by default
        selected_columns.append(col)

# --- Apply filters ---
filtered_df = df.copy()

if selected_values:
    filtered_df = filtered_df[filtered_df[filter_column].isin(selected_values)]

#if selected_villages:
#    filtered_df = filtered_df[filtered_df["village_marathi"].isin(selected_villages)]

if selected_talukas:
    filtered_df = filtered_df[filtered_df["taluka_marathi"].isin(selected_talukas)]

# --- Final columns for export ---
final_columns = mandatory_columns + selected_columns
final_columns = [col for col in final_columns if col in filtered_df.columns]
export_df = filtered_df[final_columns]

# --- Show filtered data ---
st.write(f"### Showing {len(export_df)} records")
st.dataframe(export_df)

# --- Export to Excel ---
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
