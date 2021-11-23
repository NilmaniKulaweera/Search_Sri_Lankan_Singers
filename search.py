from math import sqrt
from collections import Counter
from elasticsearch import Elasticsearch
import json
import math

es = Elasticsearch([{'host': 'localhost', 'port':9200}])

def get_cosine_sim(word1, word2):
    vec1 = word2vec(word1)
    vec2 = word2vec(word2)
    return cos_dis(vec1, vec2)
   
def word2vec(word):
    # count the characters in word
    cw = Counter(word)
    # precomputes a set of the different characters
    sw = set(cw)
    # precomputes the "length" of the word vector
    lw = sqrt(sum(c*c for c in cw.values()))

    # return a tuple
    return cw, sw, lw

def cos_dis(v1, v2):
    # which characters are common to the two words?
    common = v1[1].intersection(v2[1])
    # by definition of cosine distance we have
    return sum(v1[0][ch]*v2[0][ch] for ch in common)/v1[2]/v2[2]

def get_similarity(word, keywords):
    keywords_simi = []
    for keyword in keywords:
         keywords_simi.append(get_cosine_sim(word, keyword))
    max_value = max(keywords_simi)
    
    return max_value, keywords_simi.index(max_value)

def intent_classifier(search_term):
    keywords_female = ["female", "lady", "ගායිකාවන්", "ගායිකාව", "ගායිකාවෝ", "ගැහැණු", "කාන්තා", "ස්ත්‍රී"]
    keywords_male = ["male", "පිරිමි"]
    keywords_song = ["song", "sing", "sings", "sang", "සිංදුව", "ගීතය", "ගයන", "ගායනා", "ගැයුව", "ගැයූ", "ගයපු"]
    keywords_instrument = ["play", "plays", "played", "වාදනය", "වයන", "වයන්න", "ගහන්න", "ගහපු"]
    keywords_occupation = ["career", "profession", "occupation", "job", "වෘත්තීය", "වෘත්තීයෙන්", "රැකියාව", "රැකියාවෙන්"]
    keywords_decade = ["decade", "decennary", "decennium", "දශකය", "දශකයේ", "දශක"]

    is_intent_female = False
    is_intent_male = False
    is_intent_song = False
    is_intent_instrument = False
    is_intent_occupation = False
    is_intent_decade = False

    search_terms = search_term.split()
    filter_word_indexes = []
    for term in search_terms:
        female_similarity = get_similarity(term, keywords_female)
        male_similarity = get_similarity(term, keywords_male)
        song_similarity = get_similarity(term, keywords_song)
        instrument_similarity = get_similarity(term, keywords_instrument)
        occupation_similarity = get_similarity(term, keywords_occupation)
        decade_similarity = get_similarity(term, keywords_decade)

        if female_similarity[0] > 0.9:
            is_intent_female = True
            filter_word_indexes.append(term)
            
        elif male_similarity[0] > 0.9:
            is_intent_male = True
            filter_word_indexes.append(term)
            
        elif song_similarity[0] > 0.9:
            is_intent_song = True
            filter_word_indexes.append(term)

        elif instrument_similarity[0] > 0.9:
            is_intent_instrument = True
            filter_word_indexes.append(term)

        elif occupation_similarity[0] > 0.9:
            is_intent_occupation = True
            filter_word_indexes.append(term)
            
        elif decade_similarity[0] > 0.9:
            is_intent_decade = True
            filter_word_indexes.append(term)

    result_word = ''
    
    query_words = search_term.split()
    result_words = []
    for word in query_words:
        if word not in filter_word_indexes:
            result_words.append(word)

    result_word = ' '.join(result_words)

    return is_intent_female, is_intent_male, is_intent_song, is_intent_instrument, is_intent_occupation, is_intent_decade, result_word

def search_all_fields(result_word, fields, gender_intent, gender_filter):
    must_array = [{ "multi_match": { "query": result_word, "fields": fields }}]
    must_array.extend(add_filter(gender_filter))

    should_array = []
    
    if gender_intent == "female":
        must_array.append({ "match": { "gender": "female" }})
    elif gender_intent == "male":
        must_array.append({ "match": { "gender": "male" }})
    elif gender_intent == "both":
        should_array.append({ "match": { "gender": "male" }})

    results = es.search(
        index="srilankan_singers", 
        query={ 
            "bool": { 
                "must": must_array,
                "should": should_array
            } 
        },
        aggs={
            "singer_gender": {
                "terms": {
                    "field": "gender.keyword",
                    "size": 3
                }
            }
        },
        from_= 0,
        size= 160
    )
    
    return results

def search_range(decade_start_year, decade_end_year, gender_intent, gender_filter):
    must_array = []
    must_array.extend(add_filter(gender_filter))

    should_array = []
    sort_array = [{ "carrer_start_year": "desc" }]
    
    if gender_intent == "female":
        must_array.append({ "match": { "gender": "female" }})
    elif gender_intent == "male":
        must_array.append({ "match": { "gender": "male" }})
    elif gender_intent == "both":
        must_array.append({ "match_all": {}})
        should_array.append({ "match": { "gender": "male" }})
        sort_array.insert(0, {"_score": "desc"})

    results = es.search(
        index="srilankan_singers", 
        query={
            "bool": {
                "must": must_array,
                "should": should_array,
                "filter": [
                    { "range": { "carrer_start_year": { "lte": decade_start_year }}},
                    { "range": { "career_end_year": { "gte": decade_end_year }}}
                ]
            }
        },
        sort=sort_array,
        aggs={
            "singer_gender": {
                "terms": {
                    "field": "gender.keyword",
                    "size": 3
                }
            }
        },
        from_= 0,
        size= 160
    )
    return results

def show_results(result):
    hits = result.get('hits').get('hits')
    for result_index in range(len(hits)):
        singer = hits[result_index].get('_source')
        print(singer.get('singer_name_en'))

def boost_field(field):
    boost_values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    
    if field == "song":
        boost_values[3] = 20
        boost_values[4] = 20
    elif field == "instrument":
        boost_values[7] = 20
        boost_values[8] = 20
    elif field == "occupation":
        boost_values[5] = 20
        boost_values[6] = 20
        
    field1 ="singer_name_en^{}".format(boost_values[0])
    field2 = "singer_name_si^{}".format(boost_values[1])
    field3 = "gender^{}".format(boost_values[2])
    field4 = "famous_songs_en^{}".format(boost_values[3])
    field5 = "famous_songs_si^{}".format(boost_values[4])
    field6 = "other_occupations_en^{}".format(boost_values[5])
    field7 = "other_occupations_si^{}".format(boost_values[6])
    field8 = "instruments_played_en^{}".format(boost_values[7])
    field9 = "instruments_played_si^{}".format(boost_values[8])
    field10 = "personal_life_en^{}".format(boost_values[9])
    field11 = "personal_life_si^{}".format(boost_values[10])
    field12 = "career_en^{}".format(boost_values[11])
    field13 = "career_si^{}".format(boost_values[12])
    print([field1, field2, field3, field4, field5, field6, field7, field8, field9, field10, field11, field12, field13])
    return [field1, field2, field3, field4, field5, field6, field7, field8, field9, field10, field11, field12, field13]

def metadata(keyword):
    elements = []
    with open('metadata/'+ keyword +'.txt', 'r', encoding="utf8") as filehandle:
        filecontents = filehandle.readlines()

        for line in filecontents:
            # remove linebreaks, commas, and apostrophes from the string
            current_element = line[3:-3]

            # add item to the list
            elements.append(current_element)
            
    return elements

def get_search_word(result_word, intent):
    if intent == "song":
        keyword = "songs"
    elif intent == "instrument":
        keyword = "instruments"
    elif intent == "occupation":
        keyword = "occupations"

    meta_data = metadata(keyword)
    similarity = get_similarity(result_word, meta_data)
    result_word = meta_data[similarity[1]]
    
    return result_word

def normal_search(user_query, gender_filter):
    is_intent_female, is_intent_male, is_intent_song, is_intent_instrument, is_intent_occupation, is_intent_decade, result_word = intent_classifier(user_query)
    print(is_intent_female, is_intent_male, is_intent_song, is_intent_instrument, is_intent_occupation, is_intent_decade, result_word)

    if is_intent_song:
        fields = boost_field("song")
        result_word = get_search_word(result_word, "song")
    elif is_intent_instrument:
        fields = boost_field("instrument")
        result_word = get_search_word(result_word, "instrument")
    elif is_intent_occupation:
        fields = boost_field("occupation")
        result_word = get_search_word(result_word, "occupation")
    else:
        fields = boost_field("none")

    if is_intent_song or is_intent_instrument or is_intent_occupation or not is_intent_decade:
        if is_intent_female:
            search_results = search_all_fields(result_word, fields, "female", gender_filter)
        elif is_intent_male:
            search_results = search_all_fields(result_word, fields, "male", gender_filter)
        else:
            search_results = search_all_fields(result_word, fields, "both", gender_filter)

    elif is_intent_decade:
        for term in result_word.split():
            if term.isnumeric():
                entered_year = int(term)
                decade_start_year = int(math.floor(entered_year/10.0)) * 10
                decade_end_year = decade_start_year + 10
                if decade_end_year > 2022:
                    decade_end_year = 2022
                break
        if is_intent_female:
            search_results = search_range(decade_start_year, decade_end_year, "female", gender_filter)
        elif is_intent_male:
            search_results = search_range(decade_start_year, decade_end_year, "male", gender_filter)
        else:
            search_results = search_range(decade_start_year, decade_end_year, "both", gender_filter)

    print(result_word)
    
    return search_results

def phrase_search(phrase, gender_filter):
    must_array = [{ "multi_match": {
                        "query": phrase,
                        "fields": [ 
                            "singer_name_en", 
                            "singer_name_si", 
                            "gender", 
                            "famous_songs_en", 
                            "famous_songs_si", 
                            "other_occupations_en",
                            "other_occupations_si", 
                            "instruments_played_en", 
                            "instruments_played_si", 
                            "personal_life_en", 
                            "personal_life_si", 
                            "career_en", 
                            "career_si"
                        ],
                        "type": "phrase"
                    }}]
    must_array.extend(add_filter(gender_filter))

    results = es.search(
        index="srilankan_singers", 
        query={
            "bool": {
                "must":must_array
            }

        },
        aggs={
            "singer_gender": {
                "terms": {
                    "field": "gender.keyword",
                    "size": 3
                }
            }
        },
        from_= 0,
        size= 160
    )
    return results

def post_processor(results, no_phrase_query_results):
    final_result = {}
    singer_genders = []
    final_result['no_phrase_query_results'] = no_phrase_query_results
    
    # to handle exceptions
    if not results:
        final_result['no_result'] = True
        return final_result
    
    hits = results.get('hits').get('hits')
    singer_count = len(hits)
    if singer_count == 0:
        final_result['no_result'] = True
    else:
        final_result['no_result'] = False
        final_result['singer_count'] = singer_count
        singers = []
        for result_index in range(len(hits)):
            singer = {}
            singer_details = hits[result_index].get('_source')
            singer['_id'] = hits[result_index].get('_id')
            singer['singer_name_en'] = singer_details.get('singer_name_en')
            singer['singer_name_si'] = singer_details.get('singer_name_si')
            singer['birth_year'] = singer_details.get('birth_year')
            singer['death_year'] = singer_details.get('death_year')
            singer['carrer_start_year'] = singer_details.get('carrer_start_year')
            singer['career_end_year'] = singer_details.get('career_end_year')
            singer['gender'] = singer_details.get('gender')
            singer['famous_songs_en'] = singer_details.get('famous_songs_en')
            singer['famous_songs_si'] = singer_details.get('famous_songs_si')
            singer['other_occupations_en'] = singer_details.get('other_occupations_en')
            singer['other_occupations_si'] = singer_details.get('other_occupations_si')
            singer['instruments_played_en'] = singer_details.get('instruments_played_en')
            singer['instruments_played_si'] = singer_details.get('instruments_played_si')
            singer['personal_life_en'] = singer_details.get('personal_life_en')
            singer['personal_life_si'] = singer_details.get('personal_life_si')
            singer['career_en'] = singer_details.get('career_en')
            singer['career_si'] = singer_details.get('career_si')
            singers.append(singer)
            
        final_result['singers'] = singers

        aggregations = results.get('aggregations')
        singer_genders = aggregations.get('singer_gender').get('buckets')
        for singer_gender in singer_genders:
            singer_gender['id'] = f'singer_gender-{singer_genders.index(singer_gender)}'
    
    return final_result, singer_genders

def add_filter(gender_filter):
    sub_query = []
    if len(gender_filter) != 0:
        for gender in gender_filter:
            sub_query.append({"match": {"gender": gender["key"]}})
    return sub_query

def search(user_query, gender_filter=[]):
    query_words = user_query.split('"')
    no_phrase_query_results = False
    
    if len(query_words) > 2:
        isPhraseQuery = True
        phrase = query_words[1]
        results = phrase_search(phrase, gender_filter)

        if results.get('hits').get('total').get('value') == 0:
            no_phrase_query_results = True
            print("No search results for phrase query. Instead doing a normal search")
            normal_query = user_query.replace('"', '')
            results = normal_search(normal_query, gender_filter)

    else:
        isPhraseQuery = False
        results = normal_search(user_query, gender_filter)
        
    return post_processor(results, no_phrase_query_results)
    #show_results(results)

# user_query = 'song hantanata payana'
# search(user_query)