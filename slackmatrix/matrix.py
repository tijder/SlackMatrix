import json
import os
from urllib import request
from urllib.request import Request, urlopen

from matrix_client.client import MatrixClient
from matrix_client.room import Room


class Matrix:
    _bridge = {}
    _slack = None

    _cache = {}
    _cache_file = 'matrix_cache.json'

    def __init__(self, user_id: str, http_matrix_server: str, token: str) -> None:
        super().__init__()
        self.user_id = user_id
        self._client = MatrixClient(http_matrix_server, token=token, user_id=user_id)
        self.__load_cache()

    def __load_cache(self):
        if os.path.isfile(self._cache_file):
            with open(self._cache_file, 'r') as jsf:
                self._cache: json = json.load(jsf)
        if 'rooms' not in self._cache:
            self._cache['rooms'] = {}
        if 'uploaded_avatars' not in self._cache:
            self._cache['uploaded_avatars'] = {}

    def __save_cache(self):
        with open(self._cache_file, 'w') as file:
            file.write(json.dumps(self._cache))

    def set_slack(self, slack):
        self._slack = slack

    def bridge_slack_room(self, matrix_room_id, slack_room_id):
        self._bridge[matrix_room_id] = slack_room_id

    def send_message(self, room_id: str, text: str, name: str = None, avatar_url: str = None, file_url: str = None, file_name: str = None, file_mimetype: str = None, file_authorization: str = None):
        room = Room(self._client, room_id)
        current_avatar_url = None
        current_name = None
        avatar_uri = None
        if room_id in self._cache['rooms']:
            current_name = self._cache['rooms'][room_id]['name']
            current_avatar_url = self._cache['rooms'][room_id]['avatar_url']
        else:
            self._cache['rooms'][room_id] = {}
        if avatar_url is not None and avatar_url != current_avatar_url:
            if avatar_url in self._cache['uploaded_avatars']:
                avatar_uri = self._cache['uploaded_avatars'][avatar_url]
                print("Use cache avatar for an user " + avatar_uri + " (" + avatar_url + ")")
            else:
                avatar_content = request.urlopen(avatar_url).read()
                avatar_uri = self._client.upload(avatar_content, 'image/png')
                self._cache['uploaded_avatars'][avatar_url] = avatar_uri
                print("Uploaded a new avatar for an user " + avatar_uri + " (" + avatar_url + ")")
        if (name is not None and name is not current_name) or avatar_uri is not None:
            room.set_user_profile(displayname=name, avatar_url=avatar_uri)
            self._cache['rooms'][room_id]['name'] = name
            self._cache['rooms'][room_id]['avatar_url'] = avatar_url
            self.__save_cache()
        if file_url is not None and file_mimetype is not None and file_name is not None:
            rq = Request(file_url)
            rq.add_header('Authorization', file_authorization)
            file_content = urlopen(rq).read()
            file_uri = self._client.upload(file_content, file_mimetype)
            if file_mimetype in ['image/png', 'image/jpeg']:
                room.send_image(file_uri, file_name)
            else:
                room.send_file(file_uri, file_name)
        if text is not None:
            room.send_text(text)

    def start_listening(self):
        self._client.add_listener(self.__on_event)
        # room.add_listener(on_message)
        # client.add_listener(on_message)
        self._client.start_listener_thread()

    def __on_event(self, event):
        print(event)
        if event['type'] == "m.room.message" and event['sender'] != self.user_id and event['room_id'] in self._bridge:
            if event['content']['msgtype'] == "m.text":
                self._slack.send_message(self._bridge[event['room_id']], event['content']['body'])

            if event['content']['msgtype'] in ["m.image", 'm.file']:
                image_url = self._client.api.get_download_url(event['content']['url'])
                self._slack.send_file(self._bridge[event['room_id']], file_url=image_url, file_title=event['content']['body'])
