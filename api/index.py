import os
import random
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# Initialize application environmental constraints
load_dotenv()

app = Flask(__name__, template_folder='../templates')

# Initialize Groq client with global API key validation
groq_api_key = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
supabase: Client = create_client(supabase_url, supabase_key) if (supabase_url and supabase_key) else None

# Validated Production Groq Inference Target
GROQ_MODEL_ID = "llama-3.1-70b-versatile"

# --- MOCK DATA ENGINE SEED MATRIX ---
random.seed(42)

UNIVERSITIES = [
    {"id": 1, "name": "MIT", "min_gpa": 3.8, "avg_sat": 1540, "avg_act": 35, "region": "Northeast", "campus_type": "Urban", "majors": ["Computer Science", "Mechanical Engineering"], "dna": ["STEM", "Research", "Innovation"], "state": "MA", "is_private": True, "in_state_tuition": 59750, "out_of_state_tuition": 59750},
    {"id": 2, "name": "Stanford University", "min_gpa": 3.9, "avg_sat": 1520, "avg_act": 34, "region": "West", "campus_type": "Suburban", "majors": ["Computer Science", "Business Administration", "Bioengineering"], "dna": ["STEM", "Leadership", "First-Gen"], "state": "CA", "is_private": True, "in_state_tuition": 62484, "out_of_state_tuition": 62484},
    {"id": 3, "name": "Harvard University", "min_gpa": 3.9, "avg_sat": 1530, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Political Science", "Economics", "History"], "dna": ["Leadership", "Community Service", "Arts"], "state": "MA", "is_private": True, "in_state_tuition": 59076, "out_of_state_tuition": 59076},
    {"id": 4, "name": "UC Berkeley", "min_gpa": 3.7, "avg_sat": 1450, "avg_act": 32, "region": "West", "campus_type": "Urban", "majors": ["Computer Science", "Data Science", "Environmental Science"], "dna": ["STEM", "Research", "Community Service"], "state": "CA", "is_private": False, "in_state_tuition": 14226, "out_of_state_tuition": 48176},
    {"id": 5, "name": "University of Michigan", "min_gpa": 3.6, "avg_sat": 1400, "avg_act": 31, "region": "Midwest", "campus_type": "Urban", "majors": ["Mechanical Engineering", "Business Administration"], "dna": ["Athletics", "Leadership", "STEM"], "state": "MI", "is_private": False, "in_state_tuition": 17768, "out_of_state_tuition": 57233},
    {"id": 6, "name": "UT Austin", "min_gpa": 3.6, "avg_sat": 1380, "avg_act": 30, "region": "South", "campus_type": "Urban", "majors": ["Computer Science", "Business Administration"], "dna": ["First-Gen", "STEM", "Innovation"], "state": "TX", "is_private": False, "in_state_tuition": 11698, "out_of_state_tuition": 41070},
    {"id": 7, "name": "NYU", "min_gpa": 3.5, "avg_sat": 1410, "avg_act": 31, "region": "Northeast", "campus_type": "Urban", "majors": ["Arts", "Film", "Economics"], "dna": ["Arts", "Innovation", "Diversity"], "state": "NY", "is_private": True, "in_state_tuition": 60438, "out_of_state_tuition": 60438},
    {"id": 8, "name": "Northwestern University", "min_gpa": 3.8, "avg_sat": 1480, "avg_act": 33, "region": "Midwest", "campus_type": "Suburban", "majors": ["Journalism", "Economics", "Communication"], "dna": ["Research", "Leadership", "Arts"], "state": "IL", "is_private": True, "in_state_tuition": 64887, "out_of_state_tuition": 64887},
    {"id": 9, "name": "Georgia Tech", "min_gpa": 3.6, "avg_sat": 1420, "avg_act": 31, "region": "South", "campus_type": "Urban", "majors": ["Aerospace Engineering", "Computer Science"], "dna": ["STEM", "Innovation", "Research"], "state": "GA", "is_private": False, "in_state_tuition": 11764, "out_of_state_tuition": 32876},
    {"id": 10, "name": "University of Florida", "min_gpa": 3.5, "avg_sat": 1360, "avg_act": 29, "region": "South", "campus_type": "Suburban", "majors": ["Biology", "Business Administration"], "dna": ["Athletics", "Community Service", "First-Gen"], "state": "FL", "is_private": False, "in_state_tuition": 6380, "out_of_state_tuition": 28658},
    {"id": 11, "name": "Williams College", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "Northeast", "campus_type": "Rural", "majors": ["Mathematics", "History"], "dna": ["Research", "Community Service", "Arts"], "state": "MA", "is_private": True, "in_state_tuition": 64540, "out_of_state_tuition": 64540},
    {"id": 12, "name": "Vanderbilt University", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "South", "campus_type": "Urban", "majors": ["Education", "Economics"], "dna": ["Leadership", "Community Service", "Innovation"], "state": "TN", "is_private": True, "in_state_tuition": 63946, "out_of_state_tuition": 63946},
    {"id": 13, "name": "University of Washington", "min_gpa": 3.5, "avg_sat": 1350, "avg_act": 29, "region": "West", "campus_type": "Urban", "majors": ["Bioengineering", "Computer Science"], "dna": ["STEM", "Research", "Diversity"], "state": "WA", "is_private": False, "in_state_tuition": 12242, "out_of_state_tuition": 40740},
    {"id": 14, "name": "Ohio State University", "min_gpa": 3.4, "avg_sat": 1310, "avg_act": 28, "region": "Midwest", "campus_type": "Urban", "majors": ["Agriculture", "Business Administration"], "dna": ["Athletics", "First-Gen", "Community Service"], "state": "OH", "is_private": False, "in_state_tuition": 12485, "out_of_state_tuition": 36722},
    {"id": 15, "name": "University of Virginia", "min_gpa": 3.7, "avg_sat": 1430, "avg_act": 32, "region": "South", "campus_type": "Suburban", "majors": ["History", "Commerce"], "dna": ["Leadership", "Research", "Honor Code"], "state": "VA", "is_private": False, "in_state_tuition": 18980, "out_of_state_tuition": 54380},
    {"id": 16, "name": "Caltech", "min_gpa": 3.9, "avg_sat": 1560, "avg_act": 36, "region": "West", "campus_type": "Suburban", "majors": ["Physics", "Mathematics", "Computer Science"], "dna": ["STEM", "Research", "Innovation"], "state": "CA", "is_private": True, "in_state_tuition": 60864, "out_of_state_tuition": 60864},
    {"id": 17, "name": "Duke University", "min_gpa": 3.8, "avg_sat": 1510, "avg_act": 34, "region": "South", "campus_type": "Suburban", "majors": ["Biology", "Public Policy"], "dna": ["Athletics", "Research", "Leadership"], "state": "NC", "is_private": True, "in_state_tuition": 63450, "out_of_state_tuition": 63450},
    {"id": 18, "name": "Dartmouth College", "min_gpa": 3.8, "avg_sat": 1480, "avg_act": 33, "region": "Northeast", "campus_type": "Rural", "majors": ["Economics", "Engineering Sciences"], "dna": ["Leadership", "Community Service", "Athletics"], "state": "NH", "is_private": True, "in_state_tuition": 63684, "out_of_state_tuition": 63684},
    {"id": 19, "name": "Purdue University", "min_gpa": 3.5, "avg_sat": 1320, "avg_act": 29, "region": "Midwest", "campus_type": "Suburban", "majors": ["Aeronautical Engineering", "Computer Science"], "dna": ["STEM", "Innovation", "First-Gen"], "state": "IN", "is_private": False, "in_state_tuition": 9992, "out_of_state_tuition": 28794},
    {"id": 20, "name": "Rice University", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "South", "campus_type": "Urban", "majors": ["Architecture", "Bioengineering"], "dna": ["Research", "Diversity", "STEM"], "state": "TX", "is_private": True, "in_state_tuition": 57210, "out_of_state_tuition": 57210}
]

def generate_mock_students():
    names = [
        "Liam Smith", "Olivia Johnson", "Noah Williams", "Emma Brown", "Oliver Jones",
        "Ava Garcia", "Elijah Miller", "Charlotte Davis", "William Rodriguez", "Sophia Martinez",
        "James Hernandez", "Amelia Lopez", "Benjamin Gonzalez", "Isabella Wilson", "Lucas Anderson",
        "Mia Thomas", "Henry Taylor", "Evelyn Moore", "Alexander Jackson", "Harper Martin",
        "Mason Lee", "Camila Perez", "Michael Thompson", "Gianna White", "Ethan Harris",
        "Abigail Sanchez", "Daniel Clark", "Luna Ramirez", "Jacob Lewis", "Ella Robinson",
        "Logan Walker", "Elizabeth Young", "Jackson Allen", "Sofia King", "Levi Wright",
        "Avery Scott", "Sebastian Torres", "Scarlett Nguyen", "Jack Hill", "Victoria Flores",
        "Aiden Green", "Madison Adams", "Owen Nelson", "Layla Baker", "Samuel Hall",
        "Chloe Rivera", "Matthew Campbell", "Arlo Mitchell", "David Carter", "Carter Roberts"
    ]
    majors = ["Computer Science", "Mechanical Engineering", "Business Administration", "Biology", "Political Science", "Economics", "Arts"]
    regions = ["Northeast", "West", "Midwest", "South"]
    campuses = ["Urban", "Suburban", "Rural"]
    dna_pools = ["STEM", "Leadership", "Community Service", "Arts", "Athletics", "First-Gen", "Research", "Innovation"]
    
    students = []
    for i in range(50):
        gpa = round(random.uniform(3.0, 4.0), 2)
        sat = int(random.randint(1100, 1600) / 10) * 10
        act = random.randint(22, 36)
        student_dna = list(set(random.choices(dna_pools, k=random.randint(2, 4))))
        
        students.append({
            "id": 1482 + i,
            "name": names[i],
            "gpa": gpa,
            "sat": sat,
            "act": act,
            "target_major": random.choice(majors),
            "preferred_region": random.choice(regions),
            "preferred_campus_type": random.choice(campuses),
            "dna": student_dna
        })
    return students

MOCK_STUDENTS = generate_mock_students()

def calculate_admission_probability(uni, gpa, sat, act, major, region, campus_type, selected_dna):
    """Calculates deterministic admission probability based on academic metrics and alignment."""
    # GPA component (0 - 40 pts)
    gpa_diff = gpa - uni['min_gpa']
    gpa_score = max(0.0, min(40.0, 30.0 + gpa_diff * 25.0))

    # SAT component (0 - 30 pts)
    sat_score = 15.0
    if sat is not None and sat > 0:
        sat_diff = sat - uni['avg_sat']
        sat_score = max(0.0, min(30.0, 20.0 + (sat_diff / 10.0) * 0.8))

    # ACT component (0 - 30 pts)
    act_score = 15.0
    if act is not None and act > 0:
        act_diff = act - uni['avg_act']
        act_score = max(0.0, min(30.0, 20.0 + act_diff * 2.5))

    academic_weight = (gpa_score * 0.40) + (sat_score * 0.30) + (act_score * 0.30)

    # Preference & Fit (0 - 40 pts)
    preference_weight = 0.0
    if region == uni['region']:
        preference_weight += 12.0
    if campus_type == uni['campus_type']:
        preference_weight += 10.0
    if major in uni['majors']:
        preference_weight += 10.0

    dna_overlap = len(set(selected_dna or []) & set(uni['dna']))
    preference_weight += min(12.0, dna_overlap * 4.0)

    total_score = academic_weight + preference_weight

    # Deterministic mapping to probability
    seed_offset = ((uni['id'] * 13) % 7) - 3
    prob = int(round(max(5.0, min(98.0, (total_score * 1.1) + seed_offset))))

    if prob >= 78:
        tier, color = "Safety", "emerald"
    elif prob >= 50:
        tier, color = "Target", "amber"
    else:
        tier, color = "Reach", "rose"

    return prob, tier, color

def calculate_financial_fit(uni, state_of_residence, household_income, family_size, annual_budget_cap):
    """Calculates residency tuition, estimated need-based financial aid, and annual budget cap status."""
    user_state = (state_of_residence or "NY").strip().upper()
    uni_state = uni.get('state', '').upper()
    is_private = uni.get('is_private', False)

    if is_private:
        tuition_type = "Private Standard"
        gross_tuition = uni.get('in_state_tuition', 60000)
    elif user_state == uni_state:
        tuition_type = "In-State"
        gross_tuition = uni.get('in_state_tuition', 12000)
    else:
        tuition_type = "Out-of-State"
        gross_tuition = uni.get('out_of_state_tuition', 40000)

    try:
        income = float(household_income) if household_income is not None else 100000.0
    except (ValueError, TypeError):
        income = 100000.0

    try:
        f_size = max(1, int(family_size)) if family_size is not None else 4
    except (ValueError, TypeError):
        f_size = 4

    try:
        budget_cap = float(annual_budget_cap) if annual_budget_cap is not None else 30000.0
    except (ValueError, TypeError):
        budget_cap = 30000.0

    per_capita = income / f_size

    if income <= 60000:
        aid_rate = min(0.95, 0.75 + (60000 - income) / 60000 * 0.20)
    elif income <= 120000:
        aid_rate = 0.35 + (120000 - income) / (120000 - 60000) * 0.40
    elif income <= 200000:
        aid_rate = 0.10 + (200000 - income) / (200000 - 120000) * 0.25
    else:
        aid_rate = max(0.0, 0.10 - (income - 200000) / 300000 * 0.10)

    if per_capita < 18000:
        aid_rate = min(0.98, aid_rate + 0.10)

    estimated_aid = int(round(gross_tuition * aid_rate))
    net_cost = max(0, gross_tuition - estimated_aid)
    budget_delta = budget_cap - net_cost

    if budget_delta >= 0:
        budget_status = f"Within Budget (Cap ${int(budget_cap):,})"
        budget_color = "emerald"
    else:
        budget_status = f"Exceeds Budget by ${int(abs(budget_delta)):,}"
        budget_color = "rose"

    return {
        "tuition_type": tuition_type,
        "gross_tuition": gross_tuition,
        "estimated_aid": estimated_aid,
        "net_cost": net_cost,
        "budget_cap": budget_cap,
        "budget_delta": budget_delta,
        "budget_status": budget_status,
        "budget_color": budget_color
    }

@app.route('/')
def home():
    return render_template(
        'index.html',
        supabase_url=os.environ.get("SUPABASE_URL", ""),
        supabase_anon_key=os.environ.get("SUPABASE_ANON_KEY", "")
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "operational",
        "localization": "US Higher-Ed Framework (4.0 Scale / SAT / ACT)",
        "active_llm_target": GROQ_MODEL_ID,
        "api_key_configured": bool(groq_client),
        "supabase_configured": bool(supabase)
    }), 200

@app.route('/api/user/profile', methods=['GET', 'POST'])
def handle_user_profile():
    if not supabase:
        return jsonify({"error": "Supabase connection uninitialized"}), 500

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip() if "Bearer " in auth_header else ""

    if not token:
        return jsonify({"error": "Missing authorization token"}), 401

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            return jsonify({"error": "Invalid authentication token"}), 401

        user_id = user_response.user.id

        if request.method == 'GET':
            res = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            profile = res.data[0] if res.data else None
            return jsonify({"profile": profile}), 200

        elif request.method == 'POST':
            data = request.json or {}
            profile_payload = {
                "id": user_id,
                "email": user_response.user.email,
                "home_city": data.get("home_city", ""),
                "gpa": float(data.get("gpa", 3.5)),
                "sat": int(data.get("sat")) if data.get("sat") else None,
                "act": int(data.get("act")) if data.get("act") else None,
                "major": data.get("major", ""),
                "region": data.get("region", ""),
                "campus": data.get("campus", ""),
                "dna": data.get("dna", []),
                "state_of_residence": data.get("state_of_residence", "NY"),
                "household_income": float(data.get("household_income", 100000)),
                "family_size": int(data.get("family_size", 4)),
                "annual_budget_cap": float(data.get("annual_budget_cap", 30000))
            }
            res = supabase.table("user_profiles").upsert(profile_payload).execute()
            return jsonify({"status": "success", "profile": res.data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/match/student', methods=['POST'])
def match_student():
    data = request.json or {}

    # Baseline Factual Inputs
    gpa = float(data.get('gpa', 3.5))
    sat = int(data.get('sat')) if data.get('sat') else None
    act = int(data.get('act')) if data.get('act') else None
    major = data.get('major', '')
    region = data.get('region', '')
    campus_type = data.get('campus_type', '')
    selected_dna = data.get('dna', [])
    state_of_residence = data.get('state_of_residence', 'NY')
    household_income = data.get('household_income', 100000)
    family_size = data.get('family_size', 4)
    annual_budget_cap = data.get('annual_budget_cap', 30000)

    # Hypothetical Scenario Parameters
    is_hypothetical = bool(data.get('is_hypothetical', False))
    target_uni_id = data.get('hypothetical_target_uni_id')

    hyp_gpa = float(data.get('hypothetical_gpa', gpa)) if is_hypothetical else gpa
    hyp_sat = int(data.get('hypothetical_sat')) if (is_hypothetical and data.get('hypothetical_sat')) else sat
    hyp_act = int(data.get('hypothetical_act')) if (is_hypothetical and data.get('hypothetical_act')) else act
    hyp_dna = data.get('hypothetical_dna', selected_dna) if is_hypothetical else selected_dna
    hyp_state = data.get('hypothetical_state', state_of_residence) if is_hypothetical else state_of_residence
    hyp_income = data.get('hypothetical_income', household_income) if is_hypothetical else household_income
    hyp_family_size = data.get('hypothetical_family_size', family_size) if is_hypothetical else family_size
    hyp_budget_cap = data.get('hypothetical_budget_cap', annual_budget_cap) if is_hypothetical else annual_budget_cap

    matches = []
    for uni in UNIVERSITIES:
        # Factual Calculation
        prob, tier, color = calculate_admission_probability(
            uni, gpa, sat, act, major, region, campus_type, selected_dna
        )
        fin_fit = calculate_financial_fit(
            uni, state_of_residence, household_income, family_size, annual_budget_cap
        )

        # Hypothetical Calculation
        hyp_data = {"active": False}
        if is_hypothetical and (target_uni_id is None or target_uni_id == "" or int(target_uni_id) == uni['id']):
            hyp_prob, hyp_tier, hyp_color = calculate_admission_probability(
                uni, hyp_gpa, hyp_sat, hyp_act, major, region, campus_type, hyp_dna
            )
            hyp_fin_fit = calculate_financial_fit(
                uni, hyp_state, hyp_income, hyp_family_size, hyp_budget_cap
            )
            prob_delta = hyp_prob - prob

            hyp_data = {
                "active": True,
                "probability": hyp_prob,
                "probability_delta": prob_delta,
                "tier": hyp_tier,
                "color": hyp_color,
                "financial": hyp_fin_fit,
                "reasoning": f"Simulated scenario shift: GPA {gpa:.2f} ➔ {hyp_gpa:.2f}, SAT {sat or 'N/A'} ➔ {hyp_sat or 'N/A'}. Probability changes by {hyp_prob - prob:+d}%."
            }

        matches.append({
            "id": uni['id'],
            "university": uni['name'],
            "rank": uni['id'],
            "tier": tier,
            "probability": prob,
            "color": color,
            "region": uni['region'],
            "campus_type": uni['campus_type'],
            "state": uni['state'],
            "location": f"{uni['region']} Campus ({uni['state']})",
            "distance_str": f"State Residency Zone: {uni['state']}",
            "known_for": ", ".join(uni['majors']),
            "testing_policy": "Test-Optional" if prob > 60 else "Test-Required",
            "testing_desc": "Standardized scores calibrated against national average matriculation standards.",
            "testing_context": "Evaluated within context of local high school benchmarks.",
            "dna_tags": uni['dna'],
            "financial": fin_fit,
            "hypothetical": hyp_data,
            "reasoning": f"Academic thresholds establish profile alignment for the {uni['region']} market framework."
        })

    if is_hypothetical:
        matches.sort(key=lambda x: x['hypothetical']['probability'] if x['hypothetical'].get('active') else x['probability'], reverse=True)
    else:
        matches.sort(key=lambda x: x['probability'], reverse=True)

    return jsonify({"matches": matches})

@app.route('/api/match/institute', methods=['POST'])
def match_institute():
    data = request.json or {}
    min_gpa = float(data.get('min_gpa', 3.0))
    target_dna = data.get('target_dna', [])
    anonymize = data.get('anonymize', False)

    candidates = []
    for s in MOCK_STUDENTS:
        if s['gpa'] < min_gpa:
            continue
            
        dna_matches = len(set(target_dna) & set(s['dna']))
        fit_score = int((dna_matches / max(len(target_dna), 1)) * 60) + int((s['gpa'] / 4.0) * 40)
        fit_score = min(100, max(15, fit_score))
        
        display_name = f"Applicant #{s['id']}" if anonymize else s['name']
        
        candidates.append({
            "id": s['id'],
            "name": display_name,
            "gpa": s['gpa'],
            "sat": s['sat'],
            "act": s['act'],
            "major": s['target_major'],
            "dna": s['dna'],
            "fit_score": fit_score
        })

    candidates.sort(key=lambda x: x['fit_score'], reverse=True)
    return jsonify({"candidates": candidates})

@app.route('/api/advisor/profile', methods=['POST'])
def profile_optimizer():
    """Generates personalized tactical advice using the active Groq inference engine."""
    data = request.json or {}
    university = data.get('university', 'Target Institution')
    tier = data.get('tier', 'Target')
    gpa = data.get('gpa', 3.5)
    sat = data.get('sat', 1300)
    act = data.get('act', 28)
    dna = data.get('dna', [])
    is_hypothetical = data.get('is_hypothetical', False)
    hypothetical_gpa = data.get('hypothetical_gpa')
    hypothetical_sat = data.get('hypothetical_sat')

    if is_hypothetical and hypothetical_gpa:
        prompt = (
            f"Context: You are the UniMatch AI Higher-Education Profile Optimizer advisor evaluating a HYPOTHETICAL scenario.\n"
            f"Task: Evaluate how changing student metrics impacts chances for {university} (currently {tier} match).\n"
            f"Factual Profile -> GPA: {gpa}/4.0, SAT: {sat}, ACT: {act}, DNA: {', '.join(dna)}.\n"
            f"Simulated Profile -> Predicted GPA: {hypothetical_gpa}/4.0, Predicted SAT: {hypothetical_sat or sat}.\n"
            f"Constraints: Provide strict, actionable advice explaining how this specific boost impacts acceptance chances and financial aid optimization. Keep output under 3 sentences."
        )
    else:
        prompt = (
            f"Context: You are the UniMatch AI Higher-Education Profile Optimizer advisor.\n"
            f"Task: Evaluate this student profile applying to {university} (categorized as a {tier} match).\n"
            f"Student Metrics: Unweighted GPA: {gpa}/4.0, SAT: {sat}, ACT: {act}, Profile Archetypes: {', '.join(dna)}.\n"
            f"Constraints: Provide strict, hyper-specific contextual advice tailored to the US university landscape. "
            f"Explicitly quantify how adding leadership or altering strategic targets impacts acceptance chances. "
            f"Keep the output professional, actionable, structured, and limited to a maximum of 3 sentences."
        )

    if not groq_client:
        if is_hypothetical:
            return jsonify({
                "advice": f"In this hypothetical scenario with a GPA of {hypothetical_gpa} and SAT of {hypothetical_sat or sat}, your profile alignment with {university} improves significantly. This metric boost elevates your admission probability tier while maximizing merit and need-based financial assistance eligibility."
            })
        return jsonify({
            "advice": f"Your current metrics match the baseline, but your profile lacks dedicated alignment with institutional targets at {university}. Adding a regional leadership role or an advanced independent research project could boost your relative target baseline by an estimated 12% to 15%."
        })

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )
        return jsonify({"advice": completion.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"advice": f"Inference pipeline execution error: {str(e)}"}), 500

@app.route('/api/advisor/outreach', methods=['POST'])
def outreach_strategy():
    """Builds an algorithmic recruitment summary outlining general strategy insights."""
    data = request.json or {}
    min_gpa = data.get('min_gpa', 3.5)
    target_dna = data.get('target_dna', [])
    
    prompt = (
        f"Context: You are an expert AI/ML Higher-Education Solutions Architect advising an admissions team.\n"
        f"Task: Create a highly analytical institutional outreach summary based on chosen parameters:\n"
        f"Recruitment Target Criteria: Minimum GPA: {min_gpa}/4.0, DNA Requirements: {', '.join(target_dna)}.\n"
        f"Constraints: Outline a data-driven strategy to capture high-yield candidates matching this DNA footprint "
        f"in the competitive US landscape. Keep the response completely objective, professional, and limited to 3 distinct sentences."
    )

    if not groq_client:
        return jsonify({
            "strategy": f"Deploy data-driven recruitment pipelines prioritizing secondary high schools with deep concentrations in {', '.join(target_dna)} tracks. Emphasize early engagement paradigms, specialized cohort scholarships, and institutional research allowances to shift yield metrics across the matching matrix."
        })

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=250
        )
        return jsonify({"strategy": completion.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"strategy": f"Strategy parsing pipeline exception: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)