import os
import time
import datetime
import random
import base64
import io
import traceback

import streamlit as st
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from contextlib import contextmanager  # for any local context managers

from database_pool import get_db_cursor, db_pool  # ↪ use the Postgres pool!

# Streamlit page config
st.set_page_config(
    page_title="CQ Resume Portal",
    page_icon='./Logo/logo2.png',
)

# ========== PERFORMANCE MONITORING ==========

# def timing_decorator(func):
#     def wrapper(*args, **kwargs):
#         start = time.time()
#         result = func(*args, **kwargs)
#         elapsed = (time.time() - start) * 1000
#         if st.session_state.get('show_performance', False):
#             st.sidebar.text(f"• {func.__name__}: {elapsed:.2f}ms")
#         return result
#     return wrapper

# @st.cache_data(ttl=60)
# def get_app_performance_stats():
#     return {"cache_hits": st.cache_data.clear.__doc__,
#             "timestamp": datetime.datetime.now()}

def timing_decorator(func):
    """Dummy decorator - performance monitoring disabled"""
    return func

@st.cache_resource
def get_cached_db_pool():
    return db_pool

@timing_decorator
@st.cache_data(ttl=300)
def load_reviewer_names():
    with get_db_cursor() as (_, cur):
        cur.execute("SELECT DISTINCT name FROM reviewer_data ORDER BY name;")
        return [r["name"] for r in cur.fetchall()]

@st.cache_data(ttl=300)
def load_profiles():
    return ['Data', 'Software', 'Consult', 'Finance-Quant', 'Product', 'FMCG']

@timing_decorator
@st.cache_data(show_spinner=False)
def pdf_to_base64(path: str):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        return None

@timing_decorator
@st.cache_data(ttl=60)
def get_reviewer_info(name: str):
    with get_db_cursor() as (_, cur):
        cur.execute("""
            SELECT reviewsnumber, rprofilez, linkedin, email
            FROM reviewer_data WHERE UPPER(name)=UPPER(%s);
        """, (name,))
        return cur.fetchone()

@timing_decorator
@st.cache_data(ttl=60)
def get_reviewer_count(name: str):
    with get_db_cursor() as (_, cur):
        cur.execute("SELECT COUNT(*) AS cnt FROM reviews_data WHERE reviewer_name=%s;", (name,))
        return cur.fetchone()['cnt']

def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'

def show_pdf(path):
    b64 = pdf_to_base64(path)
    if b64:
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="700" height="1000"></iframe>',
                    unsafe_allow_html=True)
    else:
        st.warning("PDF preview unavailable.")

# def course_recommender(course_list):
#     st.subheader("**Courses & Certificates Recommendations 🎓**")
#     c = 0
#     rec_course = []
#     no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
#     random.shuffle(course_list)
#     for c_name, c_link in course_list:
#         c += 1
#         st.markdown(f"({c}) [{c_name}]({c_link})")
#         rec_course.append(c_name)
#         if c == no_of_reco:
#             break
#     return rec_course

#CONNECT TO DATABASE

load_dotenv()

def insert_data_simple(name, roll_no, email, drive_link, profile):
    """Optimized user data insertion"""
    insert_sql = """
        INSERT INTO user_data (Name, Roll_No, Email_ID, drive_link, status_num, profiles)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with get_db_cursor() as (_, cursor):  # ✅ Uses context manager
        cursor.execute(insert_sql, (name, roll_no, email, drive_link, 1, profile))
        # ✅ No manual commit/rollback - context manager handles it

def insert_data_reviewers(name, pwd, reviewsnum, cvsreviewed, linkedin, email, rprofilez=None):
    """Optimized reviewer insertion - now uses Name instead of UserName"""
    insert_sql = """
        INSERT INTO reviewer_data (Name, Password, ReviewsNumber, Cvsreviewed, LinkedIn, Email, Rprofilez)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    with get_db_cursor() as (_, cursor):
        cursor.execute(insert_sql, (name, pwd, reviewsnum, cvsreviewed, linkedin, email, rprofilez))

# Keep legacy function for backward compatibility but redirect to optimized version
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses, drive_link, status, profile):
    """Legacy function - maintained for compatibility"""
    if name and email and drive_link and profile:
        insert_data_simple(name, email, email, drive_link, profile)
    else:
        st.error("Missing required fields for user data insertion")

def init_db():
    """Initialize database and tables once at startup"""
    with get_db_cursor() as (_, cursor):  # ✅ Uses context manager
        # Create the database
        cursor.execute("CREATE DATABASE IF NOT EXISTS cdc_companion")
        cursor.execute("USE cdc_companion")

        # Create user_data table with assigned_to column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(500) NOT NULL,
                Roll_No VARCHAR(10) NOT NULL,
                Email_ID VARCHAR(500),
                drive_link VARCHAR(500),
                status_num INT DEFAULT 0,
                profiles VARCHAR(500),
                assigned_to VARCHAR(30) NULL,
                submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_assigned_to (assigned_to),
                INDEX idx_status_profile (status_num, profiles)
            )
        """)

        # Create reviewer_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviewer_data (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(500) NOT NULL UNIQUE,
                Password VARCHAR(30) NOT NULL,
                ReviewsNumber INT NOT NULL,
                Cvsreviewed INT NOT NULL DEFAULT 0,
                LinkedIn VARCHAR(500),
                Email VARCHAR(500),
                Rprofilez VARCHAR(500),
                INDEX idx_name (Name)
            )
        """)

        # Create reviews_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(255),
                Roll_No VARCHAR(10),
                Email_ID VARCHAR(255),
                Reviewer_Name VARCHAR(255),
                Reviewer_LinkedIn VARCHAR(500),
                Reviewer_Email VARCHAR(500),
                Drive_Link VARCHAR(255),
                Review TEXT,
                submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_roll_reviewer (Roll_No, Reviewer_Name)
            )
        """)
        # ✅ No manual commit needed - context manager handles it

def display_error_details(error_msg, exception):
    """Display detailed error information for debugging"""
    st.error(f"💥 {error_msg}")
    st.exception(exception)  # Shows full traceback in Streamlit
    print(f"\n{'='*50}")
    print(f"ERROR: {error_msg}")
    print(f"{'='*50}")
    print(traceback.format_exc())  # Logs to console
    print(f"{'='*50}\n")

def run():
    # Initialize both session state keys at the very top
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'admin_user' not in st.session_state:
        st.session_state.admin_user = ""
    # if 'show_performance' not in st.session_state:
    #     st.session_state.show_performance = False
    
    img = Image.open('./Logo/CQlogo2.png')
    img = img.resize((1000, 300))
    st.image(img)
    st.title("Communiqué - CV Portal")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Reviewer" ,"Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
    # Performance monitoring section in sidebar
    # st.sidebar.markdown("---")
    # st.sidebar.markdown("### 🔧 Debug Tools")
    # st.session_state.show_performance = st.sidebar.checkbox(
    #     "Show Performance Metrics", 
    #     value=st.session_state.show_performance,
    #     help="Display execution times for database queries and other operations"
    # )
    
    # if st.session_state.show_performance:
    #     st.sidebar.markdown("**Performance Metrics:**")
    #     if 'performance_metrics' not in st.session_state:
    #         st.session_state.performance_metrics = {}
    
    link = '[Developed by ©Communiqué](https://www.cqiitkgp.com/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)


    # ✅ No DB initialization here - done once at startup
    # Continue with UI logic...

    if choice == 'User':
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Enter your Name:", placeholder="Jhonny Bravo")
        with col2:
            roll_no = st.text_input("Enter your Roll Number:", placeholder="22XX9999")
        
        if name and roll_no:
            st.markdown('''
                <h3 style='text-align: left; color: #FF4B4B; margin-top: 20px; margin-bottom: 20px;'>
                    📄 Drop your Resume here to get it reviewed by seniors
                </h3>
                <p style='text-align: left; color: #FFF; font-size: 16px;'>
                    Get personalized feedback from seniors in your chosen field
                </p>
                ''', unsafe_allow_html=True)
            
            pdf_file = st.file_uploader("Upload your Resume (PDF format)", type=["pdf"])
            if pdf_file is not None and roll_no:
                # Enforce 2 MB max
                if pdf_file.size > 2 * 1024 * 1024:
                    st.error("🚨 File too large—please upload a PDF under 2 MB.")
                else:
                    # Always save as <roll_no>.pdf so display_code can find it
                    save_path = f'./Uploaded_Resumes/{roll_no}.pdf'
                    with st.spinner('Processing your Resume...'):
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(pdf_file.getbuffer())
                    show_pdf(save_path)

            # Move profile selection here, after file upload and preview
            profile = st.selectbox("Select your target profile:", load_profiles(), 
                                 help="Choose the profile you're interested in for your career")
            
            st.markdown(
                """
                <div style='background-color: #1E1E1E; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                    <h2 style='color: #FF4B4B;'>Almost there! 🎯</h2>
                    <p style='color: #FFF; font-size: 16px;'>Please provide your contact details below to receive your review.</p>
                    <p style='color: #888; font-size: 14px;'>Note: You can submit only one CV for review</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

            # ✅ FIXED: Always show inputs, check duplicates only on Submit
            st.write("( Make sure you have provided access to your CV in the drive link )")
            email_input = st.text_input("Enter your KGP EmailID here: ")
            drive_link = st.text_input("Enter your Drive Link: ")
            
            if st.button("Submit for Review", type="primary"):
                try:
                    # 1️⃣ Check duplicates only now
                    with get_db_cursor() as (_, cursor):
                        cursor.execute(
                            "SELECT status_num FROM user_data WHERE Roll_No = %s",
                            (roll_no,)
                        )
                        status_row = cursor.fetchone()

                    if status_row and status_row['status_num'] == 1:
                        st.warning(f"⚠️ You have already submitted a CV for review.")
                        st.info("💡 Each student may only submit once.")

                    # 2️⃣ Not a duplicate → proceed
                    elif email_input and drive_link:
                        insert_data_simple(name, roll_no, email_input, drive_link, profile)
                        
                        # ✅ Persistent success message
                        st.success("🎉 **CV Submission Successful!**")
                        st.markdown(
                            f"""
                            <div style='background-color: #1E3A8A; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                                <h3 style='color: #60A5FA; margin-bottom: 15px; text-align: center;'>✅ Thank you, {name}!</h3>
                                <div style='color: #FFF; font-size: 16px; text-align: center;'>
                                    <p><strong>Your CV for the {profile} profile has been submitted successfully!</strong></p>
                                    <p>📧 You'll receive detailed feedback from our expert reviewers soon.</p>
                                    <p style='color: #60A5FA;'>💡 You will receive an email soon with your review!</p>
                                </div>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        st.balloons()
                        
                    else:
                        st.error("Please provide both email and drive link.")

                except Exception as e:
                    display_error_details("CV submission failed", e)
    elif choice == 'Admin':
        # First check session state
        if not st.session_state.admin_logged_in:
            st.success('Welcome to Admin Side')
            user = st.text_input("Username", key="admin_user_input")
            pwd = st.text_input("Password", type="password", key="admin_pass_input")
            if st.button("Login"):
                if user == "sujay" and pwd == "sujay123":
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = user
                    st.rerun()
                else:
                    st.error("Wrong ID & Password")
            return  # Don't render anything else until they're logged in

        # ---- LOGGED IN! ----
        st.success(f"Welcome {st.session_state.admin_user}!")
        
        # Logout button
        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        # 1) Always re-fetch your tables here
        with get_db_cursor() as (_, cursor):
            try:
                # 📊 EDITABLE USER DATA
                st.header("**User's Data (Editable)**")
                cursor.execute("""
                    SELECT
                        ID,
                        Name,
                        Roll_No,
                        Email_ID,
                        drive_link,
                        status_num,
                        profiles,
                        assigned_to
                    FROM user_data
                """)
                user_data = cursor.fetchall()
                user_df = pd.DataFrame(user_data, columns=[
                    'ID', 'Name', 'Roll_No', 'Email_ID', 'drive_link', 
                    'status_num', 'profiles', 'assigned_to'
                ])

                # Get list of reviewers for the dropdown
                reviewer_names = load_reviewer_names()
                
                # Configure column types for better editing experience
                column_config = {
                    "ID": st.column_config.NumberColumn("ID", disabled=True),
                    "status_num": st.column_config.SelectboxColumn(
                        "Status",
                        options=[0, 1, 2],
                        help="0=Submitted, 1=Pending Review, 2=Reviewed"
                    ),
                    "profiles": st.column_config.SelectboxColumn(
                        "Profile",
                        options=load_profiles()
                    ),
                    "assigned_to": st.column_config.TextColumn(
                        "Assigned To",
                        help="Reviewer who has claimed this CV"
                    ),
                    "drive_link": st.column_config.LinkColumn("Drive Link"),
                }

                # 2) Show the editor
                edited_user_df = st.data_editor(
                    user_df,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="user_data_editor"
                )

                # 3) Save button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save User Data Changes", type="primary"):
                        try:
                            # 🔧 FIX: Normalize ID columns to handle int/float mismatch
                            original_ids = set(user_df['ID'].tolist())
                            edited_ids = {
                                int(x) for x in edited_user_df['ID'].tolist()
                                if not pd.isna(x)
                            }
                            deleted_ids = original_ids - edited_ids
                            
                            # Delete removed rows
                            for deleted_id in deleted_ids:
                                cursor.execute("DELETE FROM user_data WHERE ID = %s", (deleted_id,))
                            
                            # Update/Insert rows
                            for _, row in edited_user_df.iterrows():
                                if pd.isna(row['ID']):
                                    # New row - INSERT
                                    cursor.execute("""
                                        INSERT INTO user_data (Name, Roll_No, Email_ID, drive_link, status_num, profiles, assigned_to)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, (row['Name'], row['Roll_No'], row['Email_ID'], row['drive_link'], 
                                          row['status_num'], row['profiles'], row['assigned_to']))
                                else:
                                    # Existing row - UPDATE
                                    cursor.execute("""
                                        UPDATE user_data 
                                        SET Name=%s, Roll_No=%s, Email_ID=%s, drive_link=%s, 
                                            status_num=%s, profiles=%s, assigned_to=%s
                                        WHERE ID=%s
                                    """, (row['Name'], row['Roll_No'], row['Email_ID'], row['drive_link'],
                                          row['status_num'], row['profiles'], row['assigned_to'], int(row['ID'])))
                            
                            st.success("✅ User data saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving user data: {e}")

                with col2:
                    st.markdown(get_table_download_link(edited_user_df,'User_Data.csv','📥 Download User Data'), unsafe_allow_html=True)

                st.markdown("---")

                # 👥 EDITABLE REVIEWER DATA  
                st.header("**Reviewer's Data (Editable)**")
                cursor.execute("""
                    SELECT
                        rd.ID,
                        rd.Name,
                        rd.Password,
                        rd.ReviewsNumber,
                        COALESCE(rv.cnt, 0) AS Cvsreviewed,
                        rd.LinkedIn,
                        rd.Email,
                        rd.Rprofilez
                    FROM reviewer_data rd
                    LEFT JOIN (
                        SELECT Reviewer_Name, COUNT(*) AS cnt
                        FROM reviews_data
                        GROUP BY Reviewer_Name
                    ) rv
                    ON rv.Reviewer_Name = rd.Name
                """)
                reviewer_data = cursor.fetchall()
                reviewer_df = pd.DataFrame(reviewer_data, columns=[
                    'ID', 'Name', 'Password', 'ReviewsNumber', 'Cvsreviewed', 'LinkedIn', 'Email', 'Rprofilez'
                ])

                reviewer_column_config = {
                    "ID": st.column_config.NumberColumn("ID", disabled=True),
                    "ReviewsNumber": st.column_config.NumberColumn("Review Quota", min_value=0, max_value=100),
                    "Cvsreviewed": st.column_config.NumberColumn("CVs Reviewed", min_value=0, disabled=True),
                    "Rprofilez": st.column_config.SelectboxColumn(
                        "Domain",
                        options=load_profiles()
                    ),
                    "LinkedIn": st.column_config.LinkColumn("LinkedIn Profile"),
                    "Email": st.column_config.TextColumn("Email"),
                    "Password": st.column_config.TextColumn("Password", help="Reviewer login password")
                }

                edited_reviewer_df = st.data_editor(
                    reviewer_df,
                    column_config=reviewer_column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="reviewer_data_editor"
                )

                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Reviewer Data Changes", type="primary"):
                        try:
                            # 🔧 FIX: Normalize ID columns
                            original_ids = set(reviewer_df['ID'].tolist())
                            edited_ids = {
                                int(x) for x in edited_reviewer_df['ID'].tolist()
                                if not pd.isna(x)
                            }
                            deleted_ids = original_ids - edited_ids
                            
                            # Delete removed rows
                            for deleted_id in deleted_ids:
                                cursor.execute("DELETE FROM reviewer_data WHERE ID = %s", (deleted_id,))
                            
                            # Update/Insert rows - Note: Cvsreviewed is now derived, not stored
                            for _, row in edited_reviewer_df.iterrows():
                                if pd.isna(row['ID']):
                                    # New row - INSERT
                                    cursor.execute("""
                                        INSERT INTO reviewer_data (Name, Password, ReviewsNumber, LinkedIn, Email, Rprofilez)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (row['Name'], row['Password'], row['ReviewsNumber'], 
                                          row['LinkedIn'], row['Email'], row['Rprofilez']))
                                else:
                                    # Existing row - UPDATE
                                    cursor.execute("""
                                        UPDATE reviewer_data 
                                        SET Name=%s, Password=%s, ReviewsNumber=%s, 
                                            LinkedIn=%s, Email=%s, Rprofilez=%s
                                        WHERE ID=%s
                                    """, (row['Name'], row['Password'], row['ReviewsNumber'],
                                          row['LinkedIn'], row['Email'], row['Rprofilez'], int(row['ID'])))
                            
                            st.success("✅ Reviewer data saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving reviewer data: {e}")

                with col2:
                    st.markdown(get_table_download_link(edited_reviewer_df,'Reviewer_Data.csv','📥 Download Reviewer Data'), unsafe_allow_html=True)

                st.markdown("---")

                # 📝 EDITABLE REVIEWS DATA
                st.header("**Reviews Data (Editable)**")
                # 1) Fetch only the columns you want, renaming Email_ID → User_Email
                cursor.execute("""
                  SELECT
                    id,
                    Name,
                    Roll_No,
                    Email_ID AS User_Email,
                    Reviewer_Name,
                    Reviewer_LinkedIn,
                    Review
                  FROM reviews_data
                """)
                cols = ["id","Name","Roll_No","User_Email","Reviewer_Name","Reviewer_LinkedIn","Review"]
                reviews_df = pd.DataFrame(cursor.fetchall(), columns=cols)

                reviews_column_config = {
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "Roll_No": st.column_config.TextColumn("Roll Number"),
                    "User_Email": st.column_config.TextColumn("Candidate Email"),
                    "Reviewer_LinkedIn": st.column_config.LinkColumn("Reviewer LinkedIn"),
                    "Review": st.column_config.TextColumn("Feedback", width="large"),
                }

                edited_reviews_df = st.data_editor(
                    reviews_df,
                    column_config=reviews_column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="reviews_data_editor"
                )

                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Reviews Data Changes", type="primary"):
                        try:
                            # Handle row deletions first
                            original_ids = set(reviews_df['id'].tolist())
                            edited_ids = {
                                int(x) for x in edited_reviews_df['id'].tolist()
                                if not pd.isna(x)
                            }
                            deleted_ids = original_ids - edited_ids
                            
                            # Delete removed rows
                            for deleted_id in deleted_ids:
                                cursor.execute("DELETE FROM reviews_data WHERE id = %s", (deleted_id,))
                            
                            # Process each row for insert/update
                            for _, row in edited_reviews_df.iterrows():
                                # map blank → None
                                def norm(v):
                                    return None if (pd.isna(v) or str(v).strip()=="") else v

                                user_email = norm(row["User_Email"])
                                linkedin   = norm(row["Reviewer_LinkedIn"])
                                feedback   = norm(row["Review"])

                                if pd.isna(row["id"]):
                                    cursor.execute(
                                      "INSERT INTO reviews_data "
                                      "(Name,Roll_No,Email_ID,Reviewer_Name,Reviewer_LinkedIn,Reviewer_Email,Drive_Link,Review) "
                                      "VALUES (%s,%s,%s,%s,%s,NULL,NULL,%s)",
                                      (row["Name"], row["Roll_No"], user_email, row["Reviewer_Name"],
                                       linkedin, feedback)
                                    )
                                else:
                                    cursor.execute(
                                      "UPDATE reviews_data SET "
                                      "Roll_No=%s,Email_ID=%s,Reviewer_LinkedIn=%s,Reviewer_Email=NULL,Drive_Link=NULL,Review=%s "
                                      "WHERE id=%s",
                                      (row["Roll_No"], user_email, linkedin, feedback, int(row["id"]))
                                    )
                            
                            st.success("✅ Reviews data saved (with NULLs where you cleared cells)!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving reviews data: {e}")

                with col2:
                    st.markdown(get_table_download_link(edited_reviews_df,'Reviews_Data.csv','📥 Download Reviews Data'), unsafe_allow_html=True)

                st.markdown("---")

                # 🚀 NEW: CV ALLOCATION MANAGEMENT
                st.header("**CV Allocation Management 🎯**")
                
                # Get allocation statistics for the download functionality
                allocation_stats = get_allocation_stats()
                
                # Unassigned CVs count
                with get_db_cursor() as (_, cur):
                    cur.execute("""
                        SELECT profiles, COUNT(*) as count
                        FROM user_data 
                        WHERE status_num = 1 AND assigned_to IS NULL
                        GROUP BY profiles
                    """)
                    unassigned_stats = cur.fetchall()
                
                if unassigned_stats:
                    st.subheader("Unassigned CVs by Profile")
                    unassigned_df = pd.DataFrame([
                        {"Profile": stat["profiles"], "Unassigned CVs": stat["count"]}
                        for stat in unassigned_stats
                    ])
                    st.dataframe(unassigned_df, use_container_width=True)
                
                # Allocation controls
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🚀 Run Smart Allocation", type="primary"):
                        allocation_result = smart_cv_allocation()
                        if allocation_result["allocated"] > 0:
                            st.success(f"✅ {allocation_result['message']}")
                            st.info("Details: " + ", ".join(allocation_result["details"]))
                            st.rerun()
                        else:
                            st.info("ℹ️ No CVs available for allocation")
                
                with col2:
                    if st.button("📊 Refresh Stats"):
                        # Clear cache to get fresh data
                        get_allocation_stats.clear()
                        st.rerun()
                
                with col3:
                    if st.button("📥 Download Allocation Report"):
                        if allocation_stats:
                            report_df = pd.DataFrame(allocation_stats)
                            st.markdown(
                                get_table_download_link(report_df, 'allocation_report.csv', '📥 Download Report'),
                                unsafe_allow_html=True
                            )

            except Exception as e:
                display_error_details("Admin dashboard data loading failed", e)
    else:
        #Reviewer Side of the page:
        def reviewer_login():
            if 'logged_in' not in st.session_state:
                st.session_state['logged_in'] = False

            if not st.session_state['logged_in']:
                st.success('Welcome to the Reviewers Side')
                reviewer_name = st.text_input("Enter your full name:")
                ad_password = st.text_input("Password", type='password')

                if st.button('Login'):
                    with get_db_cursor() as (conn, cursor):
                        try:
                            # Case-insensitive name lookup
                            cursor.execute(
                                "SELECT Name, Password FROM reviewer_data WHERE UPPER(Name) = UPPER(%s)",
                                (reviewer_name,)
                            )
                            row = cursor.fetchone()
                            if row and ad_password == row['Password']:
                                st.session_state['logged_in'] = True
                                st.session_state['ad_user'] = row['Name']  # Use the exact name from DB
                                st.success(f"Welcome {row['Name']}!")
                                st.rerun()
                            else:
                                st.error("Invalid name or password")
                        except Exception as e:
                            display_error_details("Reviewer login failed", e)
            else:
                display_review_section(st.session_state['ad_user'])

        # Function to display the review section
        def display_review_section(ad_user):
            if st.button('Logout'):
                st.session_state['logged_in'] = False
                st.rerun()

            st.success(f'Hello {ad_user}!')

            # Show any persisted success message
            if 'review_success_msg' in st.session_state:
                st.success(st.session_state['review_success_msg'])
                # Clear the message after showing it
                del st.session_state['review_success_msg']

            # 🔧 Get reviewer's quota & profile
            info = get_reviewer_info(ad_user)
            if not info:
                st.error("Reviewer not found!")
                return

            ReviewsNumber = info["ReviewsNumber"]
            domain = info["Rprofilez"]
            linkedin = info["LinkedIn"]
            reviewer_email = info["Email"]

            # ✅ Compute the actual number of reviews this reviewer has already submitted
            reviewed_count = get_reviewer_count(ad_user)
            remaining = ReviewsNumber - reviewed_count

            if remaining <= 0:
                st.success("🎉 You've completed all your assigned reviews!")
                return

            # 🚀 NEW: Show allocation statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Reviews Completed", reviewed_count)
            with col2:
                st.metric("Remaining Capacity", remaining)
            with col3:
                st.metric("Your Domain", domain)

            # 🚀 NEW: Admin allocation control
            if st.button("🔄 Run Smart Allocation", help="Automatically assign unassigned CVs to best reviewers"):
                allocation_result = smart_cv_allocation()
                if allocation_result["allocated"] > 0:
                    st.success(f"✅ {allocation_result['message']}")
                    if st.session_state.show_performance:
                        st.info("Allocation details: " + ", ".join(allocation_result["details"]))
                else:
                    st.info("ℹ️ No CVs available for allocation")

            st.info(f"📝 You can review **{remaining}** more CV(s) in **{domain}**.")

            # 🔗 LinkedIn Profile Section (One-time setup)
            st.markdown("---")
            st.markdown("### 🔗 Your LinkedIn Profile")
            
            with st.form(key="linkedin_form"):
                current_linkedin = linkedin if linkedin else ""
                linkedin_input = st.text_input(
                    "LinkedIn URL (Optional)", 
                    value=current_linkedin,
                    placeholder="https://linkedin.com/in/your-profile",
                    help="Your LinkedIn profile will be shared with reviewees for networking opportunities"
                )
                
                linkedin_submitted = st.form_submit_button("💾 Update LinkedIn Profile")
                
                if linkedin_submitted:
                    final_linkedin = linkedin_input.strip() if linkedin_input.strip() else None
                    
                    # Update reviewer's LinkedIn profile
                    with get_db_cursor() as (_, cur):
                        cur.execute(
                            "UPDATE reviewer_data SET LinkedIn = %s WHERE Name = %s",
                            (final_linkedin, ad_user)
                        )
                        # Clear cache to get updated LinkedIn info
                        get_reviewer_info.clear()
                        
                        if final_linkedin:
                            st.success("✅ LinkedIn profile updated successfully!")
                        else:
                            st.success("✅ LinkedIn profile cleared!")
                        
                        time.sleep(1)
                        st.rerun()

            st.markdown("---")

            # 🚀 NEW: Use improved CV fetching
            cvs = get_reviewer_assigned_cvs(ad_user, ReviewsNumber)

            if not cvs:
                st.warning("No CVs assigned to you right now.")
                st.info("💡 Click 'Run Smart Allocation' to get new CVs or wait for admin to assign them.")
                return

            # 4️⃣ Loop & render one form per CV
            for cv in cvs:
                roll, student, link, email_id, status, existing_review = (
                    cv["Roll_No"], cv["Name"], cv["drive_link"], cv["Email_ID"], 
                    cv["status_num"], cv["existing_review"]
                )

                st.markdown("---")
                
                # 🚀 NEW: Enhanced CV header with submission time
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.image("./Logo/CVlogo.png", width=120)
                    st.write(f"**{student}**  (Roll: {roll})")
                with col2:
                    status_emoji = "✅" if status == 2 else "⏳"
                    status_text = "Reviewed" if status == 2 else "Pending"
                    st.write(f"{status_emoji} {status_text}")
                
                try:
                    show_pdf(f"./Uploaded_Resumes/{roll}.pdf")
                except FileNotFoundError:
                    st.warning("📄 PDF preview not available locally.")
                    st.markdown(f"[View on Drive]({link})")

                # the form itself - always enabled
                with st.form(key=f"form_{roll}", clear_on_submit=True):
                    st.markdown("### ✍️ Your Review")
                    review_text = st.text_area(
                        "", 
                        value=existing_review or "",
                        height=180,
                        placeholder="Provide constructive feedback on content, structure, skills, formatting…"
                    )
                    
                    # If they've already written one, give them an "Update" button
                    btn_label = "✏️ Update Review" if existing_review else "🚀 Submit Review"
                    submitted = st.form_submit_button(btn_label)

                # handle submission
                if submitted:
                    if not review_text.strip():
                        st.error("❌ Please enter some feedback before submitting.")
                    else:
                        with get_db_cursor() as (_, cur2):
                            # Get current LinkedIn from reviewer profile (updated at the top)
                            current_info = get_reviewer_info(ad_user)
                            current_linkedin = current_info["LinkedIn"] if current_info else linkedin
                            
                            if existing_review:
                                # They're editing an old review: update the review and LinkedIn
                                cur2.execute(
                                    "UPDATE reviews_data SET Review=%s, Reviewer_LinkedIn=%s WHERE Roll_No=%s AND Reviewer_Name=%s",
                                    (review_text, current_linkedin, roll, ad_user)
                                )
                                # Store success message in session state for persistence
                                st.session_state['review_success_msg'] = f"✅ Updated review for {student}!"
                                st.success(f"✅ Updated review for {student}!")
                            else:
                                # First-time review: insert + mark the CV reviewed
                                cur2.execute("""
                                    INSERT INTO reviews_data
                                      (Name, Roll_No, Email_ID, Reviewer_Name, Reviewer_LinkedIn,
                                       Reviewer_Email, Drive_Link, Review)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    student,
                                    roll,
                                    email_id,
                                    ad_user,
                                    current_linkedin,
                                    reviewer_email or None,
                                    link,
                                    review_text
                                ))
                                cur2.execute(
                                    "UPDATE user_data SET status_num = 2 WHERE Roll_No = %s",
                                    (roll,)
                                )
                                # Store success message in session state for persistence
                                st.session_state['review_success_msg'] = f"✅ Submitted review for {student}!"
                                st.success(f"✅ Submitted review for {student}!")
                        
                        # Add a small delay to let user see the message before rerun
                        import time
                        time.sleep(1.5)
                        st.rerun()

        reviewer_login()


# @contextmanager
# def get_db_cursor():
#     conn = db_pool.get_connection()
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
#     try:
#         yield conn, cursor
#         conn.commit()
#     except:
#         conn.rollback()
#         raise
#     finally:
#         cursor.close()
#         conn.close()

# ========== IMPROVED CV ALLOCATION SYSTEM ==========

@st.cache_data(ttl=30)  # Cache for 30 seconds to prevent race conditions
def get_allocation_stats():
    """Get current allocation statistics for load balancing"""
    with get_db_cursor() as (_, cur):
        cur.execute("""
            SELECT 
                r.Name,
                r.Rprofilez,
                r.ReviewsNumber,
                COALESCE(rv.completed, 0) as completed_reviews,
                COALESCE(rv.completed, 0) + COALESCE(pending.pending_count, 0) as total_assigned,
                r.ReviewsNumber - COALESCE(rv.completed, 0) as remaining_capacity
            FROM reviewer_data r
            LEFT JOIN (
                SELECT Reviewer_Name, COUNT(*) as completed
                FROM reviews_data
                GROUP BY Reviewer_Name
            ) rv ON rv.Reviewer_Name = r.Name
            LEFT JOIN (
                SELECT assigned_to, COUNT(*) as pending_count
                FROM user_data 
                WHERE status_num = 1 AND assigned_to IS NOT NULL
                GROUP BY assigned_to
            ) pending ON pending.assigned_to = r.Name
            WHERE r.ReviewsNumber > COALESCE(rv.completed, 0)
            ORDER BY r.Rprofilez, total_assigned ASC
        """)
        return cur.fetchall()

def smart_cv_allocation():
    """Intelligent CV allocation system with load balancing"""
    with get_db_cursor() as (_, cur):
        # Get unassigned CVs by profile
        cur.execute("""
            SELECT Roll_No, profiles
            FROM user_data 
            WHERE status_num = 1 AND assigned_to IS NULL
            ORDER BY profiles, ID ASC
        """)
        unassigned_cvs = cur.fetchall()
        
        if not unassigned_cvs:
            return {"allocated": 0, "message": "No unassigned CVs"}
        
        # Get available reviewers
        allocation_stats = get_allocation_stats()
        
        allocated_count = 0
        allocations_made = []
        
        for cv in unassigned_cvs:
            roll_no = cv["Roll_No"]
            profile = cv["profiles"]
            
            # Find best reviewer for this profile
            best_reviewer = None
            min_workload = float('inf')
            
            for reviewer in allocation_stats:
                if (reviewer["Rprofilez"] == profile and 
                    reviewer["remaining_capacity"] > 0 and
                    reviewer["total_assigned"] < min_workload):
                    best_reviewer = reviewer["Name"]
                    min_workload = reviewer["total_assigned"]
            
            if best_reviewer:
                # Assign CV to best reviewer
                cur.execute(
                    "UPDATE user_data SET assigned_to = %s WHERE Roll_No = %s",
                    (best_reviewer, roll_no)
                )
                allocated_count += 1
                allocations_made.append(f"{roll_no} → {best_reviewer}")
                
                # Update local stats to prevent double-assignment in this batch
                for reviewer in allocation_stats:
                    if reviewer["Name"] == best_reviewer:
                        reviewer["total_assigned"] += 1
                        reviewer["remaining_capacity"] -= 1
                        break
        
        return {
            "allocated": allocated_count,
            "message": f"Allocated {allocated_count} CVs",
            "details": allocations_made
        }

@timing_decorator
def get_reviewer_assigned_cvs(reviewer_name: str, max_capacity: int):
    """Get CVs assigned to a specific reviewer"""
    with get_db_cursor() as (_, cur):
        cur.execute("""
            SELECT u.Roll_No, u.Name, u.drive_link, u.Email_ID, u.status_num,
                   r.Review AS existing_review
              FROM user_data u
              LEFT JOIN reviews_data r 
                ON u.Roll_No = r.Roll_No 
               AND r.Reviewer_Name = %s
             WHERE u.assigned_to = %s
             ORDER BY u.status_num ASC, u.ID ASC
             LIMIT %s
        """, (reviewer_name, reviewer_name, max_capacity))
        return cur.fetchall()

if __name__ == "__main__":
    # ✅ Initialize database once at startup
    # init_db()
    
    # ✅ Run the main application
    run()