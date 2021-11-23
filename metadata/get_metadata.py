import json
import pandas as pd
import numpy as np
import math

with open('../singer_corpus/translated_singer_information.json', 'r', encoding="utf8") as data_file:
    json_data = json.load(data_file)
dfItem = pd.DataFrame.from_records(json_data)

famous_songs_english = dfItem["famous_songs_en"].explode().unique().tolist()
famous_songs_sinhala = dfItem["famous_songs_si"].explode().unique().tolist()
total_songs = famous_songs_english + famous_songs_sinhala

cleaned_list_songs = [x for x in total_songs if isinstance(x, str)]
final_list_songs = list(set([i.strip() for i in cleaned_list_songs]))
print("songs", final_list_songs)

instruments_played_english = dfItem["instruments_played_en"].explode().unique().tolist()
instruments_played_sinhala = dfItem["instruments_played_si"].explode().unique().tolist()
total_instruments = instruments_played_english + instruments_played_sinhala

cleaned_list_instruments = [x for x in total_instruments if isinstance(x, str)]
final_list_instruments = list(set([i.strip() for i in cleaned_list_instruments]))
print("instruments", final_list_instruments)

other_occupations_english = dfItem["other_occupations_en"].explode().unique().tolist()
other_occupations_sinhala = dfItem["other_occupations_si"].explode().unique().tolist()
total_occupations = other_occupations_english + other_occupations_sinhala

cleaned_list_occupations = [x for x in total_occupations if isinstance(x, str)]
final_list_occupations = list(set([i.strip() for i in cleaned_list_occupations]))
print("occupations", final_list_occupations)

