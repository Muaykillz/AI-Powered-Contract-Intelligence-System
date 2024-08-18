import streamlit as st
from src.services.chat import Solar
from src.database.vector_db import vector_db
import json

solar = Solar()


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
                
                st.markdown(result["answer"])
                # # Perform hybrid search
                # query_embedding = solar.embed_query(prompt)
                # search_results = vector_db.hybrid_search(
                #     query_embedding = query_embedding, 
                #     keywords=analysis['keywords'], 
                #     n_results=5
                # )

                # # Generate response
                # response = solar.generate_response(prompt, search_results)
                
                # st.markdown(response["answer"])
                #st.write("References:")
                for ref in result["references"]:
                    st.write(f"- Document: {ref['document']}, Relevance: {ref['relevance']}")

                st.write(f"Confidence: {result['confidence']:.2f}")
                st.write(f"Evaluation Score: {result['evaluation_score']:.2f}")
                
                with st.expander("See evaluation details"):
                    st.write("Feedback:", result["feedback"])
                    st.write("Suggestions for improvement:")
                    for suggestion in result["suggestions_for_improvement"]:
                        st.write(f"- {suggestion}")

        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

if __name__ == "__main__":
    render()