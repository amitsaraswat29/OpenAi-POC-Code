import streamlit as st
from openai import OpenAI
import base64
import json

# --- Helper Function ---
# OpenAI requires images to be sent in base64 format when using the API directly
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Snap & Sync SFS", page_icon="📸", layout="centered")

st.title("📸 Snap & Sync: Field Notes Digitizer")
st.markdown("""
**Agentforce / AI Proof of Concept** Upload a photo of handwritten field notes. The AI will read the handwriting, extract the context, and format it into a structured JSON payload ready for the Salesforce REST API.
""")

st.divider()

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Enter your personal OpenAI API Key to run this demo.")
    st.markdown("[Get an OpenAI API key here](https://platform.openai.com/account/api-keys)")
    st.caption("Note: Your key is not saved anywhere. It only lives in memory during this session.")

# --- Main App Logic ---
uploaded_file = st.file_uploader("Upload Handwritten Notes (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the uploaded image
    st.image(uploaded_file, caption="Preview of Uploaded Notes", use_container_width=True)

    # Process Button
    if st.button("Process Image & Extract Data", type="primary"):
        if not api_key:
            st.warning("⚠️ Please enter your OpenAI API key in the sidebar first.")
        else:
            with st.spinner("🤖 AI is reading the handwriting and structuring the data..."):
                try:
                    # Initialize OpenAI Client
                    client = OpenAI(api_key=api_key)
                    base64_image = encode_image(uploaded_file)

                    # --- THE SYSTEM PROMPT ---
                    # This is where the magic happens. We instruct the AI exactly how to behave
                    # and define the strict JSON structure we need for Salesforce.
                    system_prompt = """
                    You are an expert AI assistant for Salesforce Field Service. 
                    Your task is to carefully read handwritten field notes from a technician and extract the information into a strict JSON object.
                    
                    The JSON must contain EXACTLY these keys:
                    - "WorkOrderNumber" (string, or null if not found)
                    - "IssueFound" (string, a clear summary of the problem)
                    - "Resolution" (string, what the technician did to fix it)
                    - "PartsUsed" (list of strings, or an empty list [] if none)
                    - "Status" (string, choose from: "Completed", "In Progress", "Cannot Complete")

                    If you cannot read a specific detail, use null. You must output ONLY valid JSON.
                    """

                    # Call the OpenAI API
                    response = client.chat.completions.create(
                        model="gpt-4o", # gpt-4o is the standard for multimodal text/image tasks
                        response_format={ "type": "json_object" }, # Forces the output to be JSON
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extract the field service data from this image of handwritten notes."},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ]
                    )

                    # Parse the string response into a Python dictionary
                    raw_json_string = response.choices[0].message.content
                    result_json = json.loads(raw_json_string)

                    st.success("✅ Extraction Complete!")
                    
                    # --- Display the Results ---
                    st.subheader("Salesforce SFS Payload")
                    st.caption("This JSON is what would be sent to Salesforce to update the Work Order automatically.")
                    st.json(result_json)

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")