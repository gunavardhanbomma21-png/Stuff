import os
import random
import math
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

# --- GEOGRAPHIC COORDINATES MATRIX FOR USA STATES, TERRITORIES & INTERNATIONAL ---
STATE_COORDINATES = {
    # 50 US States + DC
    "AL": (32.806671, -86.791130), "AK": (61.370716, -152.404419), "AZ": (33.729759, -111.431221),
    "AR": (34.969704, -92.373123), "CA": (36.116203, -119.681564), "CO": (39.059811, -105.311104),
    "CT": (41.597782, -72.755371), "DE": (39.318523, -75.507141), "DC": (38.897438, -77.026817),
    "FL": (27.766279, -81.686783), "GA": (33.040619, -83.643074), "HI": (21.094318, -157.498337),
    "ID": (44.240459, -114.478828), "IL": (40.349457, -88.986137), "IN": (39.849426, -86.258278),
    "IA": (42.011539, -92.980016), "KS": (38.526600, -96.726486), "KY": (37.668140, -84.670067),
    "LA": (31.169546, -91.867805), "ME": (44.693947, -69.381927), "MD": (39.063946, -76.802101),
    "MA": (42.230171, -71.530106), "MI": (43.326618, -84.536095), "MN": (45.694454, -93.900192),
    "MS": (32.741646, -89.678696), "MO": (38.456085, -92.288368), "MT": (46.921925, -110.454353),
    "NE": (41.125370, -98.268082), "NV": (38.313515, -117.055374), "NH": (43.452492, -71.563896),
    "NJ": (40.298960, -74.521011), "NM": (34.840515, -106.248482), "NY": (42.165726, -74.948051),
    "NC": (35.630066, -79.806419), "ND": (47.528912, -99.784012), "OH": (40.388783, -82.764915),
    "OK": (35.565342, -96.928917), "OR": (44.572021, -122.070938), "PA": (40.590752, -77.209755),
    "RI": (41.680893, -71.511780), "SC": (33.856892, -80.945007), "SD": (44.299782, -99.438828),
    "TN": (35.747845, -86.692345), "TX": (31.054487, -97.563461), "UT": (40.150032, -111.862434),
    "VT": (44.045876, -72.710686), "VA": (37.769337, -78.169968), "WA": (47.400902, -121.490494),
    "WV": (38.491226, -80.954453), "WI": (44.268543, -89.616508), "WY": (42.755966, -107.302490),
    # US Territories
    "PR": (18.220833, -66.590149), "GU": (13.444304, 144.793731), "VI": (18.335765, -64.896335),
    "AS": (-14.270972, -170.132217), "MP": (15.097900, 145.673900),
    # Foreign / International Student
    "INT": (20.000000, 0.000000)
}

def calculate_approx_distance(user_state, uni_state):
    """Calculates approximate geographical distance in miles using Haversine formula."""
    s1 = (user_state or 'NY').strip().upper()
    s2 = (uni_state or 'NY').strip().upper()

    if s1 == 'INT':
        return 4800  # Baseline flight distance approximation for foreign students

    if s1 == s2:
        return 35  # Baseline intra-state distance approximation

    coord1 = STATE_COORDINATES.get(s1, STATE_COORDINATES.get('NY'))
    coord2 = STATE_COORDINATES.get(s2, STATE_COORDINATES.get('NY'))

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(round(R * c))

# --- MOCK DATA ENGINE SEED MATRIX ---
random.seed(42)

# Standardized Universities Matrix Aligned with US News National Universities & Colleges Rankings
UNIVERSITIES = [
    {"id": 1, "name": "Princeton University", "min_gpa": 3.9, "avg_sat": 1540, "avg_act": 35, "region": "Northeast", "campus_type": "Suburban", "majors": ["Public Policy", "Computer Science", "Economics", "Mathematics", "Physics"], "dna": ["Research", "Leadership", "STEM", "Student Government"], "state": "NJ", "is_private": True, "in_state_tuition": 59710, "out_of_state_tuition": 59710, "us_news_rank": 1},
    {"id": 2, "name": "MIT", "min_gpa": 3.8, "avg_sat": 1540, "avg_act": 35, "region": "Northeast", "campus_type": "Urban", "majors": ["Computer Science", "Mechanical Engineering", "Electrical Engineering", "Bioengineering", "Data Science"], "dna": ["STEM", "Research", "Innovation", "Robotics"], "state": "MA", "is_private": True, "in_state_tuition": 59750, "out_of_state_tuition": 59750, "us_news_rank": 2},
    {"id": 3, "name": "Harvard University", "min_gpa": 3.9, "avg_sat": 1530, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Political Science", "Economics", "History", "Psychology", "Biochemistry"], "dna": ["Leadership", "Community Service", "Arts", "Debate & Model UN", "Student Government"], "state": "MA", "is_private": True, "in_state_tuition": 59076, "out_of_state_tuition": 59076, "us_news_rank": 3},
    {"id": 4, "name": "Stanford University", "min_gpa": 3.9, "avg_sat": 1520, "avg_act": 34, "region": "West", "campus_type": "Suburban", "majors": ["Computer Science", "Business Administration", "Bioengineering", "Data Science", "Psychology"], "dna": ["STEM", "Leadership", "First-Gen", "DECA & Business"], "state": "CA", "is_private": True, "in_state_tuition": 62484, "out_of_state_tuition": 62484, "us_news_rank": 4},
    {"id": 5, "name": "Yale University", "min_gpa": 3.9, "avg_sat": 1520, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Political Science", "History", "Economics", "Biology", "English & Literature"], "dna": ["Leadership", "Arts", "Research", "Debate & Model UN"], "state": "CT", "is_private": True, "in_state_tuition": 62250, "out_of_state_tuition": 62250, "us_news_rank": 5},
    {"id": 6, "name": "University of Chicago", "min_gpa": 3.8, "avg_sat": 1520, "avg_act": 34, "region": "Midwest", "campus_type": "Urban", "majors": ["Economics", "Mathematics", "Sociology", "Political Science", "Physics"], "dna": ["Research", "Innovation", "Debate & Model UN", "Journalism & Publishing"], "state": "IL", "is_private": True, "in_state_tuition": 63801, "out_of_state_tuition": 63801, "us_news_rank": 6},
    {"id": 7, "name": "Johns Hopkins University", "min_gpa": 3.9, "avg_sat": 1530, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Bioengineering", "Biology", "Neuroscience", "Public Health", "Chemistry"], "dna": ["STEM", "Research", "Tutoring & Mentorship", "Community Service"], "state": "MD", "is_private": True, "in_state_tuition": 60480, "out_of_state_tuition": 60480, "us_news_rank": 7},
    {"id": 8, "name": "University of Pennsylvania", "min_gpa": 3.8, "avg_sat": 1510, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Finance", "Business Administration", "Economics", "Nursing", "Computer Science"], "dna": ["DECA & Business", "Leadership", "STEM", "Innovation"], "state": "PA", "is_private": True, "in_state_tuition": 63452, "out_of_state_tuition": 63452, "us_news_rank": 7},
    {"id": 9, "name": "Northwestern University", "min_gpa": 3.8, "avg_sat": 1480, "avg_act": 33, "region": "Midwest", "campus_type": "Suburban", "majors": ["Journalism", "Economics", "Communication", "Theater", "Psychology"], "dna": ["Research", "Leadership", "Arts", "Journalism & Publishing"], "state": "IL", "is_private": True, "in_state_tuition": 64887, "out_of_state_tuition": 64887, "us_news_rank": 9},
    {"id": 10, "name": "Duke University", "min_gpa": 3.8, "avg_sat": 1510, "avg_act": 34, "region": "South", "campus_type": "Suburban", "majors": ["Biology", "Public Policy", "Computer Science", "Economics", "Biochemistry"], "dna": ["Athletics", "Research", "Leadership", "Debate & Model UN"], "state": "NC", "is_private": True, "in_state_tuition": 63450, "out_of_state_tuition": 63450, "us_news_rank": 10},
    {"id": 11, "name": "Caltech", "min_gpa": 3.9, "avg_sat": 1560, "avg_act": 36, "region": "West", "campus_type": "Suburban", "majors": ["Physics", "Mathematics", "Computer Science", "Electrical Engineering", "Aerospace Engineering"], "dna": ["STEM", "Research", "Innovation", "Robotics"], "state": "CA", "is_private": True, "in_state_tuition": 60864, "out_of_state_tuition": 60864, "us_news_rank": 11},
    {"id": 12, "name": "Dartmouth College", "min_gpa": 3.8, "avg_sat": 1480, "avg_act": 33, "region": "Northeast", "campus_type": "Rural", "majors": ["Economics", "Engineering Sciences", "Government", "Environmental Science", "History"], "dna": ["Leadership", "Community Service", "Athletics", "Environmental Club"], "state": "NH", "is_private": True, "in_state_tuition": 63684, "out_of_state_tuition": 63684, "us_news_rank": 12},
    {"id": 13, "name": "Brown University", "min_gpa": 3.8, "avg_sat": 1500, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Computer Science", "Biology", "Economics", "International Relations", "Public Health"], "dna": ["Research", "Innovation", "Arts", "Environmental Club"], "state": "RI", "is_private": True, "in_state_tuition": 62680, "out_of_state_tuition": 62680, "us_news_rank": 13},
    {"id": 14, "name": "Vanderbilt University", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "South", "campus_type": "Urban", "majors": ["Education", "Economics", "Music & Performing Arts", "Mechanical Engineering", "Psychology"], "dna": ["Leadership", "Community Service", "Innovation", "Student Government"], "state": "TN", "is_private": True, "in_state_tuition": 63946, "out_of_state_tuition": 63946, "us_news_rank": 14},
    {"id": 15, "name": "Rice University", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "South", "campus_type": "Urban", "majors": ["Architecture", "Bioengineering", "Computer Science", "Sport Management", "Psychology"], "dna": ["Research", "Diversity", "STEM", "Music & Performing Arts"], "state": "TX", "is_private": True, "in_state_tuition": 57210, "out_of_state_tuition": 57210, "us_news_rank": 15},
    {"id": 16, "name": "Washington University in St. Louis", "min_gpa": 3.8, "avg_sat": 1500, "avg_act": 33, "region": "Midwest", "campus_type": "Suburban", "majors": ["Biology", "Finance", "Graphic Design", "Psychology", "Computer Science"], "dna": ["Research", "Community Service", "Arts", "DECA & Business"], "state": "MO", "is_private": True, "in_state_tuition": 60590, "out_of_state_tuition": 60590, "us_news_rank": 15},
    {"id": 17, "name": "Cornell University", "min_gpa": 3.8, "avg_sat": 1470, "avg_act": 33, "region": "Northeast", "campus_type": "Rural", "majors": ["Computer Science", "Agriculture", "Hotel Administration", "Mechanical Engineering", "Architecture"], "dna": ["STEM", "Research", "Environmental Club", "Leadership"], "state": "NY", "is_private": True, "in_state_tuition": 63200, "out_of_state_tuition": 63200, "us_news_rank": 17},
    {"id": 18, "name": "Columbia University", "min_gpa": 3.8, "avg_sat": 1500, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Political Science", "Economics", "Film & Media", "Computer Science", "Neuroscience"], "dna": ["Leadership", "Arts", "Journalism & Publishing", "Debate & Model UN"], "state": "NY", "is_private": True, "in_state_tuition": 65340, "out_of_state_tuition": 65340, "us_news_rank": 18},
    {"id": 19, "name": "University of Notre Dame", "min_gpa": 3.7, "avg_sat": 1450, "avg_act": 33, "region": "Midwest", "campus_type": "Suburban", "majors": ["Finance", "Political Science", "Civil Engineering", "Theology", "Economics"], "dna": ["Leadership", "Community Service", "Athletics", "Tutoring & Mentorship"], "state": "IN", "is_private": True, "in_state_tuition": 60301, "out_of_state_tuition": 60301, "us_news_rank": 19},
    {"id": 20, "name": "UC Berkeley", "min_gpa": 3.7, "avg_sat": 1450, "avg_act": 32, "region": "West", "campus_type": "Urban", "majors": ["Computer Science", "Data Science", "Environmental Science", "Economics", "Cell Biology"], "dna": ["STEM", "Research", "Community Service", "Environmental Club"], "state": "CA", "is_private": False, "in_state_tuition": 14226, "out_of_state_tuition": 48176, "us_news_rank": 20},
    {"id": 21, "name": "UCLA", "min_gpa": 3.7, "avg_sat": 1440, "avg_act": 32, "region": "West", "campus_type": "Urban", "majors": ["Psychology", "Biology", "Film & Media", "Business Economics", "Political Science"], "dna": ["Arts", "Athletics", "STEM", "Diversity"], "state": "CA", "is_private": False, "in_state_tuition": 13804, "out_of_state_tuition": 44830, "us_news_rank": 20},
    {"id": 22, "name": "Carnegie Mellon University", "min_gpa": 3.8, "avg_sat": 1510, "avg_act": 34, "region": "Northeast", "campus_type": "Urban", "majors": ["Computer Science", "Electrical Engineering", "Robotics", "Fine Arts", "Business Administration"], "dna": ["STEM", "Robotics", "Innovation", "Arts"], "state": "PA", "is_private": True, "in_state_tuition": 61344, "out_of_state_tuition": 61344, "us_news_rank": 22},
    {"id": 23, "name": "Emory University", "min_gpa": 3.7, "avg_sat": 1450, "avg_act": 32, "region": "South", "campus_type": "Suburban", "majors": ["Nursing", "Business Administration", "Biology", "Psychology", "Neuroscience"], "dna": ["Community Service", "Research", "Tutoring & Mentorship", "DECA & Business"], "state": "GA", "is_private": True, "in_state_tuition": 57948, "out_of_state_tuition": 57948, "us_news_rank": 23},
    {"id": 24, "name": "Georgetown University", "min_gpa": 3.7, "avg_sat": 1460, "avg_act": 33, "region": "Northeast", "campus_type": "Urban", "majors": ["International Relations", "Political Science", "Finance", "Government", "Public Policy"], "dna": ["Debate & Model UN", "Leadership", "Student Government", "Community Service"], "state": "DC", "is_private": True, "in_state_tuition": 62052, "out_of_state_tuition": 62052, "us_news_rank": 24},
    {"id": 25, "name": "University of Michigan", "min_gpa": 3.6, "avg_sat": 1400, "avg_act": 31, "region": "Midwest", "campus_type": "Urban", "majors": ["Mechanical Engineering", "Business Administration", "Computer Science", "Psychology", "Sports Management"], "dna": ["Athletics", "Leadership", "STEM", "DECA & Business"], "state": "MI", "is_private": False, "in_state_tuition": 17768, "out_of_state_tuition": 57233, "us_news_rank": 25},
    {"id": 26, "name": "USC", "min_gpa": 3.7, "avg_sat": 1440, "avg_act": 32, "region": "West", "campus_type": "Urban", "majors": ["Film & Media", "Business Administration", "Communications", "Computer Science", "Performing Arts"], "dna": ["Arts", "Innovation", "Leadership", "DECA & Business"], "state": "CA", "is_private": True, "in_state_tuition": 64632, "out_of_state_tuition": 64632, "us_news_rank": 26},
    {"id": 27, "name": "University of Virginia", "min_gpa": 3.7, "avg_sat": 1430, "avg_act": 32, "region": "South", "campus_type": "Suburban", "majors": ["History", "Commerce", "Economics", "Psychology", "Biochemistry"], "dna": ["Leadership", "Research", "Honor Code", "Debate & Model UN"], "state": "VA", "is_private": False, "in_state_tuition": 18980, "out_of_state_tuition": 54380, "us_news_rank": 27},
    {"id": 28, "name": "UNC Chapel Hill", "min_gpa": 3.6, "avg_sat": 1390, "avg_act": 31, "region": "South", "campus_type": "Suburban", "majors": ["Journalism", "Biology", "Business Administration", "Political Science", "Psychology"], "dna": ["Community Service", "Athletics", "Journalism & Publishing", "Leadership"], "state": "NC", "is_private": False, "in_state_tuition": 8998, "out_of_state_tuition": 37558, "us_news_rank": 28},
    {"id": 29, "name": "NYU", "min_gpa": 3.5, "avg_sat": 1410, "avg_act": 31, "region": "Northeast", "campus_type": "Urban", "majors": ["Fine Arts", "Film & Media", "Economics", "Performing Arts", "Business Administration"], "dna": ["Arts", "Innovation", "Diversity", "Music & Performing Arts", "Journalism & Publishing"], "state": "NY", "is_private": True, "in_state_tuition": 60438, "out_of_state_tuition": 60438, "us_news_rank": 29},
    {"id": 30, "name": "University of Florida", "min_gpa": 3.5, "avg_sat": 1360, "avg_act": 29, "region": "South", "campus_type": "Suburban", "majors": ["Biology", "Business Administration", "Engineering", "Nursing", "Psychology"], "dna": ["Athletics", "Community Service", "First-Gen", "Tutoring & Mentorship"], "state": "FL", "is_private": False, "in_state_tuition": 6380, "out_of_state_tuition": 28658, "us_news_rank": 30},
    {"id": 31, "name": "UT Austin", "min_gpa": 3.6, "avg_sat": 1380, "avg_act": 30, "region": "South", "campus_type": "Urban", "majors": ["Computer Science", "Business Administration", "Petroleum Engineering", "Advertising", "Biology"], "dna": ["First-Gen", "STEM", "Innovation", "Robotics"], "state": "TX", "is_private": False, "in_state_tuition": 11698, "out_of_state_tuition": 41070, "us_news_rank": 31},
    {"id": 32, "name": "Georgia Tech", "min_gpa": 3.6, "avg_sat": 1420, "avg_act": 31, "region": "South", "campus_type": "Urban", "majors": ["Aerospace Engineering", "Computer Science", "Industrial Engineering", "Electrical Engineering", "Cybersecurity"], "dna": ["STEM", "Innovation", "Research", "Robotics"], "state": "GA", "is_private": False, "in_state_tuition": 11764, "out_of_state_tuition": 32876, "us_news_rank": 32},
    {"id": 33, "name": "UC Davis", "min_gpa": 3.5, "avg_sat": 1330, "avg_act": 28, "region": "West", "campus_type": "Suburban", "majors": ["Agriculture", "Environmental Science", "Biochemistry", "Psychology", "Veterinary Studies"], "dna": ["Environmental Club", "STEM", "Community Service", "Research"], "state": "CA", "is_private": False, "in_state_tuition": 14800, "out_of_state_tuition": 44500, "us_news_rank": 33},
    {"id": 34, "name": "UC San Diego", "min_gpa": 3.6, "avg_sat": 1370, "avg_act": 30, "region": "West", "campus_type": "Suburban", "majors": ["Bioengineering", "Data Science", "Computer Science", "Oceanography", "Economics"], "dna": ["STEM", "Research", "Innovation", "Environmental Club"], "state": "CA", "is_private": False, "in_state_tuition": 14900, "out_of_state_tuition": 44600, "us_news_rank": 34},
    {"id": 35, "name": "UIUC", "min_gpa": 3.5, "avg_sat": 1350, "avg_act": 29, "region": "Midwest", "campus_type": "Suburban", "majors": ["Computer Science", "Civil Engineering", "Accounting", "Physics", "Agriculture"], "dna": ["STEM", "Robotics", "Innovation", "DECA & Business"], "state": "IL", "is_private": False, "in_state_tuition": 17366, "out_of_state_tuition": 36068, "us_news_rank": 35},
    {"id": 36, "name": "University of Wisconsin-Madison", "min_gpa": 3.5, "avg_sat": 1340, "avg_act": 29, "region": "Midwest", "campus_type": "Urban", "majors": ["Biology", "Economics", "Psychology", "Computer Science", "Journalism"], "dna": ["Athletics", "Research", "Community Service", "Leadership"], "state": "WI", "is_private": False, "in_state_tuition": 10796, "out_of_state_tuition": 39427, "us_news_rank": 36},
    {"id": 37, "name": "Boston University", "min_gpa": 3.5, "avg_sat": 1380, "avg_act": 30, "region": "Northeast", "campus_type": "Urban", "majors": ["Communications", "Business Administration", "Biochemistry", "International Relations", "Film & Media"], "dna": ["Arts", "Leadership", "Diversity", "Journalism & Publishing"], "state": "MA", "is_private": True, "in_state_tuition": 61050, "out_of_state_tuition": 61050, "us_news_rank": 37},
    {"id": 38, "name": "Purdue University", "min_gpa": 3.5, "avg_sat": 1320, "avg_act": 29, "region": "Midwest", "campus_type": "Suburban", "majors": ["Aerospace Engineering", "Computer Science", "Agriculture", "Cybersecurity", "Mechanical Engineering"], "dna": ["STEM", "Innovation", "First-Gen", "Robotics"], "state": "IN", "is_private": False, "in_state_tuition": 9992, "out_of_state_tuition": 28794, "us_news_rank": 38},
    {"id": 39, "name": "Ohio State University", "min_gpa": 3.4, "avg_sat": 1310, "avg_act": 28, "region": "Midwest", "campus_type": "Urban", "majors": ["Agriculture", "Business Administration", "Finance", "Nursing", "Psychology"], "dna": ["Athletics", "First-Gen", "Community Service"], "state": "OH", "is_private": False, "in_state_tuition": 12485, "out_of_state_tuition": 36722, "us_news_rank": 39},
    {"id": 40, "name": "University of Washington", "min_gpa": 3.5, "avg_sat": 1350, "avg_act": 29, "region": "West", "campus_type": "Urban", "majors": ["Bioengineering", "Computer Science", "Environmental Science", "Nursing", "Business Administration"], "dna": ["STEM", "Research", "Diversity", "Environmental Club"], "state": "WA", "is_private": False, "in_state_tuition": 12242, "out_of_state_tuition": 40740, "us_news_rank": 40},
    {"id": 41, "name": "Williams College", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "Northeast", "campus_type": "Rural", "majors": ["Mathematics", "History", "Economics", "English & Literature", "Art History"], "dna": ["Research", "Community Service", "Arts", "Tutoring & Mentorship"], "state": "MA", "is_private": True, "in_state_tuition": 64540, "out_of_state_tuition": 64540, "us_news_rank": 41},
    {"id": 42, "name": "Amherst College", "min_gpa": 3.8, "avg_sat": 1480, "avg_act": 33, "region": "Northeast", "campus_type": "Rural", "majors": ["Economics", "English & Literature", "Mathematics", "Political Science", "Psychology"], "dna": ["Leadership", "Arts", "Research", "Community Service"], "state": "MA", "is_private": True, "in_state_tuition": 63800, "out_of_state_tuition": 63800, "us_news_rank": 42},
    {"id": 43, "name": "Swarthmore College", "min_gpa": 3.8, "avg_sat": 1490, "avg_act": 33, "region": "Northeast", "campus_type": "Suburban", "majors": ["Economics", "Biology", "Political Science", "Engineering", "Sociology"], "dna": ["Research", "Debate & Model UN", "Community Service", "STEM"], "state": "PA", "is_private": True, "in_state_tuition": 58856, "out_of_state_tuition": 58856, "us_news_rank": 43},
    {"id": 44, "name": "Bowdoin College", "min_gpa": 3.8, "avg_sat": 1470, "avg_act": 32, "region": "Northeast", "campus_type": "Rural", "majors": ["Government", "Economics", "Environmental Science", "History", "Mathematics"], "dna": ["Leadership", "Environmental Club", "Athletics", "Community Service"], "state": "ME", "is_private": True, "in_state_tuition": 60952, "out_of_state_tuition": 60952, "us_news_rank": 44},
    {"id": 45, "name": "Pomona College", "min_gpa": 3.8, "avg_sat": 1480, "avg_act": 33, "region": "West", "campus_type": "Suburban", "majors": ["Economics", "Computer Science", "Mathematics", "Media Studies", "Neuroscience"], "dna": ["STEM", "Arts", "Leadership", "Diversity"], "state": "CA", "is_private": True, "in_state_tuition": 58328, "out_of_state_tuition": 58328, "us_news_rank": 45}
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
    majors = [
        "Computer Science", "Data Science", "Mechanical Engineering", "Electrical Engineering",
        "Bioengineering", "Business Administration", "Finance", "Economics", "Biology",
        "Psychology", "Political Science", "Journalism", "Fine Arts", "Mathematics"
    ]
    minors = [
        "None / Undecided", "Data Analytics", "Entrepreneurship", "Creative Writing",
        "Spanish", "Mathematics", "Statistics", "Psychology", "Economics", "Environmental Studies"
    ]
    regions = ["Northeast", "West", "Midwest", "South"]
    campuses = ["Urban", "Suburban", "Rural"]
    dna_pools = [
        "STEM", "Leadership", "Community Service", "Arts", "Athletics", "First-Gen", 
        "Research", "Innovation", "Debate & Model UN", "Robotics", "Student Government", 
        "Music & Performing Arts", "DECA & Business", "Environmental Club", "Tutoring & Mentorship", "Journalism & Publishing"
    ]
    
    students = []
    for i in range(50):
        gpa = round(random.uniform(3.0, 4.0), 2)
        sat = int(random.randint(1100, 1600) / 10) * 10
        act = random.randint(22, 36)
        student_dna = list(set(random.choices(dna_pools, k=random.randint(2, 5))))
        
        students.append({
            "id": 1482 + i,
            "name": names[i],
            "gpa": gpa,
            "sat": sat,
            "act": act,
            "major": random.choice(majors),
            "minor": random.choice(minors),
            "target_major": random.choice(majors),
            "target_minor": random.choice(minors),
            "preferred_region": random.choice(regions),
            "preferred_campus_type": random.choice(campuses),
            "dna": student_dna,
            "is_real_user": False
        })
    return students

MOCK_STUDENTS = generate_mock_students()

def calculate_admission_probability(uni, gpa, sat, act, major, region, campus_type, selected_dna, minor=None):
    """Calculates deterministic admission probability with heavy emphasis on GPA, SAT, ACT, and Extracurricular DNA."""
    # 1. GPA Component (Up to 45 pts) - Primary Academic Benchmark
    gpa_diff = gpa - uni['min_gpa']
    if gpa_diff >= 0:
        gpa_score = min(45.0, 25.0 + gpa_diff * 40.0)
    else:
        gpa_score = max(0.0, 25.0 + gpa_diff * 50.0)

    # 2. SAT Component (Up to 30 pts)
    sat_score = 15.0
    if sat is not None and sat > 0:
        sat_diff = sat - uni['avg_sat']
        if sat_diff >= 0:
            sat_score = min(30.0, 20.0 + (sat_diff / 10.0) * 1.25)
        else:
            sat_score = max(0.0, 20.0 + (sat_diff / 10.0) * 1.5)

    # 3. ACT Component (Up to 30 pts)
    act_score = 15.0
    if act is not None and act > 0:
        act_diff = act - uni['avg_act']
        if act_diff >= 0:
            act_score = min(30.0, 20.0 + act_diff * 3.0)
        else:
            act_score = max(0.0, 20.0 + act_diff * 4.0)

    # Combine academic components with heavy weighting (GPA 45%, SAT 30%, ACT 25%)
    academic_weight = (gpa_score * 0.45) + (sat_score * 0.30) + (act_score * 0.25)

    # 4. Extracurricular DNA Alignment Component (Up to 25 pts)
    dna_matches = len(set(selected_dna or []) & set(uni['dna']))
    extracurricular_score = min(25.0, dna_matches * 7.5)

    # 5. General Preference Alignment (Region, Campus, Major, Minor) (Up to 15 pts)
    pref_score = 0.0
    if region == uni['region']:
        pref_score += 4.0
    if campus_type == uni['campus_type']:
        pref_score += 3.0
    if major in uni['majors']:
        pref_score += 6.0
    if minor and minor != "None / Undecided" and minor in uni['majors']:
        pref_score += 2.0

    # Selectivity penalty scaling with official US News National Rank
    us_news_rank = uni.get('us_news_rank', uni['id'])
    selectivity_factor = max(0.82, 1.0 - (50 - us_news_rank) * 0.003)

    raw_total = (academic_weight * 1.35) + (extracurricular_score * 1.1) + pref_score
    seed_offset = ((uni['id'] * 13) % 7) - 3
    prob = int(round(max(5.0, min(98.0, (raw_total * selectivity_factor) + seed_offset))))

    if prob >= 75:
        tier, color = "Safety", "emerald"
    elif prob >= 45:
        tier, color = "Target", "amber"
    else:
        tier, color = "Reach", "rose"

    return prob, tier, color

def calculate_financial_fit(uni, state_of_residence, household_income, family_size, annual_budget_cap):
    """Calculates residency tuition, estimated need-based financial aid, and annual budget cap status."""
    user_state = (state_of_residence or "NY").strip().upper()
    uni_state = uni.get('state', '').upper()
    is_private = uni.get('is_private', False)

    if user_state == "INT":
        tuition_type = "International Standard"
        gross_tuition = uni.get('out_of_state_tuition', 50000)
    elif is_private:
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

def calculate_candidate_fit_score(candidate, min_gpa, min_sat, min_act, testing_mode, target_major, target_dna, target_minor=None):
    """Calculates dynamic institutional fit score (0-100%) emphasizing academic & extracurricular benchmarks."""
    score = 50.0

    # 1. GPA Baseline Fit (Up to 35 pts)
    cand_gpa = float(candidate.get("gpa", 0.0))
    if cand_gpa >= min_gpa:
        score += 20.0 + min(15.0, (cand_gpa - min_gpa) * 30.0)
    else:
        score -= min(35.0, (min_gpa - cand_gpa) * 45.0)

    # 2. Testing Baseline Fit (SAT & ACT) (Up to 30 pts)
    cand_sat = candidate.get("sat")
    cand_act = candidate.get("act")

    if testing_mode == "sat_only":
        if cand_sat and cand_sat >= min_sat:
            score += 25.0 + min(5.0, (cand_sat - min_sat) / 15.0)
        else:
            score -= 20.0
    elif testing_mode == "act_only":
        if cand_act and cand_act >= min_act:
            score += 25.0 + min(5.0, (cand_act - min_act) * 2.0)
        else:
            score -= 20.0
    elif testing_mode == "superscore":
        sat_passed = bool(cand_sat and cand_sat >= min_sat)
        act_passed = bool(cand_act and cand_act >= min_act)
        if sat_passed or act_passed:
            score += 28.0
        else:
            score -= 15.0
    else:  # "all" or default
        if cand_sat and min_sat > 0 and cand_sat >= min_sat:
            sat_boost = min(15.0, 10.0 + (cand_sat - min_sat) / 20.0)
            score += sat_boost
        if cand_act and min_act > 0 and cand_act >= min_act:
            act_boost = min(15.0, 10.0 + (cand_act - min_act) * 1.5)
            score += act_boost

    # 3. Target Major & Minor Alignment (Up to 10 pts)
    cand_major = candidate.get("major") or candidate.get("target_major", "")
    if target_major and target_major.strip():
        if cand_major.lower() == target_major.strip().lower():
            score += 8.0
        else:
            score -= 3.0

    cand_minor = candidate.get("minor") or candidate.get("target_minor", "")
    if target_minor and target_minor.strip() and target_minor != "None / Undecided":
        if cand_minor.lower() == target_minor.strip().lower():
            score += 4.0

    # 4. Extracurricular & Club Priorities Overlap (Up to 25 pts)
    cand_dna = candidate.get("dna", [])
    if target_dna and len(target_dna) > 0:
        matches = len(set(cand_dna) & set(target_dna))
        score += min(25.0, matches * 9.0)

    return int(round(max(5.0, min(99.0, score))))

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
                "minor": data.get("minor", "None / Undecided"),
                "region": data.get("region", ""),
                "campus": data.get("campus_type") or data.get("campus", ""),
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
    minor = data.get('minor', 'None / Undecided')
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
    hyp_minor = data.get('hypothetical_minor', minor) if is_hypothetical else minor
    hyp_dna = data.get('hypothetical_dna', selected_dna) if is_hypothetical else selected_dna
    hyp_state = data.get('hypothetical_state', state_of_residence) if is_hypothetical else state_of_residence
    hyp_income = data.get('hypothetical_income', household_income) if is_hypothetical else household_income
    hyp_family_size = data.get('hypothetical_family_size', family_size) if is_hypothetical else family_size
    hyp_budget_cap = data.get('hypothetical_budget_cap', annual_budget_cap) if is_hypothetical else annual_budget_cap

    matches = []
    for uni in UNIVERSITIES:
        prob, tier, color = calculate_admission_probability(
            uni, gpa, sat, act, major, region, campus_type, selected_dna, minor
        )
        fin_fit = calculate_financial_fit(
            uni, state_of_residence, household_income, family_size, annual_budget_cap
        )

        approx_dist = calculate_approx_distance(state_of_residence, uni['state'])
        if state_of_residence == "INT":
            dist_str = f"International Student Zone (~{approx_dist:,} mi)"
        elif state_of_residence == uni['state']:
            dist_str = f"In-State Zone (~{approx_dist} mi)"
        else:
            dist_str = f"Out-of-State Zone (~{approx_dist:,} mi)"

        hyp_data = {"active": False}
        if is_hypothetical and (target_uni_id is None or target_uni_id == "" or int(target_uni_id) == uni['id']):
            hyp_prob, hyp_tier, hyp_color = calculate_admission_probability(
                uni, hyp_gpa, hyp_sat, hyp_act, major, region, campus_type, hyp_dna, hyp_minor
            )
            hyp_fin_fit = calculate_financial_fit(
                uni, hyp_state, hyp_income, hyp_family_size, hyp_budget_cap
            )
            prob_delta = hyp_prob - prob

            hyp_dist = calculate_approx_distance(hyp_state, uni['state'])

            hyp_data = {
                "active": True,
                "probability": hyp_prob,
                "probability_delta": prob_delta,
                "tier": hyp_tier,
                "color": hyp_color,
                "financial": hyp_fin_fit,
                "distance_miles": hyp_dist,
                "reasoning": f"Simulated scenario shift: GPA {gpa:.2f} ➔ {hyp_gpa:.2f}, SAT {sat or 'N/A'} ➔ {hyp_sat or 'N/A'}. Match probability changes by {hyp_prob - prob:+d}%."
            }

        matches.append({
            "id": uni['id'],
            "university": uni['name'],
            "rank": uni.get('us_news_rank', uni['id']),
            "us_news_rank": uni.get('us_news_rank', uni['id']),
            "tier": tier,
            "probability": prob,
            "color": color,
            "region": uni['region'],
            "campus_type": uni['campus_type'],
            "state": uni['state'],
            "location": f"{uni['region']} Campus ({uni['state']})",
            "distance_miles": approx_dist,
            "distance_str": dist_str,
            "known_for": ", ".join(uni['majors']),
            "testing_policy": "Test-Optional" if prob > 60 else "Test-Required",
            "testing_desc": f"Avg SAT: {uni['avg_sat']} | Avg ACT: {uni['avg_act']}",
            "reasoning": f"Academic metrics (GPA {gpa:.2f}, SAT {sat or 'N/A'}, ACT {act or 'N/A'}, Extracurriculars: {len(selected_dna)}) heavily weighted for {uni['name']} benchmarks.",
            "dna_tags": uni['dna'],
            "financial": fin_fit,
            "hypothetical": hyp_data
        })

    matches.sort(key=lambda x: x['probability'], reverse=True)
    return jsonify({"matches": matches}), 200

@app.route('/api/match/institute', methods=['POST'])
def match_institute():
    data = request.json or {}

    min_gpa = float(data.get('min_gpa', 0.0))
    min_sat = int(data.get('min_sat', 0))
    min_act = int(data.get('min_act', 0))
    testing_mode = data.get('testing_mode', 'all')
    candidate_source = data.get('candidate_source', 'all')
    target_major = data.get('target_major', '')
    target_minor = data.get('target_minor', '')
    target_dna = data.get('target_dna', [])
    anonymize = bool(data.get('anonymize', False))

    candidate_pool = []

    # 1. Fetch Real Users from Supabase database
    if supabase and candidate_source in ['all', 'real_only']:
        try:
            res = supabase.table("user_profiles").select("*").execute()
            if res and res.data:
                for idx, u in enumerate(res.data):
                    user_email = u.get("email", "")
                    cand_name = user_email.split("@")[0].capitalize() if user_email else f"Real Student #{idx + 101}"
                    if anonymize:
                        cand_name = f"Real Candidate #{idx + 101}"

                    candidate_pool.append({
                        "id": f"real_{u.get('id', idx)}",
                        "name": cand_name,
                        "gpa": float(u.get("gpa", 0.0)),
                        "sat": u.get("sat"),
                        "act": u.get("act"),
                        "major": u.get("major", "Undecided"),
                        "minor": u.get("minor", "None / Undecided"),
                        "dna": u.get("dna", []),
                        "is_real_user": True
                    })
        except Exception as err:
            print("Error retrieving real user candidates from Supabase:", err)

    # 2. Include Benchmark Generated Mock Candidates if requested
    if candidate_source != 'real_only':
        for idx, m in enumerate(MOCK_STUDENTS):
            cand_name = f"Candidate #{m['id']}" if anonymize else m['name']
            candidate_pool.append({
                "id": m['id'],
                "name": cand_name,
                "gpa": m['gpa'],
                "sat": m['sat'],
                "act": m['act'],
                "major": m.get('target_major', 'Undecided'),
                "minor": m.get('target_minor', 'None / Undecided'),
                "dna": m.get('dna', []),
                "is_real_user": False
            })

    # 3. Evaluate & Filter Candidates
    evaluated_candidates = []
    for cand in candidate_pool:
        fit_score = calculate_candidate_fit_score(
            cand, min_gpa, min_sat, min_act, testing_mode, target_major, target_dna, target_minor
        )

        cand_copy = dict(cand)
        cand_copy['fit_score'] = fit_score
        evaluated_candidates.append(cand_copy)

    # Sort candidates by best fit score descending
    evaluated_candidates.sort(key=lambda x: x['fit_score'], reverse=True)

    return jsonify({"candidates": evaluated_candidates}), 200

@app.route('/api/advisor/profile', methods=['POST'])
def advisor_profile():
    data = request.json or {}
    university = data.get('university', 'Target University')
    tier = data.get('tier', 'Target')
    gpa = data.get('gpa')
    sat = data.get('sat')
    act = data.get('act')

    if groq_client:
        try:
            prompt = f"Provide concise, high-impact tactical advice for a high school applicant targeting {university} (Match Tier: {tier}). GPA: {gpa}, SAT: {sat}, ACT: {act}."
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL_ID,
            )
            advice = chat_completion.choices[0].message.content
            return jsonify({"advice": advice}), 200
        except Exception as e:
            print("Groq Advisor Profile Error:", e)

    return jsonify({
        "advice": f"For {university}, focus on boosting core STEM/leadership extracurricular impact, maintaining high academic rigor in senior year courses, and refining your unique essay narrative."
    }), 200

@app.route('/api/advisor/outreach', methods=['POST'])
def advisor_outreach():
    data = request.json or {}
    min_gpa = data.get('min_gpa', 3.5)
    min_sat = data.get('min_sat', 1300)
    target_dna = data.get('target_dna', [])

    if groq_client:
        try:
            prompt = f"Provide strategic institutional recruitment guidance for target baseline candidates with min GPA {min_gpa}, min SAT {min_sat}, and focus tags: {', '.join(target_dna)}."
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL_ID,
            )
            strategy = chat_completion.choices[0].message.content
            return jsonify({"strategy": strategy}), 200
        except Exception as e:
            print("Groq Advisor Outreach Error:", e)

    return jsonify({
        "strategy": f"Target pipeline outreach strategy: Allocate merit scholarship incentives towards top candidates matching baseline GPA {min_gpa}+ and SAT {min_sat}+. Focus outreach on specialized STEM and Leadership club profiles."
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
