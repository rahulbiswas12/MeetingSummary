import streamlit as st
import google.generativeai as genai
import docx
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API using environment variable
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    st.error("Please set GEMINI_API_KEY in your .env file")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def read_docx(file):
    """Read content from a .docx file"""
    doc = docx.Document(file)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)

def read_file_content(uploaded_file):
    """Read content from uploaded file based on file type"""
    content = ""
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_type == 'txt':
            content = uploaded_file.getvalue().decode('utf-8')
        elif file_type in ['docx', 'doc']:
            bytes_data = io.BytesIO(uploaded_file.getvalue())
            content = read_docx(bytes_data)
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None
        
    return content

def generate_summary(text, custom_prompt=""):
    """Generate meeting summary using Gemini API"""
    try:
        # Use custom prompt if provided, otherwise use default
        if custom_prompt.strip():
            prompt = f"{custom_prompt}\n\nHere's the transcript:\n{text}"
        else:
            prompt = f"""
            Please analyze this meeting transcript and provide a comprehensive summary with the following structure:
            1. Key Discussion Points
            2. Action Items
            3. Decisions Made
            4. Next Steps
            
            Here's the transcript:
            {text}
            """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def main():
    st.set_page_config(page_title="Meeting Summary Generator", layout="centered")
    
    # Initialize session state for storing summary
    if 'current_summary' not in st.session_state:
        st.session_state.current_summary = None
    if 'original_text' not in st.session_state:
        st.session_state.original_text = None
    
    # Add custom CSS for styling
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
        }
        .prompt-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("📝 Meeting Summary Generator")
    st.markdown("Upload your meeting transcript and get an AI-generated summary!")
    
    # Custom Prompt Input
    with st.expander("Customize Summary Requirements", expanded=False):
        custom_prompt = st.text_area(
            "Custom Prompt (Leave empty for default format)",
            placeholder="Example: Please summarize this meeting focusing on technical decisions and action items.",
            help="Customize how you want the summary to be generated. Leave empty to use the default format."
        )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['txt', 'docx', 'doc'],
        help="Upload your meeting transcript in TXT or DOCX format"
    )
    
    if uploaded_file:
        # Display file details
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB",
            "File type": uploaded_file.type
        }
        st.write("**File Details:**")
        for key, value in file_details.items():
            st.write(f"- {key}: {value}")
        
        # Read file content
        text_content = read_file_content(uploaded_file)
        if text_content:
            st.session_state.original_text = text_content
            
            # Add a collapsible section to show raw transcript
            with st.expander("View Original Transcript"):
                st.text_area("Transcript", text_content, height=200)
            
            # Generate Summary button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Generate Summary"):
                    with st.spinner("Generating summary... Please wait."):
                        summary = generate_summary(text_content, custom_prompt)
                        st.session_state.current_summary = summary
            
            with col2:
                if st.session_state.current_summary and st.button("Regenerate Summary"):
                    with st.spinner("Regenerating summary... Please wait."):
                        summary = generate_summary(text_content, custom_prompt)
                        st.session_state.current_summary = summary
            
            # Display summary if available
            if st.session_state.current_summary:
                st.markdown("### 📋 Meeting Summary")
                st.markdown(st.session_state.current_summary)
                
                # Add download button for summary
                st.download_button(
                    label="Download Summary",
                    data=st.session_state.current_summary,
                    file_name="meeting_summary.txt",
                    mime="text/plain"
                )
        else:
            st.error("Failed to read the file. Please make sure it's a valid document.")
    
    # Add footer with instructions
    st.markdown("---")
    st.markdown("""
    ### How to use:
    1. (Optional) Customize the summary requirements
    2. Upload a transcript file (supported formats: .txt, .doc, .docx)
    3. Click "Generate Summary" to process the transcript
    4. Use "Regenerate Summary" if you want a different version
    5. Download the summary if needed
    
    ### Note:
    - Supports text files and Word documents
    - Custom prompts can help focus the summary on specific aspects
    - Use the regenerate option to get different perspectives
    - For best results, ensure the transcript is clear and well-formatted
    """)

if __name__ == "__main__":
    main()