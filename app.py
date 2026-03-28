import streamlit as st
import pandas as pd
import os
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Job Application Tracker", page_icon="💼", layout="wide")

DATA_FILE = "jobs.csv"

# --- HELPER FUNCTIONS ---
def init_db():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["ID", "Company Name", "Role", "Status", "Date Applied", "Notes"])
        df.to_csv(DATA_FILE, index=False)

def load_data():
    init_db()
    try:
        df = pd.read_csv(DATA_FILE)
        if 'ID' in df.columns:
            df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
        return df
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=["ID", "Company Name", "Role", "Status", "Date Applied", "Notes"])
        save_data(df)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- APP UI ---
st.title("💼 Job Application Tracker")
st.markdown("### Manage your job search seamlessly")

df = load_data()

# --- SIDEBAR (FILTERS & SELECTION) ---
with st.sidebar:
    st.header("🎛️ Filters")
    status_filter = st.selectbox("Filter by Status", ["All", "Applied", "Interview", "Offer", "Rejected"])
    search_query = st.text_input("Search Company or Role").lower()
    
# --- DASHBOARD METRICS ---
st.header("📊 Dashboard")
col1, col2, col3, col4 = st.columns(4)

total_jobs = len(df)
total_interviews = len(df[df["Status"] == "Interview"])
total_offers = len(df[df["Status"] == "Offer"])
total_rejections = len(df[df["Status"] == "Rejected"])

col1.metric(label="Total Applications 📝", value=total_jobs)
col2.metric(label="Interviews 🗣️", value=total_interviews)
col3.metric(label="Offers 🎉", value=total_offers)
col4.metric(label="Rejections ❌", value=total_rejections)

st.divider()

# --- MAIN LAYOUT (TABS) ---
tab_add, tab_view, tab_charts = st.tabs(["➕ Add Job", "📄 View & Manage", "📈 Analytics"])

with tab_add:
    st.subheader("Add New Application")
    with st.form("job_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            company = st.text_input("Company Name *")
            role = st.text_input("Role *")
        with c2:
            status = st.selectbox("Status *", ["Applied", "Interview", "Offer", "Rejected"])
            date_applied = st.date_input("Date Applied *", datetime.date.today())
        
        notes = st.text_area("Notes (Optional)")
        submit_btn = st.form_submit_button("Save Application")
        
        if submit_btn:
            if company and role:
                new_id = 1 if df.empty or pd.isna(df["ID"].max()) else int(df["ID"].max()) + 1
                new_record = {
                    "ID": new_id,
                    "Company Name": company,
                    "Role": role,
                    "Status": status,
                    "Date Applied": date_applied.strftime("%Y-%m-%d"),
                    "Notes": notes
                }
                new_df = pd.DataFrame([new_record])
                df = pd.concat([df, new_df], ignore_index=True)
                save_data(df)
                st.success("✅ Application saved successfully!")
                st.rerun()
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

with tab_view:
    st.subheader("Job Applications")
    
    filtered_df = df.copy()
    if search_query:
        query = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["Company Name"].astype(str).str.lower().str.contains(query) |
            filtered_df["Role"].astype(str).str.lower().str.contains(query)
        ]
        
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]
    
    if filtered_df.empty:
        st.info("No applications found matching your criteria.")
    else:
        st.dataframe(
            filtered_df.drop(columns=["ID"]), 
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        st.subheader("⚙️ Manage Applications")
        
        manage_options = ["Select a job..."] + [
            f"{row['Company Name']} - {row['Role']} (ID: {row['ID']})" 
            for _, row in filtered_df.iterrows()
        ]
        
        selected_manage = st.selectbox("Choose a job to edit or delete", manage_options)
        
        if selected_manage != "Select a job...":
            job_id_str = selected_manage.split("ID: ")[-1].replace(")", "")
            try:
                job_id_to_manage = int(float(job_id_str))
                job_row = df[df["ID"] == job_id_to_manage].iloc[0]
                
                edit_col1, edit_col2 = st.columns(2)
                
                with edit_col1:
                    st.write("**✏️ Edit Status**")
                    status_list = ["Applied", "Interview", "Offer", "Rejected"]
                    current_status = job_row["Status"]
                    status_index = status_list.index(current_status) if current_status in status_list else 0
                    
                    new_status = st.selectbox("Update Status", status_list, index=status_index, label_visibility="collapsed")
                    if st.button("Update Status", type="primary", key="update_btn"):
                        df.loc[df["ID"] == job_id_to_manage, "Status"] = new_status
                        save_data(df)
                        st.success("✅ Status updated successfully!")
                        st.rerun()
                        
                with edit_col2:
                    st.write("**🗑️ Delete Application**")
                    st.write("Warning: This action cannot be undone.")
                    if st.button("Delete Job", type="primary", key="delete_btn"):
                        df = df[df["ID"] != job_id_to_manage]
                        save_data(df)
                        st.success("✅ Job deleted successfully!")
                        st.rerun()
            except ValueError:
                st.error("Error parsing Job ID.")

with tab_charts:
    st.subheader("Application Status Distribution")
    if df.empty:
        st.info("Add some jobs to see your analytics!")
    else:
        chart_data = df["Status"].value_counts().reset_index()
        chart_data.columns = ["Status", "Count"]
        
        st.bar_chart(data=chart_data, x="Status", y="Count", color="#4CAF50")
