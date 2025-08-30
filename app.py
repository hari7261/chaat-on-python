from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}
room_users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_room', methods=['POST'])
def create_room():
    room_name = request.form['room_name']
    room_id = str(uuid.uuid4())[:8]
    rooms[room_id] = {'name': room_name, 'messages': []}
    room_users[room_id] = set()
    return redirect(url_for('chat_room', room_id=room_id))

@app.route('/join_room', methods=['POST'])
def join_room_route():
    room_id = request.form['room_id']
    if room_id in rooms:
        return redirect(url_for('chat_room', room_id=room_id))
    return render_template('index.html', error='Room ID not found.')

@app.route('/room/<room_id>')
def chat_room(room_id):
    if room_id not in rooms:
        return redirect(url_for('index'))
    room = rooms[room_id]
    users = list(room_users.get(room_id, []))
    return render_template('chat.html', room_id=room_id, room_name=room['name'], messages=room['messages'], users=users)

@socketio.on('send_message')
def handle_message(data):
    room_id = data['room_id']
    user = data['user']
    message = {'user': user, 'text': data['text']}
    rooms[room_id]['messages'].append(message)
    send(message, room=room_id)

@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    user = data['user']
    join_room(room_id)
    room_users.setdefault(room_id, set()).add(user)
    # Broadcast updated user list
    socketio.emit('user_list', list(room_users[room_id]), room=room_id)
@socketio.on('leave')
def on_leave(data):
    room_id = data['room_id']
    user = data['user']
    leave_room(room_id)
    if room_id in room_users and user in room_users[room_id]:
        room_users[room_id].remove(user)
        socketio.emit('user_list', list(room_users[room_id]), room=room_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)
