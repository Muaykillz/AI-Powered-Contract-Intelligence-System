import streamlit as st
import json
import re
from datetime import datetime

def display_summary(summary):
    def priority_color(priority):
        if priority == "high":
            return "#FEE2E2"  # light red
        elif priority == "medium":
            return "#FEF3C7"  # light yellow
        else:
            return "#D1FAE5"  # light green

    try:
        data = json.loads(summary)
        print(data)

        # Display the title
        st.title(f"{data['title']}")

        # Display warning
        st.warning("⚠️ This summary may not include all contract details. It is provided for easier understanding and decision-making only. Always refer to the full contract for complete information.")

        # Display the contract overview
        st.markdown("""
        <div style="border: 1px solid #E5E7EB; border-radius: 0.375rem; padding: 1rem; margin-bottom: 2rem;">
        <h3 style="margin-top: 0;">📋 Contract Overview</h3>
        <p style="margin-bottom: 0;">{}</p>
        </div>
        """.format(data["overview"]), unsafe_allow_html=True)

        # Key conditions
        st.markdown('<div class="section-spacing">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown("### 🔑 Key Conditions")
        with col3:
            if st.button("See more", key="conditions_more"):
                st.session_state.show_all_conditions = True
        
        for i, condition in enumerate(data["key_conditions"]):
            if i < 2 or st.session_state.get('show_all_conditions', False):
                st.markdown(f"""
                <div style="background-color: {priority_color(condition['priority'])}; padding: 0.5rem; border-radius: 0.375rem; margin-bottom: 0.5rem;">
                <span style="background-color: {'#DC2626' if condition['priority'] == 'high' else '#D97706' if condition['priority'] == 'medium' else '#059669'}; color: white; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: bold;">{condition['priority'].upper()}</span>
                <p style="margin-top: 0.25rem; margin-bottom: 0;">{condition['description']}</p>
                <p style="margin-top: 0.25rem; margin-bottom: 0; font-style: italic;">Impact: {condition['potential_impact']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Important dates
        st.markdown('<div class="section-spacing">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown("### 📅 Important Dates")
        with col3:
            if st.button("See more", key="dates_more"):
                st.session_state.show_all_dates = True
        
        for i, date in enumerate(data["important_dates"]):
            if i < 2 or st.session_state.get('show_all_dates', False):
                st.markdown(f"""
                <div style="background-color: {priority_color(date['priority'])}; padding: 0.5rem; border-radius: 0.375rem; margin-bottom: 0.5rem;">
                <span style="background-color: {'#DC2626' if date['priority'] == 'high' else '#D97706' if date['priority'] == 'medium' else '#059669'}; color: white; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: bold;">{date['priority'].upper()}</span>
                <p style="margin-top: 0.25rem; margin-bottom: 0;"><strong>{date['date']}:</strong> {date['description']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Edit see more buttons
        st.markdown(
                """
                <style>
                    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
                        width: 100%;
                    }
                </style>
                """,
                unsafe_allow_html=True
        )

        # Contract Details
        st.markdown('<div class="section-spacing">', unsafe_allow_html=True)
        st.markdown("### 📊 Contract Details")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="border: 1px solid #E5E7EB; border-radius: 0.375rem; padding: 1rem;">
            <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.25rem;">Contract Duration</p>
            <p style="font-weight: bold; margin: 0;">Start: {data["duration"]["start_date"]}</p>
            <p style="font-weight: bold; margin: 0;">End: {data["duration"]["end_date"]}</p>
            <p style="font-weight: bold; margin: 0;">Initial Term: {data["duration"]["initial_term"]}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="border: 1px solid #E5E7EB; border-radius: 0.375rem; padding: 1rem;">
            <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.25rem;">Contracting Parties</p>
            {"".join(f'<p style="font-weight: bold; margin: 0;">{party["name"]} ({party["role"]})</p>' for party in data["parties"])}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    except json.JSONDecodeError:
        st.error("Error: Invalid JSON format in the summary.")
        st.text(summary)

def extract_events_from_summary(data):
    events = []
    if 'important_dates' in data:
        for event in data['important_dates']:
            date = event['date']
            if re.match(r'\d{4}-\d{2}-\d{2}', date):
                events.append({
                    'title': event['description'],
                    'start': date,
                    'end': date,
                    'type': event['priority'].capitalize()
                })
            else:
                # Handle non-specific dates
                events.append({
                    'title': f"{date}: {event['description']}",
                    'start': datetime.now().strftime('%Y-%m-%d'),  # Use current date as placeholder
                    'end': datetime.now().strftime('%Y-%m-%d'),
                    'type': 'Non-specific'
                })
    return events