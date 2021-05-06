from flask import Flask, request, render_template, jsonify, session
import cloudscraper

app = Flask(__name__)
app.secret_key = 'a3856188398a44f899c72d184e91f424'
app.debug = True

scraper = cloudscraper.create_scraper()
TOTAL_CACHED_SEARCHES = 6

playlists = ['1v1', '2v2', '3v3', 'Hoops', 'Rumble', 'Dropshot', 'Snowday']
playlist_ids = {'1v1': 10, '2v2' : 11, '3v3': 13, 'Hoops': 27, 'Rumble': 28, 'Dropshot': 29, 'Snowday': 30}
ranks = ['Unranked', 'Bronze I', 'Bronze II', 'Bronze III', 'Silver I', 'Silver II', 'Silver III',
         'Gold I', 'Gold II', 'Gold III', 'Platinum I', 'Platinum II', 'Platinum III',
         'Diamond I', 'Diamond II', 'Diamond III', 'Champion I', 'Champion II', 'Champion III',
         'Grand Champion I', 'Grand Champion II', 'Grand Champion III', 'Supersonic Legend']

def url_index_in_session(url, session):
    for i in range(len(session['recent_searches'])):
        search = session['recent_searches'][i]
        if search['url'] == url:
            return i
    return -1

@app.route('/')
def home():
    form = dict()

    platform = request.args.get('platform', 'epic') if request.args.get('platform', 'epic') != '' else 'epic'
    name = request.args.get('name', False)

    if name is not False:
        response = scraper.get(f'https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform}/{name}/')
    else:
        return render_template('home.html', message='Please enter a valid name.', form=form)

    json = response.json()

    if 'errors' in json:
        return render_template('home.html', message=json['errors'][0]['message'], form=form)

    if 'recent_searches' not in session:
        session['recent_searches'] = []

    form['name'] = name
    form['platform'] = platform

    data = dict()
    data['name'] = json['data']['platformInfo']['platformUserHandle']
    data['platform'] = json['data']['platformInfo']['platformSlug']
    data['goals'] = json['data']['segments'][0]['stats']['goals']['displayValue']
    data['ranks'] = dict()

    recent_url_index = url_index_in_session(request.url, session)

    if recent_url_index == -1:
        if len(session['recent_searches']) >= TOTAL_CACHED_SEARCHES:
            temp = session['recent_searches']
            temp.pop(0)
            session['recent_searches'] = temp

        search = dict()
        search['name'] = data['name']
        search['platform'] = platform
        search['url'] = request.url

        temp = session['recent_searches']
        temp.append(search)
        session['recent_searches'] = temp
    else:
        temp = session['recent_searches']
        search = temp.pop(recent_url_index)
        temp.append(search)
        session['recent_searches'] = temp

    for playlist in playlists:
        for segment in json['data']['segments']:
            if 'attributes' in segment and 'playlistId' in segment['attributes']:
                if segment['attributes']['playlistId'] == playlist_ids[playlist]:
                    data['ranks'][playlist] = dict()
                    data['ranks'][playlist]['tier'] = ranks[segment['stats']['tier']['value']]
                    data['ranks'][playlist]['division'] = segment['stats']['division']['value'] + 1
                    data['ranks'][playlist]['mmr'] = segment['stats']['rating']['value']
                    break

    return render_template('home.html', data=data, form=form)


if __name__ == '__main__':
    app.run()