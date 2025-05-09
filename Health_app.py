from dotenv import load_dotenv

import streamlit as st
st.set_page_config(page_title="NutriGenie", layout="wide", page_icon="🍎")

import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError, InvalidArgument
from PIL import Image
import sqlite3
import io
from database import save_search, delete_search, get_previous_searches, init_db
from auth import login_page, registration_page, get_cookie, set_cookie
from datetime import datetime, timedelta
import time, random

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Intialize database
init_db()

# Function to get Gemini API response
# def get_gemini_response(input_prompt, image=None):
#     try:
#         model = genai.GenerativeModel("gemini-2.0-flash" if image else "gemini-2.0-flash")
#         if image:
#             response = model.generate_content([input_prompt, image[0]])
#         else:
#             response = model.generate_content([input_prompt])
#         return response.text
#     except Exception as e:
#         return f"Error: {e}"
# Define models in priority order
GEMINI_MODELS = [
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash"
]

def get_gemini_response(prompt: str, image_data=None): 
    for model_name in GEMINI_MODELS:
        try:
            print(f"Trying model: {model_name}")
            model = genai.GenerativeModel(model_name=model_name)
            
            # Check if image data is provided
            if image_data:
                response = model.generate_content([prompt, image_data[0]])
            else:
                response = model.generate_content(prompt)
            
            if hasattr(response, 'text') and response.text.strip():
                return {
                    "model_used": model_name,
                    "response": response.text.strip()
                }
        except ResourceExhausted:
            print(f"[Quota Exhausted] - {model_name}")
        except InvalidArgument as e:
            print(f"[Invalid Argument] - {model_name}: {e}")
        except GoogleAPIError as e:
            print(f"[API Error] - {model_name}: {e}")
        except Exception as e:
            print(f"[Unknown Error] - {model_name}: {e}")

    # If none worked
    return {
        "model_used": None,
        "response": "🚫 All Gemini models failed due to quota or configuration issues. Please try again later."
    }

def health():
    st.warning("!!    Login to keep track of your history and to explore our other more advanced features   !!")
    st.markdown(
    """
    <style>
        /* Responsive Container */
        .responsive-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .responsive-container h1 {
            font-size: 2.5rem;
            margin-top: 20px;
        }

        /* Ensures all text and headings in tabs stay in one line on smaller screens */
        .tab-content, .tab-content h1, .tab-content h2, .tab-content p, .tab-content span {
            white-space: nowrap; /* Prevent text wrapping */
            overflow: hidden; /* Hide overflow if necessary */
            text-overflow: ellipsis; /* Adds ellipsis (...) for overflowing text */
        }

        /* Media Queries for responsiveness */
        @media (max-width: 768px) {
            .responsive-container h1 {
                font-size: 2rem;  /* Adjust font size for tablets */
            }
            .tab-content, .tab-content h1, .tab-content h2, .tab-content p {
                font-size: 1rem; /* Adjust font size for smaller screens */
            }
        }

        @media (max-width: 480px) {
            .responsive-container h1 {
                font-size: 1.5rem; /* Adjust font size for mobile devices */
            }
            .tab-content, .tab-content h1, .tab-content h2, .tab-content p {
                font-size: 0.9rem; /* Smaller font size for very small screens */
            }
        }
    </style>
    <div class="responsive-container">
        <h1>🍎 NutriGenie 🥗</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

    st.markdown(
    '<p class="info"><br>Welcome to your personalized <strong>AI-powered health assistant!</strong> '
    'Get detailed dietary and lifestyle recommendations based on your health concerns.</p>',
    unsafe_allow_html=True,
)


    st.header("Your Health Companion")
    col1, col2 = st.columns([9, 1])

    # Text input
    user_query = col1.text_input("Enter your health problem (e.g., diabetes, obesity, heart related, etc):", key="input_box",
    placeholder="Type your health condition here...")
    
    if st.button(" 🔍 Get Recommendations"):
       if not user_query.strip():  # Ensures it's not just spaces
            st.error("Please enter a health problem")
       else:
            prompt = f"""
            You are a certified nutritionist. A user has the following health problem: {user_query}.
            Provide detailed recommendations, including:
            1. Foods to eat.
            2. Foods to avoid.
            3. Lifestyle and exercise tips.
            """
            response = get_gemini_response(prompt)
            st.success("🎉 **Your Recommendations Are Ready!**")
            st.write(response["response"])
            if st.session_state["logged_in"]:
                save_search(st.session_state["user_id"], user_query, response["response"])
            else:
                st.write("")

# Read login state from cookies
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = get_cookie("logged_in") == "True"
    st.session_state["user_id"] = get_cookie("user_id") or None
    st.session_state["username"] = get_cookie("username") or ""



# Sidebar Navigation
if not st.session_state["logged_in"]:
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 2, 2])
    with col3:
        if st.button("Home"):
            st.session_state["page"] = "Home"
    with col4:
        if st.button("Login"):
            st.session_state["page"] = "Login"
    with col5:
        if st.button("Sign up"):
            st.session_state["page"] = "Sign up"
else:
    st.sidebar.write(f"👤 Welcome, {st.session_state['username']}!")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = None
        st.session_state["username"] = ""

        # Clear Cookies on Logout
        set_cookie("logged_in", "False")
        set_cookie("user_id", "")
        set_cookie("username", "")

        st.cache_data.clear()  # Clear Streamlit cache
        st.rerun()

# Authentication Pages
if not st.session_state["logged_in"]:
    page = st.session_state.get("page", "Home")

    if page == "Home":
        health()
    elif page == "Sign up":
        registration_page()
    elif page == "Login":
        login_page()
    
    st.stop()

st.markdown(
    """
    <style>
        /* Responsive Container */
        .responsive-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .responsive-container h1 {
            font-size: 2.5rem;
            margin-top: 20px;
        }

        /* Ensures all text and headings in tabs stay in one line on smaller screens */
        .tab-content, .tab-content h1, .tab-content h2, .tab-content p, .tab-content span {
            white-space: nowrap; /* Prevent text wrapping */
            overflow: hidden; /* Hide overflow if necessary */
            text-overflow: ellipsis; /* Adds ellipsis (...) for overflowing text */
        }

        /* Media Queries for responsiveness */
        @media (max-width: 768px) {
            .responsive-container h1 {
                font-size: 2rem;  /* Adjust font size for tablets */
            }
            .tab-content, .tab-content h1, .tab-content h2, .tab-content p {
                font-size: 1rem; /* Adjust font size for smaller screens */
            }
        }

        @media (max-width: 480px) {
            .responsive-container h1 {
                font-size: 1.5rem; /* Adjust font size for mobile devices */
            }
            .tab-content, .tab-content h1, .tab-content h2, .tab-content p {
                font-size: 0.9rem; /* Smaller font size for very small screens */
            }
        }
    </style>
    
    <div class="responsive-container">
        <h1>🍎 NutriGenie 🥗</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="info"><br>Welcome to your personalized <strong>AI-powered health assistant!</strong> '
    'Get detailed dietary and lifestyle recommendations based on your health concerns.</p>',
    unsafe_allow_html=True,
)


tab1, tab2, tab3, tab4, tab5 = st.tabs(["NutriGenie", "AI-Calorie Tracker", " MetaboTrack", "RecipeMaster", "SmartShopper"])
with tab1:
    st.header("Your Health Companion")
    col1, col2 = st.columns([9, 1])

    # Text input
    user_query = col1.text_input("Enter your health problem (e.g., diabetes, obesity, heart related, etc):", key="input_box",
    placeholder="Type your health condition here...")
    
    if st.button(" 🔍 Get Recommendations"):
       if not user_query.strip():  # Ensures it's not just spaces
            st.error("Please enter a health problem")
       else:
            prompt = f"""
            You are a certified nutritionist. A user has the following health problem: {user_query}.
            Provide detailed recommendations, including:
            1. Foods to eat.
            2. Foods to avoid.
            3. Lifestyle and exercise tips.
            """
            response = get_gemini_response(prompt)
            st.success("🎉 **Your Recommendations Are Ready!**")
            st.write(response["response"])
            if st.session_state["logged_in"]:
                save_search(st.session_state["user_id"], "Nutrigenie", user_query, response["response"])
            else:
                st.sidebar.warning("Please Login!")

    if st.session_state["logged_in"]:
        previous_searches = get_previous_searches(st.session_state["user_id"], "Nutrigenie")
        st.sidebar.title("📁Previous Searches")
        if previous_searches:
            st.sidebar.header("📁NutriGenie")
            for search_id, user_query, response in previous_searches:
                with st.sidebar.expander(f"NutriGenie:  {user_query[:20]}"):
                    st.write(response)
                    if st.button("🗑️ Delete", key=f"delete_nutrigenie_{search_id}"):
                        delete_search(search_id)
                        st.rerun()

# Tab 2: Calorie Tracker with AI - Total Calories
if st.session_state["logged_in"]:
   with tab2:
    st.header("Track Calories, Stay Healthy")
    # Drag and Drop File Section
    st.markdown("### Upload Your Meal Image")
    uploaded_file = st.file_uploader("Drag and drop a food image here...", type=["jpg", "jpeg", "png"])

    # Camera Toggle Option
    st.markdown("### Or Capture Your Meal")
    enable_camera = st.checkbox("Enable Camera")

    # Conditional Camera Input
    camera_input = None
    if enable_camera:
        camera_input = st.camera_input("Take a photo of your meal")
        # Close Camera Button
        if st.button("Close Camera"):
            enable_camera = False  # Reset the checkbox (simulated close behavior)

    # Display uploaded or captured image
    image = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
    elif camera_input is not None:
        image = Image.open(camera_input)
        st.image(image, caption="Captured Image", use_column_width=True)

    # Analyze Image
    if st.button("Calculate calories"):
        if image:
            try:
                # Process the image as binary data for the Gemini API
                image_data = [{"mime_type": "image/jpeg", "data": camera_input.getvalue() if camera_input else uploaded_file.getvalue()}]
                input_prompt = """
                You are an expert nutritionist. Analyze the image to identify the food items 
                and calculate the total calories. Provide the result in the following format:
                Calories
                1. Item 1 - no. of calories
                2. Item 2 - no. of calories
                ----

                Protein
                1.Item 1 - no. of protein
                2.Item 2 - no. of protein
                ----

                Carbs
                1.Item 1 - no. of carbs
                2.Item 2 - no. of carbs
                ----

                Fats
                1.Item 1 - no. of fats
                2.Item 2 - no. of fats
                ----

                1.Total Calories: XX
                2.Total Protein: XX
                3.Total Carbs: XX
                4.Total Fats: XX
                """

                response = get_gemini_response(input_prompt, image_data)
                st.subheader("Analysis Result:")
                st.write(response["response"])
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please upload or capture an image to analyze.")

# Tab 3: Calorie Needs by Age
if st.session_state["logged_in"]:
    with tab3:
        st.header("⚡ MetaboTrack - AI Metabolic Health Analyzer")

        # User Inputs
        activity_level = st.selectbox("🏋️ Select Your Activity Level:", [
            "Sedentary (Little or no exercise)",
            "Lightly active (Exercise 1-3 days per week)",
            "Moderately active (Exercise 3-5 days per week)",
            "Very active (Daily intense exercise)",
        ])

        sleep_hours = st.slider("🛌 How many hours did you sleep last night?", 3, 10, 7)

        # Initialize session state for time and date if not already set
        if "meal_date" not in st.session_state:
            st.session_state["meal_date"] = datetime.today().date()

        if "last_meal_time" not in st.session_state:
            st.session_state["last_meal_time"] = (datetime.now() - timedelta(hours=1)).time()
        
        # Proper time and date selection
        st.session_state["meal_date"] = st.date_input("📅 Select the date of your last meal:", value=st.session_state["meal_date"])
        st.session_state["last_meal_time"] = st.time_input("🍽️ What time did you last eat?", value=st.session_state["last_meal_time"])

        # Combine date and time to form a full datetime object
        last_meal_datetime = datetime.combine(st.session_state["meal_date"], st.session_state["last_meal_time"])

        if st.button("🔍 Analyze My Metabolism"):
            # Ensure the selected time is valid (past time)
            current_time = datetime.now()
            if last_meal_datetime > current_time:
                st.error("The last meal time cannot be in the future! Please select a valid time.")
            else:
                # Generate input prompt for Gemini API
                prompt = f"""
                You are a highly advanced AI metabolism tracker.
                A user wants to optimize their metabolism and improve health.
                Analyze the user's data and provide personalized suggestions.

                User Information:
                - Activity Level: {activity_level}
                - Sleep Duration: {sleep_hours} hours
                - Last Meal Time: {last_meal_datetime.strftime('%Y-%m-%d %H:%M:%S')}

                Your Analysis Should Include:
                1. Metabolism Score (0-100) based on their inputs.
                2. Identify if the user is in Fat Storage Mode, Balanced Metabolism, or Fat Burning Mode.
                3. Best time for the user to eat, exercise, and rest for optimal metabolism.
                4. Personalized advice to improve metabolic health.
                """

                # Call Gemini API to get response
                response = get_gemini_response(prompt)
                
                st.success("🎉 **Your AI-Powered Metabolism Analysis is Ready!**")
                st.write(response["response"])
                if st.session_state["logged_in"]:
                   save_search(st.session_state["user_id"], "MetaboTrack", prompt, response["response"])
                else:
                    st.sidebar.warning("Please Login!")

        if st.session_state["logged_in"]:
            previous_searches = get_previous_searches(st.session_state["user_id"], "MetaboTrack")
            if previous_searches:
                st.sidebar.header("📁Metabotrack")
                for search_id, user_query, response in previous_searches:
                    with st.sidebar.expander(f"Metabotrack: {user_query[:30]}"):
                        st.write(response)
                        if st.button("🗑️ Delete", key=f"delete_metabotrack_{search_id}"):
                            delete_search(search_id)
                            st.rerun()

# Tab 4: Recipe Suggestions
if st.session_state["logged_in"]:
   with tab4:
    st.header("RecipeMaster - Personalized Recipe Suggestions 🍳")
    st.markdown("### Get customized recipes based on your preferences, goals, and ingredients!")

    # User Inputs
    st.subheader("1. Dietary Preferences")
    dietary_preferences = st.selectbox(
        "Select your dietary preference:",
        ["No Preference", "Vegetarian", "Vegan", "Non-vegetarians", "Keto", "Gluten-Free", "Low-Carb", "High-Protein", "Mediterranean"
        "Raw Food", "Low-Fat", "Dairy-Free"]
    )

    st.subheader("2. Health Goals")
    health_goal = st.selectbox(
        "Select your health goal:",
        ["No Specific Goal", "Weight Loss", "Muscle Gain", "Managing Diabetes", "Boosting Immunity", "Heart Health", "Improving Gut Health", "Blood Pressure", "Better Skin and Hair",
        "Improving Mental Health", "Pregnancy Diet", "Healthy Aging", "Managing Thyroid", "Improving Stamina"]
    )

    st.subheader("3. Ingredients Available at Home")
    ingredients = st.text_area(
        "Enter the ingredients you have (comma-separated):",
        placeholder="e.g., chicken, tomatoes, garlic, onions",
        key="ingredients_input"
    )

    # Suggest Recipes Button
    if st.button("🍽️ Suggest Recipes"):
        if not ingredients.strip():
            st.error("Please enter at least one ingredient.")
        else:
            # Generate a prompt for recipe suggestions
            recipe_prompt = f"""
            You are a master chef and nutritionist. Based on the following inputs:
            - Dietary Preference: {dietary_preferences}
            - Health Goal: {health_goal}
            - Ingredients: {ingredients}

            Suggest 3 healthy and delicious recipes. For each recipe, include:
            1. Recipe name
            2. Brief description
            3. Ingredients list
            4. Step-by-step cooking instructions
            5. Nutritional information (calories, protein, carbs, fats)
            """

            # Fetch recipe suggestions using Gemini API
            recipe_response = get_gemini_response(recipe_prompt)

            # Display the Response
            st.success("🎉 *Your Recipe Suggestions Are Ready!*")
            if recipe_response:
                st.write(recipe_response["response"])
                if st.session_state["logged_in"]:
                   save_search(st.session_state["user_id"], "RecipeMaster" , recipe_prompt, recipe_response["response"])
                else:
                    st.sidebar.warning("Please Login!")
            else:
                st.error("Unable to fetch recipes. Please try again.")

    if st.session_state["logged_in"]:
        previous_searches = get_previous_searches(st.session_state["user_id"], "RecipeMaster")
        if previous_searches:
            st.sidebar.header("📁RecipeMaster")
            for search_id, user_query, response in previous_searches:
                with st.sidebar.expander(f"RecipeMaster: {user_query[:20]}..."):
                    st.write(response)
                    if st.button("🗑️ Delete", key=f"delete_recipemaster_{search_id}"):
                        delete_search(search_id)
                        st.rerun()

if st.session_state["logged_in"]:
   with tab5:
    st.header("SmartShopper - AI-Generated Shopping List 🛒")
    st.markdown("### Create a smart shopping list based on your planned meals!")

    # User Input: Planned Meals
    st.subheader("1. Select Planned Recipes")
    planned_recipes = st.text_area(
        "Enter the recipes you want to make (comma-separated):",
        placeholder="e.g., Chicken Curry, Vegan Pasta, Greek Salad",
        key="planned_recipes"
    )

    # User Input: Ingredients at Home
    st.subheader("2. Ingredients You Already Have")
    available_ingredients = st.text_area(
        "Enter the ingredients you have at home (comma-separated):",
        placeholder="e.g., rice, garlic, olive oil, tomatoes",
        key="available_ingredients"
    )

    # Generate Shopping List Button
    if st.button("🛍️ Generate Shopping List"):
        if not planned_recipes.strip():
            st.error("Please enter at least one planned recipe.")
        elif not available_ingredients.strip():
            st.error("Please enter the ingredients you have at home.")
        else:
            # Generate a prompt for shopping list creation
            shopping_list_prompt = f"""
            You are a kitchen assistant. Based on the following inputs:
            - Planned Recipes: {planned_recipes}
            - Ingredients at Home: {available_ingredients}

            Create a smart shopping list by identifying the missing ingredients needed to make the planned recipes.
            Categorize the ingredients into sections (e.g., Vegetables, Spices, Dairy, etc.) for easy shopping.
            """

            # Fetch shopping list using Gemini API
            shopping_list_response = get_gemini_response(shopping_list_prompt)

            # Display the Shopping List
            st.success("✅ *Your Smart Shopping List is Ready!*")
            if shopping_list_response:
                st.write(shopping_list_response["response"])
                if st.session_state["logged_in"]:
                    save_search(st.session_state["user_id"], "SmartShopper", shopping_list_prompt, shopping_list_response["response"])
                else:
                   st.sidebar.warning("Please Login!")
            else:
                st.error("Unable to generate shopping list. Please try again.")

    if st.session_state["logged_in"]:
        previous_searches = get_previous_searches(st.session_state["user_id"], "SmartShopper")
        if previous_searches:
            st.sidebar.header("📁SmartShopper")
            for search_id, user_query, response in previous_searches:
                with st.sidebar.expander(f"SmartShopper: {user_query[:30]}..."):
                    st.write(response)
                    if st.button("🗑️ Delete", key=f"delete_smartshopper_{search_id}"):
                        delete_search(search_id)
                        st.rerun()