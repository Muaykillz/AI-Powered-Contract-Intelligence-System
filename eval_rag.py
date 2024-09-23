import os
import json
from typing import List, Dict, Any
from src.utils.config import load_environment_variables
from src.services.chat import Solar
from src.database.vector_db import vector_db
from ragchecker import RAGResults, RAGChecker
from ragchecker.metrics import all_metrics
from pdf_processor import process_pdf
#from refchecker import LLMExtractor, LLMChecker

#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_environment_variables()

def load_checking_inputs(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f)

def process_pdfs(pdf_directory: str, output_directory: str) -> Dict[str, Any]:
    processed_docs = {}
    for filename in os.listdir(pdf_directory):
        if filename.endswith('.pdf'):
            input_path = os.path.join(pdf_directory, filename)
            output_path = os.path.join(output_directory, f"processed_{filename}")
            result = process_pdf(input_path, output_path)
            if result is not None:
                processed_docs[filename] = result
            else:
                print(f"Warning: processing {filename} returned None")
    return processed_docs

def main():
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"UPSTAGE_API_KEY: {os.getenv('UPSTAGE_API_KEY')}")
    
    # Initialize your systems
    solar = Solar()

    # Load checking inputs
    checking_inputs_path = os.path.join(PROJECT_ROOT, 'checking_inputs.json')
    print(f"Checking inputs path: {checking_inputs_path}")
    if not os.path.exists(checking_inputs_path):
        raise FileNotFoundError(f"The file {checking_inputs_path} does not exist.")
    checking_inputs = load_checking_inputs(checking_inputs_path)

    # # Process PDFs
    pdf_directory = os.path.join(PROJECT_ROOT, 'pdf_test')
    output_directory = os.path.join(PROJECT_ROOT, 'processed_pdfs')
    print(f"PDF directory: {pdf_directory}")
    print(f"Output directory: {output_directory}")
    if not os.path.exists(pdf_directory):
        raise FileNotFoundError(f"The directory {pdf_directory} does not exist.")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    processed_docs = process_pdfs(pdf_directory, output_directory)

    # Save processed docs to vector DB
    for filename, doc in processed_docs.items():
        if 'summary' in doc and 'ocr_result' in doc:
            vector_db.save_to_vector_db(doc['summary'], doc['ocr_result'], filename)
        else:
            print(f"Warning: {filename} does not have 'summary' or 'ocr_result' keys")

    # Process queries and collect results
    rag_results = []
    for input_item in checking_inputs['results']:
        query_id = input_item['query_id']
        query = input_item['query']
        gt_answer = input_item['gt_answer']
        
        try:
            response = solar.process_query(query, vector_db)
            
            rag_result = solar.response_to_eval(
                query_id=query_id,
                query=query,
                gt_answer=gt_answer,
                response=response
            )
            rag_results.append(rag_result)
        except Exception as e:
            print(f"Error processing query {query_id}: {str(e)}")
            print(f"Query: {query}")
            print(f"Response: {response}")

    # Create RAGResults object
    try:
        rag_results_obj = RAGResults.from_dict({"results": rag_results})
    except Exception as e:
        print(f"Error creating RAGResults object: {str(e)}")
        print("rag_results:")
        for result in rag_results:
            print(json.dumps(result, indent=2))
        return

    print("RAGResults object created successfully")
    
    # Initialize RAGChecker
    evaluator = RAGChecker(
        extractor_name="gpt-4o",
        checker_name="gpt-4o",
        batch_size_extractor=64,  
        batch_size_checker=64
    )

    # Evaluate using RAGChecker
    try:
        
        evaluation_results = evaluator.evaluate(rag_results_obj, all_metrics)
        print("Successfully evaluated all results together")
        print("Overall Metrics:")
        print(json.dumps(evaluation_results.overall_metrics, indent=2))
    except Exception as e:
        print(f"Error during batch evaluation: {str(e)}")
        print("Falling back to individual result evaluation")
        
        # Initialize containers for aggregating results
        all_results = []
        overall_metrics = {metric: [] for metric in all_metrics}
        
        # Evaluate each result individually
        for result in rag_results_obj.results:
            try:
                single_result = RAGResults(results=[result])
                single_evaluation = evaluator.evaluate(single_result, all_metrics)
                all_results.append(single_evaluation.results[0])
                
                # Aggregate metrics
                for metric, value in single_evaluation.overall_metrics.items():
                    if isinstance(value, (int, float)):
                        overall_metrics[metric].append(value)
                
                print(f"Successfully evaluated Query ID: {result.query_id}")
            except Exception as inner_e:
                print(f"Failed to evaluate Query ID: {result.query_id}")
                print(f"Error: {str(inner_e)}")
        
        # Calculate average for numerical metrics
        final_overall_metrics = {}
        for metric, values in overall_metrics.items():
            if values:
                final_overall_metrics[metric] = sum(values) / len(values)
        
        # Create a new RAGResults object with all successful evaluations
        evaluation_results = RAGResults(results=all_results, overall_metrics=final_overall_metrics)
    
    print("\nOverall Evaluation Results:")
    print(json.dumps(evaluation_results.overall_metrics, indent=2))
    
    print("\nIndividual Query Results:")
    for result in evaluation_results.results:
        print(f"Query ID: {result.query_id}")
        print(f"Metrics: {json.dumps(result.metrics, indent=2)}")
        print("---")
        
    results_path = os.path.join(PROJECT_ROOT, 'evaluation_results_final_3.json')
    try:
        with open(results_path, 'w') as f:
            json.dump(evaluation_results.to_dict(), f, indent=2)
        print(f"Results saved to {results_path}")
    except Exception as e:
        print(f"Error saving results to file: {str(e)}")

if __name__ == "__main__":
    main()