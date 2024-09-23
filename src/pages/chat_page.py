import streamlit as st
from src.services.chat import Solar
from src.database.vector_db import vector_db
import json
import re

#vector_db = VectorDB(clear_on_init=False)  
solar = Solar()
actual_dimension = solar.check_embedding_dimension()
print(f"Actual query embedding dimension: {actual_dimension}")

def extract_info(text, key):
    pattern = rf"{key}:\s*(.*?)(?=\s*[A-Z][\w\s]*:|\s*$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else "Information not available"

def beautify_summary(summary_text):
    try:
        summary = json.loads(summary_text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', summary_text)
        if json_match:
            try:
                summary = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                st.write(summary_text)
                return
        else:
            st.write(summary_text)
            return

    st.markdown("""
    <style>
    .contract-summary {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .contract-summary h3 {
        color: #1f1f1f;
        margin-bottom: 15px;
    }
    .contract-summary ul {
        list-style-type: none;
        padding-left: 0;
    }
    .contract-summary li {
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
    }
    .contract-summary .icon {
        margin-right: 10px;
        min-width: 24px;
    }
    .contract-summary .key {
        font-weight: bold;
        margin-right: 5px;
    }
    .contract-summary .footer {
        margin-top: 15px;
        font-size: 0.9em;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="contract-summary">
        <h3>{summary.get('title', 'Contract Summary')}</h3>
        <p>{summary.get('overview', 'No overview available.')}</p>
        <ul>
            <li><span class="icon">📅</span> <span class="key">Duration:</span> {summary.get('duration', {}).get('initial_term', 'Not specified')}</li>
            <li><span class="icon">🤝</span> <span class="key">Joint Promotion:</span> {summary.get('key_terms', {}).get('joint_promotion', 'Not specified')}</li>
            <li><span class="icon">💡</span> <span class="key">Intellectual Property:</span> {summary.get('key_terms', {}).get('intellectual_property', 'Not specified')}</li>
            <li><span class="icon">🔒</span> <span class="key">Confidentiality:</span> {summary.get('key_terms', {}).get('confidentiality', 'Not specified')}</li>
            <li><span class="icon">🚫</span> <span class="key">Termination:</span> {summary.get('key_terms', {}).get('termination', 'Not specified')}</li>
            <li><span class="icon">⚖️</span> <span class="key">Governing Law:</span> {summary.get('key_terms', {}).get('governing_law', 'Not specified')}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if summary.get('key_conditions'):
        st.markdown("### Key Conditions")
        for condition in summary['key_conditions']:
            st.markdown(f"- **{condition['description']}** (Priority: {condition['priority']})")
            st.markdown(f"  Potential Impact: {condition['potential_impact']}")

    if summary.get('important_dates'):
        st.markdown("### Important Dates")
        for date in summary['important_dates']:
            st.markdown(f"- **{date['date']}** (Priority: {date['priority']})")
            st.markdown(f"  Description: {date['description']}")

def display_references(references):
    if references:
        with st.expander("📎 References"):
            references_by_file = {}
            for ref in references:
                file_name = ref.get('file_name', 'Unknown File')
                if file_name not in references_by_file:
                    references_by_file[file_name] = []
                references_by_file[file_name].append(ref)
            
            for file_name, refs in references_by_file.items():
                st.markdown(f"**File: {file_name}**")
                for ref in refs:
                    st.markdown(f"""
                    * **Document:** {ref.get('document', 'Unknown Document')}
                      - **Section:** {ref.get('section', 'N/A')}
                      - **Clause:** {ref.get('clause', 'N/A')}
                      - **Page:** {ref.get('page', 'N/A')}
                      - **Relevance:** {ref.get('relevance', 'N/A')}
                    """)
    else:
        st.write("No specific references provided.")

def render():
    st.title("📄 Contract Chatbot")
    st.markdown("""
    <div style="background-color: #e6f2ff; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <strong>User guidelines:</strong> You can ask any question about contracts. Feel free to inquire about specific terms, clauses, or general contract information. For a summary, include "summarize" or "summary" in your query.
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = {}
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💼" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know about the contracts?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing and retrieving information..."):
                # Analyze the query
                analysis = solar.analyze_user_query(prompt)
                if not analysis["is_contract_related"]:
                    result = {"answer": solar.talk_general(prompt), "references": []}
                else:
                    with st.expander("📊 See Query Analysis"):
                        st.json(analysis)
                    # Process the query using self-RAG and hybrid search with graph nodes
                    result = solar.process_query(prompt, vector_db)
                
                    # Check if it's a summarization request
                    if "summarize" in prompt.lower() or "summary" in prompt.lower():
                        summary = result.get("summary", result.get("answer", ""))
                        if summary:
                            beautify_summary(summary)
                        else:
                            st.error("Failed to generate a summary. Please try again.")
                    else:
                        st.markdown(result.get("answer", "Sorry, I couldn't generate an answer."))
                    print("Debug - References:", result.get("references", []))
                    display_references(result.get("references", []))

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confidence", f"{result.get('confidence', 0.0):.2f}")
                with col2:
                    st.metric("Evaluation Score", f"{result.get('evaluation_score', 0.0):.2f}")

                st.markdown("---")
                with st.expander("👤 See User Preferences"):
                    st.json(st.session_state.user_preferences)
                
                with st.expander("📝 See Evaluation Details"):
                    st.write("Groundedness Score:", result.get('groundedness', {}).get('score', 0.0))
                    st.write("Groundedness Feedback:", result.get('groundedness', {}).get('feedback', "No feedback available."))
                    st.write("Evaluation Feedback:", result.get('feedback', "No feedback available."))
                    st.write("Suggestions for improvement:")
                    for suggestion in result.get('suggestions_for_improvement', ["No suggestions available."]):
                        st.write(f"- {suggestion}")    

        st.session_state.messages.append({"role": "assistant", "content": result.get("answer", "Sorry, I couldn't generate an answer.")})

if __name__ == "__main__":
    render()