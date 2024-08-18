import streamlit as st
from src.services.chat import Solar
from src.database.vector_db import vector_db
import json

solar = Solar()

# ยังไม่สมบูรณ์

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
                st.write("Query Analysis:", analysis)

                # # Search in Vector DB
                # search_results = []
                # for keyword in analysis["keywords"]:
                #     results = vector_db.search_documents(keyword, n_results=2)
                #     search_results.extend(results["documents"][0])

                # # Generate response
                # response = solar.generate_response(prompt, search_results)
                
                return # ยังไม่สมบูรณ์

                st.markdown(response["answer"])
                st.write("References:")
                for ref in response["references"]:
                    st.write(f"- Document: {ref['document']}, Relevance: {ref['relevance']}")

        st.session_state.messages.append({"role": "assistant", "content": response["answer"]})

if __name__ == "__main__":
    render()