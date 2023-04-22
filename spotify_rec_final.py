import spotipy
import json
import os
import networkx as nx
from spotipy.oauth2 import SpotifyClientCredentials
import networkx as nx
from scipy import spatial
from networkx.readwrite import json_graph

# link to api_key.py file
from client_credential import client_id, client_secret

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_data(genres, artists, songs):
    """
    Get data from Spotify API for a list of genres, artists and songs.

    Parameters
    ----------
    genres : list of str
        The genres to search for tracks.
    artists : list of str
        The artists to search for tracks.
    songs : list of str
        The songs to search for tracks and get recommendations.

    Returns
    -------
    data : list of dict
        The data for each track, containing the track information and the audio features.

    Raises
    ------
    Exception
        If there is an error while searching or getting audio features from Spotify API.
    """
    # Generate an acronym from the user's input genres, artist names, and song names
    acronym = ''.join([word[0].upper() for word in ' '.join(genres + artists + songs).split()])
    # Use the acronym as the cache file name
    cache_file = f'{acronym}_data.json'
    if os.path.exists(cache_file):
        # Load data from cache file
        with open(cache_file, 'r') as f:
            data = json.load(f)
        return data

    # Gather data on popular songs and artists that match the user's preferences
    tracks = []
    for genre in genres:
        results = sp.search(q='genre:' + genre, type='track', limit=5)
        tracks.extend(results['tracks']['items'])
    for artist in artists:
        results = sp.search(q='artist:' + artist, type='track', limit=20)
        tracks.extend(results['tracks']['items'])
    for song in songs:
        results = sp.search(q='track:' + song, type='track', limit=1)
        if results['tracks']['items']:
            track_id = results['tracks']['items'][0]['id']
            # Get recommendations based on the input song
            results = sp.recommendations(seed_tracks=[track_id], limit=20)
            tracks.extend(results['tracks'])

    # Gather audio features for these songs
    track_ids = [track['id'] for track in tracks]
    audio_features = sp.audio_features(track_ids)

    # Split track_ids into batches of 100 to prevent error or return incomplete results
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        audio_features.extend(sp.audio_features(batch))

    # Combine track and audio feature data
    data = []
    for i in range(len(tracks)):
        track = tracks[i]
        # Exclude the available_markets field from the track data
        track.pop('available_markets', None)
        track['album'].pop('available_markets', None)
        data.append({'track': track, 'audio_features': audio_features[i]})

    # Save data to cache file
    with open(cache_file, 'w') as f:
        json.dump(data, f)

    return data

def create_graph(data):
    """
    Create a graph to represent the relationships between different songs based on their audio features.

    Parameters
    ----------
    data : list of dict
        The data for each song, containing the track information and the audio features.

    Returns
    -------
    G : networkx.Graph
        The graph object with nodes representing songs and edges representing similarity.

    Notes
    -----
    The similarity between two songs is calculated based on their audio features, such as key, mode, tempo, energy, etc.
    The similarity score is a sum of cosine similarity for continuous features and exact match for categorical features.
    An edge is added between two nodes if their similarity score is above a certain threshold (5 in this case).
    """

    # Create a graph to represent the relationships between different songs
    G = nx.Graph()

    # Add nodes to the graph representing each song
    for item in data:
        track = item['track']
        G.add_node(track['id'], name=track['name'], artist=track['artists'][0]['name'], album=track['album']['name'], url=track['external_urls']['spotify'])

    # Define a list of audio features to compare
    audio_features = ['key', 'mode', 'tempo', 'energy', 'danceability', 'acousticness', 'instrumentalness', 'loudness']

    # Connect nodes based on their similarity in terms of audio features
    for i in range(len(data)):
        for j in range(i+1, len(data)):
            track1 = data[i]['track']
            track2 = data[j]['track']
            audio_features1 = data[i]['audio_features']
            audio_features2 = data[j]['audio_features']

            # Calculate similarity score based on audio features
            similarity = 0
            for feature in audio_features:
                # Use cosine similarity for continuous features and exact match for categorical features
                if feature in ['key', 'mode']:
                    if audio_features1[feature] == audio_features2[feature]:
                        similarity += 1
                else:
                    similarity += 1 - spatial.distance.cosine([audio_features1[feature]], [audio_features2[feature]])

            # Add an edge between the nodes if their similarity score is above a certain threshold
            if similarity >= 4:
                G.add_edge(track1['id'], track2['id'], weight=similarity)

    return G

def get_recommendations(G, artists, songs):

    """
    Analyze the user's input and generate a playlist of recommended songs using the graph-based algorithm.

    Parameters
    ----------
    G : networkx.Graph
        The graph object with nodes representing songs and edges representing similarity.
    artists : list of str
        The artists that the user likes or wants to listen to.
    songs : list of str
        The songs that the user likes or wants to listen to.

    Returns
    -------
    playlist : list of tuple
        The playlist of recommended songs, each tuple containing the track name, artist name, album name and Spotify URL.

    Notes
    -----
    The algorithm works as follows:
    - For each artist in the input, find the nodes in the graph that match the artist name and add them to the playlist.
    - For each node added to the playlist, find its most similar neighbors in the graph and add them to the playlist as well.
    - For each song in the input, find the nodes in the graph that match the song name and add them to the playlist.
    - For each node added to the playlist, find its most similar neighbors in the graph and add them to the playlist as well.
    - Remove any duplicates from the playlist and limit it to 15 songs.
    - Ensure that no more than 3 songs from the same artist are in the playlist.
    - Ensure that no songs from the same artist and album are in the playlist.
    """

    playlist = []

    # Define a limit for the number of songs from the same artist
    artist_limit = 3

    # Create a dictionary to keep track of how many songs from each artist are in the playlist
    artist_count = {}

    # Create a set to keep track of the songs that are already in the playlist
    song_set = set()

    def add_to_playlist(node):
        """
        Add a node to the playlist if it meets the criteria.

        Parameters
        ----------
        node : tuple
            The node to be added, containing the node id and the node attributes.

        Notes
        -----
        The criteria for adding a node to the playlist are:
        - The artist limit is not exceeded for the node's artist.
        - The song is not already in the playlist.
        - The song has a Spotify URL or an empty string as a placeholder.
        """

        # Get the artist name from the node
        artist = node[1]['artist']
        # Check if the artist limit is not exceeded
        if artist_count.get(artist, 0) < artist_limit:
            # Check if the node has the url field
            if 'url' in node[1]:
                # Get the Spotify URL for the track
                url = node[1]['url']
            else:
                # Use an empty string as the URL
                url = ''
            # Create a tuple with the song name, artist name and album name
            song = (node[1]['name'], artist, node[1]['album'])
            # Check if the song is already in the playlist or not
            if song not in song_set:
                # Add the track name, artist name, album name and URL to the playlist
                playlist.append(song + (url,))
                # Update the artist count and the song set
                artist_count[artist] = artist_count.get(artist, 0) + 1
                song_set.add(song)

    def add_neighbors_to_playlist(node):
        """
        Add the most similar neighbors of a node to the playlist.

        Parameters
        ----------
        node : tuple
            The node whose neighbors are to be added, containing the node id and the node attributes.

        Notes
        -----
        The similarity between two nodes is determined by the weight of the edge connecting them in the graph.
        The neighbors are sorted by their similarity in descending order and only the top 20 are added to the playlist.
        """
        # Get the neighbors of the node in the graph
        neighbors = G.neighbors(node[0])
        # Sort the neighbors by their similarity weight in descending order
        sorted_neighbors = sorted(neighbors, key=lambda x: G[node[0]][x]['weight'], reverse=True)
        # Loop through the top 20 neighbors and add them to the playlist
        for neighbor in sorted_neighbors[:20]:
            add_to_playlist((neighbor, G.nodes[neighbor]))

    # Loop through the artists in the input and find matching nodes in the graph
    for artist in artists:
        for node in G.nodes(data=True):
            if node[1]['artist'].lower() == artist.lower():
                # Add the node to the playlist
                add_to_playlist(node)
                # Add its neighbors to the playlist as well
                add_neighbors_to_playlist(node)

    # Loop through the songs in the input and find matching nodes in the graph
    for song in songs:
        for node in G.nodes(data=True):
            if node[1]['name'].lower() == song.lower():
                # Add the node to the playlist
                add_to_playlist(node)
                # Add its neighbors to the playlist as well
                add_neighbors_to_playlist(node)

    # Remove any duplicates from the playlist and limit it to 15 songs
    playlist = list(dict.fromkeys(playlist))[:15]
    return playlist


# Define the main function to take user's preferred genres, artists, and songs as input and return the generated playlist with additional information
def main():

    print('\nWelcome to the Spotify Playlist Generator! Please enter your preferred genres, artists, and songs to get started. \nFeel free to enter a maximum of 3 genres, 2 artists, and 2 songs.')

    while True:
        # Ask user for input
        genres = input("\nPlease enter a genre (separate multiple genres by comma): ").strip().split(",")
        artists = input("\nPlease enter an artist (separate multiple artists by comma): ").strip().split(",")
        songs = input("\nPlease enter a song (separate multiple songs by comma): ").strip().split(",")

        # Process user input
        data = get_data(genres, artists, songs)
        G = create_graph(data)
        recommendations = get_recommendations(G, artists, songs)

        # Print recommendations
        print("\nHere are your recommended songs:")
        for i, item in enumerate(recommendations, start=1):
            print(f"\n{i}. {item[0]} by {item[1]} from {item[2]} \nSpotify URL: {item[3]}")

        # Convert your graph to a dictionary of nodes and links
        data = json_graph.node_link_data(G)
        with open('graph.json', 'w') as f:
            json.dump(data, f)

        # Ask user if they want another recommendation
        again = input("\nWould you like another list of recommendations? (yes/no): ").strip().lower()
        if again != "yes":
            break

    print('\nThank you for using the Spotify Playlist Generator! \nHope you enjoy your playlist! \nHappy listening!')

#
# The following two-line "magic sequence" must be the last thing in
# your file.  After you write the main() function, this line it will
# cause the program to automatically run the recommended songs when you run it.
#
if __name__ == '__main__':
    main()