import streamlit as st

st.set_page_config(
    page_title="Congressional Bill Outcome Predictor",
    layout="wide"
)

st.title("Congressional Bill Outcome Predictor")
st.caption("DS 6021 | Predictive Modeling Final Project")

tab1, tab2, tab3 = st.tabs([
    "Predict a Bill",
    "Explore the Data",
    "Model Performance"
])

with tab1:
    st.header("Predict a Bill")
    st.text_area("Enter a bill title")

with tab2:
    st.header("Explore the Data")

with tab3:
    st.header("Model Performance")
