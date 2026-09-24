import os
import sys
import json


def old_parser(text):
    return text.split(",")


def parse(text):
    return json.loads(text)
