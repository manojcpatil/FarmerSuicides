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

# --- Session-based login ---
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

# --- Update load_data to return additional sheets ---
@st.cache_data
def load_data():
    url = "https://github.com/manojcpatil-students/PRERNA/raw/main/SurveyData.xlsx"
    response = requests.get(url)
    xls = pd.ExcelFile(io.BytesIO(response.content))
    main_df = pd.read_excel(xls, sheet_name=0)
    
    # Load additional sheets if needed later
    job_df = pd.read_excel(xls, sheet_name="JobSupport")
    health_df = pd.read_excel(xls, sheet_name="Health support")
    
    return main_df, job_df, health_df

df, job_support_df, health_support_df = load_data()
df["Priority"] = df["Priority"].replace({1: "Top", 2: "Moderate", 3: "Less"})

# --- Column definitions ---
mandatory_columns = [
    "farmer_id", "Priority", "farmers_name_marathi",
    "village_marathi", "taluka_marathi", "informant_name", "informant_mobile"
]

support_columns = [
    "Widow (Needy)", "Job/Support", "OldAge",
    "Child Edu", "Marriage", "Business / Shop", "Poultry", "Goat", "Dairy",
    "Garkul", "Health", "AgriEqui", "Shivankam", "Psychological", "SpecialChild"
]

# --- Support filter ---
st.sidebar.header("🧩 Support Filter")

# Add "All" at the top of the list
support_options = ["All"] + [col for col in support_columns if col in df.columns]

support_col = st.sidebar.selectbox(
    "Select Support Criteria",
    support_options
)

# Apply filter only if user selected a specific support column
if support_col != "All":
    filtered_df = df[df[support_col].notna() & (df[support_col] != "")].copy()
else:
    filtered_df = df.copy()

st.title("📊 Record of Deceased Farmers: "+str(support_col)+" Support")

# --- Primary filter ---
st.sidebar.header("🔍 Primary Filter Criteria")
filter_column = st.sidebar.selectbox("Choose column to filter by", filtered_df.columns)
unique_values = filtered_df[filter_column].dropna().unique()
selected_values = st.sidebar.multiselect(f"Select value(s) from '{filter_column}'", unique_values)

if selected_values:
    filtered_df = filtered_df[filtered_df[filter_column].isin(selected_values)]

# --- Taluka filter ---
taluka_values = filtered_df['taluka_marathi'].dropna().unique()
selected_talukas = st.sidebar.multiselect("Select taluka(s)", taluka_values)

if selected_talukas:
    filtered_df = filtered_df[filtered_df["taluka_marathi"].isin(selected_talukas)]

# --- Column selection ---
st.sidebar.header("📁 Columns to Export (Excluding Mandatory)")
search_term = st.sidebar.text_input("🔎 Search optional columns", "")
available_optional_columns = [col for col in filtered_df.columns if col not in mandatory_columns]
matching_cols = [col for col in available_optional_columns if search_term.lower() in col.lower()]

selected_columns = [
    col for col in matching_cols
    if st.sidebar.checkbox(col, value=False, key=col)
]


# --- Conditionally show additional sheet based on support_col ---
if support_col == "Job/Support":
    st.subheader("🧾 Additional Information: Job Support Details")
    st.dataframe(job_support_df)
    
    job_excel = convert_df_to_excel(job_support_df)
    st.download_button(
        label="📥 Download Job Support Table",
        data=job_excel,
        file_name="job_support_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif support_col == "Health":
    st.subheader("🧾 Additional Information: Health Support Details")
    st.dataframe(health_support_df)
    
    health_excel = convert_df_to_excel(health_support_df)
    st.download_button(
        label="📥 Download Health Support Table",
        data=health_excel,
        file_name="health_support_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- Finalize and display ---
final_columns = mandatory_columns + selected_columns
final_columns = [col for col in final_columns if col in filtered_df.columns]
export_df = filtered_df[final_columns]

st.write(f"### Showing {len(export_df)} records")
st.dataframe(export_df)

# --- Excel export ---
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
