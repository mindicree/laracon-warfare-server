from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_apscheduler import APScheduler
from random import uniform

config = {
    'FLASK_HOST': '127.0.0.1',
    'FLASK_PORT': '5050',
    'FLASK_DEBUG': True,
    'FLASK_SECRET': 's3cr3t!'
}

app = Flask(__name__)
app.config['SECRET_KEY'] = config['FLASK_SECRET']
CORS(app)
scheduler = APScheduler()
socketio = SocketIO(app, cors_allowed_origins="*")

def calculateAttackExp(level = 1):
    if level == 1:
        return 100
    return int(calculateAttackExp(level - 1)**1.05)

def calculateDefenseExp(level = 1):
    if level == 1:
        return 250
    return int(calculateAttackExp(level - 1)**1.05)

gameState = {
    "packagers": {
        'damage': 0,
        "strength_level": 1,
        "strength_counter": 0,
        "strength_next_level": calculateAttackExp(1),
        "defense_level": 1,
        "defense_counter": 0,
        "defense_next_level": calculateDefenseExp(1),
        "big_damage_counter": 0,
        "victory_points": 0, 
    },
    "composers": {
        'damage': 0,
        "strength_level": 1,
        "strength_counter": 0,
        "strength_next_level": calculateAttackExp(1),
        "defense_level": 1,
        "defense_counter": 0,
        "defense_next_level": calculateDefenseExp(1),
        "big_damage_counter": 0, 
        "victory_points": 0,
    },
}

@socketio.on('connect')
def socket_connect():
    pass

@socketio.on('disconnect')
def socket_disconnect():
    pass

@socketio.on('event_attack')
def attack(json):
    team = json["team"]
    opposer = "composers" if team == "packagers" else "packagers"
    damage = calculateDamage(team, opposer)
    gameState[opposer]["damage"] += damage
    sendGameState()
    print('attack!')
    pass

@socketio.on('event_strengthen')
def strengthen(json):
    team = json["team"]
    gameState[team]["strength_counter"] += 1
    if (gameState[team]["strength_counter"] >= gameState[team]["strength_next_level"]):
        gameState[team]["strength_counter"] = 0
        gameState[team]["strength_level"] += 1
        gameState[team]["strength_next_level"] = calculateAttackExp(gameState[team]["strength_level"])
    sendGameState()
    print('Strengthen!')

@socketio.on('event_defense')
def defend(json):
    team = json["team"]
    gameState[team]["defense_counter"] += 1
    if (gameState[team]["defense_counter"] >= gameState[team]["defense_next_level"]):
        gameState[team]["defense_counter"] = 0
        gameState[team]["defense_level"] += 1
        gameState[team]["defense_next_level"] = calculateDefenseExp(gameState[team]["defense_level"])
    sendGameState()
    print('Build Defense!')

@socketio.on('event_big_damage')
def increase_strength(json):
    team = json["team"]
    opposer = "composers" if team == "packagers" else "packagers"
    gameState[team]["big_damage_counter"] += 1
    if (gameState[team]["big_damage_counter"] >= 1000):
        gameState[team]["big_damage_counter"] = 0
        damage = calculateDamage(team, opposer, 100)
        
    sendGameState()
    print('Big Damage!')

@socketio.on('requestGameState')
def emit_game_state():
    sendGameState()

def calculateDamage(team, opposer, big=1):
    strength = gameState[team]["strength_level"]
    defense = gameState[opposer]["defense_level"]
    damage = int((strength * big) / defense * 100 * uniform(0.85, 1))
    return max(damage, 10)

def sendGameState():
    emit('updateGameState', gameState, broadcast=True)

@scheduler.task('cron', id="victory_point_scorer", minute="*")
def score_victory_points():
    print('Scoring...')
    if gameState["packagers"]["damage"] > gameState["composers"]["damage"]:
        gameState["composers"]["victory_points"] += 1
    elif gameState["packagers"]["damage"] < gameState["composers"]["damage"]:
        gameState["packagers"]["victory_points"] += 1
    sendGameState()

if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    socketio.run(app, host=config['FLASK_HOST'], port=config['FLASK_PORT'], debug=config['FLASK_DEBUG'])