import os
import streamlit as st
import pandas as pd
from audit_engine import get_engine, run_sequence_gap_audit, run_off_hours_audit, run_duplicate_audit
from seed import seed_database

st.set_page_config(page_title="Transaction Audit & Anomaly Engine", layout="wide")

DB_HOST = os.getenv("DB_HOST", "localhost")

@st.cache_resource
def init_db():
    try:
        engine = get_engine(DB_HOST)
        df = pd.read_sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='ledger_transactions'", engine)
        if df.iloc[0, 0] == 0:
            seed_database()
        return engine
    except Exception as e:
        return None

engine = init_db()

st.title("🛡️ Transaction Anomaly & Data Integrity Audit Engine")
st.markdown("Automated IS Auditor Dashboard detecting sequence gaps, off-hours activity, and data anomalies.")

if engine is None:
    st.error("Could not connect to the PostgreSQL database. Please ensure Docker containers are running.")
else:
    if st.button("🔄 Reset & Re-seed Dummy Data"):
        with st.spinner("Seeding database with anomalies..."):
            seed_database()
            st.success("Database re-seeded successfully!")
            st.rerun()

    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    df_all = pd.read_sql("SELECT * FROM ledger_transactions", engine)
    
    with col1:
        st.metric("Total Transactions Audited", len(df_all))
    with col2:
        gaps_df = run_sequence_gap_audit(engine)
        st.metric("Sequence Gaps Detected", len(gaps_df))
    with col3:
        off_hours_df = run_off_hours_audit(engine)
        st.metric("Off-Hours Anomalies", len(off_hours_df))

    st.markdown("### 🔍 Detailed Audit Reports")
    
    tab1, tab2, tab3 = st.tabs(["Sequence Gaps", "Off-Hours Transactions", "Duplicate / Value Clones"])
    
    with tab1:
        st.subheader("Missing Transaction ID Sequences")
        if not gaps_df.empty:
            st.dataframe(gaps_df, use_container_width=True)
        else:
            st.success("No sequence gaps detected!")

    with tab2:
        st.subheader("Unusual Off-Hours Modifications (1 AM - 4 AM)")
        if not off_hours_df.empty:
            st.dataframe(off_hours_df, use_container_width=True)
        else:
            st.success("No off-hours anomalies detected!")

    with tab3:
        st.subheader("Duplicate Amount & Account Patterns")
        dup_df = run_duplicate_audit(engine)
        if not dup_df.empty:
            st.dataframe(dup_df, use_container_width=True)
        else:
            st.success("No duplicate patterns detected!")
