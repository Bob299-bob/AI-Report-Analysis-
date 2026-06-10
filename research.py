from groq import Groq
from dotenv import load_dotenv
import os
import numpy as np
import faiss
import streamlit as st
import pdfplumber
import cv2
import pytesseract
#fetch api
load_dotenv()
client=Groq(api_key=os.getenv('GROQ_API_KEY'))

#vector Embedding model useing as Summerizer
from sentence_transformers import SentenceTransformer
@st.cache_resource
def load_model():
    model=SentenceTransformer(
        "all-MiniLM-L6-v2"
    )
    return model
model=load_model()
#Extract data

def extract_pdf(data_path):
    pdf_text=""
    with pdfplumber.open(data_path) as file:
        for page in file.pages:
            page_text=page.extract_text()
            if page_text:
                pdf_text+=page_text+" "
    return pdf_text           

def extract_img(img_path):
    file_bytes = np.asarray(
        bytearray(img_path.read()),
        dtype=np.uint8
    )
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(gray,config="--psm 6")
    return text


#Rag system
@st.cache_data(show_spinner=False)
def rag_system(data):
    chunks = [c.strip() for c in data.split("\n\n") if len(c.strip()) > 20]
    embed_data=model.encode(chunks)
    embed_data=np.array(embed_data).astype('float32')
    faiss.normalize_L2(embed_data)
    index=faiss.IndexFlatL2(embed_data.shape[1])
    index.add(embed_data)
    return index,chunks
    
    

#Retrieval system
def retrieve(index,chunks,query):
    embed_query=model.encode([query]).astype('float32')
    faiss.normalize_L2(embed_query)
    distance,indices=index.search(embed_query,k=3)
    context=[]
    for idx in indices[0]:
        context.append(chunks[idx])
    return context

#Function to collect data from internet
from ddgs import DDGS
@st.cache_data(show_spinner=False)
def search_net(query):
    results=[]
    try:
        with DDGS() as ddgs:
            search_results=list(ddgs.text(query,max_results=5))
            for result in search_results:
                results.append(f"""
                Content:{result.get('body','')}
                """)
    except Exception as e:
        print('search_error',e)
    return "\n\n".join(results)
@st.cache_data(show_spinner=True)
def generate_report(answer,result,query):
    context="\n\n".join(answer)
    context=context[:6000]
    prompt = f"""
You are an experienced Medical Report Analysis Assistant.

Patient Medical Report:
{context}

Additional Information from Web Search:
{result}

Task:
Analyze the medical report and generate a detailed patient-friendly report.

Rules:
- Use ONLY the information provided in the medical report.
- Do NOT make up diagnoses.
- Clearly mention if any values are outside normal ranges.
- Explain medical terms in simple language.
- Mention possible health concerns only if supported by the report.
- If information is insufficient, explicitly state that.
- Avoid giving definitive medical diagnoses.
- Suggest consulting a qualified doctor when appropriate.

Generate the report in the following format:

# Medical Report Summary

## Patient Overview
- Brief summary of the report

## Key Test Results
- List important findings
- Mention normal and abnormal values

## Abnormal Findings
- Highlight any concerning results
- Explain what they may indicate

## Health Interpretation
- Simple explanation of what the report suggests

## Risk Indicators
- Any potential risks visible in the report

## Recommended Follow-Up
- Suggested medical consultations
- Additional tests if necessary

## Conclusion
- Overall assessment in simple language

User Question:
{query}
"""
    response=client.chat.completions.create(
         model='llama-3.1-8b-instant',
        messages=[{'role':'user','content':prompt}]
    )
    return response.choices[0].message.content