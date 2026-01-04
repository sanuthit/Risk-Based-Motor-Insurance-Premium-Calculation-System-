import streamlit as st
from risk_engine import calculate_risk, is_blacklisted

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Risk-Based Motor Insurance System",
    layout="wide"
)

# --------------------------------------------------
# Custom CSS (YOUR COLOR PALETTE)
# --------------------------------------------------
st.markdown("""
<style>
.risk-box {
    padding: 28px;
    border-radius: 18px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}
.risk-high {
    background: linear-gradient(135deg, #6a040f, #d00000);
}
.risk-medium {
    background: linear-gradient(135deg, #f48c06, #faa307);
    color: #03071e;
}
.risk-low {
    background: linear-gradient(135deg, #03071e, #370617);
}

.subtle-box {
    background-color: #f6f7f9;
    padding: 18px;
    border-radius: 14px;
    text-align: center;
    border-left: 6px solid #dc2f02;
}

.section-title {
    margin-top: 10px;
    margin-bottom: 5px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Title
# --------------------------------------------------
st.title("🚗 Risk-Based Motor Insurance System")
st.markdown("Enter customer and vehicle details to calculate accident risk probability.")
st.divider()

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None

if "blacklisted" not in st.session_state:
    st.session_state.blacklisted = False

# IMPORTANT: init widget state ONCE (no 'value=' in widget)
if "years_of_driving_experience" not in st.session_state:
    st.session_state.years_of_driving_experience = 10

# --------------------------------------------------
# Input Form
# --------------------------------------------------
with st.form("risk_form"):

    st.subheader("👤 Driver Details")
    c1, c2, c3 = st.columns(3)

    with c1:
        driver_age = st.number_input("Driver Age", 18, 90, 35, step=1)
        driver_gender = st.selectbox("Driver Gender", ["Male", "Female"])

    # Dynamic max experience based on license age
    MIN_LICENSE_AGE = 18
    max_exp = max(int(driver_age) - MIN_LICENSE_AGE, 0)

    # If user previously selected a value that is now invalid, auto-correct it
    if st.session_state.years_of_driving_experience > max_exp:
        st.session_state.years_of_driving_experience = max_exp

    with c2:
        driver_occupation = st.selectbox(
            "Driver Occupation",
            ["Private", "Government", "Self-employed", "Student", "Unemployed", "Other"]
        )

        # ✅ FIX: remove 'value=' because we already use session state via key
        years_of_driving_experience = st.number_input(
            "Years of Driving Experience",
            min_value=0,
            max_value=max_exp,
            step=1,
            help=f"Max allowed = {max_exp} (Age {driver_age} - {MIN_LICENSE_AGE})",
            key="years_of_driving_experience"
        )
        st.caption(f"Maximum possible experience for age {driver_age}: {max_exp} years")

    with c3:
        member_automobile_assoc_ceylon = st.selectbox(
            "AAC Membership", [0, 1],
            format_func=lambda x: "Yes" if x == 1 else "No"
        )

    st.subheader("📜 Insurance History")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        has_previous_motor_policy = st.selectbox(
            "Previous Motor Policy", [0, 1],
            format_func=lambda x: "Yes" if x == 1 else "No"
        )

    with c2:
        accidents_last_3_years = st.number_input(
            "Accidents (Last 3 Years)", 0, 10, 0, step=1
        )

    with c3:
        ncb_percentage = st.selectbox(
            "NCB %", [0, 10, 20, 30, 40, 50, 60, 70]
        )

    with c4:
        num_claims_within_1_year = st.number_input(
            "Claims (Last Year)", 0, 10, 0, step=1
        )

    st.subheader("🚙 Vehicle Details")
    c1, c2, c3 = st.columns(3)

    with c1:
        vehicle_type = st.selectbox(
            "Vehicle Type",
            ["Car", "SUV", "Van", "Truck", "Motorcycle", "Three-Wheeler", "Bus"]
        )
        vehicle_segment = st.selectbox(
            "Vehicle Segment",
            ["Sedan", "Hatchback", "Wagon", "Pickup", "MPV", "Other"]
        )
        engine_capacity_cc = st.number_input(
            "Engine Capacity (cc)", 50, 8000, 1500, step=10
        )

    with c2:
        fuel_type = st.selectbox(
            "Fuel Type",
            ["Petrol", "Diesel", "Hybrid", "Electric", "Other"]
        )
        vehicle_age_years = st.number_input(
            "Vehicle Age (Years)", 0, 60, 8, step=1
        )
        vehicle_usage_type = st.selectbox(
            "Usage Type",
            ["Private", "Business", "Rent", "Taxi", "School", "Other"]
        )

    with c3:
        registration_district = st.selectbox(
            "Registration District",
            ["Colombo", "Gampaha", "Kalutara", "Kandy",
             "Galle", "Matara", "Jaffna", "Other"]
        )
        parking_type = st.selectbox(
            "Parking Type",
            ["Garage", "Street", "Car Park", "Other"]
        )
        has_lpg_conversion = st.selectbox(
            "LPG Conversion", [0, 1],
            format_func=lambda x: "Yes" if x == 1 else "No"
        )

    customer_id = st.text_input("Customer ID (optional)", "")

    submit = st.form_submit_button("🔍 Calculate Risk", use_container_width=True)

# --------------------------------------------------
# Risk Calculation
# --------------------------------------------------
if submit:

    input_policy = {
        "driver_age": int(driver_age),
        "driver_gender": driver_gender,
        "driver_occupation": driver_occupation,
        "years_of_driving_experience": int(st.session_state.years_of_driving_experience),
        "member_automobile_assoc_ceylon": int(member_automobile_assoc_ceylon),
        "has_previous_motor_policy": int(has_previous_motor_policy),
        "accidents_last_3_years": int(accidents_last_3_years),
        "ncb_percentage": int(ncb_percentage),
        "num_claims_within_1_year": int(num_claims_within_1_year),
        "vehicle_type": vehicle_type,
        "vehicle_segment": vehicle_segment,
        "engine_capacity_cc": int(engine_capacity_cc),
        "fuel_type": fuel_type,
        "vehicle_age_years": int(vehicle_age_years),
        "vehicle_usage_type": vehicle_usage_type,
        "registration_district": registration_district,
        "parking_type": parking_type,
        "has_lpg_conversion": int(has_lpg_conversion),
        "customer_id": customer_id.strip(),
    }

    if is_blacklisted(customer_id):
        st.session_state.blacklisted = True
        st.session_state.result = None
    else:
        st.session_state.blacklisted = False
        with st.spinner("Calculating risk..."):
            st.session_state.result = calculate_risk(input_policy)

# --------------------------------------------------
# Results
# --------------------------------------------------
st.divider()
st.subheader("📊 Risk Assessment Result")

if st.session_state.blacklisted:
    st.error("⛔ BLACK LISTED – Customer cannot be insured.")

elif st.session_state.result:
    r = st.session_state.result
    risk_pct = r["risk_probability"] * 100
    label = r["risk_label"].lower()

    st.markdown(
        f"""
        <div class="risk-box risk-{label}">
            <h1>{risk_pct:.2f}%</h1>
            <h2>{r["risk_label"]} RISK</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div class="subtle-box">
                <h4>EBM Risk</h4>
                <p>{r['ebm_probability']*100:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="subtle-box">
                <h4>NGBoost Risk</h4>
                <p>{r['ngboost_probability']*100:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.info("Fill the form and click **Calculate Risk**.")
