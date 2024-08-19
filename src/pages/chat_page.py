import streamlit as st
from src.services.chat import Solar
from src.database.vector_db import vector_db
import json

solar=Solar()

def render():
    st.title("Contract Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know about the contracts?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Analyze the query
                analysis = solar.analyze_user_query(prompt)
                with st.expander("See Query Analysis"):
                    st.write("Query Analysis:", analysis)
                # Process the query using self-RAG
                result = solar.process_query(prompt, vector_db)
                
                st.markdown(result.get("answer", "Sorry, I couldn't generate an answer."))

                if "references" in result:
                    for ref in result["references"]:
                        st.write(f"- Document: {ref.get('document', 'N/A')}, Relevance: {ref.get('relevance', 'N/A')}")

                st.write(f"Confidence: {result.get('confidence', 0.0):.2f}")
                st.write(f"Evaluation Score: {result.get('evaluation_score', 0.0):.2f}")
                
                with st.expander("See evaluation details"):
                    st.write("Feedback:", result.get("evaluation_feedback", "No feedback available."))
                    st.write("Suggestions for improvement:")
                    for suggestion in result.get("suggestions_for_improvement", ["No suggestions available."]):
                        st.write(f"- {suggestion}")

        st.session_state.messages.append({"role": "assistant", "content": result.get("answer", "Sorry, I couldn't generate an answer.")})

if __name__ == "__main__":
    render()