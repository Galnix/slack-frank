import os
import time
from slackclient import SlackClient
# Plugins
from plugins import points
from plugins import meme

# Plugin handlers
plugin_handlers = [points.handle, 
                   meme.random_meme, 
                   meme.create_meme_from_last_text,
                   meme.request_meme]

# Slack token
BOT_TOKEN = os.environ['FRANK_SLACK_CLIENT_KEY']

# Frank's ID 
BOT_ID = 'U5BGCL405'

# Constants
AT_BOT = "<@" + BOT_ID + ">"

# Initialize slack
slack_client = SlackClient(BOT_TOKEN)

def handle_plugins(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    
    for handle in plugin_handlers:
        response = handle(command, channel, user)
        if response != "":
            slack_client.api_call("chat.postMessage", channel=channel,
                                  text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None when the bot is the 
        user that sent a message.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and 'user' in output and BOT_ID not in output['user']:
                # return text if frank isn't the sender
                return output['text'].strip(), \
                       output['channel'], \
                       output['user']
    return None, None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    while True:
        try:
            if slack_client.rtm_connect():
                print("Frank connected and running!")
                while True:
                    command, channel, user = parse_slack_output(slack_client.rtm_read())
                    if command and channel:
                        handle_plugins(command, channel, user)
                    time.sleep(READ_WEBSOCKET_DELAY)
            else:
                print("Connection failed. Invalid Slack token or bot ID?")
        except:
            print("Retrying connection.")
            