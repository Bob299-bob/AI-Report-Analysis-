import streamlit as st
from research import extract_pdf,extract_img
import requests

st.set_page_config(
    page_title="AI Medical Report Analysis",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>

.stApp{
    background: linear-gradient(135deg,#0f172a,#1e293b);
}

h1,h2,h3,p,label{
    color:white !important;
}

[data-testid="stFileUploader"]{
    background:#1e293b;
    padding:20px;
    border-radius:15px;
    border:1px solid #334155;
}

[data-testid="stTextInputRootElement"]{
    background:white;
    border-radius:10px;
}

.stButton button{
    width:100%;
    background:#2563eb;
    color:white;
    border:none;
    border-radius:10px;
    height:50px;
    font-size:18px;
}

.stButton button:hover{
    background:#1d4ed8;
}

.report-box{
    background:white;
    padding:25px;
    border-radius:15px;
    color:black;
    box-shadow:0px 4px 15px rgba(0,0,0,0.2);
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)


st.title('AI Medical Report Analysis')

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

def create_beautiful_pdf(report_text, query):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.darkblue,
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16
    )

    elements = []

    # Title
    elements.append(Paragraph("🏥 Medical Report Analysis", title_style))
    elements.append(Spacer(1, 12))

    # Query section
    elements.append(Paragraph("Patient Query:", heading_style))
    elements.append(Paragraph(query, body_style))
    elements.append(Spacer(1, 12))

    # Report section
    elements.append(Paragraph("AI Generated Report:", heading_style))
    elements.append(Paragraph(report_text.replace("\n", "<br/>"), body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
#file uploader
file_upload=st.file_uploader('upload your report',
                            type=['pdf','png','jpg','jpeg'])
if file_upload is not None:
    extention=file_upload.name.split('.')[-1].lower()
    #funtion to decide which file is uploaded
    def extention_data(extention):
        if extention=='pdf':
            input_data=extract_pdf(file_upload)
        elif extention in ['jpg','jpeg','png']:
            input_data=extract_img(file_upload)
        else:
            st.error('Please Provide pdf/img file')
            st.stop()
        return input_data
    input_data=extention_data(extention)
    st.success('File uploaded Successfully')
    #query
    query=st.text_input('Enter Your Query')
    if query:
        if st.button('Press'):
            url='http://127.0.0.1:8000/report'
            data={
                'input_data':input_data,
                'query':query
            }
            response=requests.post(url,json=data)
            if response.status_code != 200:
                st.error(response.text)
                st.stop()
            try:
                result = response.json()
                pdf_file = create_beautiful_pdf(result, query)
                st.download_button(
                label="📥 Download Professional PDF Report",
                data=pdf_file,
                file_name="Medical_Report_Analysis.pdf",
                mime="application/pdf"
                )
                st.write(result)
            except:
                st.error("Invalid response")
                st.write(response.text)