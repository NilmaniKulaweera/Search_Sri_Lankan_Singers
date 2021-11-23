import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import wikipedia
wikipedia.set_lang("en")

main_page_url = "https://en.wikipedia.org/wiki/List_of_Sri_Lankan_musicians"

def extract_info_box_content(singer_url, index):
    page = requests.get(singer_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    infobox = soup.find(class_="infobox")
    
    birthday = None
    birth_data = None
    birth_year = None
    death_data = None
    death_year = None
    years_active = None
    other_occupations = None
    instruments_played = None
    
    if (infobox != None):
        items = infobox.find_all('tr')
      
        for i in items:
            header = i.find('th')
            if header != None:
                if (header.get_text() == "Born"):
                    #birthday = i.find(class_="bday").get_text()
                    birth_data = i.find('td').get_text()
                    if (re.search(r"(\d{4})", birth_data) != None):
                        birth_year = re.search(r"(\d{4})", birth_data).group(0)
                elif (header.get_text() == "Died"):
                    death_data = i.find('td').get_text()
                    if (re.search(r"(\d{4})", death_data) != None):
                        death_year = re.search(r"(\d{4})", death_data).group(0)
                elif (header.get_text() == "Years\xa0active" or header.get_text() == "Years active"):
                    years_active = i.find('td').get_text()
                elif (header.get_text() == "Occupation" or header.get_text() == "Occupation(s)"):
                    other_occupations = i.find('td').get_text()
                elif (header.get_text() == "Instruments"):
                    instruments_played = i.find('td').get_text()

    singer_info_box_items = pd.DataFrame({
        #"birthday": birthday,
        #"birth_data": birth_data,
        "birth_year": birth_year,
        #"death_data":death_data,
        "death_year": death_year,
        "years_active": years_active,
        "other_occupations": other_occupations,
        "instruments_played":instruments_played
    }, index=[index])

    return singer_info_box_items

def extractCareer(page_lines):
    career_pattern = re.compile(r'^=[\w\W\D\d\s\S]*(career|Career)[\w\W\d\D\s\D]*=$')
    extract_end_pattern = re.compile(r'^=[\w\W\D\d\s\S]*=$')
    is_career_pattern_found = False
    career = ''
    for string in page_lines:

        if career_pattern.search(string) is not None:
            is_career_pattern_found = True
            continue

        if is_career_pattern_found and extract_end_pattern.search(string) is not None:
            is_career_pattern_found = False
            continue

        if is_career_pattern_found:
            career += string + " "
            
    alphabet_pattern = re.compile(r'^[\w\W\D\d\s\S]*[A-Za-z][\w\W\d\D\s\D]*$')
    if (alphabet_pattern.search(career) is not None):
        return career
    else:
        return None

def extractPersonalLife(page_lines):
    personal_life_pattern = re.compile(r'^=[\w\W\D\d\s\S]*(personal|Personal|life|Life|Biography|biography)[\w\W\d\D\s\D]*=$')
    extract_end_pattern = re.compile(r'^=[\w\W\D\d\s\S]*=$')
    is_personal_life_pattern_found = False
    personal_life = ''
    for string in page_lines:

        if personal_life_pattern.search(string) is not None:
            is_personal_life_pattern_found = True
            continue

        if is_personal_life_pattern_found and extract_end_pattern.search(string) is not None:
            is_personal_life_pattern_found = False
            continue

        if is_personal_life_pattern_found:
            personal_life += string + " "
            
    alphabet_pattern = re.compile(r'^[\w\W\D\d\s\S]*[A-Za-z][\w\W\d\D\s\D]*$')
    if (alphabet_pattern.search(personal_life) is not None):
            return personal_life
    else:
        return None

def extract_personal_life_and_career(singer_name, index):
    
    page = wikipedia.page(singer_name)
    
    page_lines = page.content.split('\n')
    
    name = page.title
    personal_life = extractPersonalLife(page_lines)
    career = extractCareer(page_lines)
    
    singer_personal_life_and_career = pd.DataFrame({
        "singer_name": name,
        "personal_life": personal_life,
        "career": career
    }, index=[index])
    
    return singer_personal_life_and_career

def get_final_dataframe(singer_url, index):
    url_items = singer_url.split('/')
    singer_name = url_items[-1].replace("_", " ")
    print(singer_name)
    info_box_content = extract_info_box_content(singer_url, index)
    personal_life_and_career = extract_personal_life_and_career(singer_name, index)
    
    final_dataframe = info_box_content.join(personal_life_and_career)
    
    first_col = final_dataframe.pop("singer_name")
    final_dataframe.insert(0, "singer_name", first_col)
    
    return final_dataframe

page = requests.get(main_page_url)
soup = BeautifulSoup(page.content, 'html.parser')
singers= soup.select(".mw-parser-output > ul > li > a")
singer_links = []
for s in singers:
    singer_link = "https://en.wikipedia.org/" + s['href']
    singer_links.append(singer_link)

singer_links.remove("https://en.wikipedia.org//wiki/Anton_Jones")
singer_links.remove("https://en.wikipedia.org//wiki/Bathiya_Jaykody")
singer_links.remove("https://en.wikipedia.org//wiki/Falan_Andrea")

singer_information = pd.DataFrame()
for link in singer_links:
    singer_information = pd.concat([singer_information, get_final_dataframe(link, singer_links.index(link))])

singer_information.to_csv("singer_information.csv")
