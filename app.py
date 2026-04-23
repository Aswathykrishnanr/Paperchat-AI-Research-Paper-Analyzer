import streamlit as st
import os
import tempfile
from pdf_processor import extract_text_from_pdf, split_text_into_chunks
from retriever import create_collection, store_chunks, search_chunks
from llm import get_answer

# Page settings
st.set_page_config(
    page_title="PaperChat",
    
    layout="centered"
)

# Clean modern styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main background */
    .stApp {
        background-color: #0f1117;
    }

    /* Header */
    .header-container {
        text-align: center;
        padding: 2.5rem 0 1.5rem 0;
    }
    .header-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.8rem;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin-top: 0.4rem;
        font-weight: 300;
    }
    .header-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    /* Section titles */
    .section-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.8rem;
    }

    /* Upload area */
    .upload-container {
        background: #1a1d27;
        border: 1px solid #2d3148;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* Process button */
    .stButton > button {
        background: #4f6ef7;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.8rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
        width: auto;
    }
    .stButton > button:hover {
        background: #3d5ce0;
        transform: translateY(-1px);
    }

    /* Success message */
    .success-box {
        background: #0d2818;
        border: 1px solid #1a4d30;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        color: #4ade80;
        font-size: 0.9rem;
        margin: 0.8rem 0;
    }

    /* Question input */
    .stTextInput > div > div > input {
        background: #1a1d27 !important;
        border: 1px solid #2d3148 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 0.8rem 1rem !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4f6ef7 !important;
        box-shadow: 0 0 0 2px rgba(79,110,247,0.15) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #4b5563 !important;
    }

    /* Chat message - You */
    .chat-you {
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0 0.4rem 0;
    }
    .chat-you-bubble {
        background: #4f6ef7;
        color: white;
        padding: 0.7rem 1.1rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    /* Chat message - PaperChat */
    .chat-bot {
        display: flex;
        justify-content: flex-start;
        margin: 0.4rem 0 0.4rem 0;
        gap: 0.6rem;
        align-items: flex-start;
    }
    .chat-bot-icon {
        font-size: 1.3rem;
        margin-top: 0.2rem;
        flex-shrink: 0;
    }
    .chat-bot-bubble {
        background: #1a1d27;
        border: 1px solid #2d3148;
        color: #e5e7eb;
        padding: 0.8rem 1.1rem;
        border-radius: 4px 18px 18px 18px;
        max-width: 80%;
        font-size: 0.92rem;
        line-height: 1.6;
    }

    /* Sources */
    .sources-container {
        margin: 0.3rem 0 1rem 2.5rem;
    }
    .source-tag {
        display: inline-block;
        background: #1a1d27;
        border: 1px solid #2d3148;
        color: #9ca3af;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        margin: 0.2rem 0.2rem 0 0;
    }

    /* Info box */
    .info-box {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1.2rem;
        color: #6b7280;
        text-align: center;
        font-size: 0.9rem;
    }

    /* Divider */
    .custom-divider {
        border: none;
        border-top: 1px solid #1f2937;
        margin: 1.5rem 0;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #374151;
        font-size: 0.78rem;
        padding: 2rem 0 1rem 0;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: transparent;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #12141e !important;
        border: 1.5px dashed #2d3148 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────
st.markdown("""
<div class="header-container">
    <h1 class="header-title">PaperChat</h1>
    <p class="header-subtitle">AI research assistant — 
    chat with any PDF instantly</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ── Session State ────────────────────────────────
if "collection" not in st.session_state:
    st.session_state.collection = None
if "papers_processed" not in st.session_state:
    st.session_state.papers_processed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Upload Section ───────────────────────────────
st.markdown('<p class="section-title">📁 Upload Papers</p>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Drop your PDF files here",
    type="pdf",
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files and not st.session_state.papers_processed:
    st.markdown(
        f'<div class="success-box">{len(uploaded_files)} file(s) uploaded</div>',
        unsafe_allow_html=True)

    if st.button("Analyse Papers →"):
        with st.spinner("Reading your files..."):
            collection = create_collection("paperchat")
            all_chunks = []

            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name

                text = extract_text_from_pdf(tmp_path)
                chunks = split_text_into_chunks(text, uploaded_file.name)
                all_chunks.extend(chunks)
                os.unlink(tmp_path)

            store_chunks(collection, all_chunks)
            st.session_state.collection = collection
            st.session_state.papers_processed = True
            st.session_state.num_papers = len(uploaded_files)
            st.rerun()

# ── Question Section ─────────────────────────────
if st.session_state.papers_processed:

    st.markdown('<p class="section-title">💬Ask a Question</p>', unsafe_allow_html=True)

    question = st.text_input(
        "question",
        placeholder="What methods were used in these papers?",
        label_visibility="collapsed"
    )

    if st.button("Get Answer →"):
        if question:
            with st.spinner("Searching through your papers..."):
                relevant_chunks, sources = search_chunks(
                    st.session_state.collection, question
                )
                answer = get_answer(question, relevant_chunks)
                unique_sources = list(set(sources))

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer,
                    "sources": unique_sources
                })
        else:
            st.warning("Please type a question first!")

    # ── Chat History ─────────────────────────────
    if st.session_state.chat_history:
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        #st.markdown('<p class="section-title">Conversations</p>', unsafe_allow_html=True)

        for chat in reversed(st.session_state.chat_history):
            # User bubble
            st.markdown(f"""
            <div class="chat-you">
                <div class="chat-you-bubble">{chat['question']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Bot bubble
            st.markdown(f"""
            <div class="chat-bot">
                <div class="chat-bot-icon">📄</div>
                <div class="chat-bot-bubble">{chat['answer']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Sources
            sources_html = "".join(
                [f'<span class="source-tag">📎 {s}</span>' for s in chat['sources']]
            )
            st.markdown(f"""
            <div class="sources-container">{sources_html}</div>
            """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="info-box">
        👆 Upload your research papers above and click <strong>Analyse Papers</strong> to get started
    </div>
    """, unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────
st.markdown("""
<div class="footer">
    
</div>
""", unsafe_allow_html=True)

