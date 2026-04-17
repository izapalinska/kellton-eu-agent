import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
from crewai.tools import BaseTool
from tavily import TavilyClient

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kellton Content Engine", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- 2. HISTORY FUNCTIONS ---
FILE_NAME = "post_history.csv"

def save_to_history(topic, content):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([[now, topic, content]], columns=['Date', 'Topic/Notes', 'Generated Content'])
    if not os.path.isfile(FILE_NAME):
        df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')

def load_history():
    if os.path.isfile(FILE_NAME):
        return pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    return pd.DataFrame(columns=['Date', 'Topic/Notes', 'Generated Content'])

# --- 3. CUSTOM CSS (Zaktualizowana Paleta i Ikony) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Instrument+Serif:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #030303;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 82px !important;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: -28px !important;
        letter-spacing: -4px;
        line-height: 1;
    }

    /* Subheader w nowym, różowym kolorze */
    .serif-akcent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 52px !important;
        letter-spacing: 4px !important;
        color: #FF749F; 
        display: block;
        margin-bottom: 4rem;
    }

    [data-testid="column"]:nth-of-type(2) {
        background: linear-gradient(160deg, #16161A 0%, #050505 100%) !important;
        border-left: 1px solid rgba(255,255,255,0.08) !important;
        padding: 50px !important;
        min-height: 100vh;
    }

    /* POLA TEKSTOWE - Fioletowy Focus (#8237FF) */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="base-input"] {
        background-color: #0F0F11 !important;
        border: 1px solid #2A1F5C !important;
        border-radius: 16px !important;
    }
    
    div[data-baseweb="input"]:focus-within > div, 
    div[data-baseweb="textarea"]:focus-within > div,
    div[data-baseweb="base-input"]:focus-within,
    .stTextArea textarea:focus, 
    .stTextInput input:focus {
        border-color: #8237FF !important;
        box-shadow: 0 0 0 1px #8237FF, 0 0 15px rgba(130, 55, 255, 0.4) !important;
        outline: none !important;
    }

    input, textarea {
        color: #FFFFFF !important;
        caret-color: #8237FF !important;
    }

    /* GŁÓWNY BUTTON - Gradient Czerwono-Pomarańczowy */
    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #E31352 0%, #F86652 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(227, 19, 82, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(248, 102, 82, 0.6) !important;
    }
    div[data-testid="stButton"] > button::before, div[data-testid="stButton"] > button::after {
        display: none !important;
    }

    /* DOWNLOAD CSV BUTTON - Lekki gradient i zielony akcent (#30AD31) z ikoną Chart */
    [data-testid="stDownloadButton"] button {
        background: linear-gradient(180deg, #2A2A35 0%, #16161A 100%) !important;
        border: 1px solid #30AD31 !important;
        color: #30AD31 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 15px rgba(48, 173, 49, 0.1) !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: linear-gradient(180deg, #32323E 0%, #1A1A22 100%) !important;
        box-shadow: 0 6px 20px rgba(48, 173, 49, 0.25) !important;
        transform: translateY(-1px) !important;
    }
    /* Ikona Chart zakodowana w CSS dla buttona */
    [data-testid="stDownloadButton"] button::before {
        content: '';
        display: inline-block;
        width: 18px;
        height: 18px;
        margin-right: 10px;
        background-image: url("data:image/svg+xml,%3Csvg width='110' height='104' viewBox='0 0 110 104' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3CforeignObject x='-8.54312' y='-8.55109' width='114.698' height='114.696'%3E%3Cdiv xmlns='http://www.w3.org/1999/xhtml' style='backdrop-filter:blur(6.5px);clip-path:url(%23bgblur_0_1_561_clip_path);height:100%25;width:100%25'%3E%3C/div%3E%3C/foreignObject%3E%3Cpath data-figma-bg-blur-radius='13' d='M56.4879 5.49146L20.5286 15.1267C7.42452 18.638 1.98921 28.0512 5.50011 41.154L15.1253 77.0758C18.6362 90.1786 28.0499 95.613 41.154 92.1018L77.1133 82.4665C90.2174 78.9553 95.6185 69.5513 92.1076 56.4484L82.4824 20.5267C78.9715 7.42382 69.592 1.98022 56.4879 5.49146Z' fill='url(%23paint0_linear_1_561)'/%3E%3Cg opacity='0.5' filter='url(%23filter1_f_1_561)'%3E%3Cpath d='M74.2065 52.5673L67.6764 27.8315C65.3078 18.8592 59.3796 14.8361 51.5848 16.8939L25.1848 23.8633C17.2622 25.9548 14.1944 32.3527 16.563 41.325L23.0931 66.0609C25.4999 75.1778 31.2869 79.0803 39.2095 76.9888L65.6096 70.0194C73.4044 67.9616 76.6133 61.6843 74.2065 52.5673Z' fill='%23FF624D'/%3E%3C/g%3E%3CforeignObject x='13.2744' y='6.4375' width='111.69' height='111.69'%3E%3Cdiv xmlns='http://www.w3.org/1999/xhtml' style='backdrop-filter:blur(7.5px);clip-path:url(%23bgblur_1_1_561_clip_path);height:100%25;width:100%25'%3E%3C/div%3E%3C/foreignObject%3E%3Cg data-figma-bg-blur-radius='15'%3E%3Cmask id='path-3-outside-1_1_561' maskUnits='userSpaceOnUse' x='28.2744' y='21.4375' width='82' height='82' fill='black'%3E%3Crect fill='white' x='28.2744' y='21.4375' width='82' height='82'/%3E%3Cpath d='M87.7495 22.4375H50.5252C36.9601 22.4375 29.2744 30.1232 29.2744 43.6883V80.8772C29.2744 94.4423 36.9601 102.128 50.5252 102.128H87.7495C101.315 102.128 108.965 94.4423 108.965 80.8772V43.6883C108.965 30.1232 101.315 22.4375 87.7495 22.4375Z'/%3E%3C/mask%3E%3Cpath d='M87.7495 22.4375H50.5252C36.9601 22.4375 29.2744 30.1232 29.2744 43.6883V80.8772C29.2744 94.4423 36.9601 102.128 50.5252 102.128H87.7495C101.315 102.128 108.965 94.4423 108.965 80.8772V43.6883C108.965 30.1232 101.315 22.4375 87.7495 22.4375Z' fill='%23FFAC95' fill-opacity='0.4'/%3E%3Cpath d='M87.7495 23.4375C88.3018 23.4375 88.7495 22.9898 88.7495 22.4375C88.7495 21.8852 88.3018 21.4375 87.7495 21.4375V23.4375ZM87.7495 21.4375C87.1972 21.4375 86.7495 21.8852 86.7495 22.4375C86.7495 22.9898 87.1972 23.4375 87.7495 23.4375V21.4375ZM87.7495 21.4375H50.5252V23.4375H87.7495V21.4375ZM50.5252 21.4375C43.5568 21.4375 37.9599 23.4148 34.1058 27.2689C30.2517 31.123 28.2744 36.7198 28.2744 43.6883H30.2744C30.2744 37.0917 32.14 32.0631 35.52 28.6831C38.9001 25.3031 43.9286 23.4375 50.5252 23.4375V21.4375ZM28.2744 43.6883V80.8772H30.2744V43.6883H28.2744ZM28.2744 80.8772C28.2744 87.8456 30.2517 93.4425 34.1058 97.2966C37.9599 101.151 43.5568 103.128 50.5252 103.128V101.128C43.9286 101.128 38.9001 99.2624 35.52 95.8824C32.14 92.5023 30.2744 87.4738 30.2744 80.8772H28.2744ZM50.5252 103.128H87.7495V101.128H50.5252V103.128ZM87.7495 103.128C94.718 103.128 100.307 101.151 104.152 97.2957C107.997 93.4412 109.965 87.8444 109.965 80.8772H107.965C107.965 87.4751 106.107 92.5036 102.736 95.8832C99.3652 99.2625 94.3461 101.128 87.7495 101.128V103.128ZM109.965 80.8772V43.6883H107.965V80.8772H109.965ZM109.965 43.6883C109.965 36.7211 107.997 31.1243 104.152 27.2697C100.307 23.4149 94.718 21.4375 87.7495 21.4375V23.4375C94.3461 23.4375 99.3652 25.303 102.736 28.6822C106.107 32.0618 107.965 37.0904 107.965 43.6883H109.965Z' fill='url(%23paint1_linear_1_561)' mask='url(%23path-3-outside-1_1_561)'/%3E%3C/g%3E%3CforeignObject x='32.3722' y='23.7303' width='73.5293' height='77.0717'%3E%3Cdiv xmlns='http://www.w3.org/1999/xhtml' style='backdrop-filter:blur(7.5px);clip-path:url(%23bgblur_2_1_561_clip_path);height:100%25;width:100%25'%3E%3C/div%3E%3C/foreignObject%3E%3Cg filter='url(%23filter3_d_1_561)' data-figma-bg-blur-radius='15'%3E%3Cmask id='path-5-inside-2_1_561' fill='white'%3E%3Cpath fill-rule='evenodd' clip-rule='evenodd' d='M69.2606 38.7303C67.4543 38.7303 65.9667 40.2178 65.9667 42.0595V82.5069C65.9667 84.3132 67.4543 85.8008 69.2606 85.8008C71.1023 85.8008 72.5899 84.3132 72.5899 82.5069V42.0595C72.5899 40.2178 71.1023 38.7303 69.2606 38.7303ZM50.666 51.8007C48.8597 51.8007 47.3722 53.2882 47.3722 55.13V82.5081C47.3722 84.3144 48.8597 85.8019 50.666 85.8019C52.5078 85.8019 53.9953 84.3144 53.9953 82.5081V55.13C53.9953 53.2882 52.5078 51.8007 50.666 51.8007ZM84.2782 69.5802C84.2782 67.7385 85.7658 66.2509 87.6075 66.2509C89.4139 66.2509 90.9014 67.7385 90.9014 69.5802V82.5078C90.9014 84.3141 89.4139 85.8016 87.5721 85.8016C85.7658 85.8016 84.2782 84.3141 84.2782 82.5078V69.5802Z'/%3E%3C/mask%3E%3Cpath fill-rule='evenodd' clip-rule='evenodd' d='M69.2606 38.7303C67.4543 38.7303 65.9667 40.2178 65.9667 42.0595V82.5069C65.9667 84.3132 67.4543 85.8008 69.2606 85.8008C71.1023 85.8008 72.5899 84.3132 72.5899 82.5069V42.0595C72.5899 40.2178 71.1023 38.7303 69.2606 38.7303ZM50.666 51.8007C48.8597 51.8007 47.3722 53.2882 47.3722 55.13V82.5081C47.3722 84.3144 48.8597 85.8019 50.666 85.8019C52.5078 85.8019 53.9953 84.3144 53.9953 82.5081V55.13C53.9953 53.2882 52.5078 51.8007 50.666 51.8007ZM84.2782 69.5802C84.2782 67.7385 85.7658 66.2509 87.6075 66.2509C89.4139 66.2509 90.9014 67.7385 90.9014 69.5802V82.5078C90.9014 84.3141 89.4139 85.8016 87.5721 85.8016C85.7658 85.8016 84.2782 84.3141 84.2782 82.5078V69.5802Z' fill='url(%23paint2_linear_1_561)'/%3E%3Cpath d='M66.3667 42.0595C66.3667 40.4359 67.678 39.1303 69.2606 39.1303V38.3303C67.2306 38.3303 65.5667 39.9997 65.5667 42.0595H66.3667ZM66.3667 82.5069V42.0595H65.5667V82.5069H66.3667ZM69.2606 85.4008C67.6752 85.4008 66.3667 84.0923 66.3667 82.5069H65.5667C65.5667 84.5341 67.2333 86.2008 69.2606 86.2008V85.4008ZM72.1899 82.5069C72.1899 84.0895 70.8842 85.4008 69.2606 85.4008V86.2008C71.3204 86.2008 72.9899 84.5369 72.9899 82.5069H72.1899ZM72.1899 42.0595V82.5069H72.9899V42.0595H72.1899ZM69.2606 39.1303C70.8814 39.1303 72.1899 40.4387 72.1899 42.0595H72.9899C72.9899 39.9969 71.3232 38.3303 69.2606 38.3303V39.1303ZM47.7722 55.13C47.7722 53.5063 49.0834 52.2007 50.666 52.2007V51.4007C48.636 51.4007 46.9722 53.0701 46.9722 55.13H47.7722ZM47.7722 82.5081V55.13H46.9722V82.5081H47.7722ZM50.666 85.4019C49.0806 85.4019 47.7722 84.0935 47.7722 82.5081H46.9722C46.9722 84.5353 48.6388 86.2019 50.666 86.2019V85.4019ZM53.5953 82.5081C53.5953 84.0907 52.2896 85.4019 50.666 85.4019V86.2019C52.7259 86.2019 54.3953 84.5381 54.3953 82.5081H53.5953ZM53.5953 55.13V82.5081H54.3953V55.13H53.5953ZM50.666 52.2007C52.2869 52.2007 53.5953 53.5091 53.5953 55.13H54.3953C54.3953 53.0673 52.7287 51.4007 50.666 51.4007V52.2007ZM87.6075 65.8509C85.5449 65.8509 83.8782 67.5176 83.8782 69.5802H84.6782C84.6782 67.9594 85.9867 66.6509 87.6075 66.6509V65.8509ZM91.3014 69.5802C91.3014 67.5203 89.6376 65.8509 87.6075 65.8509V66.6509C89.1902 66.6509 90.5014 67.9566 90.5014 69.5802H91.3014ZM91.3014 82.5078V69.5802H90.5014V82.5078H91.3014ZM87.5721 86.2016C89.632 86.2016 91.3014 84.5378 91.3014 82.5078H90.5014C90.5014 84.0904 89.1957 85.4016 87.5721 85.4016V86.2016ZM83.8782 82.5078C83.8782 84.535 85.5449 86.2016 87.5721 86.2016V85.4016C85.9867 85.4016 84.6782 84.0932 84.6782 82.5078H83.8782ZM83.8782 69.5802V82.5078H84.6782V69.5802H83.8782Z' fill='url(%23paint3_linear_1_561)' mask='url(%23path-5-inside-2_1_561)'/%3E%3C/g%3E%3Cdefs%3E%3CclipPath id='bgblur_0_1_561_clip_path' transform='translate(8.54312 8.55109)'%3E%3Cpath d='M56.4879 5.49146L20.5286 15.1267C7.42452 18.638 1.98921 28.0512 5.50011 41.154L15.1253 77.0758C18.6362 90.1786 28.0499 95.613 41.154 92.1018L77.1133 82.4665C90.2174 78.9553 95.6185 69.5513 92.1076 56.4484L82.4824 20.5267C78.9715 7.42382 69.592 1.98022 56.4879 5.49146Z'/%3E%3C/clipPath%3E%3Cfilter id='filter1_f_1_561' x='2.78293' y='3.36597' width='85.2076' height='87.1744' filterUnits='userSpaceOnUse' color-interpolation-filters='sRGB'%3E%3CfeFlood flood-opacity='0' result='BackgroundImageFix'/%3E%3CfeBlend mode='normal' in='SourceGraphic' in2='BackgroundImageFix' result='shape'/%3E%3CfeGaussianBlur stdDeviation='6.5' result='effect1_foregroundBlur_1_561'/%3E%3C/filter%3E%3CclipPath id='bgblur_1_1_561_clip_path' transform='translate(-13.2744 -6.4375)'%3E%3Cpath d='M87.7495 22.4375H50.5252C36.9601 22.4375 29.2744 30.1232 29.2744 43.6883V80.8772C29.2744 94.4423 36.9601 102.128 50.5252 102.128H87.7495C101.315 102.128 108.965 94.4423 108.965 80.8772V43.6883C108.965 30.1232 101.315 22.4375 87.7495 22.4375Z'/%3E%3C/clipPath%3E%3Cfilter id='filter3_d_1_561' x='32.3722' y='23.7303' width='73.5293' height='77.0717' filterUnits='userSpaceOnUse' color-interpolation-filters='sRGB'%3E%3CfeFlood flood-opacity='0' result='BackgroundImageFix'/%3E%3CfeColorMatrix in='SourceAlpha' type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0' result='hardAlpha'/%3E%3CfeOffset dx='5' dy='5'/%3E%3CfeGaussianBlur stdDeviation='5'/%3E%3CfeColorMatrix type='matrix' values='0 0 0 0 1 0 0 0 0 0.447059 0 0 0 0 0.368627 0 0 0 0.5 0'/%3E%3CfeBlend mode='normal' in2='BackgroundImageFix' result='effect1_dropShadow_1_561'/%3E%3CfeBlend mode='normal' in='SourceGraphic' in2='effect1_dropShadow_1_561' result='shape'/%3E%3C/filter%3E%3CclipPath id='bgblur_2_1_561_clip_path' transform='translate(-32.3722 -23.7303)'%3E%3Cpath fill-rule='evenodd' clip-rule='evenodd' d='M69.2606 38.7303C67.4543 38.7303 65.9667 40.2178 65.9667 42.0595V82.5069C65.9667 84.3132 67.4543 85.8008 69.2606 85.8008C71.1023 85.8008 72.5899 84.3132 72.5899 82.5069V42.0595C72.5899 40.2178 71.1023 38.7303 69.2606 38.7303ZM50.666 51.8007C48.8597 51.8007 47.3722 53.2882 47.3722 55.13V82.5081C47.3722 84.3144 48.8597 85.8019 50.666 85.8019C52.5078 85.8019 53.9953 84.3144 53.9953 82.5081V55.13C53.9953 53.2882 52.5078 51.8007 50.666 51.8007ZM84.2782 69.5802C84.2782 67.7385 85.7658 66.2509 87.6075 66.2509C89.4139 66.2509 90.9014 67.7385 90.9014 69.5802V82.5078C90.9014 84.3141 89.4139 85.8016 87.5721 85.8016C85.7658 85.8016 84.2782 84.3141 84.2782 82.5078V69.5802Z'/%3E%3C/clipPath%3E%3ClinearGradient id='paint0_linear_1_561' x1='55.8524' y1='52.4372' x2='-2.97539' y2='103.453' gradientUnits='userSpaceOnUse'%3E%3Cstop stop-color='%23FFA78F'/%3E%3Cstop offset='1' stop-color='%23F23E2C'/%3E%3C/linearGradient%3E%3ClinearGradient id='paint1_linear_1_561' x1='41.9598' y1='31.7215' x2='92.7939' y2='94.6807' gradientUnits='userSpaceOnUse'%3E%3Cstop stop-color='white' stop-opacity='0.25'/%3E%3Cstop offset='1' stop-color='white' stop-opacity='0'/%3E%3C/linearGradient%3E%3ClinearGradient id='paint2_linear_1_561' x1='36.1046' y1='73.6678' x2='56.4956' y2='115.558' gradientUnits='userSpaceOnUse'%3E%3Cstop stop-color='white'/%3E%3Cstop offset='1' stop-color='white' stop-opacity='0.2'/%3E%3C/linearGradient%3E%3ClinearGradient id='paint3_linear_1_561' x1='54.3013' y1='44.2142' x2='84.7371' y2='79.0728' gradientUnits='userSpaceOnUse'%3E%3Cstop stop-color='white' stop-opacity='0.25'/%3E%3Cstop offset='1' stop-color='white' stop-opacity='0'/%3E%3C/linearGradient%3E%3C/defs%3E%3C/svg%3E%0A");
        background-size: cover;
    }

    /* BIAŁE KARTY WYNIKÓW - Nowy gradient obwódki */
    .result-card {
        background: #FFFFFF !important;
        color: #1A1A1A !important;
        padding: 35px;
        border-radius: 24px;
        margin-bottom: 30px;
        position: relative;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        border: 2px solid transparent;
    }
    .result-card::before {
        content: '';
        position: absolute;
        top: -2px; bottom: -2px; left: -2px; right: -2px;
        background: linear-gradient(90deg, #8237FF, #FF749F); /* Fiolet do Różu */
        z-index: -1;
        border-radius: 26px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #060514 !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. PIN LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<h1 class="main-title">Security <span style="font-family: \'Instrument Serif\'; font-style: italic; color: #8237FF; font-size: 40px; letter-spacing: 8px;">Check</span></h1>', unsafe_allow_html=True)
    pin = st.text_input("Enter your access PIN:", type="password")
    if st.button("Enter Access"):
        if pin == "4014": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")
    st.stop()

# --- 5. LOAD KEYS & TOOLS ---
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

class CustomTavilySearchTool(BaseTool):
    name: str = "Tavily Web Search"
    description: str = "Search the web for the latest information and news."
    def _run(self, search_query: str) -> str:
        try:
            client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            response = client.search(query=search_query, max_results=4)
            results = response.get("results", [])
            return "\n\n".join([f"Link: {r.get('url', '')}\nSnippet: {r.get('content', '')}" for r in results]) if results else "No results."
        except Exception as e:
            return f"Search failed: {str(e)}"

search_tool = CustomTavilySearchTool()
scrape_tool = ScrapeWebsiteTool()

# --- 6. AGENTS ---
kellton_brand_voice = """
Identity: Kellton Europe. Results-oriented, casual but sharp. 
Style: Active voice, use contractions, no fluff.
Banned: synergy, leverage, game-changing, revolutionary, utilize, delve, etc.
Constraint: No "Not just X, but Y". Use spaced en-dash ( – ).
"""

researcher = Agent(
    role='Senior Market Researcher',
    goal='Search for 2026 data and trends.',
    backstory='Sharp B2B researcher. Translates topics into English queries.',
    verbose=True,
    tools=[search_tool]
)

copywriter = Agent(
    role='Lead Content Strategist',
    goal='Write sharp LinkedIn posts based strictly on research.',
    backstory=kellton_brand_voice,
    verbose=True,
    tools=[scrape_tool]
)

art_director = Agent(
    role='Art Director',
    goal='Generate ONE Midjourney prompt.',
    backstory="Kellton Europe KV style. Use negative space.",
    verbose=True
)

# --- 7. APP LAYOUT ---

with st.sidebar:
    # Ikona Document + Fioletowy Nagłówek (#8237FF)
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 20px; margin-bottom: 20px;">
           <svg width="24" height="24" viewBox="0 0 102 106" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M8 63.1828L8 22.9945C8.00001 12.9627 16.0501 4.83203 25.9827 4.83203L57.8628 4.83203C68.2759 4.83203 76.7666 13.3672 76.7666 23.8844L76.7666 27.3846V67.573C76.7666 77.6048 68.7165 85.7354 58.784 85.7354H26.9038C16.4907 85.7354 8.00002 77.2003 8.00002 66.683L8 63.1828Z" fill="url(#paint0_linear_1_511)"/>
<g opacity="0.5" filter="url(#filter0_f_1_511)">
<rect x="21" y="63" width="42" height="36" rx="5" transform="rotate(-90 21 63)" fill="#8237FF" fill-opacity="0.5"/>
</g>
<foreignObject x="-1.96582" y="-1.79102" width="118.767" height="130.902"><div xmlns="http://www.w3.org/1999/xhtml" style="backdrop-filter:blur(12px);clip-path:url(#bgblur_0_1_511_clip_path);height:100%;width:100%"></div></foreignObject><path data-figma-bg-blur-radius="24" d="M92.3008 85.9482C92.3008 96.2515 84.0316 104.611 73.8184 104.611H41.9385C31.2459 104.611 22.5342 95.8486 22.5342 85.0586L22.5342 41.4521C22.5343 31.1498 30.8428 22.7091 41.0967 22.709L70.8359 22.709C70.9747 22.709 71.1076 22.7666 71.2021 22.8682L92.167 45.4199C92.2528 45.5123 92.3007 45.6336 92.3008 45.7598L92.3008 85.9482Z" fill="#BA90FF" fill-opacity="0.35" stroke="url(#paint1_linear_1_511)" stroke-linecap="round" stroke-linejoin="round"/>
<mask id="path-4-inside-1_1_511" fill="white">
<path fill-rule="evenodd" clip-rule="evenodd" d="M57.1141 54.9453H43.577C41.935 54.9453 40.5732 56.3206 40.5732 57.9791C40.5732 59.6376 41.935 60.9725 43.577 60.9725H57.1141C58.7561 60.9725 60.1179 59.6376 60.1179 57.9791C60.1179 56.3206 58.7561 54.9453 57.1141 54.9453ZM43.5771 81.1968H65.3646C67.0066 81.1968 68.3683 79.8215 68.3683 78.163C68.3683 76.5045 67.0066 75.1696 65.3646 75.1696H43.5771C41.935 75.1696 40.5733 76.5045 40.5733 78.163C40.5733 79.8215 41.935 81.1968 43.5771 81.1968Z"/>
</mask>
<path fill-rule="evenodd" clip-rule="evenodd" d="M57.1141 54.9453H43.577C41.935 54.9453 40.5732 56.3206 40.5732 57.9791C40.5732 59.6376 41.935 60.9725 43.577 60.9725H57.1141C58.7561 60.9725 60.1179 59.6376 60.1179 57.9791C60.1179 56.3206 58.7561 54.9453 57.1141 54.9453ZM43.5771 81.1968H65.3646C67.0066 81.1968 68.3683 79.8215 68.3683 78.163C68.3683 76.5045 67.0066 75.1696 65.3646 75.1696H43.5771C41.935 75.1696 40.5733 76.5045 40.5733 78.163C40.5733 79.8215 41.935 81.1968 43.5771 81.1968Z" fill="url(#paint2_linear_1_511)"/>
<path d="M43.577 55.3453H57.1141V54.5453H43.577V55.3453ZM40.9732 57.9791C40.9732 56.5378 42.1596 55.3453 43.577 55.3453V54.5453C41.7103 54.5453 40.1732 56.1035 40.1732 57.9791H40.9732ZM43.577 60.5725C42.1526 60.5725 40.9732 59.4135 40.9732 57.9791H40.1732C40.1732 59.8618 41.7173 61.3725 43.577 61.3725V60.5725ZM57.1141 60.5725H43.577V61.3725H57.1141V60.5725ZM59.7179 57.9791C59.7179 59.4135 58.5385 60.5725 57.1141 60.5725V61.3725C58.9738 61.3725 60.5179 59.8618 60.5179 57.9791H59.7179ZM57.1141 55.3453C58.5315 55.3453 59.7179 56.5378 59.7179 57.9791H60.5179C60.5179 56.1035 58.9808 54.5453 57.1141 54.5453V55.3453ZM65.3646 80.7968H43.5771V81.5968H65.3646V80.7968ZM67.9683 78.163C67.9683 79.6043 66.782 80.7968 65.3646 80.7968V81.5968C67.2313 81.5968 68.7683 80.0386 68.7683 78.163H67.9683ZM65.3646 75.5696C66.789 75.5696 67.9683 76.7286 67.9683 78.163H68.7683C68.7683 76.2804 67.2243 74.7696 65.3646 74.7696V75.5696ZM43.5771 75.5696H65.3646V74.7696H43.5771V75.5696ZM40.9733 78.163C40.9733 76.7286 42.1527 75.5696 43.5771 75.5696V74.7696C41.7174 74.7696 40.1733 76.2804 40.1733 78.163H40.9733ZM43.5771 80.7968C42.1597 80.7968 40.9733 79.6043 40.9733 78.163H40.1733C40.1733 80.0386 41.7104 81.5968 43.5771 81.5968V80.7968Z" fill="url(#paint3_linear_1_511)" mask="url(#path-4-inside-1_1_511)"/>
<foreignObject x="51.4658" y="13.2207" width="49.9558" height="50.8023"><div xmlns="http://www.w3.org/1999/xhtml" style="backdrop-filter:blur(7.5px);clip-path:url(#bgblur_1_1_511_clip_path);height:100%;width:100%"></div></foreignObject><g filter="url(#filter2_d_1_511)" data-figma-bg-blur-radius="15">
<mask id="path-6-inside-2_1_511" fill="white">
<path d="M74.544 48.99C77.3355 49.0184 81.2164 49.0305 84.5086 49.0184C86.1947 49.0143 87.0518 46.9796 85.8823 45.754C81.653 41.3124 74.0874 33.3638 69.758 28.8171C68.5605 27.5591 66.4658 28.4248 66.4658 30.1682V40.8311C66.4658 45.305 70.1144 48.99 74.544 48.99Z"/>
</mask>
<path d="M74.544 48.99C77.3355 49.0184 81.2164 49.0305 84.5086 49.0184C86.1947 49.0143 87.0518 46.9796 85.8823 45.754C81.653 41.3124 74.0874 33.3638 69.758 28.8171C68.5605 27.5591 66.4658 28.4248 66.4658 30.1682V40.8311C66.4658 45.305 70.1144 48.99 74.544 48.99Z" fill="url(#paint4_linear_1_511)"/>
<path d="M84.5086 49.0184L84.5076 48.6184L84.5071 48.6184L84.5086 49.0184ZM85.8823 45.754L85.5926 46.0298L85.5929 46.0301L85.8823 45.754ZM69.758 28.8171L69.4682 29.0929L69.4683 29.093L69.758 28.8171ZM74.5399 49.39C77.3335 49.4184 81.2162 49.4305 84.51 49.4183L84.5071 48.6184C81.2166 48.6305 77.3376 48.6184 74.5481 48.5901L74.5399 49.39ZM84.5095 49.4184C86.5535 49.4134 87.5793 46.9531 86.1717 45.4778L85.5929 46.0301C86.5242 47.0062 85.8359 48.6152 84.5076 48.6184L84.5095 49.4184ZM86.172 45.4781C81.9398 41.0336 74.3801 33.0911 70.0476 28.5413L69.4683 29.093C73.7948 33.6365 81.3662 41.5913 85.5926 46.0298L86.172 45.4781ZM70.0477 28.5414C68.5913 27.0114 66.0658 28.078 66.0658 30.1682H66.8658C66.8658 28.7715 68.5296 28.1069 69.4682 29.0929L70.0477 28.5414ZM66.0658 30.1682V40.8311H66.8658V30.1682H66.0658ZM66.0658 40.8311C66.0658 45.5221 69.8898 49.39 74.544 49.39V48.59C70.3391 48.59 66.8658 45.0878 66.8658 40.8311H66.0658Z" fill="url(#paint5_linear_1_511)" mask="url(#path-6-inside-2_1_511)"/>
</g>
<defs>
<filter id="filter0_f_1_511" x="0" y="0" width="78" height="84" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feFlood flood-opacity="0" result="BackgroundImageFix"/>
<feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
<feGaussianBlur stdDeviation="10.5" result="effect1_foregroundBlur_1_511"/>
</filter>
<clipPath id="bgblur_0_1_511_clip_path" transform="translate(1.96582 1.79102)"><path d="M92.3008 85.9482C92.3008 96.2515 84.0316 104.611 73.8184 104.611H41.9385C31.2459 104.611 22.5342 95.8486 22.5342 85.0586L22.5342 41.4521C22.5343 31.1498 30.8428 22.7091 41.0967 22.709L70.8359 22.709C70.9747 22.709 71.1076 22.7666 71.2021 22.8682L92.167 45.4199C92.2528 45.5123 92.3007 45.6336 92.3008 45.7598L92.3008 85.9482Z"/>
</clipPath><filter id="filter2_d_1_511" x="51.4658" y="13.2207" width="49.9558" height="50.8023" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feFlood flood-opacity="0" result="BackgroundImageFix"/>
<feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
<feOffset dx="5" dy="5"/>
<feGaussianBlur stdDeviation="5"/>
<feColorMatrix type="matrix" values="0 0 0 0 0.577356 0 0 0 0 0.359375 0 0 0 0 0.9375 0 0 0 0.25 0"/>
<feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_1_511"/>
<feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_1_511" result="shape"/>
</filter>
<clipPath id="bgblur_1_1_511_clip_path" transform="translate(-51.4658 -13.2207)"><path d="M74.544 48.99C77.3355 49.0184 81.2164 49.0305 84.5086 49.0184C86.1947 49.0143 87.0518 46.9796 85.8823 45.754C81.653 41.3124 74.0874 33.3638 69.758 28.8171C68.5605 27.5591 66.4658 28.4248 66.4658 30.1682V40.8311C66.4658 45.305 70.1144 48.99 74.544 48.99Z"/>
</clipPath><linearGradient id="paint0_linear_1_511" x1="57.3577" y1="4.83203" x2="57.3577" y2="85.7355" gradientUnits="userSpaceOnUse">
<stop stop-color="#BC94FF"/>
<stop offset="1" stop-color="#9F66FF"/>
</linearGradient>
<linearGradient id="paint1_linear_1_511" x1="33.9807" y1="32.6342" x2="86.7032" y2="88.1375" gradientUnits="userSpaceOnUse">
<stop stop-color="white" stop-opacity="0.25"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
<linearGradient id="paint2_linear_1_511" x1="66.3977" y1="59.6858" x2="35.4406" y2="60.7545" gradientUnits="userSpaceOnUse">
<stop stop-color="white"/>
<stop offset="1" stop-color="white" stop-opacity="0.2"/>
</linearGradient>
<linearGradient id="paint3_linear_1_511" x1="44.9978" y1="58.0036" x2="61.5175" y2="79.6667" gradientUnits="userSpaceOnUse">
<stop stop-color="white" stop-opacity="0.25"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
<linearGradient id="paint4_linear_1_511" x1="85.0068" y1="31.9772" x2="62.776" y2="32.6725" gradientUnits="userSpaceOnUse">
<stop stop-color="white"/>
<stop offset="1" stop-color="white" stop-opacity="0.2"/>
</linearGradient>
<linearGradient id="paint5_linear_1_511" x1="69.6425" y1="30.6442" x2="83.0177" y2="46.5357" gradientUnits="userSpaceOnUse">
<stop stop-color="white" stop-opacity="0.25"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
</defs>
</svg>
            <span style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 20px; letter-spacing: 1px; color: #8237FF;">Archive</span>
        </div>
    ''', unsafe_allow_html=True)
    
    hist_df = load_history()
    
    if not hist_df.empty:
        st.dataframe(hist_df[['Date', 'Topic/Notes']].tail(5), use_container_width=True)
    else:
        st.markdown("<p style='color: #888; font-size: 14px;'>Waiting for your first post...</p>", unsafe_allow_html=True)
        
    st.download_button(
        label="DOWNLOAD CSV", 
        data=hist_df.to_csv(index=False).encode('utf-8-sig'), 
        file_name="kellton_plan.csv", 
        mime="text/csv",
        use_container_width=True
    )

# WIDOK GŁÓWNY
st.markdown('<h1 class="main-title">KELLTON EUROPE</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">Social Media Specialist</span>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    # Ikona Edit (Pen) + Zielony Nagłówek (#30AD31)
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="28" height="28" viewBox="0 0 104 101" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M66.7719 10.2218C62.4325 7.96417 57.372 7.57499 52.7613 9.12456L22.3462 17.2743C17.5458 18.2464 13.358 21.1136 10.7287 25.2386C8.47099 29.578 8.0818 34.6384 9.64008 39.2817L17.7897 69.6966C18.7618 74.4969 21.6291 78.6847 25.754 81.314C30.0935 83.5716 35.1539 83.9608 39.7972 82.4025L70.2124 74.2528C74.9802 73.2894 79.2006 70.4134 81.8299 66.2885C84.055 61.9577 84.4767 56.8886 82.9185 52.2454L74.7688 21.8305C73.7641 17.0389 70.8969 12.8511 66.7719 10.2218Z" fill="url(#paint0_linear_1_317)"/>
<g opacity="0.5" filter="url(#filter0_f_1_317)">
<path d="M51.4166 18.7934L28.4797 25.1913C20.1599 27.512 16.5106 33.1467 18.5579 40.4865L25.492 65.3453C27.5729 72.8053 33.5849 75.6414 41.9047 73.3207L64.8417 66.9227C73.2956 64.5646 76.8349 59.0644 74.754 51.6043L67.8199 26.7455C65.7726 19.4058 59.8705 16.4353 51.4166 18.7934Z" fill="#30AD31"/>
</g>
<foreignObject x="4.20251" y="0.991783" width="123.365" height="123.365"><div xmlns="http://www.w3.org/1999/xhtml" style="backdrop-filter:blur(12px);clip-path:url(#bgblur_0_1_317_clip_path);height:100%;width:100%"></div></foreignObject><g data-figma-bg-blur-radius="24">
<mask id="path-3-outside-1_1_317" maskUnits="userSpaceOnUse" x="28.2025" y="24.9918" width="76" height="76" fill="black">
<rect fill="white" x="28.2025" y="24.9918" width="76" height="76"/>
<path d="M97.3995 31.1233C93.4786 27.5321 88.275 25.6999 82.9982 26.0297H48.772C43.4586 25.6999 38.255 27.5321 34.334 31.1233C30.7429 35.0442 28.9106 40.2477 29.2404 45.5612V79.787C28.9106 85.1005 30.7429 90.304 34.334 94.2249C38.255 97.8161 43.4586 99.6483 48.772 99.3185H82.9982C88.275 99.6483 93.5152 97.8161 97.4362 94.2249C100.991 90.304 102.86 85.1005 102.53 79.787V45.5612C102.823 40.2477 100.991 35.0442 97.3995 31.1233Z"/>
</mask>
<path d="M97.3995 31.1233C93.4786 27.5321 88.275 25.6999 82.9982 26.0297H48.772C43.4586 25.6999 38.255 27.5321 34.334 31.1233C30.7429 35.0442 28.9106 40.2477 29.2404 45.5612V79.787C28.9106 85.1005 30.7429 90.304 34.334 94.2249C38.255 97.8161 43.4586 99.6483 48.772 99.3185H82.9982C88.275 99.6483 93.5152 97.8161 97.4362 94.2249C100.991 90.304 102.86 85.1005 102.53 79.787V45.5612C102.823 40.2477 100.991 35.0442 97.3995 31.1233Z" fill="#72DC60" fill-opacity="0.35"/>
<path d="M96.7241 31.8607C97.1314 32.2337 97.764 32.206 98.137 31.7987C98.51 31.3914 98.4822 30.7588 98.075 30.3858L96.7241 31.8607ZM82.9982 26.0297V27.0297C83.019 27.0297 83.0398 27.029 83.0606 27.0277L82.9982 26.0297ZM48.772 26.0297L48.7101 27.0278C48.7307 27.0291 48.7514 27.0297 48.772 27.0297V26.0297ZM34.334 31.1233L33.6586 30.3858C33.6371 30.4056 33.6164 30.4263 33.5966 30.4479L34.334 31.1233ZM29.2404 45.5612H30.2404C30.2404 45.5405 30.2398 45.5198 30.2385 45.4992L29.2404 45.5612ZM29.2404 79.787L30.2385 79.849C30.2398 79.8283 30.2404 79.8077 30.2404 79.787H29.2404ZM34.334 94.2249L33.5966 94.9003C33.6164 94.9219 33.6371 94.9426 33.6586 94.9623L34.334 94.2249ZM48.772 99.3185V98.3185C48.7514 98.3185 48.7307 98.3191 48.7101 98.3204L48.772 99.3185ZM82.9982 99.3185L83.0606 98.3204C83.0398 98.3191 83.019 98.3185 82.9982 98.3185V99.3185ZM97.4362 94.2249L98.1116 94.9623C98.1344 94.9414 98.1563 94.9195 98.1771 94.8966L97.4362 94.2249ZM102.53 79.787H101.53C101.53 79.8077 101.53 79.8283 101.532 79.849L102.53 79.787ZM102.53 45.5612L101.531 45.5061C101.53 45.5244 101.53 45.5428 101.53 45.5612H102.53ZM98.137 30.4479C97.764 30.0406 97.1314 30.0128 96.7241 30.3858C96.3169 30.7589 96.2891 31.3914 96.6621 31.7987L98.137 30.4479ZM98.075 30.3858C93.9537 26.6112 88.4838 24.6849 82.9358 25.0316L83.0606 27.0277C88.0662 26.7149 93.0034 28.453 96.7241 31.8607L98.075 30.3858ZM82.9982 25.0297H48.772V27.0297H82.9982V25.0297ZM48.834 25.0316C43.2507 24.6851 37.7806 26.6105 33.6586 30.3858L35.0094 31.8607C38.7294 28.4537 43.6665 26.7147 48.7101 27.0278L48.834 25.0316ZM33.5966 30.4479C29.8213 34.5698 27.8958 40.0398 28.2423 45.6231L30.2385 45.4992C29.9255 40.4556 31.6644 35.5186 35.0715 31.7987L33.5966 30.4479ZM28.2404 45.5612V79.787H30.2404V45.5612H28.2404ZM28.2423 79.7251C27.8958 85.3084 29.8213 90.7783 33.5966 94.9003L35.0715 93.5495C31.6644 89.8296 29.9255 84.8925 30.2385 79.849L28.2423 79.7251ZM33.6586 94.9623C37.7806 98.7376 43.2507 100.663 48.834 100.317L48.7101 98.3204C43.6665 98.6334 38.7294 96.8945 35.0094 93.4875L33.6586 94.9623ZM48.772 100.318H82.9982V98.3185H48.772V100.318ZM82.9358 100.317C88.4821 100.663 93.9891 98.7381 98.1116 94.9623L96.7608 93.4875C93.0413 96.894 88.0679 98.6334 83.0606 98.3204L82.9358 100.317ZM98.1771 94.8966C101.909 90.7795 103.875 85.3127 103.528 79.7251L101.532 79.849C101.845 84.8882 100.072 89.8284 96.6953 93.5533L98.1771 94.8966ZM103.53 79.787V45.5612H101.53V79.787H103.53ZM103.528 45.6162C103.836 40.0378 101.912 34.57 98.137 30.4479L96.6621 31.7987C100.069 35.5185 101.81 40.4577 101.531 45.5061L103.528 45.6162Z" fill="url(#paint1_linear_1_317)" mask="url(#path-3-outside-1_1_317)"/>
</g>
<foreignObject x="32.0844" y="26.0738" width="71.3994" height="71.3165"><div xmlns="http://www.w3.org/1999/xhtml" style="backdrop-filter:blur(7.5px);clip-path:url(#bgblur_1_1_317_clip_path);height:100%;width:100%"></div></foreignObject><g filter="url(#filter2_d_1_317)" data-figma-bg-blur-radius="15">
<mask id="path-5-inside-2_1_317" fill="white">
<path d="M86.8072 55.7132L62.1453 80.4482C60.8628 81.6941 59.1771 82.3904 57.4182 82.3904H48.8067C48.3303 82.3904 47.8905 82.2071 47.5607 81.8773C47.2309 81.5475 47.0844 81.1078 47.0844 80.6314L47.3042 71.9467C47.3409 70.2244 48.0371 68.6121 49.2464 67.4028L66.7259 49.9234C67.0191 49.6303 67.5321 49.6303 67.8252 49.9234L73.9449 56.0064C74.348 56.4095 74.9343 56.666 75.5573 56.666C76.9131 56.666 77.9758 55.5667 77.9758 54.2475C77.9758 53.5879 77.7193 53.0016 77.3162 52.5618C77.2063 52.4153 71.3798 46.6254 71.3798 46.6254C71.0133 46.259 71.0133 45.636 71.3798 45.2696L73.835 42.7778C76.1069 40.5058 79.7714 40.5058 82.0434 42.7778L86.8072 47.5415C89.0425 49.7769 89.0425 53.4413 86.8072 55.7132Z"/>
</mask>
<path d="M86.8072 55.7132L62.1453 80.4482C60.8628 81.6941 59.1771 82.3904 57.4182 82.3904H48.8067C48.3303 82.3904 47.8905 82.2071 47.5607 81.8773C47.2309 81.5475 47.0844 81.1078 47.0844 80.6314L47.3042 71.9467C47.3409 70.2244 48.0371 68.6121 49.2464 67.4028L66.7259 49.9234C67.0191 49.6303 67.5321 49.6303 67.8252 49.9234L73.9449 56.0064C74.348 56.4095 74.9343 56.666 75.5573 56.666C76.9131 56.666 77.9758 55.5667 77.9758 54.2475C77.9758 53.5879 77.7193 53.0016 77.3162 52.5618C77.2063 52.4153 71.3798 46.6254 71.3798 46.6254C71.0133 46.259 71.0133 45.636 71.3798 45.2696L73.835 42.7778C76.1069 40.5058 79.7714 40.5058 82.0434 42.7778L86.8072 47.5415C89.0425 49.7769 89.0425 53.4413 86.8072 55.7132Z" fill="url(#paint2_linear_1_317)"/>
<path d="M62.1453 80.4482L62.2847 80.5917L62.2869 80.5894L62.1453 80.4482ZM47.0844 80.6314L46.8844 80.6264V80.6314H47.0844ZM47.3042 71.9467L47.5042 71.9518L47.5042 71.951L47.3042 71.9467ZM49.2464 67.4028L49.3878 67.5442V67.5442L49.2464 67.4028ZM66.7259 49.9234L66.5845 49.782V49.782L66.7259 49.9234ZM67.8252 49.9234L67.6838 50.0649L67.6842 50.0653L67.8252 49.9234ZM73.9449 56.0064L74.0863 55.865L74.0859 55.8646L73.9449 56.0064ZM77.3162 52.5618L77.1562 52.6818L77.1621 52.6897L77.1688 52.697L77.3162 52.5618ZM71.3798 46.6254L71.2384 46.7669L71.2388 46.7673L71.3798 46.6254ZM71.3798 45.2696L71.5212 45.411L71.5222 45.41L71.3798 45.2696ZM73.835 42.7778L73.6935 42.6364L73.6925 42.6374L73.835 42.7778ZM82.0434 42.7778L81.902 42.9192L82.0434 42.7778ZM86.8072 47.5415L86.9486 47.4001V47.4001L86.8072 47.5415ZM86.6656 55.572L62.0037 80.307L62.2869 80.5894L86.9488 55.8545L86.6656 55.572ZM62.006 80.3047C60.7597 81.5154 59.1237 82.1904 57.4182 82.1904V82.5904C59.2305 82.5904 60.9658 81.8728 62.2847 80.5917L62.006 80.3047ZM57.4182 82.1904H48.8067V82.5904H57.4182V82.1904ZM48.8067 82.1904C48.383 82.1904 47.9942 82.028 47.7022 81.7359L47.4193 82.0188C47.7868 82.3863 48.2775 82.5904 48.8067 82.5904V82.1904ZM47.7022 81.7359C47.4174 81.4511 47.2844 81.0665 47.2844 80.6314H46.8844C46.8844 81.1492 47.0445 81.6439 47.4193 82.0188L47.7022 81.7359ZM47.2843 80.6365L47.5042 71.9518L47.1043 71.9416L46.8844 80.6264L47.2843 80.6365ZM47.5042 71.951C47.5397 70.2807 48.2147 68.7173 49.3878 67.5442L49.105 67.2614C47.8595 68.5068 47.142 70.1682 47.1043 71.9425L47.5042 71.951ZM49.3878 67.5442L66.8673 50.0649L66.5845 49.782L49.105 67.2614L49.3878 67.5442ZM66.8673 50.0649C67.0824 49.8498 67.4688 49.8498 67.6838 50.0649L67.9667 49.782C67.5954 49.4108 66.9557 49.4108 66.5845 49.782L66.8673 50.0649ZM67.6842 50.0653L73.8039 56.1482L74.0859 55.8646L67.9662 49.7816L67.6842 50.0653ZM73.8035 56.1478C74.2437 56.588 74.8807 56.866 75.5573 56.866V56.466C74.988 56.466 74.4523 56.231 74.0863 55.865L73.8035 56.1478ZM75.5573 56.866C77.0255 56.866 78.1758 55.6751 78.1758 54.2475H77.7758C77.7758 55.4582 76.8007 56.466 75.5573 56.466V56.866ZM78.1758 54.2475C78.1758 53.5344 77.8981 52.9007 77.4636 52.4267L77.1688 52.697C77.5405 53.1025 77.7758 53.6414 77.7758 54.2475H78.1758ZM77.4762 52.4418C77.4597 52.4199 77.4182 52.3765 77.3753 52.3321C77.3259 52.2809 77.2571 52.2106 77.172 52.1243C77.0018 51.9515 76.7648 51.713 76.4839 51.4312C75.922 50.8676 75.1832 50.1299 74.448 49.397C73.7127 48.6641 72.9809 47.9357 72.4329 47.3906C72.1589 47.118 71.9309 46.8913 71.7714 46.7327C71.6916 46.6534 71.6289 46.5911 71.5862 46.5486C71.5649 46.5274 71.5485 46.5112 71.5375 46.5002C71.532 46.4947 71.5278 46.4906 71.525 46.4878C71.5236 46.4864 71.5225 46.4853 71.5218 46.4846C71.5215 46.4843 71.5212 46.484 71.521 46.4838C71.5209 46.4837 71.5209 46.4837 71.5208 46.4836C71.5208 46.4836 71.5208 46.4836 71.3798 46.6254C71.2388 46.7673 71.2388 46.7673 71.2389 46.7674C71.2389 46.7674 71.239 46.7675 71.2391 46.7676C71.2392 46.7677 71.2395 46.768 71.2399 46.7684C71.2406 46.7691 71.2416 46.7701 71.243 46.7715C71.2458 46.7743 71.25 46.7784 71.2555 46.7839C71.2665 46.7949 71.2829 46.8111 71.3042 46.8323C71.3469 46.8748 71.4096 46.937 71.4893 47.0163C71.6489 47.1749 71.8769 47.4017 72.1508 47.6742C72.6988 48.2192 73.4305 48.9475 74.1656 49.6803C74.9007 50.4132 75.6392 51.1505 76.2006 51.7136C76.4814 51.9953 76.7177 52.2331 76.8871 52.405C76.9719 52.4911 77.0395 52.5602 77.0875 52.6099C77.1421 52.6664 77.159 52.6855 77.1562 52.6818L77.4762 52.4418ZM71.5212 46.484C71.2329 46.1957 71.2329 45.6994 71.5212 45.411L71.2384 45.1282C70.7938 45.5727 70.7938 46.3223 71.2384 46.7669L71.5212 46.484ZM71.5222 45.41L73.9774 42.9181L73.6925 42.6374L71.2373 45.1292L71.5222 45.41ZM73.9764 42.9192C76.1703 40.7254 79.7081 40.7254 81.902 42.9192L82.1848 42.6364C79.8347 40.2863 76.0436 40.2863 73.6935 42.6364L73.9764 42.9192ZM81.902 42.9192L86.6658 47.683L86.9486 47.4001L82.1848 42.6364L81.902 42.9192ZM86.6658 47.683C88.8224 49.8395 88.824 53.3782 86.6646 55.573L86.9498 55.8535C89.261 53.5044 89.2627 49.7142 86.9486 47.4001L86.6658 47.683Z" fill="url(#paint3_linear_1_317)" fill-opacity="0.5" mask="url(#path-5-inside-2_1_317)"/>
</g>
<defs>
<filter id="filter0_f_1_317" x="0" y="0" width="93.3364" height="92.1102" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feFlood flood-opacity="0" result="BackgroundImageFix"/>
<feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
<feGaussianBlur stdDeviation="9" result="effect1_foregroundBlur_1_317"/>
</filter>
<clipPath id="bgblur_0_1_317_clip_path" transform="translate(-4.20251 -0.991783)"><path d="M97.3995 31.1233C93.4786 27.5321 88.275 25.6999 82.9982 26.0297H48.772C43.4586 25.6999 38.255 27.5321 34.334 31.1233C30.7429 35.0442 28.9106 40.2477 29.2404 45.5612V79.787C28.9106 85.1005 30.7429 90.304 34.334 94.2249C38.255 97.8161 43.4586 99.6483 48.772 99.3185H82.9982C88.275 99.6483 93.5152 97.8161 97.4362 94.2249C100.991 90.304 102.86 85.1005 102.53 79.787V45.5612C102.823 40.2477 100.991 35.0442 97.3995 31.1233Z"/>
</clipPath><filter id="filter2_d_1_317" x="32.0844" y="26.0738" width="71.3994" height="71.3165" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feFlood flood-opacity="0" result="BackgroundImageFix"/>
<feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
<feOffset dx="5" dy="5"/>
<feGaussianBlur stdDeviation="5"/>
<feColorMatrix type="matrix" values="0 0 0 0 0.454902 0 0 0 0 0.870588 0 0 0 0 0.376471 0 0 0 0.5 0"/>
<feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_1_317"/>
<feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_1_317" result="shape"/>
</filter>
<clipPath id="bgblur_1_1_317_clip_path" transform="translate(-32.0844 -26.0738)"><path d="M86.8072 55.7132L62.1453 80.4482C60.8628 81.6941 59.1771 82.3904 57.4182 82.3904H48.8067C48.3303 82.3904 47.8905 82.2071 47.5607 81.8773C47.2309 81.5475 47.0844 81.1078 47.0844 80.6314L47.3042 71.9467C47.3409 70.2244 48.0371 68.6121 49.2464 67.4028L66.7259 49.9234C67.0191 49.6303 67.5321 49.6303 67.8252 49.9234L73.9449 56.0064C74.348 56.4095 74.9343 56.666 75.5573 56.666C76.9131 56.666 77.9758 55.5667 77.9758 54.2475C77.9758 53.5879 77.7193 53.0016 77.3162 52.5618C77.2063 52.4153 71.3798 46.6254 71.3798 46.6254C71.0133 46.259 71.0133 45.636 71.3798 45.2696L73.835 42.7778C76.1069 40.5058 79.7714 40.5058 82.0434 42.7778L86.8072 47.5415C89.0425 49.7769 89.0425 53.4413 86.8072 55.7132Z"/>
</clipPath><linearGradient id="paint0_linear_1_317" x1="70.1423" y1="4.43124" x2="38.5791" y2="70.5115" gradientUnits="userSpaceOnUse">
<stop stop-color="#9BF763"/>
<stop offset="1" stop-color="#26AB5B"/>
</linearGradient>
<linearGradient id="paint1_linear_1_317" x1="40.881" y1="34.5389" x2="87.6798" y2="92.5003" gradientUnits="userSpaceOnUse">
<stop stop-color="white" stop-opacity="0.25"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
<linearGradient id="paint2_linear_1_317" x1="85.5485" y1="48.5348" x2="39.4338" y2="50.0413" gradientUnits="userSpaceOnUse">
<stop stop-color="white"/>
<stop offset="1" stop-color="white" stop-opacity="0.2"/>
</linearGradient>
<linearGradient id="paint3_linear_1_317" x1="51.544" y1="54.9335" x2="86.6977" y2="55.128" gradientUnits="userSpaceOnUse">
<stop stop-color="white"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
</defs>
</svg>

            <span style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 24px; letter-spacing: 1px; color: #30AD31;">What are we writing about today?</span>
        </div>
    ''', unsafe_allow_html=True)
    
    temat = st.text_area("", height=300, placeholder="Np. Strategia AI w designie --- Trendy UX 2026", label_visibility="collapsed")
    btn = st.button("GET TO WORK, BRO")

with col2:
    # Ikona Chat + Fioletowy Nagłówek (#8237FF)
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="28" height="28" viewBox="0 0 104 96" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M65.936 26C84.528 26 98.0001 41.168 98.0001 58C98.0001 63.376 96.4321 68.912 93.6801 73.9681C93.1681 74.8001 93.1041 75.8561 93.4561 76.8481L95.6001 84.0161C96.0801 85.7441 94.6081 87.0241 92.9761 86.5121L86.512 84.5921C84.752 84.0161 83.376 84.7521 81.7408 85.7441C77.0688 88.4961 71.248 89.9041 66 89.9041C50.128 89.9041 34 77.6481 34 57.904C34 40.88 47.76 26 65.936 26Z" fill="url(#paint0_linear_1_106)"/>
<g opacity="0.5" filter="url(#filter0_f_1_106)">
<path d="M86.3695 58.319C86.3695 69.7353 77.1171 78.9857 65.7029 78.9857C54.2887 78.9857 45.0362 69.7353 45.0362 58.319C45.0362 46.9069 54.2887 37.6523 65.7029 37.6523C77.1171 37.6523 86.3695 46.9069 86.3695 58.319Z" fill="#8237FF"/>
</g>
<foreignObject x="-24" y="-24" width="131.667" height="131.544"><div xmlns="http://www.w3.org/1999/xhtml" style="backdrop-filter:blur(12px);clip-path:url(#bgblur_0_1_106_clip_path);height:100%;width:100%"></div></foreignObject><g data-figma-bg-blur-radius="24">
<mask id="path-3-outside-1_1_106" maskUnits="userSpaceOnUse" x="0" y="0" width="84" height="84" fill="black">
<rect fill="white" width="84" height="84"/>
<path d="M41.915 1C18.1908 1 1 20.355 1 41.8333C1 48.6933 3.00083 55.7575 6.5125 62.2092C7.16583 63.2708 7.2475 64.6183 6.79833 65.8842L4.0625 75.0308C3.45 77.2358 5.32833 78.8692 7.41083 78.2158L15.6592 75.7658C17.905 75.0308 19.6608 75.97 21.7474 77.2358C27.7091 80.7475 35.1367 82.5442 41.8333 82.5442C62.0867 82.5442 82.6667 66.905 82.6667 41.7108C82.6667 19.9875 65.1083 1 41.915 1Z"/>
</mask>
<path d="M41.915 1C18.1908 1 1 20.355 1 41.8333C1 48.6933 3.00083 55.7575 6.5125 62.2092C7.16583 63.2708 7.2475 64.6183 6.79833 65.8842L4.0625 75.0308C3.45 77.2358 5.32833 78.8692 7.41083 78.2158L15.6592 75.7658C17.905 75.0308 19.6608 75.97 21.7474 77.2358C27.7091 80.7475 35.1367 82.5442 41.8333 82.5442C62.0867 82.5442 82.6667 66.905 82.6667 41.7108C82.6667 19.9875 65.1083 1 41.915 1Z" fill="#BA90FF" fill-opacity="0.35"/>
<path d="M41.915 2C42.4673 2 42.915 1.55228 42.915 1C42.915 0.447715 42.4673 0 41.915 0V2ZM6.5125 62.2092L5.63418 62.6872C5.64266 62.7028 5.65155 62.7182 5.66084 62.7333L6.5125 62.2092ZM6.79833 65.8842L5.85591 65.5498C5.85029 65.5656 5.84508 65.5815 5.84027 65.5976L6.79833 65.8842ZM4.0625 75.0308L3.10444 74.7443C3.10256 74.7506 3.10074 74.7569 3.09898 74.7632L4.0625 75.0308ZM7.41083 78.2158L7.1261 77.2572C7.12122 77.2587 7.11635 77.2602 7.11149 77.2617L7.41083 78.2158ZM15.6592 75.7658L15.9439 76.7244C15.9527 76.7218 15.9615 76.7191 15.9702 76.7162L15.6592 75.7658ZM21.7474 77.2358L21.2287 78.0909L21.2399 78.0975L21.7474 77.2358ZM41.915 0C41.3627 0 40.915 0.447715 40.915 1C40.915 1.55228 41.3627 2 41.915 2V0ZM41.915 0C17.6057 0 0 19.8362 0 41.8333H2C2 20.8738 18.776 2 41.915 2V0ZM0 41.8333C0 48.8843 2.05494 56.1114 5.63418 62.6872L7.39082 61.7311C3.94672 55.4036 2 48.5024 2 41.8333H0ZM5.66084 62.7333C6.13142 63.498 6.22039 64.5226 5.85591 65.5498L7.74076 66.2186C8.27461 64.7141 8.20025 63.0437 7.36416 61.6851L5.66084 62.7333ZM5.84027 65.5976L3.10444 74.7443L5.02056 75.3174L7.75639 66.1707L5.84027 65.5976ZM3.09898 74.7632C2.69802 76.2067 3.10385 77.5598 4.04824 78.4305C4.98142 79.2907 6.34982 79.5968 7.71017 79.17L7.11149 77.2617C6.38935 77.4882 5.77733 77.3043 5.40385 76.96C5.04157 76.626 4.81448 76.06 5.02602 75.2985L3.09898 74.7632ZM7.69557 79.1744L15.9439 76.7244L15.3744 74.8072L7.1261 77.2572L7.69557 79.1744ZM15.9702 76.7162C17.7353 76.1386 19.1168 76.8096 21.2287 78.0908L22.2661 76.3809C20.2048 75.1304 18.0747 73.9231 15.3481 74.8154L15.9702 76.7162ZM21.2399 78.0975C27.371 81.7089 34.9772 83.5442 41.8333 83.5442V81.5442C35.2961 81.5442 28.0472 79.7861 22.255 76.3742L21.2399 78.0975ZM41.8333 83.5442C62.5583 83.5442 83.6667 67.5346 83.6667 41.7108H81.6667C81.6667 66.2754 61.615 81.5442 41.8333 81.5442V83.5442ZM83.6667 41.7108C83.6667 19.4575 65.6827 0 41.915 0V2C64.534 2 81.6667 20.5175 81.6667 41.7108H83.6667Z" fill="url(#paint1_linear_1_106)" mask="url(#path-3-outside-1_1_106)"/>
</g>
<foreignObject x="2.70117" y="21.6465" width="78.1025" height="40.4539"><div xmlns="http://www.w3.org/1999/xhtml" style="backdrop-filter:blur(7.5px);clip-path:url(#bgblur_1_1_106_clip_path);height:100%;width:100%"></div></foreignObject><g filter="url(#filter2_d_1_106)" data-figma-bg-blur-radius="15">
<mask id="path-5-inside-2_1_106" fill="white">
<path fill-rule="evenodd" clip-rule="evenodd" d="M41.7535 47.1003C38.8543 47.0595 36.5268 44.732 36.5268 41.8328C36.5268 38.9745 38.8951 36.6062 41.7535 36.647C44.6526 36.647 46.9801 38.9745 46.9801 41.8737C46.9801 44.732 44.6526 47.1003 41.7535 47.1003ZM22.9278 47.1004C20.0695 47.1004 17.7012 44.7321 17.7012 41.8738C17.7012 38.9746 20.0287 36.6471 22.9278 36.6471C25.827 36.6471 28.1545 38.9746 28.1545 41.8738C28.1545 44.7321 25.827 47.0596 22.9278 47.1004ZM55.3504 41.8737C55.3504 44.732 57.6779 47.1003 60.577 47.1003C63.4762 47.1003 65.8037 44.732 65.8037 41.8737C65.8037 38.9745 63.4762 36.647 60.577 36.647C57.6779 36.647 55.3504 38.9745 55.3504 41.8737Z"/>
</mask>
<path fill-rule="evenodd" clip-rule="evenodd" d="M41.7535 47.1003C38.8543 47.0595 36.5268 44.732 36.5268 41.8328C36.5268 38.9745 38.8951 36.6062 41.7535 36.647C44.6526 36.647 46.9801 38.9745 46.9801 41.8737C46.9801 44.732 44.6526 47.1003 41.7535 47.1003ZM22.9278 47.1004C20.0695 47.1004 17.7012 44.7321 17.7012 41.8738C17.7012 38.9746 20.0287 36.6471 22.9278 36.6471C25.827 36.6471 28.1545 38.9746 28.1545 41.8738C28.1545 44.7321 25.827 47.0596 22.9278 47.1004ZM55.3504 41.8737C55.3504 44.732 57.6779 47.1003 60.577 47.1003C63.4762 47.1003 65.8037 44.732 65.8037 41.8737C65.8037 38.9745 63.4762 36.647 60.577 36.647C57.6779 36.647 55.3504 38.9745 55.3504 41.8737Z" fill="url(#paint2_linear_1_106)"/>
<path d="M41.7535 47.1003L41.7478 47.5003H41.7535V47.1003ZM41.7535 36.647L41.7478 37.047H41.7535V36.647ZM22.9278 47.1004V47.5005L22.9335 47.5004L22.9278 47.1004ZM36.1268 41.8328C36.1268 44.954 38.6333 47.4564 41.7479 47.5003L41.7591 46.7004C39.0754 46.6626 36.9268 44.51 36.9268 41.8328H36.1268ZM41.7592 36.247C38.6744 36.203 36.1268 38.7547 36.1268 41.8328H36.9268C36.9268 39.1943 39.1159 37.0094 41.7478 37.047L41.7592 36.247ZM47.3801 41.8737C47.3801 38.7536 44.8736 36.247 41.7535 36.247V37.047C44.4317 37.047 46.5801 39.1954 46.5801 41.8737H47.3801ZM41.7535 47.5003C44.8756 47.5003 47.3801 44.9509 47.3801 41.8737H46.5801C46.5801 44.5131 44.4297 46.7003 41.7535 46.7003V47.5003ZM17.3012 41.8738C17.3012 44.953 19.8486 47.5004 22.9278 47.5004V46.7004C20.2904 46.7004 18.1012 44.5112 18.1012 41.8738H17.3012ZM22.9278 36.2471C19.8078 36.2471 17.3012 38.7537 17.3012 41.8738H18.1012C18.1012 39.1955 20.2496 37.0471 22.9278 37.0471V36.2471ZM28.5545 41.8738C28.5545 38.7537 26.0479 36.2471 22.9278 36.2471V37.0471C25.6061 37.0471 27.7545 39.1955 27.7545 41.8738H28.5545ZM22.9335 47.5004C26.046 47.4565 28.5545 44.9561 28.5545 41.8738H27.7545C27.7545 44.5081 25.608 46.6626 22.9222 46.7005L22.9335 47.5004ZM60.577 46.7003C57.9008 46.7003 55.7504 44.5131 55.7504 41.8737H54.9504C54.9504 44.9509 57.4549 47.5003 60.577 47.5003V46.7003ZM65.4037 41.8737C65.4037 44.5131 63.2533 46.7003 60.577 46.7003V47.5003C63.6991 47.5003 66.2037 44.9509 66.2037 41.8737H65.4037ZM60.577 37.047C63.2553 37.047 65.4037 39.1954 65.4037 41.8737H66.2037C66.2037 38.7536 63.6971 36.247 60.577 36.247V37.047ZM55.7504 41.8737C55.7504 39.1954 57.8988 37.047 60.577 37.047V36.247C57.457 36.247 54.9504 38.7536 54.9504 41.8737H55.7504Z" fill="url(#paint3_linear_1_106)" mask="url(#path-5-inside-2_1_106)"/>
</g>
<defs>
<filter id="filter0_f_1_106" x="28.0362" y="20.6523" width="75.3333" height="75.3333" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feFlood flood-opacity="0" result="BackgroundImageFix"/>
<feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"/>
<feGaussianBlur stdDeviation="8.5" result="effect1_foregroundBlur_1_106"/>
</filter>
<clipPath id="bgblur_0_1_106_clip_path" transform="translate(24 24)"><path d="M41.915 1C18.1908 1 1 20.355 1 41.8333C1 48.6933 3.00083 55.7575 6.5125 62.2092C7.16583 63.2708 7.2475 64.6183 6.79833 65.8842L4.0625 75.0308C3.45 77.2358 5.32833 78.8692 7.41083 78.2158L15.6592 75.7658C17.905 75.0308 19.6608 75.97 21.7474 77.2358C27.7091 80.7475 35.1367 82.5442 41.8333 82.5442C62.0867 82.5442 82.6667 66.905 82.6667 41.7108C82.6667 19.9875 65.1083 1 41.915 1Z"/>
</clipPath><filter id="filter2_d_1_106" x="2.70117" y="21.6465" width="78.1025" height="40.4539" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
<feFlood flood-opacity="0" result="BackgroundImageFix"/>
<feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>
<feOffset dx="5" dy="5"/>
<feGaussianBlur stdDeviation="5"/>
<feColorMatrix type="matrix" values="0 0 0 0 0.577356 0 0 0 0 0.359375 0 0 0 0 0.9375 0 0 0 0.5 0"/>
<feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_1_106"/>
<feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_1_106" result="shape"/>
</filter>
<clipPath id="bgblur_1_1_106_clip_path" transform="translate(-2.70117 -21.6465)"><path fill-rule="evenodd" clip-rule="evenodd" d="M41.7535 47.1003C38.8543 47.0595 36.5268 44.732 36.5268 41.8328C36.5268 38.9745 38.8951 36.6062 41.7535 36.647C44.6526 36.647 46.9801 38.9745 46.9801 41.8737C46.9801 44.732 44.6526 47.1003 41.7535 47.1003ZM22.9278 47.1004C20.0695 47.1004 17.7012 44.7321 17.7012 41.8738C17.7012 38.9746 20.0287 36.6471 22.9278 36.6471C25.827 36.6471 28.1545 38.9746 28.1545 41.8738C28.1545 44.7321 25.827 47.0596 22.9278 47.1004ZM55.3504 41.8737C55.3504 44.732 57.6779 47.1003 60.577 47.1003C63.4762 47.1003 65.8037 44.732 65.8037 41.8737C65.8037 38.9745 63.4762 36.647 60.577 36.647C57.6779 36.647 55.3504 38.9745 55.3504 41.8737Z"/>
</clipPath><linearGradient id="paint0_linear_1_106" x1="66" y1="26" x2="66" y2="89.9041" gradientUnits="userSpaceOnUse">
<stop stop-color="#BC94FF"/>
<stop offset="1" stop-color="#9F66FF"/>
</linearGradient>
<linearGradient id="paint1_linear_1_106" x1="14" y1="10.5" x2="66" y2="75" gradientUnits="userSpaceOnUse">
<stop stop-color="white" stop-opacity="0.25"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
<linearGradient id="paint2_linear_1_106" x1="62.3932" y1="38.5342" x2="9.93538" y2="46.4043" gradientUnits="userSpaceOnUse">
<stop stop-color="white"/>
<stop offset="1" stop-color="white" stop-opacity="0.2"/>
</linearGradient>
<linearGradient id="paint3_linear_1_106" x1="25.3583" y1="37.8644" x2="27.6808" y2="51.1001" gradientUnits="userSpaceOnUse">
<stop stop-color="white" stop-opacity="0.25"/>
<stop offset="1" stop-color="white" stop-opacity="0"/>
</linearGradient>
</defs>
</svg>
            <span style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 24px; letter-spacing: 1px; color: #8237FF;">Result</span>
        </div>
    ''', unsafe_allow_html=True)
    
    if btn and temat:
        lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
        
        for index, pojedynczy_temat in enumerate(lista_tematow):
            with st.spinner(f'Processing Batch {index + 1}...'):
                rok = datetime.now().year
                t0 = Task(description=f"Find {rok} news on: '{pojedynczy_temat}'.", expected_output="Facts/URLs.", agent=researcher)
                t1 = Task(description="Write LinkedIn post. Brand voice.", expected_output="Post text.", agent=copywriter)
                t2 = Task(description="Midjourney prompt for this post.", expected_output="Prompt string.", agent=art_director)
                
                crew = Crew(agents=[researcher, copywriter, art_director], tasks=[t0, t1, t2])
                crew.kickoff()
                
                post_text = getattr(t1.output, 'raw_output', str(t1.output))
                visual_prompt = getattr(t2.output, 'raw_output', str(t2.output))
                
                save_to_history(pojedynczy_temat, f"{post_text}\n\nPrompt: {visual_prompt}")
                
                clean_post = post_text.replace('\n', '<br>')
                
                st.markdown(f'''
                    <div class="result-card">
                        <div style="font-weight: 800; color: #8237FF; font-size: 14px; letter-spacing: 1px; margin-bottom: 15px;">BATCH {index + 1} READY</div>
                        <div style="color: #1A1A1A; font-size: 16px; margin-bottom: 25px; font-weight: 400;">{clean_post}</div>
                        <div style="background: #F4F4F9; padding: 20px; border-radius: 12px; border-left: 4px solid #FF749F;">
                            <strong style="color: #000; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">📸 Visual Prompt</strong><br>
                            <span style="color: #444; font-size: 14px; font-style: italic;">{visual_prompt}</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                with st.expander("🔍 Sources, please!"):
                    st.write(getattr(t0.output, 'raw_output', str(t0.output)))
