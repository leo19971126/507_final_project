import spotipy
import json
import os
import networkx as nx
from spotipy.oauth2 import SpotifyClientCredentials
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

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
    print(tracks)
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
        G.add_node(track['id'], name=track['name'], artist=track['artists'][0]['name'], album=track['album']['name'])
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
            if similarity >= 1:
                G.add_edge(track1['id'], track2['id'], weight=similarity)

    return G

def cluster_graph(G):
    # Cluster the nodes of the graph into different groups based on their similarity
    # Use the KMeans algorithm from sklearn library
    # Convert the graph into a matrix of edge weights
    A = nx.to_numpy_matrix(G)
    # Choose the number of clusters (k) based on some criteria (e.g. elbow method)
    k = 3 # For simplicity, assume k = 3
    # Create a KMeans object with k clusters
    kmeans = KMeans(n_clusters=k)
    # Fit the matrix to the KMeans object
    kmeans.fit(A)
    # Get the labels of each node (which cluster they belong to)
    labels = kmeans.labels_
    # Assign the labels as an attribute to each node in the graph
    for i, node in enumerate(G.nodes()):
        G.nodes[node]['cluster'] = labels[i]
    return G

def recommend_song(G, song_id, same_cluster=True):
    # Recommend another song from the graph based on a given song id and a preference
    # If same_cluster is True, recommend a song from the same cluster as the given song
    # If same_cluster is False, recommend a song from a different cluster than the given song
    # Get the name, artist, album, and cluster of the given song
    name = G.nodes[song_id]['name']
    artist = G.nodes[song_id]['artist']
    album = G.nodes[song_id]['album']
    cluster = G.nodes[song_id]['cluster']
    print(f"You chose {name} by {artist} from {album}.")
    # Get the list of neighbors of the given song (songs that are connected by an edge)
    neighbors = list(G.neighbors(song_id))
    # Filter the neighbors by their cluster attribute
    if same_cluster:
        # Keep only the neighbors that have the same cluster as the given song
        neighbors = [n for n in neighbors if G.nodes[n]['cluster'] == cluster]
        print(f"Here are some songs from the same cluster that you might like:")
    else:
        # Keep only the neighbors that have a different cluster than the given song
        neighbors = [n for n in neighbors if G.nodes[n]['cluster'] != cluster]
        print(f"Here are some songs from a different cluster that you might find interesting:")
    # If there are no neighbors left after filtering, print a message and return None
    if not neighbors:
        print(f"Sorry, there are no songs that match your preference.")
        return None
    # Otherwise, choose a random neighbor from the list and print its name, artist, and album
    import random
    choice = random.choice(neighbors)
    choice_name = G.nodes[choice]['name']
    choice_artist = G.nodes[choice]['artist']
    choice_album = G.nodes[choice]['album']
    print(f"We recommend {choice_name} by {choice_artist} from {choice_album}.")

def visualize_graph(G):
    # Draw the graph
    pos = nx.spring_layout(G)
    nx.draw_networkx(G, with_labels=True)

    # Show the plot
    plt.show()

def get_recommendations(G, artists, songs):
    # Analyze the user's input and generate a playlist of recommended songs using the graph-based algorithm
    playlist = []

    # Traverse the graph starting from the nodes representing the user's preferred songs or artists
    for artist in artists:
        for node in G.nodes(data=True):
            if node[1]['artist'] == artist:
                # Add the node to the playlist
                playlist.append((node[1]['name'], node[1]['artist'], node[1]['album']))
                # Get the neighbors of the node
                neighbors = G.neighbors(node[0])
                # Sort the neighbors by their edge weight and add them to the playlist
                sorted_neighbors = sorted(neighbors, key=lambda x: G[node[0]][x]['weight'], reverse=True)
                for neighbor in sorted_neighbors[:20]:
                    playlist.append((G.nodes[neighbor]['name'], G.nodes[neighbor]['artist'], G.nodes[neighbor]['album']))

    for song in songs:
        for node in G.nodes(data=True):
            if node[1]['name'] == song:
                # Add the node to the playlist
                playlist.append((node[1]['name'], node[1]['artist'], node[1]['album']))
                # Get the neighbors of the node
                neighbors = G.neighbors(node[0])
                # Sort the neighbors by their edge weight and add them to the playlist
                sorted_neighbors = sorted(neighbors, key=lambda x: G[node[0]][x]['weight'], reverse=True)
                for neighbor in sorted_neighbors[:20]:
                    playlist.append((G.nodes[neighbor]['name'], G.nodes[neighbor]['artist'], G.nodes[neighbor]['album']))

    # Remove duplicate songs from the playlist and keep only the top 20 songs
    playlist = list(dict.fromkeys(playlist))[:20]

    return playlist

# Define the main function to take user's preferred genres, artists, and songs as input and return the generated playlist with additional information
def main():
    print('hi')
    genres = ['pop', 'rock']
    artists = ['Taylor Swift']
    songs = ['Death of a Bachelor']
    data = get_data(genres, artists, songs)
    print(get_data(genres, artists, songs))
    g = create_graph(data)
    g = cluster_graph(g)
    # visualize_graph(g)
    playlist = get_recommendations(g, artists, songs)
    # print(recommend_song(g, '3Qm86XLflmIXVm1wcwkgDK', same_cluster=True))
    print('Recommended songs:')
    for song in playlist:
        print(f'{song[0]} by {song[1]} from the Album: {song[2]}')
    # print(playlist)

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