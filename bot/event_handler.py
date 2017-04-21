import json
import logging
import re

logger = logging.getLogger(__name__)


class RtmEventHandler(object):
    def __init__(self, slack_clients, msg_writer):
        self.clients = slack_clients
        self.msg_writer = msg_writer

        users = self.clients.rtm.api_call("users.list")['members']
        user_ids = [ u['id'] for u in users ]
        groups = self.clients.rtm.api_call("groups.list")['groups']
        for g in groups:
            for uid in g['members']:
                if (uid in user_ids):
                    user_ids.remove(uid)
        
        for u in user_ids:
            new_g = self.clients.rtm.api_call("groups.create", name="anonchannel - " + u)
            if new_g['ok'] == True:
                self.clients.rtm.api_call("groups.invite", channel=new_g['id'], user=u)
        
        self.groups = self.clients.rtm.api_call("groups.list")['groups']
    
    def handle(self, event):

        if 'type' in event:
            self._handle_by_type(event['type'], event)

    def _handle_by_type(self, event_type, event):
        # See https://api.slack.com/rtm for a full list of events
        if event_type == 'error':
            # error
            self.msg_writer.write_error(event['channel'], json.dumps(event))
        elif event_type == 'message':
            # message was sent to channel
            self._handle_message(event)
        elif event_type == 'channel_joined':
            # you joined a channel
            #users = self.clients.rtm.api_call("users.list")['members']
            #for u in users:
            #    self.clients.rtm.api_call("im.open",user=u['id'])
            self.clients.rtm.api_call("channels.leave",channel=event['channel'])
            #elif event_type == 'group_joined':
            # you joined a private group
            #self.clients.rtm.api_call("groups.leave",channel=event['channel'])
        else:
            pass

    def _handle_message(self, event):
        # Filter out messages from the bot itself, and from non-users (eg. webhooks)
        if ('user' in event) and (not self.clients.is_message_from_me(event['user'])):

            msg_txt = event['text']

            if self._is_group_message(event['channel']):
                # forward to everyone
                for g in self.groups:
                    for p in self.groups:
                        self.clients.rtm.api_call("chat.postMessage", channel=g['id'], text=p['id'])
                	if event['user'] not in g['members']:
            			self.clients.rtm.api_call("chat.postMessage", channel=g['id'], text=msg_txt)
            #else:
            #    self.clients.rtm.api_call("chat.postMessage", channel="C11TX2B8X", text=event['user'])
    
    def _is_direct_message(self, channel):
        """Check if channel is a direct message channel

        Args:
            channel (str): Channel in which a message was received
        """
        return channel.startswith('D')
    
    def _is_group_message(self, channel):
        """Check if channel is a direct message channel

        Args:
            channel (str): Channel in which a message was received
        """
        return channel.startswith('G')
