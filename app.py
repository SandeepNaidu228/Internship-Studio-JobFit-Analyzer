import os
import streamlit as st
from dotenv import load_dotenv
import fitz  # PyMuPDF for PDF text extraction
import google.generativeai as genai
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import tempfile

# Prompt Templates
prompts = {
    "review": """You are an experienced Technical Human Resource Manager. Review the resume against the job description and provide:
    1. Overall match percentage
    2. Key strengths
    3. Areas for improvement
    4. Specific recommendations
    Format your response in clear sections with bullet points.""",
    
    "improve": """You are a skilled ATS scanner. Analyze the resume and provide:
    1. Missing technical skills
    2. Required certifications
    3. Experience gaps
    4. Actionable improvement steps
    Format your response in clear sections.""",
    
    "keywords": """Identify and categorize missing keywords from the resume based on the job description:
    1. Technical skills
    2. Soft skills
    3. Tools and technologies
    4. Industry-specific terms
    Format as a bulleted list.""",
    
    "match": """Provide a detailed match analysis:
    1. Overall match percentage
    2. Missing keywords
    3. Strengths
    4. Areas for improvement
    5. Final recommendations
    Format with clear sections and bullet points.""",
    
    "rank": """You are an expert HR manager. Analyze the following resumes and rank them from best to worst match for the job description.
    For each resume, provide:
    1. Match percentage (0-100)
    2. Key strengths
    3. Major gaps
    4. Overall ranking (1 being best)
    
    Format your response as a JSON with the following structure:
    {
        "rankings": [
            {
                "resume_name": "filename.pdf",
                "match_percentage": 85,
                "rank": 1,
                "strengths": ["skill1", "skill2"],
                "gaps": ["gap1", "gap2"]
            }
        ]
    }"""
}

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Check API Key
if not GOOGLE_API_KEY:
    st.error("❌ Missing Google API Key. Please set the GOOGLE_API_KEY in your environment variables.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Function to List Available Models (for debugging)
def list_available_models():
    try:
        models = genai.list_models()
        return [model.name for model in models]  # Extract model names
    except Exception as e:
        return [f"Error fetching models: {str(e)}"]

# Ensure Correct Model Name
AVAILABLE_MODELS = list_available_models()
DEFAULT_MODEL = "models/gemini-1.5-pro-latest"

def get_gemini_response(input_text, pdf_content, prompt):
    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)  # ✅ Use Correct Model Name
        response = model.generate_content([input_text, pdf_content, prompt])

        if hasattr(response, "text"):
            return response.text
        else:
            return "❌ Error: Unexpected response format from Gemini API."
    except Exception as e:
        return f"❌ API Error: {str(e)}"

# Function to Extract Text from PDF
def extract_text_from_pdf(uploaded_file):
    try:
        document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in document])
        return text.strip()
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return ""

def generate_analysis_report(response, job_description, resume_content):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = f"""
# Resume Analysis Report
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Job Description
{job_description}

## Resume Content
{resume_content}

## Analysis Results
{response}
    """
    return report

def process_bulk_resumes(job_description, uploaded_files):
    all_resumes = []
    for file in uploaded_files:
        try:
            content = extract_text_from_pdf(file)
            all_resumes.append({
                "name": file.name,
                "content": content
            })
        except Exception as e:
            st.error(f"Error processing {file.name}: {str(e)}")
    
    if not all_resumes:
        return None
    
    # Combine all resume contents for analysis
    combined_prompt = f"Job Description:\n{job_description}\n\nResumes to analyze:\n"
    for resume in all_resumes:
        combined_prompt += f"\nResume: {resume['name']}\n{resume['content']}\n---\n"
    
    try:
        response = get_gemini_response(combined_prompt, "", prompts["rank"])
        
        # Try to extract JSON from the response
        try:
            # First try direct JSON parsing
            rankings = json.loads(response)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON-like structure
            try:
                # Look for JSON-like structure in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    rankings = json.loads(json_str)
                else:
                    # If no JSON structure found, create a structured response
                    rankings = {
                        "rankings": [
                            {
                                "resume_name": resume["name"],
                                "match_percentage": 0,
                                "rank": idx + 1,
                                "strengths": ["Unable to analyze strengths"],
                                "gaps": ["Unable to analyze gaps"]
                            }
                            for idx, resume in enumerate(all_resumes)
                        ]
                    }
            except Exception as e:
                st.warning(f"Could not parse JSON response: {str(e)}")
                # Create a fallback structured response
                rankings = {
                    "rankings": [
                        {
                            "resume_name": resume["name"],
                            "match_percentage": 0,
                            "rank": idx + 1,
                            "strengths": ["Unable to analyze strengths"],
                            "gaps": ["Unable to analyze gaps"]
                        }
                        for idx, resume in enumerate(all_resumes)
                    ]
                }
        
        # Validate the rankings structure
        if not isinstance(rankings, dict) or "rankings" not in rankings:
            rankings = {
                "rankings": [
                    {
                        "resume_name": resume["name"],
                        "match_percentage": 0,
                        "rank": idx + 1,
                        "strengths": ["Unable to analyze strengths"],
                        "gaps": ["Unable to analyze gaps"]
                    }
                    for idx, resume in enumerate(all_resumes)
                ]
            }
        
        return rankings
    except Exception as e:
        st.error(f"Error analyzing resumes: {str(e)}")
        # Return a fallback response
        return {
            "rankings": [
                {
                    "resume_name": resume["name"],
                    "match_percentage": 0,
                    "rank": idx + 1,
                    "strengths": ["Unable to analyze strengths"],
                    "gaps": ["Unable to analyze gaps"]
                }
                for idx, resume in enumerate(all_resumes)
            ]
        }

# Streamlit UI
st.set_page_config(page_title="Internship Studio JobFit Analyzer", layout="wide")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Comprehensive", "Quick Scan", "Detailed Technical"]
    )
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    Internship Studio JobFit Analyzer uses advanced AI to evaluate your resume against job descriptions.
    Get instant feedback and suggestions to improve your application.
    """)

# Main content
st.header("Internship Studio JobFit Analyzer - AI-Powered Resume Review")

# Create tabs for different modes
tab1, tab2 = st.tabs(["📄 Single Resume Analysis", "📑 Bulk Resume Ranking"])

with tab1:
    # File upload section
    col1, col2 = st.columns([2, 1])
    with col1:
        input_text = st.text_area("📌 Paste the Job Description:", placeholder="Enter job description here...", height=150)
    with col2:
        uploaded_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])
        if uploaded_file:
            st.success("✅ PDF Uploaded Successfully!")

    # Analysis buttons
    st.markdown("### 🔍 Analysis Options")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Comprehensive Review", use_container_width=True):
            if uploaded_file and input_text.strip():
                with st.spinner("🔍 Analyzing your resume..."):
                    pdf_content = extract_text_from_pdf(uploaded_file)
                    response = get_gemini_response(input_text, pdf_content, prompts["review"])
                    
                    # Display results in tabs
                    tab1, tab2, tab3 = st.tabs(["📊 Overall Score", "📝 Detailed Analysis", "📥 Export"])
                    
                    with tab1:
                        # Simulate score (you can modify this based on actual analysis)
                        score = 75
                        st.metric("Overall Match Score", f"{score}%")
                        st.progress(score/100)
                    
                    with tab2:
                        st.markdown(response)
                    
                    with tab3:
                        report = generate_analysis_report(response, input_text, pdf_content)
                        st.download_button(
                            "📥 Download Analysis Report",
                            report,
                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )

    with col2:
        if st.button("🔧 Skill Gap Analysis", use_container_width=True):
            if uploaded_file and input_text.strip():
                with st.spinner("🔍 Analyzing skill gaps..."):
                    pdf_content = extract_text_from_pdf(uploaded_file)
                    response = get_gemini_response(input_text, pdf_content, prompts["improve"])
                    
                    # Create a more comprehensive skill gap visualization
                    # Using a fixed set of skills for demonstration
                    skills_data = {
                        'Category': ['Technical Skills', 'Technical Skills', 'Technical Skills', 'Technical Skills',
                                   'Soft Skills', 'Soft Skills', 'Soft Skills', 'Soft Skills'],
                        'Type': ['Required', 'Required', 'Required', 'Required',
                                'Required', 'Required', 'Required', 'Required'],
                        'Skills': ['Python', 'SQL', 'Machine Learning', 'Data Analysis',
                                 'Communication', 'Leadership', 'Problem Solving', 'Team Work']
                    }
                    
                    # Create DataFrame for visualization
                    df = pd.DataFrame(skills_data)
                    
                    st.subheader("📊 Skill Gap Analysis")
                    
                    # Create a grouped bar chart
                    fig = px.bar(df, 
                               x='Category', 
                               y='Skills',
                               color='Type',
                               title='Required Skills Analysis',
                               barmode='group',
                               labels={'Category': 'Skill Category', 'Skills': 'Skill Name', 'Type': 'Skill Type'})
                    
                    # Update layout for better visualization
                    fig.update_layout(
                        showlegend=True,
                        legend_title_text='Skill Type',
                        xaxis_title='Skill Category',
                        yaxis_title='Skills',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display the analysis response
                    st.markdown("### 🔍 Detailed Analysis")
                    st.markdown(response)

    with col3:
        if st.button("🔍 Keyword Analysis", use_container_width=True):
            if uploaded_file and input_text.strip():
                with st.spinner("🔍 Analyzing keywords..."):
                    pdf_content = extract_text_from_pdf(uploaded_file)
                    response = get_gemini_response(input_text, pdf_content, prompts["keywords"])
                    st.markdown(response)

    with col4:
        if st.button("📈 Match Percentage", use_container_width=True):
            if uploaded_file and input_text.strip():
                with st.spinner("🔍 Calculating match..."):
                    pdf_content = extract_text_from_pdf(uploaded_file)
                    response = get_gemini_response(input_text, pdf_content, prompts["match"])
                    st.markdown(response)

with tab2:
    st.header("📑 Bulk Resume Ranking")
    st.markdown("Upload multiple resumes to get a ranked list based on job fit.")
    
    bulk_job_description = st.text_area("📌 Job Description for Ranking:", 
                                      placeholder="Enter job description here...", 
                                      height=150)
    
    uploaded_files = st.file_uploader("📄 Upload Multiple Resumes (PDF)", 
                                    type=["pdf"], 
                                    accept_multiple_files=True)
    
    if uploaded_files and bulk_job_description.strip():
        if st.button("🔍 Rank Resumes", use_container_width=True):
            with st.spinner("🔍 Analyzing and ranking resumes..."):
                rankings = process_bulk_resumes(bulk_job_description, uploaded_files)
                
                if rankings and "rankings" in rankings:
                    # Create DataFrame for visualization
                    df = pd.DataFrame(rankings["rankings"])
                    
                    # Display rankings
                    st.subheader("📊 Resume Rankings")
                    
                    # Create a bar chart for match percentages
                    fig = px.bar(df, 
                               x='resume_name', 
                               y='match_percentage',
                               title='Resume Match Percentages',
                               labels={'match_percentage': 'Match Percentage (%)', 'resume_name': 'Resume Name'})
                    st.plotly_chart(fig)
                    
                    # Display detailed rankings
                    st.subheader("📝 Detailed Rankings")
                    for idx, row in df.iterrows():
                        with st.expander(f"Rank {row['rank']}: {row['resume_name']} ({row['match_percentage']}% match)"):
                            st.markdown("**Strengths:**")
                            for strength in row['strengths']:
                                st.markdown(f"- {strength}")
                            
                            st.markdown("**Gaps:**")
                            for gap in row['gaps']:
                                st.markdown(f"- {gap}")
                    
                    # Download rankings as CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Rankings as CSV",
                        csv,
                        file_name=f"resume_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Failed to generate rankings. Please try again.")
    else:
        st.info("👆 Upload multiple resumes and enter a job description to get started with ranking.")
