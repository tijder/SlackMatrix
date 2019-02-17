import json

from slack import Slack
from matrix import Matrix
import threading

with open('config.json', 'r') as jf:
    config: json = json.load(jf)
    print(config)

# matrix info
matrix_token = config['matrix_token']
matrix_user_id = config['matrix_user_id']
matrix_http_server = config['matrix_http_server']

# slack info
slack_token = config['slack_token']
slack_user_id = config['slack_user_id']

# create objects
matrix = Matrix(matrix_user_id, matrix_http_server, matrix_token)
slack = Slack(slack_token, slack_user_id)

# create bridges
slack.set_matrix(matrix)
matrix.set_slack(slack)

for room in config['rooms']:
    print("Bridge room " + room['matrix_room_id'] + " en " + room['slack_room_id'])
    slack.bridge_matrix_room(room['slack_room_id'], room['matrix_room_id'])
    matrix.bridge_slack_room(room['matrix_room_id'], room['slack_room_id'])

threads = []

thread_slack = threading.Thread(target=slack.start_listening)
thread_slack.daemon = True
thread_slack.start()

thread_matrix = threading.Thread(target=matrix.start_listening)
thread_matrix.daemon = True
thread_matrix.start()

threads.append(thread_slack)
threads.append(thread_matrix)

for t in threads:
    t.join()
print("Exiting Main Thread")
