# Astro Bot

This bot allows the user to only enter the following details :
- Date of birth (YYYY-MM-DD)
- Time of birth (HH:MM, 24h)
- Place of birth (city or state name)
- Timezone offset (e.g., 5.5 for IST)
- Free-text question (e.g., "Am I Manglik?")

The app looks up the place in a built-in dictionary to get latitude/longitude,
computes planetary positions and houses using `pyswisseph`, and answers rules-based
questions (Manglik, Moon sign, simplified Vimshottari Mahadasha), always returning
the computed data for transparency.

# Requirements
- pyswisseph==2.12.0
- gradio==3.40.0
