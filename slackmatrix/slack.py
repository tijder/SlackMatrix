import time

from slackclient import SlackClient


class Slack:
    bridge = {}
    matrix = None

    def __init__(self, slack_token: str, user_id: str) -> None:
        super().__init__()

        self.sc = SlackClient(slack_token)
        self.user_id = user_id

        # print(self.sc.api_call(
        #     "conversations.list",
        #     types="im"
        # ))

        # print(self.sc.api_call(
        #     "conversations.info",
        #     channel="D6T8YUDUY",
        # ))
        # self.send_message("D6T8YUDUY", "Hello from Python2! :tada:")

    def set_matrix(self, matrix):
        self.matrix = matrix

    def bridge_matrix_room(self, slack_room_id, matrix_room_id):
        self.bridge[slack_room_id] = matrix_room_id

    def send_message(self, room_id: str, text: str):
        self.sc.api_call(
            "chat.postMessage",
            channel=room_id,
            text=text,
            as_user=True
        )

    def __mark_read(self, room_id: str, ts: str):
        self.sc.api_call(
            "im.mark",
            channel=room_id,
            ts=ts
        )

    def start_listening(self):
        if self.sc.rtm_connect(with_team_state=False, reconnect=True):
            while self.sc.server.connected is True:
                for event in self.sc.rtm_read():
                    self.__process_event_in_room(event)
                time.sleep(1)
        else:
            print("Connection Failed")

    def __process_event_in_room(self, event):
        print(event)
        # if event['type'] == "message":
        if event['type'] == "message" and ('user' not in event or event['user'] != self.user_id):
            if 'text' in event and event['channel'] in self.bridge:
                name = "Bot"
                avatar_url = None
                if 'user' in event:
                    user = self.sc.api_call("users.info", user=event['user'])
                    name = user['user']['real_name']
                    avatar_url = user['user']['profile']['image_192']

                self.matrix.send_message(self.bridge[event['channel']], event['text'], name=name, avatar_url=avatar_url)

                if 'ts' in event:
                    self.__mark_read(event['channel'], event['ts'])
