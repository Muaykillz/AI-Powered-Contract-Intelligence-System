import streamlit as st
from streamlit_calendar import calendar
from src.database.sqlite_db import get_all_events

@st.cache_data
def fetch_events():
    return get_all_events()

def render():
    st.title("📅 Contract Calendar")

    # Fetch events from SQLite using cached function
    db_events = fetch_events()

    # Convert events to the format expected by the calendar
    calendar_events = [
        {
            "title": event['title'],
            "start": event['start'],
            "end": event['end'],
            "color": {
                "Key Date": "#FF6C6C",
                "Renewal": "#4CAF50",
                "Expiration": "#F44336",
                "Payment Due": "#2196F3",
                "Review": "#FFC107"
            }.get(event['type'], "#9E9E9E")
        }
        for event in db_events
    ]

    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,dayGridDay,listMonth"
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "editable": False,
        "nowIndicator": True,
        "dayMaxEvents": True,
        "weekNumbers": True,
        "navLinks": True,
    }

    custom_css = """
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: bold;
    }
    .fc-toolbar-title {
        color: #1E88E5;
        font-size: 2rem;
    }
    """

    cal = calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=custom_css
    )

    # Handle calendar interactions
    if cal.get("dateClick") is not None:
        st.write("Date clicked:", cal["dateClick"]["date"])
    elif cal.get("eventClick") is not None:
        st.write("Event clicked:", cal["eventClick"]["event"]["title"])


if __name__ == "__main__":
    render()