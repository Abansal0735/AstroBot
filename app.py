# app.py - Astro Bot 
# User enters: Date of birth, Time of birth, Place of birth (text), and a free-text question.
# The program looks up place -> lat/lon from a built-in offline dictionary, computes the chart,
# detects intent from the question, and returns data-backed answers with transparent calculations.

import argparse, json
from astro_calc import AstroCalc, ManglikRule, MoonSignRule, VimshottariDasha, PLACE_DICT
try:
    import gradio as gr
except Exception:
    gr = None

def lookup_place(place_text):
    """Simple case-insensitive lookup in built-in PLACE_DICT.
    If not found, returns None."""
    if not place_text:
        return None
    key = place_text.strip().lower()
    if key in PLACE_DICT:
        return PLACE_DICT[key]
    for token in key.replace(',', ' ').split():
        if token in PLACE_DICT:
            return PLACE_DICT[token]
    return None

def answer_query(dob, time, place, tz, question):
    place_info = lookup_place(place)
    if place_info is None:
        return json.dumps({'error': 'Place not found in offline database. Please provide a nearby city (e.g., Delhi, Mumbai).'}, indent=2)

    birth = {
        'date': dob.strip(),
        'time': time.strip(),
        'lat': float(place_info['lat']),
        'lon': float(place_info['lon']),
        'tz': float(tz)
    }

    calc = AstroCalc(birth)
    computed = calc.compute_all()

    q = (question or '').lower()
    answers = []

    # Intent matching: keywords based (expandable)
    if any(k in q for k in ['manglik', 'mangal', 'manglik dosha']):
        res = ManglikRule(calc).check()
        answers.append({'intent': 'manglik', 'answer': res['conclusion'], 'explanation': res['explanation'], 'data_used': {'mars_longitude': res['mars_longitude'], 'mars_house': res['mars_house']}, 'rule': 'Mars in houses 1,2,4,7,8,12 from Ascendant'})

    if any(k in q for k in ['moon sign', 'moon', 'chandra']):
        res = MoonSignRule(calc).get()
        answers.append({'intent': 'moon_sign', 'answer': res['moon_sign'], 'explanation': res['explanation'], 'data_used': {'moon_longitude': res['moon_longitude']}, 'rule': 'Moon sign = zodiac sign containing Moon longitude'})

    if any(k in q for k in ['dasha', 'mahadasha', 'vimshottari']):
        res = VimshottariDasha(calc).current_dasha()
        answers.append({'intent': 'dasha', 'answer': res['mahadasha'], 'explanation': res['explanation'], 'data_used': {'moon_longitude': res['moon_longitude']}, 'rule': 'Simplified Vimshottari based on Moon nakshatra index'})

    # if user asks for chart or houses
    if any(k in q for k in ['chart', 'houses', 'house', 'full chart', 'show chart']):
        answers.append({'intent': 'chart', 'answer': 'Computed chart attached', 'explanation': 'See computed data', 'data_used': computed})

    if not answers:
        # return computed data 
        answers.append({'intent': 'computed', 'answer': 'Computed chart attached', 'explanation': 'No specific intent detected. Try asking: "Am I Manglik?", "What is my Moon sign?", "Which Mahadasha am I in?"', 'data_used': computed})

    response = {'place_used': place_info, 'computed': computed, 'answers': answers}
    return json.dumps(response, indent=2)

def gradio_interface():
    with gr.Blocks() as demo:
        gr.Markdown('# Astro Bot — Offline Place Lookup (Vedic assistant)')
        gr.Markdown('Enter date, time, place (city/state), timezone offset (e.g., 5.5 for IST), and your question. Place lookup is offline from a built-in dictionary.')
        with gr.Row():
            dob = gr.Textbox(value='2006-10-12', label='Date of birth (YYYY-MM-DD)')
            time = gr.Textbox(value='20:27', label='Time of birth (HH:MM 24h)')
            place = gr.Textbox(value='Delhi', label='Place of birth (city or state)')
            tz = gr.Textbox(value='5.5', label='Timezone offset (e.g., 5.5 for IST)')
        question = gr.Textbox(value='Am I Manglik?', label='Question (free text)')
        out = gr.JSON(label='Response')
        btn = gr.Button('Ask')
        btn.click(fn=answer_query, inputs=[dob, time, place, tz, question], outputs=[out])
    demo.launch()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true', help='Run CLI mode (no Gradio)')
    args = parser.parse_args()

    if args.cli or gr is None:
        print('Offline-place mode. Provide DOB, time, place name, timezone, and question.')
        dob = input('Date of birth (YYYY-MM-DD): ').strip()
        time = input('Time of birth (HH:MM 24h): ').strip()
        place = input('Place of birth (city/state): ').strip()
        tz = input('Timezone offset (hours, e.g., 5.5): ').strip()
        question = input('Question: ').strip()
        print(answer_query(dob, time, place, tz, question))
    else:
        gradio_interface()
