"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6
For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import os
import xml.etree.ElementTree as etree
import boto3  # wolf_db
import time  # wolf_db

try:
    from urllib.request import urlopen
    from urllib.parse import urlencode
except ImportError:
    # Python2
    from urllib2 import urlopen
    from urllib import urlencode

__version__ = 'v0.1.2'



def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID
    to prevent someone else from configuring a skill that sends requests to
    this function.
    """
    if (event['session']['application']['applicationId'] !=
            os.environ["SKILL_ID"]):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" +
          session_started_request['requestId'] +
          ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "wolfman":
        return ask_wolfram_alpha(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior -----------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Wolfram Alpha. What is your question?"
    # If the user either does not reply to the welcome message or says
    # something that is not understood, they will be prompted again with this
    # text.
    reprompt_text = ("I didn't catch that. Ask a question for Wolfram Alpha.")
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def ask_wolfram_alpha(intent, session):
    client = boto3.resource('dynamodb', region_name='us-east-1')  # wolf_db
    table = client.Table('wolf_db')  # wolf_db create table instance

    session_attributes = {}
    should_end_session = False
    reprompt_text = "I didn't catch that. Care to try again?"
    speech_output = "Try asking a question you would ask Wolfram Alpha."

    api_root = "http://api.wolframalpha.com/v1/spoken?"

    appid = os.environ["appid"]

    query = intent['slots']['response'].get('value')
    if query:

        payload = {
            'appid': appid,
            'i': query
        }

        resp = urlopen(api_root + urlencode(payload))
        tree = resp.read()

        speech_output = "Wolfram Alpha says " + tree

        milli_sec = int(round(time.time() * 1000))

        new_query_response = {
            'time_stamp': milli_sec,
            'wf_query': query,
            'wf_response': tree
        }

        table.put_item(Item=new_query_response)

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Helpers that build all of the responses ---------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }