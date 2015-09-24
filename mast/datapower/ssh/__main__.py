# -*- coding: utf-8 -*-
from mast.datapower.datapower import Environment
from mast.cli import Cli
import sys
import os

try:
    import readline
except ImportError as e:
    import pyreadline as readline  # lint:ok
import atexit

histfile = os.path.join(os.path.expanduser("~"), '.mast_ssh_history')
try:
    readline.read_history_file(histfile)
except IOError:
    pass
atexit.register(readline.write_history_file, histfile)


class Input(object):
    """This is a class representing the ssh command prompt. This is a
    very simple CLI. It has a queue (python list) named commands which
    can be added to. If next() is called and this list is empty then
    the user is prompted for the next command"""
    def __init__(self, prompt):
        """Initialization method"""
        self.commands = []
        self.prompt = prompt

    def send(self, command):
        """Adds a command to the queue (the python list) commands"""
        self.commands.append(command)

    def next(self):  # lint:ok
        """This is provided so that this object can function as an iterator."""
        try:
            return self.commands.pop(0)
        except IndexError:  # lint:ok
            return raw_input(self.prompt)

    def __iter__(self):
        """return self as an iterator"""
        return self


def initialize_appliances(env, domain='default'):
    """This initiates an ssh session, extracts the prompt and
    displays the initial output."""
    responses = []
    for appliance in env.appliances:
        responses.append(appliance.ssh_connect(domain=domain))
    output = format_output(responses, env)
    prompt = output.splitlines()[-1:][0] + ' '
    output = '\n'.join(output.splitlines()[:-1]) + '\n'
    display_output(output)
    return prompt


def issue_command(command, env, timeout=60):
    """This method issues a command to the DataPower's CLI."""
    responses = []
    for appliance in env.appliances:
        resp = appliance.ssh_issue_command(command)
        responses.append(resp)
    return responses


def compare(array):
    """Return True if all responses from the DataPowers are the same,
    False otherwise."""
    return array.count(array[0]) == len(array)


def format_output(array, env):
    """Format the output based on the output of compare(array). If all of
    the appliances responded with the same output, then it will be printed
    only once (This is to make it appear as if you are speaking to one
    appliance). Otherwise, if any of the output is different then every
    response is printed individually prepended wiht the appliance's name/ip."""
    seperator = '\n\n{}\n----\n\n'
    if compare(array):
        return array[0]
    response = ''
    for index, appliance in enumerate(env.appliances):
        response += seperator.format(appliance.hostname) + array[index]
    return response + '\n\n> '


def display_output(string):
    """This outputs string to stdout and immediately flushes stdout. This is
    used to prevent the print statment from printing a newline each time it
    is invoked."""
    sys.stdout.write(string)
    sys.stdout.flush()


def main(appliances=[], credentials=[], domain="default", input_file=""):
    """Main program loop. Ask user for input, execute the command..."""
    env = Environment(appliances, credentials)
    prompt = initialize_appliances(env, domain)
    global _input
    _input = Input(prompt)
    if input_file:
        if not os.path.exists(input_file) and os.path.isfile(input_file):
            print "input_file must be a file containing cli commands to issue"
            sys.exit(-1)
        with open(input_file, "r") as fin:
            for command in fin:
                output = issue_command(command, env)
                output = format_output(output, env)
                prompt = output.splitlines()[-1:][0] + ' '
                _input.prompt = prompt
                output = '\n'.join(output.splitlines()[:-1]) + '\n'
                display_output(output)
                if ('Goodbye' in prompt) or ('Goodbye' in output):
                    print('Goodbye')
                    sys.exit(0)
    for command in _input:
        output = issue_command(command, env)
        output = format_output(output, env)
        prompt = output.splitlines()[-1:][0] + ' '
        _input.prompt = prompt
        output = '\n'.join(output.splitlines()[:-1]) + '\n'
        display_output(output)
        if ('Goodbye' in prompt) or ('Goodbye' in output):
            print('Goodbye')
            break
    raise SystemExit


if __name__ == '__main__':
    try:
        cli = Cli(main=main)
        cli.run()
    except Exception, e:
        # generic try...except just for future use
        raise
