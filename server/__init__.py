# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 10:56:00 2018

@author: lucas.tostes
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, emit
from random import shuffle
from os.path import exists
from os import makedirs
from datetime import datetime

# attempt a relative import
try:
    from .game import engine
except (ImportError, ValueError):
    from game import engine

app = Flask(__name__, template_folder="../templates", \
                      static_folder="../static")

socketio = SocketIO(app)

GAMES = {}

def get_stats():

    game_json = {}

    if not 'DEFAULT' in GAMES:
        game = engine.GameInfo(default_game_id=True)
        game.standard_player_setup(10)
        game.start_round()

        GAMES['DEFAULT'] = game

    game_json = GAMES['DEFAULT'].round_to_json()

    number_of_players   = len(game_json['players'])
    start_time          = game_json['date_created']
    round               = game_json['round_number']

    return number_of_players, start_time, round

def get_player_word(player_number):

    game_json = GAMES['DEFAULT'].round_to_json()

    return game_json['round_info']['player_info'][player_number-1]['round_word']


def get_word_message(player_number):

    return "That's your word, player #{player_number}.".format(**{"player_number":player_number})


def get_round_message(round):

    return "By the way, this is round {round}.".format(**{"round":round})

# a route where we will display a welcome message via an HTML template
@app.route("/")
def hello():
    message = "You are playing Shakeaspeare in Paradise!"

    number_of_players, start_time, round = get_stats()

    return render_template('index.html', message=message, \
                                         number_of_players=number_of_players, \
                                         start_time=start_time, \
                                         round = round)

# a route where we will display a welcome message via an HTML template
@app.route("/player/<int:player_number>")
def player(player_number):

    player_background_colors    = ['#8749b3',' #ff4d4d', '#ffa600', '#1732ff', '#ff4400', '#eb1f10', '#452302', '#098a00', '#adadad', '#000000', '#ffffff']
    player_text_colors          = ['#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#000000']

    # Purple, Pink, Yellow, Blue, Orange, Red, Brown, Green, Gray, Black, White

    number_of_players, start_time, round = get_stats()

    if (player_number > number_of_players):
        return render_template('player.html', player_number=player_number,
                                              player_word="Oops...",
                                              start_time=start_time,
                                              round=round,
                                              word_message="Seems like this player is not in the game this round ",
                                              round_message="...And this is still round "+str(round),
                                              player_background_colors = player_background_colors,
                                              player_text_colors = player_text_colors)

    player_word = get_player_word(player_number)

    return render_template('player.html', player_number=player_number,
                                          player_word=player_word,
                                          start_time=start_time,
                                          round=round,
                                          word_message=get_word_message(player_number),
                                          round_message=get_round_message(round),
                                          player_background_colors = player_background_colors,
                                          player_text_colors = player_text_colors)

# a route where we will display a welcome message via an HTML template
@app.route("/set/<int:number_of_players>")
def set_for_players(number_of_players):

    game = engine.GameInfo(default_game_id=True)
    game.standard_player_setup(number_of_players)
    game.start_round()

    start_time = GAMES['DEFAULT'].round_to_json()['date_created']

    GAMES['DEFAULT'] = game

    return render_template('index.html', message="Started for " + str(number_of_players) + " players", \
                                         number_of_players=number_of_players, \
                                         start_time=start_time)

@app.route("/newround")
def newround():

    GAMES['DEFAULT'].start_round()

    number_of_players, start_time, round = get_stats()

    return render_template('index.html', message="New round!", \
                                         round=round, \
                                         number_of_players=number_of_players, \
                                         start_time=start_time)

@app.route("/cheatsheet")
def cheatsheet():

    number_of_players, start_time, round = get_stats()

    number_of_players = int(number_of_players)

    players = []

    for player_number in range(1,number_of_players+1):
        player = {}
        player['word'] = get_player_word(player_number)
        player['number'] = player_number

        players.append(player)

    return render_template('cheatsheet.html', message="" + str(number_of_players) + " players game", \
                                              number_of_players=number_of_players, \
                                              start_time=start_time, \
                                              players=players, \
                                              round=round)


# a route where we will display a welcome message via an HTML template
@app.route("/reset")
def reset_rounds():

    game = engine.GameInfo(default_game_id=True)
    game.standard_player_setup(10)
    game.start_round()

    GAMES['DEFAULT'] = game

    number_of_players, start_time, round = get_stats()

    return render_template('index.html', message="Game reset! Please set the first round with the correct num of players", \
                                         number_of_players=10, \
                                         start_time=start_time, \
                                         round=round)

# Socket implementation
@socketio.on('create')
def on_create(data):
    """Create a game lobby"""
    gm = engine.GameInfo()
        #size=data['size'],
        #teams=data['teams'],
        #dictionary=data['dictionary'])
    room = gm.game_id
    GAMES[room] = gm
    join_room(room)
    emit('join_room', {'room': room})

@socketio.on('join')
def on_join(data):
    """Join a game lobby"""
    # username = data['username']
    room = data['room']
    if room in ROOMS:
        # add player and rebroadcast game object
        # rooms[room].add_player(username)
        join_room(room)
        send(ROOMS[room].to_json(), room=room)
    else:
        emit('error', {'error': 'Unable to join room. Room does not exist.'})

@app.route('/socket_test')
def index():
    """Serve the socket test HTML"""
    return render_template('socket_test.html')

# run the application
if __name__ == "__main__":
    socketio.run(app,host= '0.0.0.0',debug=True)
