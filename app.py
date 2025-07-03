import streamlit as st
import pandas as pd
import io
import requests

# --- Safe rerun helper ---
def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            st.error("Streamlit version too old for rerun support.")
            st.stop()

# --- Simple session-based login ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## 🔒 Secure Access")
    password_input = st.text_input("Enter Password:", type="password")

    if password_input:
        if password_input == st.secrets["password"]:
            st.session_state.authenticated = True
            safe_rerun()
        else:
            st.warning("Invalid password")
    st.stop()

# --- Load Excel file from GitHub ---
@st.cache_data
def load_data():
    url = "https://github.com/manojcpatil-students/PRERNA/raw/main/SurveyData.xlsx"
    response = requests.get(url)
    xls = pd.ExcelFile(io.BytesIO(response.content))
    main_df = pd.read_excel(xls, sheet_name=0)
    return main_df

df = load_data()
df["Priority"] = df["Priority"].replace({1: "Top", 2: "Moderate", 3: "Less"})

st.title("📊 Record of Deceased Farmers with Codes")

# --- Mandatory columns ---
mandatory_columns = [
    "farmer_id", "Priority", "farmers_name_marathi",
    "village_marathi", "taluka_marathi", "informant_name", "informant_mobile"
]

# --- Support columns from "Support" sheet ---
support_columns = [
    "Widow (Needy)", "Dependents", "Job/Support", "OldAge",
    "Child Edu", "Marriage", "Business / Shop", "Poultry", "Goat", "Dairy",
    "Garkul", "Health", "AgriEqui", "Shivankam", "Psychological", "SpecialChild"
]

# --- STEP 1: Apply support filters ---
st.sidebar.header("🧩 Support Filter (Non-empty)")
selected_support_columns = st.sidebar.multiselect(
    "Select Support Criteria (non-empty rows only)",
    [col for col in support_columns if col in df.columns]
)

filtered_df = df.copy()
for col in selected_support_columns:
    if col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[col].notna() & (filtered_df[col] != "")]


# --- STEP 3: Apply other filters ---
st.sidebar.header("🔍 Primary Filter Criteria")
filter_column = st.sidebar.selectbox("Choose column to filter by", filtered_df.columns)
unique_values = filtered_df[filter_column].dropna().unique()
selected_values = st.sidebar.multiselect(f"Select value(s) from '{filter_column}'", unique_values)

# --- STEP 2: Column selection (excluding mandatory) ---
st.sidebar.header("📁 Columns to Export (Excluding Mandatory)")
search_term = st.sidebar.text_input("🔎 Search optional columns", "")

available_optional_columns = [col for col in filtered_df.columns if col not in mandatory_columns]
matching_cols = [col for col in available_optional_columns if search_term.lower() in col.lower()]

selected_columns = []
for col in matching_cols:
    if st.sidebar.checkbox(col, value=False, key=col):
        selected_columns.append(col)

if selected_values:
    filtered_df = filtered_df[filtered_df[filter_column].isin(selected_values)]

taluka_values = filtered_df['taluka_marathi'].dropna().unique()
selected_talukas = st.sidebar.multiselect("Select taluka(s)", taluka_values)

if selected_talukas:
    filtered_df = filtered_df[filtered_df["taluka_marathi"].isin(selected_talukas)]

# --- STEP 4: Finalize export columns ---
final_columns = mandatory_columns + selected_columns
final_columns = [col for col in final_columns if col in filtered_df.columns]
export_df = filtered_df[final_columns]

# --- Show results ---
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
