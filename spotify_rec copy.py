import spotipy
import json
import os
import networkx as nx
from spotipy.oauth2 import SpotifyClientCredentials
import networkx as nx
import matplotlib.pyplot as plt


# link to api_key.py file
from client_credential import client_id, client_secret

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_data(genres, artists, songs):
    # Check for cache file
    cache_file = (f'{artists}_data.json')
    if os.path.exists(cache_file):
        # Load data from cache file
        with open(cache_file, 'r') as f:
            data = json.load(f)
        return data

    # Gather data on popular songs and artists that match the user's preferences
    tracks = []
    for genre in genres:
        results = sp.search(q='genre:' + genre, type='track')
        tracks.extend(results['tracks']['items'])
    for artist in artists:
        results = sp.search(q='artist:' + artist, type='track')
        tracks.extend(results['tracks']['items'])
    for song in songs:
        results = sp.search(q='track:' + song, type='track')
        tracks.extend(results['tracks']['items'])

    # Gather audio features for these songs
    track_ids = [track['id'] for track in tracks]
    audio_features = sp.audio_features(track_ids)

    # Combine track and audio feature data
    data = []
    for i in range(len(tracks)):
        data.append({'track': tracks[i], 'audio_features': audio_features[i]})

    # Save data to cache file
    with open(cache_file, 'w') as f:
        json.dump(data, f)

    return data

def create_graph(data):
    # Create a graph to represent the relationships between different songs
    G = nx.Graph()

    # Add nodes to the graph representing each song
    for item in data:
        track = item['track']
        G.add_node(track['id'], name=track['name'], artist=track['artists'][0]['name'])

    # Connect nodes based on their similarity in terms of audio features
    for i in range(len(data)):
        for j in range(i+1, len(data)):
            track1 = data[i]['track']
            track2 = data[j]['track']
            audio_features1 = data[i]['audio_features']
            audio_features2 = data[j]['audio_features']

            # Calculate similarity score based on audio features
            similarity = 0
            if audio_features1['key'] == audio_features2['key']:
                similarity += 1
            if audio_features1['mode'] == audio_features2['mode']:
                similarity += 1
            if abs(audio_features1['tempo'] - audio_features2['tempo']) < 5:
                similarity += 1

            # Add an edge between the nodes if their similarity score is above a certain threshold
            if similarity >= 2:
                G.add_edge(track1['id'], track2['id'], weight=similarity)

    return G

def get_recommendations(G, artists, songs):
    # Analyze the user's input and generate a playlist of recommended songs using the graph-based algorithm
    playlist = []

    # Traverse the graph starting from the nodes representing the user's preferred songs or artists
    for artist in artists:
        for node in G.nodes(data=True):
            if node[1]['artist'] == artist:
                neighbors = G.neighbors(node[0])
                for neighbor in neighbors:
                    playlist.append(G.nodes[neighbor]['name'])

    for song in songs:
        for node in G.nodes(data=True):
            if node[1]['name'] == song:
                neighbors = G.neighbors(node[0])
                for neighbor in neighbors:
                    playlist.append(G.nodes[neighbor]['name'])

    return playlist

# Define the main function to take user's preferred genres, artists, and songs as input and return the generated playlist with additional information
def main():
    print('hi')
    genres = ['pop', 'rock']
    artists = ['Taylor Swift']
    songs = ['Death of a Bachelor']
    data = get_data(genres, artists, songs)
    g = create_graph(data)
    # visualize_graph(g)
    playlist = get_recommendations(g, artists, songs)
    print(playlist)
    # results = gather_data('Radiohead', 'Creep')
    # print(results[0]['id'])
    # print(create_graph1(client_id, client_secret))
    # print(results)
    # print(gather_audio_features([results[0]['id']]))
    # print(create_graph(results, gather_audio_features([results[0]['id']])))
    # print(generate_playlist(create_graph(results, gather_audio_features([results[0]['id']]))))
#     genres = input('Enter your preferred genres (comma-separated): ')
#     artists = input('Enter your preferred artists (comma-separated): ')
#     songs = input('Enter your preferred songs (comma-separated): ')
#     tracks = gather_data(genres, artists, songs)
#     track_ids = [track['id'] for track in tracks]
#     features = gather_audio_features(track_ids)
#     graph = create_graph(tracks, features)
#     playlist = generate_playlist(graph)
#     feedback = get_user_feedback(playlist)
#     while 's' in feedback:
#         playlist = generate_playlist(graph)
#         feedback = get_user_feedback(playlist)
#     print('Playlist generated successfully!')
#     for i, song in enumerate(playlist):
#         if feedback[i] == 'y':
#             print(f"{i+1}. {song['name']} - {song['artist']} ({song['album']} - {song['release_year']})")

#
# The following two-line "magic sequence" must be the last thing in
# your file.  After you write the main() function, this line it will
# cause the program to automatically play 20 Questions when you run
# it.
#
if __name__ == '__main__':
    main()

# def generate_playlist(genres, artists, songs):
#     """
#     Generates a playlist of recommended songs based on the user's input.

#     Parameters
#     ----------
#     genres : list of str
#         The user's preferred genres.
#     artists : list of str
#         The user's preferred artists.
#     songs : list of str
#         The user's preferred songs.

#     Returns
#     -------
#     list of dict
#         A list of recommended songs, where each song is represented as a dictionary containing information such as the song's name, artist, album, and release year.
#     """

#     # Gather data on popular songs and artists using the Spotify API
#     popular_songs = sp.search(q='genre:' + ' OR genre:'.join(genres), type='track', limit=50)['tracks']['items']
#     popular_artists = sp.search(q='artist:' + ' OR artist:'.join(artists), type='artist', limit=50)['artists']['items']

#     # Gather audio features for the popular songs
#     audio_features = sp.audio_features([song['id'] for song in popular_songs])

#     # TODO: Implement a graph-based algorithm to represent the relationships between different songs, artists, and genres

#     # TODO: Analyze the user's input and generate the most appropriate playlist for their preferences

#     # TODO: Allow the user to provide feedback on the recommended songs to refine future recommendations

#     # TODO: Return the generated playlist with additional information such as the artist’s name, album name, and release year of each song

#     return []

# # Example usage
# genres = ['rock', 'pop']
# artists = ['The Beatles', 'Queen']
# songs = ['Let it Be', 'Bohemian Rhapsody']
# playlist = generate_playlist(genres, artists, songs)
# print(playlist)