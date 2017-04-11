from thread import start_new_thread
from subprocess32 import call
import logging

def shutdown():
    run_command_async("/sbin/poweroff")

def reboot():
    run_command_async("/sbin/reboot")

def update():
    run_command_async("./build.sh")

def test():
    run_command_async("sleep", "3")

def resetsensor():
    run_command_async("/home/pi/reset-sensor")

def error():
    logging.warn("shell error")

def run_command_async(*args):
    def run(*args):
        try:
            result = call(args)
            logging.info("command result:" + str(result))
        except Exception as e:
            logging.error(e.message)
        logging.info("running command finished")

    start_new_thread(run, args)

commands = {
    'rs': shutdown,
    'rr': reboot,
    'ru': update
}

def is_raspberry_command(s):
    """ Check this is a command for the raspberry rather than the sensor. First letter must be an 'r'"""
    if s[0] == 'r':
        command = commands.get(s)
        if callable(command):
            command()
        else:
            logging.warn("command not found: %s" % s)
        return True
    else:
        return False


