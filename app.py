from flask import Flask, render_template, request, redirect, url_for
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

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

# REST API endpoints for polling
@app.route('/api/messages/<room_id>', methods=['GET'])
def get_messages(room_id):
    if room_id not in rooms:
        return jsonify([])
    return jsonify(rooms[room_id]['messages'])

@app.route('/api/messages/<room_id>', methods=['POST'])
def post_message(room_id):
    data = request.get_json()
    user = data.get('user', 'Anonymous')
    text = data.get('text', '')
    if room_id in rooms and text:
        message = {'user': user, 'text': text}
        rooms[room_id]['messages'].append(message)
        room_users.setdefault(room_id, set()).add(user)
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/users/<room_id>', methods=['GET'])
def get_users(room_id):
    return jsonify(list(room_users.get(room_id, [])))

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
if __name__ == '__main__':
    app.run(debug=True)
    room_id = data['room_id']
