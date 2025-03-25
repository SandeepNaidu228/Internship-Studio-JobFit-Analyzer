# Internship Studio JobFit Analyzer

An AI-powered resume analysis tool that helps job seekers evaluate their resumes against job descriptions using Google's Gemini AI.

## Author
- **M V N Sandeep Naidu**
- Email: mvnsandeepsandeep@gmail.com

## Features

- **Single Resume Analysis**
  - Comprehensive review with match percentage
  - Skill gap analysis with visualizations
  - Keyword analysis
  - Match percentage calculation
  - Exportable analysis reports

- **Bulk Resume Ranking**
  - Upload multiple resumes
  - Get ranked list based on job fit
  - Visual comparison of match percentages
  - Detailed strengths and gaps analysis
  - Export rankings as CSV

## Prerequisites

- Python 3.7+
- Google API Key for Gemini AI
- Required Python packages:
  - streamlit
  - python-dotenv
  - PyMuPDF (fitz)
  - google-generativeai
  - pandas
  - plotly

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd GeminiCode
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Choose between Single Resume Analysis or Bulk Resume Ranking

4. For Single Resume Analysis:
   - Paste the job description
   - Upload your resume (PDF)
   - Select the type of analysis
   - View results and download reports

5. For Bulk Resume Ranking:
   - Paste the job description
   - Upload multiple resumes
   - Get ranked results with detailed analysis
   - Export rankings as CSV

## Features in Detail

### Single Resume Analysis
- **Comprehensive Review**: Get detailed feedback on your resume's match with the job description
- **Skill Gap Analysis**: Visual representation of required vs. present skills
- **Keyword Analysis**: Identify missing keywords from the job description
- **Match Percentage**: Calculate overall match score
- **Export Reports**: Download detailed analysis reports in Markdown format

### Bulk Resume Ranking
- **Multiple Resume Upload**: Compare multiple resumes against the same job description
- **Ranked Results**: Get a sorted list of resumes based on match percentage
- **Visual Comparison**: Bar chart showing match percentages
- **Detailed Analysis**: Expandable sections for each resume showing strengths and gaps
- **CSV Export**: Download rankings in CSV format for further analysis

