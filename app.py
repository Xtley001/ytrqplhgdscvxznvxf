import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import base64
import pdf2image
import io
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get response from Gemini API
def get_gemini_response(input_text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_text)
    return response.text

# Function to extract text from uploaded PDF file
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    return text

# Prompt Template for evaluating resumes for various job roles
input_prompt = """
You are an experienced Application Tracking System (ATS) with expertise in evaluating resumes
for a wide range of job roles across different industries. Your task is to assess the candidate's
suitability for the role based on the provided job description.

Please assign a percentage match based on how well the resume aligns with the job description
and highlight any missing keywords with high accuracy.

Key areas to evaluate:
- Relevant skills and competencies
- Professional experience and achievements
- Educational background and qualifications
- Certifications and training
- Knowledge of industry-specific tools and technologies
- Soft skills and personal attributes
- Alignment with the job responsibilities and requirements

resume: {text}
job_description: {job_description}

I want the response in a structured format:
{{"JD Match": "%", "MissingKeywords": [], "Profile Summary": ""}}
"""

# Streamlit App
st.set_page_config(page_title="SkillSync")
st.title("SkillSync")

# Text area for job description input
job_description = st.text_area("Paste the Job Description:")

# File uploader for resume (PDF) input
uploaded_file = st.file_uploader("Upload Your Resume (PDF)...", type=["pdf"])

# Adding widgets
st.sidebar.header("Customize Your Experience")
show_summary = st.sidebar.checkbox("Show Profile Summary")
match_threshold = st.sidebar.slider("Set Match Threshold", 0, 100, 85)

# Submit button for processing the resume and job description
submit = st.button("Submit")

if submit:
    if job_description and uploaded_file:
        try:
            # Extract text from PDF
            resume_text = input_pdf_text(uploaded_file)
            
            # Prepare prompt with extracted resume text and job description
            input_prompt_filled = input_prompt.format(text=resume_text, job_description=job_description)
            
            # Get response from Gemini API
            response = get_gemini_response(input_prompt_filled)
            
            # Parse response
            response_json = json.loads(response)
            
            # Display the Gemini Response in a block format
            st.markdown("### Response:")
            st.json(response_json)
            
            # Extract percentage match and missing keywords
            percentage_match = int(response_json.get("JD Match", "0").strip('%'))
            missing_keywords = response_json.get("MissingKeywords", [])
            
            # Display percentage match
            st.markdown("### Percentage Match:")
            st.write(f"{percentage_match}%")
            
            # Display pie chart for percentage match
            fig = go.Figure(data=[go.Pie(labels=['Match', 'Gap'], values=[percentage_match, 100 - percentage_match])])
            st.plotly_chart(fig)
            
            # Display bar chart for missing keywords
            if missing_keywords:
                keyword_counts = {keyword: 1 for keyword in missing_keywords}
                keywords_df = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count'])
                bar_fig = px.bar(keywords_df, x='Keyword', y='Count', title='Missing Keywords')
                st.plotly_chart(bar_fig)
            
            # Optionally show profile summary
            if show_summary:
                st.markdown("### Profile Summary:")
                st.write(response_json.get("Profile Summary", "No profile summary available."))
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    elif not job_description:
        st.warning("Please paste the job description.")
    elif not uploaded_file:
        st.warning("Please upload a resume.")
