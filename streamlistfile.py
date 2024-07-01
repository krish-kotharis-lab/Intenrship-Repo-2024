import streamlit as st
import test2
from test2 import generate_P, run_model, plot1, plot2, plot3, plot4, plot5, plot6

## Define page states
PAGES = {
    "Home": "home",
    "Second Page": "second_page",
    "Third Page": "third_page",
    "Fourth Page": "fourth_page",
    "Fifth Page": "fifth_page",
    "Sixth Page": "sixth_page",
    "Next": "next_button",
    "Back": "back_button"
}
#==============================================================================================================================
def main():
    st.title("Welcome to Our Climate UI!")

    # Use columns to organize layout
    col1, col2 = st.columns(2)

    global P
    P = {}

    with col1:
        st.header("We are glad to have you here.")
        st.write("""
        This is a place where you will be asked to give some time to aid the environment.
        We hope that is ok with you. Please do enjoy your stay.
        """)

        if st.button("Get Started"):
            st.session_state.page = PAGES["Second Page"]  # Set page state to Second Page upon button click

    with col2:
        st.image("https://www.ipsl.fr/wp-content/themes/ipsltheme/themes/logo/logo_ipsl_1.png")

    # Sidebar with more information
    st.sidebar.title("About Us")
    st.sidebar.write("""
    We are a dedicated team trying to aid the world against the battles of climate change.
    Learn more about our mission and values.
    """)

    # Handle page navigation based on state
    if "page" not in st.session_state:
        st.session_state.page = PAGES["Home"]  # Default to Home page

    if st.session_state.page == PAGES["Second Page"]:
        second_page()

    if st.session_state.page == PAGES["Third Page"]:
        third_page()

    if st.session_state.page == PAGES["Fourth Page"]:
        fourth_page()

    if st.session_state.page == PAGES["Fifth Page"]:
        fifth_page()

    if st.session_state.page == PAGES["Sixth Page"]:
        sixth_page()
#==============================================================================================================================
def second_page():
    st.title("Selection Task #1")
    st.write("Choose the number of actors participating.")
    if "selected_actor" not in st.session_state:
        st.session_state.selected_actor = None

    Actors = ["1 Actor", "2 Actors", "3 Actors"]
    selected_actor = st.radio("How many actors are participating?:", Actors)

    if selected_actor:
        st.session_state.selected_actor = selected_actor
        st.session_state.selected_actor_count = int(selected_actor.split()[0])
        st.session_state.current_actor_index = 1
        st.session_state.results = []
        if st.button("Yes", key="start_button"):  # Unique key for the button
            st.session_state.page = PAGES["Third Page"]
#==============================================================================================================================
def third_page():
    st.title(f"Selection Task #2 for Actor {st.session_state.current_actor_index}")
    st.write("Please select one area to protect.")

    if "selected_region" not in st.session_state:
        st.session_state.selected_region = None

    regions = ["NHST", "SHST", "GMST", "monsoon"]

    selected_region = st.radio("Regions", options=regions, key=f"region_actor_{st.session_state.current_actor_index}")

    st.session_state.selected_region = selected_region

    if st.session_state.selected_region:
        st.write(f"You selected: {st.session_state.selected_region}.")
        next_button_key = f"next_button_third_page_{st.session_state.current_actor_index}"
        back_button_key = f"back_button_third_page_{st.session_state.current_actor_index}"
        if st.button("Next", key=next_button_key):  # Unique key for the button
            st.session_state.page = PAGES["Fourth Page"]
        elif st.button("Back", key=back_button_key):
            st.session_state.page = PAGES["Second Page"]
#==============================================================================================================================
def fourth_page():
    st.title(f"Selection Task #3 for Actor {st.session_state.current_actor_index}")
    st.write("Please select an emipoint.")

    # Initialize selected angle for the current actor
    if "selected_angle" not in st.session_state:
        st.session_state.selected_angle = None

    emipoints = ["60N", "30N", "15N", "eq", "15S", "30S", "60S"]
    selected_angle = st.multiselect("Choose at least ONE emission point:", emipoints, key=f"angle_{st.session_state.current_actor_index}")

    # Update selected angle in session state
    if selected_angle:
        st.session_state.selected_angle = selected_angle
        st.write(f"You selected: {st.session_state.selected_actor}, {st.session_state.selected_region}, and {st.session_state.selected_angle}.")

    # Ensure the current actor's dictionary in P is initialized
    #if st.session_state.current_actor_index not in P:
        #P[st.session_state.current_actor_index] = {}

    # Handle 'Next' button click
    next_button_key = f"next_button_fourth_page_{st.session_state.current_actor_index}"
    back_button_key = f"back_button_fourth_page_{st.session_state.current_actor_index}"
    if st.button("Next", key=next_button_key):  # Unique key for the button
        st.session_state.page = PAGES["Fifth Page"]
    elif st.button("Back", key=back_button_key):
        st.session_state.page = PAGES["Third Page"]
#=============================================================================================================================
def fifth_page():
    st.title(f"Selection Task #4 for Actor {st.session_state.current_actor_index}")
    st.write("Please select a setpoint.")

    # Initialize selected setpoint for the current actor
    if "setpoint" not in st.session_state:
        st.session_state.selected_setpoint = None

    setpoint = st.number_input("Insert a number from -10.0 -> 10.0", min_value=-10.0, max_value=10.0, step=1.0, placeholder="0.0")

    # Update selected setpoint in session state
    if setpoint is not None:
        st.session_state.selected_setpoint = setpoint
        st.write(f"You selected: {st.session_state.selected_actor}, {st.session_state.selected_region}, {st.session_state.selected_angle}, and {st.session_state.selected_setpoint}.")

    if st.session_state.selected_setpoint is None:
        st.session_state.selected_setpoint = 0.0
    
    # Ensure the current actor's dictionary in P is initialized
    if st.session_state.current_actor_index not in P:
        P[st.session_state.current_actor_index] = {}

    P[st.session_state.current_actor_index]['setpoint'] = st.session_state.selected_setpoint

    # Handle 'Next' button click
    next_button_key = f"next_button_fifth_page_{st.session_state.current_actor_index}"
    back_button_key = f"back_button_fifth_page_{st.session_state.current_actor_index}"
    if st.button("Next", key=next_button_key):
        # Append current actor's result to results list
        result = {
            "Actor": st.session_state.current_actor_index,
            "type": st.session_state.selected_region,
            "emipoints": st.session_state.selected_angle,
            "setpoint": st.session_state.selected_setpoint
        }
        st.session_state.results.append(result)

        # Move to the next actor or to the results page
        if st.session_state.current_actor_index < st.session_state.selected_actor_count:
            st.session_state.current_actor_index += 1
            #st.session_state.selected_region = None  # Reset selected regions for next actor
            #st.session_state.selected_angle = None  # Reset selected angle for next actor
            st.session_state.page = PAGES["Third Page"]
        else:
            st.session_state.page = PAGES["Sixth Page"]
    elif st.button("Back", key=back_button_key):
        st.session_state.page = PAGES["Fourth Page"]
#==============================================================================================================================
def sixth_page():
    st.title("Your Results")
    st.write("These are your results:")
    #P[st.session_state.current_actor_index] = {}
    
    #P[st.session_state.current_actor_index]['emipoints'] = st.session_state.selected_angle
    
    if "results" in st.session_state:
        for result in st.session_state.results:
            st.write(f"Actor {result['Actor']}: Region - {result['type']}, Emission Point(s) - {result['emipoints']}, Setpoint - {result['setpoint']}")
        P = generate_P(st.session_state.results)
        run_model(P)
        #
        fig1 = plot1()
        fig2 = plot2()
        fig3 = plot3(P)
        fig4 = plot4()
        fig5 = plot5()
        fig6 = plot6()
        #
        st.pyplot(fig1)
        st.pyplot(fig2)
        st.pyplot(fig3)
        st.pyplot(fig4)
        st.pyplot(fig5)
        st.pyplot(fig6)
        #
    else:
        st.write("No results to display.")
        
    if st.button("Restart"):
        # Reset session state variables to their initial values
        st.session_state.selected_actor = None
        st.session_state.selected_region = None
        st.session_state.selected_angle = None
        st.session_state.selected_setpoint = None
        st.session_state.results = []
        st.session_state.page = PAGES["Home"]
#==============================================================================================================================
if __name__ == "__main__":
    main()