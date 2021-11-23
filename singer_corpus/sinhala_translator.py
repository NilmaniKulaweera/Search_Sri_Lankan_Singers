import json
from googletrans import Translator
from google.transliteration import transliterate_text

def format_meta_data(dict_meta_data):
    formatted_meta_data={}
    for key in dict_meta_data:
        if (key == "famous_songs" or key == "other_occupations" or key == "instruments_played"):
            if (dict_meta_data[key] == ""):
                list = []
            else:
                list = dict_meta_data[key].split(",")
            formatted_meta_data[key] = list
        else:
            formatted_meta_data[key] = dict_meta_data[key]
    return formatted_meta_data

def translate_to_sinhala(value):
	translator = Translator()
	sinhala_val = translator.translate(value, dest='si')
	return sinhala_val.text

def translate_and_transliterate_values(dict_meta_data):
	ignore_key_list = ["index", "birth_year", "death_year", "carrer_start_year", "career_end_year", "gender"]
	transliterate_key_list = ["singer_name", "famous_songs"]
	sinhala_meta_data = {}
	for key in dict_meta_data:
		if key in ignore_key_list:
			sinhala_meta_data[key] = dict_meta_data[key]
		elif type(dict_meta_data[key]) == list :
			value_list = []
			if key in transliterate_key_list:
				for i in dict_meta_data[key]:
					value_list.append(transliterate_text(i, lang_code='si'))
				sinhala_meta_data['{}_en'.format(key)] = dict_meta_data[key]
				sinhala_meta_data['{}_si'.format(key)] = value_list
			else:
				for i in dict_meta_data[key]:
					value_list.append(translate_to_sinhala(i))
				sinhala_meta_data['{}_en'.format(key)] = dict_meta_data[key]
				sinhala_meta_data['{}_si'.format(key)] = value_list
		else:
			if key in transliterate_key_list:
				sinhala_meta_data['{}_en'.format(key)] = dict_meta_data[key]
				sinhala_meta_data['{}_si'.format(key)] = transliterate_text(dict_meta_data[key], lang_code='si')
			else:
				sinhala_meta_data['{}_en'.format(key)] = dict_meta_data[key]
				sinhala_meta_data['{}_si'.format(key)] = translate_to_sinhala(dict_meta_data[key])
	return sinhala_meta_data


with open('singer_information_list.txt', 'r', encoding="utf8") as data_file:
    json_data = data_file.read()

data = json.loads(json_data)

formatted_data = []
for dict_meta_data in data:
    formatted_data.append(format_meta_data(dict_meta_data))

# sinhala_translated_data = []
# for dict_meta_data in formatted_data:
#     sinhala_translated_data.append(translate_values(dict_meta_data)) 

print (translate_and_transliterate_values(formatted_data[0]))