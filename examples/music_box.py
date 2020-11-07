#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repeat a sequence using the fluidsynth sequencer.

The tempo can be configured with a program argument.

Program based on the "music box" example from the fluidsynth documentation
(http://fluidsynth.sourceforge.net/api/index.html#Sequencer), but
with a different and more recognizable sequence.
"""


# PSL imports
import argparse
from ctypes import CFUNCTYPE, c_uint, c_void_p
import time

# pyfluidsynth3 imports
from pyfluidsynth3 import fluidaudiodriver, fluidevent, fluidhandle, \
    fluidsequencer, fluidsettings, fluidsynth, utility

# ----------------------------------------------------------------------------
#     Global variables
# ----------------------------------------------------------------------------

ARG = None  # program arguments

TPB = 240  # tick per beats = constant by convention in music_box.py
DEFAULT_BPM = 120
BPM_CHANGE_STEP = 10  # by default, bpm will change by steps of 10

UPDATE_BPM = None

HANDLE = None
SYNTH = None
ADRIVER = None
SEQUENCER = None
SYNTH_SEQ_ID = None
MY_SEQ_ID = 0
SEQ_START = 0
SEQ_DURATION = 4 * TPB  # 4 beats in the sequence


# ----------------------------------------------------------------------------
#     Synth
# ----------------------------------------------------------------------------

def create_synth():
    global HANDLE
    global SYNTH
    global ADRIVER
    global SEQUENCER
    global SYNTH_SEQ_ID
    global MY_SEQ_ID
    global SEQ_DURATION

    HANDLE = fluidhandle.FluidHandle()

    settings = fluidsettings.FluidSettings(HANDLE)
    settings['synth.gain'] = 0.2
    settings['synth.reverb.active'] = 'yes'
    settings['synth.chorus.active'] = 'no'
    SYNTH = fluidsynth.FluidSynth(HANDLE, settings)
    settings['audio.driver'] = 'alsa'
    ADRIVER = fluidaudiodriver.FluidAudioDriver(HANDLE, SYNTH, settings)

    SEQUENCER = fluidsequencer.FluidSequencer(HANDLE)
    # rem: the demo C code calls 'new_fluid_sequencer2(0)' while
    # the pyfluidsynth3 code calls new_fluid_sequencer()
    SEQUENCER.ticks_per_beat = TPB
    SEQUENCER.beats_per_minute = DEFAULT_BPM

    # register synth as first destination
    (SYNTH_SEQ_ID, name) = SEQUENCER.add_synth(SYNTH)

    # register myself as second destination
    MY_SEQ_ID = HANDLE.fluid_sequencer_register_client(
        SEQUENCER.seq, utility.fluidstring('me'), seq_callback, None)


def delete_synth():
    global SEQUENCER, ADRIVER, SYNTH

    # The following line is needed at least to avoid that seq_callback() gets called after the
    # sequencer is deleted:
    HANDLE.fluid_sequencer_unregister_client(SEQUENCER.seq, MY_SEQ_ID)

    del SEQUENCER
    del ADRIVER
    del SYNTH


def load_soundfont():
    soundfont = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
    SYNTH.load_soundfont(soundfont)


def send_noteon(channel, key, date):
    event = fluidevent.FluidEvent(HANDLE)
    event.source = -1
    event.dest = SYNTH_SEQ_ID
    event.noteon(channel, key, 127)
    SEQUENCER.send(event, int(date), absolute=True)


# ----------------------------------------------------------------------------
#     Sequencer
# ----------------------------------------------------------------------------

def schedule_next_callback():
    # I want to be called back before the end of the next sequence
    callback_date = int(SEQ_START + SEQ_DURATION / 2)
    event = fluidevent.FluidEvent(HANDLE)
    event.source = -1
    event.dest = MY_SEQ_ID
    event.timer()
    SEQUENCER.send(event, callback_date, absolute=True)


def schedule_next_sequence():
    """
    Notes:
      Called more or less before each sequence start
    """
    global SEQ_START

    # the sequence to play:

    # - the bass line (in ABC format: |: C2 G,2 :|)
    send_noteon(0, 60, SEQ_START)
    send_noteon(0, 55, SEQ_START + 2 * TPB)

    # - the melody (in ABC format: |: c e g e :|)
    send_noteon(1, 72, SEQ_START)
    send_noteon(1, 76, SEQ_START + TPB)
    send_noteon(1, 79, SEQ_START + 2 * TPB)
    send_noteon(1, 76, SEQ_START + 3 * TPB)

    # so that we are called back early enough to schedule the next sequence
    schedule_next_callback()

    # the next sequence start date
    SEQ_START = SEQ_START + SEQ_DURATION


def py_seq_callback(time, event, seq, data):
    schedule_next_sequence()


FLUID_EVENT_CALLBACK = CFUNCTYPE(None, c_uint, c_void_p, c_void_p, c_void_p)
# https://docs.python.org/3/library/ctypes.html#callback-functions
# CFUNCTYPE 1st arg = return type; other args: params

seq_callback = FLUID_EVENT_CALLBACK(py_seq_callback)


# ----------------------------------------------------------------------------
#     Main
# ----------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug',
                        help='display debug messages',
                        action='store_true')
    parser.add_argument('-b', '--bpm', help='set beats per minute', type=int)
    args = parser.parse_args()
    return args


def main():
    global SEQ_START

    create_synth()
    load_soundfont()

    if ARGS.bpm is not None:
        SEQUENCER.beats_per_minute = ARGS.bpm
    else:
        SEQUENCER.beats_per_minute = 90

    # initialize our absolute date
    now = SEQUENCER.ticks
    if ARGS.debug:
        print('<debug> Current tick:', now)
    SEQ_START = now + 10  # keep a small margin before the first note
    schedule_next_sequence()

    print('Playing...')
    print('Hit Ctrl+C to stop')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Done playing')

    delete_synth()  # seems needed to avoid segfault at the end


if __name__ == "__main__":
    ARGS = parse_args()
    main()
