import streamlit as st
import datetime
import os
from downloader import Downloader
from PIL import Image



# ========================================================
# TODO:
# ========================================================
# 1. Get input from user
# NOTE: Pull down Menu / Text prompt
#   a. Let user specify date range
#   b. Let user specify time range
#   c. Let user specify cadence
#   d. Let user specify wavelength
#   e. Let user specify directory to save to
#   f. Let user specify file type
#   g. Let user specify file name (?) <-- in question ¯\_(ツ)_/¯
#   h. Get user email
#   i. Get instrument (HMI or AIA)

# 2. Display Image to be downloaded <-- Need Andres' help with this

# 3. Download Button to download image

# 4. ⭐ Make it pretty ⭐

# 5. 💰💰💰 Profit 💰💰💰



def get_date_range():
    # NOTE: Make sure this returns string for Downloader to use
    start_date = st.sidebar.date_input("Start Date", datetime.date.today())
    end_date = st.sidebar.date_input("End Date", datetime.date.today())
    return start_date, end_date

def get_email():
    email = st.text_input("JSOC-Registered Email: ")
    return email  

def get_wavelength():
    wavelength = st.sidebar.selectbox("Wavelength", ["1700", "1600", "304", "171", "193", "211", "335", "94", "131"])
    return wavelength

def get_file_type():
    file_type = st.sidebar.selectbox("File Type", ["jpg", "fits"])
    return file_type

def get_instrument():
    instrument = st.sidebar.selectbox("Instrument", ["HMI", "AIA"])
    return instrument 

def choose_cadence():
    cadence = st.sidebar.selectbox("Cadence", ["h", "m", "d", "s"])
    return cadence

def choose_spikes():
    spikes = st.sidebar.selectbox("Include spikes?", ["YES", "NO"])
    return spikes
    
# ==============================================================================================================



def main():
    st.title("HITS SDO Downloader")
    st.write("This app downloads HMI Intensitygram and Magnetogram images from the SDO website.")

    # Get user input
    start_date, end_date = get_date_range()
    email = get_email()
    wavelength = get_wavelength()
    file_type = get_file_type()
    instrument = get_instrument()
    cadence = choose_cadence()
    spikes = choose_spikes()
    
    st.write("Your email is: ", email)
    st.write("💪😎 We be balling 🏀⛹️")


    # https://discuss.streamlit.io/t/multiple-images-along-the-same-row/118/7
    # https://gist.github.com/treuille/2ce0acb6697f205e44e3e0f576e810b7
    st.image('https://media.istockphoto.com/id/1354219060/vector/sun-vector-cartoon-vector-logo-for-web-design-vector-illustration.jpg?s=612x612&w=0&k=20&c=nBAAzTT-al6gqBfdQi4E3l6AUK1g_b0LG0rBo0QlGDU=', caption='Sunrise by the mountains')



if __name__ == "__main__":
    main()