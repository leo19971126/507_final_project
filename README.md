# 507_final_project

#Spotify Song Recommendation
This program recommends songs based on user input genres, artists, and songs using the Spotify API. The program uses the user input to gather data on popular songs and artists that match the user's preferences. Then it gathers audio features for these songs and creates a graph to represent the relationships between different songs. The program connects nodes based on their similarity in terms of audio features.

##Prerequisites
The following Python packages are required for this program to run:

spotipy
json
os
networkx
scipy
The spotipy package can be installed using pip:
pip install spotipy
The remaining packages can also be installed using pip:

##Getting Started
To use this program, follow these steps:

- Clone or download the repository from GitHub.
- Create a Spotify developer account and create a new project to get a client ID and client secret. You can come to this website (https://developer.spotify.com/) to create a new project. You can access it through this steps:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and log in with your Spotify account.
2. Click on the `CREATE AN APP` button and fill in the required information.
3. Once your app is created, you will be provided with a `Client ID` and `Client Secret`.
4. Use these credentials to authenticate your requests to the Spotify API.

- Create a new file named client_credential.py in the same directory as recommendation.py. Add the following code to the file, replacing YOUR_CLIENT_ID and YOUR_CLIENT_SECRET with your own values:

client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'

Open a terminal or command prompt and navigate to the directory containing recommendation.py.
Run the program using the following command:
python recommendation.py

Follow the prompts to enter your preferred genres, artists, and songs.
The program will recommend 15 songs based on your input.

###Notes:
- The program caches data to speed up subsequent runs. Cached data is saved to a JSON file named <acronym>_data.json, where <acronym> is an acronym generated from the user's input genres, artists, and songs.
- The program uses the cosine similarity measure to compare audio features. The audio features used are: key, mode, tempo, energy, danceability, acousticness, instrumentalness, and loudness.
- The program connects nodes in the graph if their similarity score is above a certain threshold (0.8 by default). You can adjust the threshold by changing the value of the similarity_threshold variable in the create_graph function.

##Data Structure
###Graphs:
- This program uses a graph data structure to represent the relationships between different songs based on their audio features. The graph is created using the NetworkX library in Python, and nodes are added to the graph to represent each song. The edges between nodes are added based on the similarity between the audio features of the corresponding songs.

- The audio features used for comparison include key, mode, tempo, energy, danceability, acousticness, instrumentalness, and loudness. The similarity score between two songs is calculated using cosine similarity for continuous features and exact match for categorical features.

- This graph data structure is created using the node-link format and used to find a path between two songs that maximizes the similarity between the songs on the path. The program takes as input a list of genres, artist names, and song names, and returns a list of recommended songs based on the input. The output is sorted by the similarity score of each recommended song to the input songs.