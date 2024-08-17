import streamlit as st
import xml.etree.ElementTree as ET
import json
import re

def display_summary(summary):
    try:
        root = ET.fromstring(summary)
        
        if root.find('title') is not None:
            st.subheader(root.find('title').text)
        
        if root.find('overview') is not None:
            st.write("**Overview:**")
            st.write(root.find('overview').text)
        
        if root.find('key_points') is not None:
            st.write("**Key Points:**")
            for point in root.find('key_points').findall('point'):
                st.write("- " + point.text)
        
        if root.find('code_examples') is not None:
            st.write("**Code Examples:**")
            for example in root.find('code_examples').findall('example'):
                st.code(example.text, language="bash")
    
    except ET.ParseError:
        st.divider()

        title_match = re.search(r'<title>(.*?)</title>', summary)
        overview_match = re.search(r'<overview>(.*?)</overview>', summary)
        key_points_match = re.search(r'<key_points>(.*?)</key_points>', summary, re.DOTALL)
        code_examples_match = re.search(r'<code_examples>(.*?)</code_examples>', summary, re.DOTALL)
        
        if title_match:
            st.subheader(title_match.group(1))
        
        if overview_match:
            st.write("**Overview:**")
            st.write(overview_match.group(1))
        
        if key_points_match:
            st.write("**Key Points:**")
            points = re.findall(r'<point>(.*?)</point>', key_points_match.group(1))
            for point in points:
                st.write("- " + point)
        
        if code_examples_match:
            st.write("**Code Examples:**")
            examples = re.findall(r'<example>(.*?)</example>', code_examples_match.group(1), re.DOTALL)
            for example in examples:
                st.code(example, language="bash")
        
        if not any([title_match, overview_match, key_points_match, code_examples_match]):
            st.write(summary)

        st.divider()

def display_summary_json(summary):
    try:
        # Parse the JSON string
        data = json.loads(summary)

        print(data)

    except json.JSONDecodeError:
        st.error("Error: Invalid JSON format in the summary.")
        st.text(summary)