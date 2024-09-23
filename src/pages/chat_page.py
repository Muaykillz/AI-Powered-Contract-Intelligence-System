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

                # Convert the analysis to text
                analysis_text = json.dumps(analysis, indent=2)
                print("Analysis:", analysis_text)

                if not analysis["is_contract_related"]:
                    response = {
                        "answer": solar.talk_general(prompt),
                        "references": []
                    }
                else:

                    # Embed the overview query
                    # overview_query_embedding = solar.embed_query(analysis_text)

                    # Perform sementic search
                    # search_results = vector_db.semantic_search(
                    #     query_embedding=overview_query_embedding,
                    #     n_results=5
                    # )

                    # Perform hybrid search
                    search_results = vector_db.hybrid_search(
                        analysis=analysis,
                        n_results=5
                    )

                    print("\n\n 🧍🏻Search Results:", search_results)

                    # Generate response
                    response = solar.generate_response(prompt, search_results)
                    print("✨ Response:", response)

                    # Evaluate the response
                    evaluation = solar.self_evaluate(prompt, response, search_results)
                    print("Evaluation:", evaluation)

                    if evaluation['evaluation_score'] < 0.7:
                        # improve with semantic search
                        # improved_results = vector_db.semantic_search(
                        #     query_embedding=overview_query_embedding,
                        #     n_results=10
                        # )

                        # improve with hybrid search
                        improved_results = vector_db.hybrid_search(
                            analysis=analysis,
                            n_results=10
                        )
                        improved_response = solar.generate_response(prompt, improved_results)
                        improved_evaluation = solar.self_evaluate(prompt, improved_response, improved_results)
                        
                        if improved_evaluation['evaluation_score'] > evaluation['evaluation_score']:
                            response = improved_response
                            evaluation = improved_evaluation

            # Write the answer
            st.write(response["answer"])

            if analysis["is_contract_related"]:
                # Write the references
                if response["references"]:
                    with st.expander("📎 References"):
                        references_by_file = {}
                        for ref in response["references"]:
                            if ref['file_name'] not in references_by_file:
                                references_by_file[ref['file_name']] = []
                            references_by_file[ref['file_name']].append(ref)
                        
                        for file_name, refs in references_by_file.items():
                            st.markdown(f"**File: {file_name}**")
                            for ref in refs:
                                st.markdown(f"* Page: {ref['page']}, Relevance: {ref['relevance']}")
                
                # Write the evaluation details
                with st.expander("Evaluation Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Confidence", f"{response.get('confidence', 0.0):.2f}")
                    with col2:
                        st.metric("Evaluation Score", f"{evaluation['evaluation_score']:.2f}")
                    
                    st.write("Feedback:", evaluation['feedback'])
                    st.write("Suggestions for improvement:")
                    for suggestion in evaluation['suggestions_for_improvement']:
                        st.markdown(f"- {suggestion}")


            

        st.session_state.messages.append({"role": "assistant", "content": response["answer"]})

if __name__ == "__main__":
    render()
