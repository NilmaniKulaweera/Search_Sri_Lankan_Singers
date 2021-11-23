from flask import Flask, render_template, request

import search

app = Flask(__name__)

global_scope = {
    'search_terms': None,
    'singer_genders': [],
    'res': None
}

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/search/results', methods=['GET', 'POST'])
def search_request():
    search_term = request.form["input"]

    res, singer_genders = search.search(search_term, gender_filter=[])

    global_scope['search_terms'] = search_term
    global_scope['singer_genders'] = singer_genders
    global_scope['res'] = res

    res['search_term'] = global_scope.get('search_terms')

    return render_template('results.html', res=res, singer_genders=singer_genders)

@app.route('/search/results/filter', methods=['GET', 'POST'])
def faceted_search_request():
    singer_gender_filter = []

    for singer_gender in global_scope.get('singer_genders'):
        if request.form['name'] == singer_gender['key']:
            singer_gender_filter.append(singer_gender)

    search_term = global_scope.get('search_terms')

    res, singer_genders = search.search(search_term, singer_gender_filter)
    global_scope['res'] = res

    res['search_term'] = global_scope.get('search_terms')

    return render_template('results.html', res=res, singer_genders=singer_genders)

@app.route('/profile/<string:id>', methods=['GET'])
def get_user_profile(id):
    singer = global_scope.get('res')['singers'][int(id)]
    
    return render_template('profile.html', res=singer)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'mysecret'
    app.run(host='0.0.0.0', port=5000)