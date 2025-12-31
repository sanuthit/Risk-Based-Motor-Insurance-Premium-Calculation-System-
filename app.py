import streamlit as st
import pandas as pd

from risk_engine import calculate_risk

st.set_page_config(
    page_title="Risk-Based Motor Insurance",
    layout="wide"
)

st.title("🚗 Risk-Based Motor Insurance Premium System")
st.caption("EBM + NGBoost risk assessment with rule-based premium calculation")

# -------------------------
# SIDEBAR INPUTS
# -------------------------
st.sidebar.header("Driver Details")

driver_age = st.sidebar.number_input("Driver Age", 18, 90, 23)
driver_gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
driver_occupation = st.sidebar.selectbox("Occupation", ["Private", "Government", "Self-Employed", "Other"])
years_of_driving_experience = st.sidebar.number_input("Years of Driving Experience", 0, 80, 2)
accidents_last_3_years = st.sidebar.number_input("Accidents (Last 3 Years)", 0, 10, 2)
ncb_percentage = st.sidebar.slider("NCB %", 0, 70, 0)

st.sidebar.header("Vehicle Details")

vehicle_type = st.sidebar.selectbox("Vehicle Type", ["Car", "Van", "SUV", "Motorcycle"])
vehicle_segment = st.sidebar.selectbox("Vehicle Segment", ["Hatchback", "Sedan", "SUV"])
engine_capacity_cc = st.sidebar.number_input("Engine Capacity (cc)", 50, 8000, 1800)
fuel_type = st.sidebar.selectbox("Fuel Type", ["Petrol", "Diesel", "Hybrid", "Electric"])
vehicle_age_years = st.sidebar.number_input("Vehicle Age (years)", 0, 60, 18)
vehicle_usage_type = st.sidebar.selectbox("Usage Type", ["Private", "Commercial"])
registration_district = st.sidebar.selectbox(
    "Registration District",
    ["Colombo", "Gampaha", "Kandy", "Galle", "Kurunegala", "Other"]
)
parking_type = st.sidebar.selectbox("Parking Type", ["Garage", "Car Park", "Road"])
has_lpg_conversion = st.sidebar.selectbox("LPG Conversion", [0, 1])

st.sidebar.header("Customer / Compliance")

is_existing_customer = st.sidebar.selectbox("Existing Customer", [0, 1])
is_blacklisted_customer = st.sidebar.selectbox("Blacklisted Customer", [0, 1])
images_uploaded = st.sidebar.selectbox("Images Uploaded", [0, 1])
inspection_report_uploaded = st.sidebar.selectbox("Inspection Report Uploaded", [0, 1])
registration_book_available = st.sidebar.selectbox("Registration Book Available", [0, 1])

st.sidebar.header("Premium Inputs")

base_premium = st.sidebar.number_input("Base Premium (LKR)", 1000, 500000, 45000)
other_discount = st.sidebar.number_input("Other Discount (LKR)", 0, 200000, 0)

# -------------------------
# BUILD POLICY DICT
# -------------------------
policy = {
    "driver_age": driver_age,
    "driver_gender": driver_gender,
    "driver_occupation": driver_occupation,
    "years_of_driving_experience": years_of_driving_experience,
    "member_automobile_assoc_ceylon": 0,
    "has_previous_motor_policy": 0,
    "ncb_percentage": ncb_percentage,
    "accidents_last_3_years": accidents_last_3_years,

    "vehicle_type": vehicle_type,
    "vehicle_segment": vehicle_segment,
    "engine_capacity_cc": engine_capacity_cc,
    "fuel_type": fuel_type,
    "vehicle_age_years": vehicle_age_years,
    "vehicle_usage_type": vehicle_usage_type,
    "registration_district": registration_district,
    "parking_type": parking_type,
    "has_lpg_conversion": has_lpg_conversion,

    "vehicle_make": "GENERIC",
    "vehicle_model": "GENERIC",
    "images_uploaded": images_uploaded,
    "inspection_report_uploaded": inspection_report_uploaded,
    "registration_book_available": registration_book_available,
    "rebate_within_company_limits": 1,
    "is_existing_customer": is_existing_customer,
    "is_blacklisted_customer": is_blacklisted_customer,

    "coverage_type": "Comprehensive",
    "approx_market_value": 0,
    "sum_insured": 0,
    "num_claims_within_1_ye
