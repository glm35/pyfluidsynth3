#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Show how to use a FluidSequencer object.

Create and configure a sequencer, then program a sequence of 5 chords, one per beat, at 120
beats per minute (bpm).

Run with:

  $ cd /path/to/pyfluidsynth3
  $ PYTHONPATH=. python3 examples/sequencer.py

Based on the examples from pyfluidsynth by MostAwesomeDude.
"""

import argparse
import pathlib
import sys
import time
from typing import Optional

from pyfluidsynth3 import fluidaudiodriver, fluidevent, fluidhandle, fluidsettings, \
    fluidsequencer, fluidsynth


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-sf", "--soundfont",
                        help="Path to the sound font .sf2 file "
                             "(optional, synth.py will try to find it).")
    parser.add_argument("-l", "--fluidsynth-library",
                        help="Path to libfluidsynth (optional, pyfluidsynth3 will try to find it).")
    parser.add_argument("-ad", "--audio-driver", default='alsa',
                        help="Audio driver to be used by fluidsynth (default: alsa)")
    return parser.parse_args()


def find_soundfont() -> Optional[pathlib.Path]:
    """Try to find a soundfont"""

    # A few sound fonts from the fluid-soundfont-gm and timgm6mb-soundfont packages:
    soundfont_catalog = ['/usr/share/sounds/sf2/FluidR3_GM.sf2',
                         '/usr/share/sounds/sf2/TimGM6mb.sf2']
    for sf in soundfont_catalog:
        sf_path = pathlib.Path(sf)
        if sf_path.exists():
            return sf_path
    return None


class Sequencer:
    def __init__(self, soundfont: Optional[pathlib.Path],
                 fluidsynth_library: Optional[str], audio_driver: str):
        self.handle = fluidhandle.FluidHandle(fluidsynth_library)
        self.settings = fluidsettings.FluidSettings(self.handle)

        self.synth = fluidsynth.FluidSynth(self.handle, self.settings)
        self.synth.load_soundfont(str(soundfont))

        self.settings['audio.driver'] = audio_driver
        self.driver = fluidaudiodriver.FluidAudioDriver(self.handle, self.synth, self.settings)

        self.sequencer = fluidsequencer.FluidSequencer(self.handle)
        self.synth_seq_id, _ = self.sequencer.add_synth(self.synth)

    def __del__(self):
        del self.sequencer
        del self.driver
        del self.synth

    def play(self):
        self.sequencer.beats_per_minute = 120
        beat_length = self.sequencer.ticks_per_beat

        print("BPM: {0}".format(self.sequencer.beats_per_minute))
        print("TPB: {0}".format(self.sequencer.ticks_per_beat))
        print("TPS: {0}".format(self.sequencer.ticks_per_second))

        c_scale = []

        for note in range(60, 72):
            event = fluidevent.FluidEvent(self.handle)
            event.dest = self.synth_seq_id
            event.note(0, note, 127, int(beat_length * 0.9))
            c_scale.append(event)

        ticks = self.sequencer.ticks + 10

        self.sequencer.send(c_scale[0], ticks)
        self.sequencer.send(c_scale[4], ticks)
        self.sequencer.send(c_scale[7], ticks)

        ticks += beat_length

        self.sequencer.send(c_scale[0], ticks)
        self.sequencer.send(c_scale[5], ticks)
        self.sequencer.send(c_scale[9], ticks)

        ticks += beat_length

        self.sequencer.send(c_scale[0], ticks)
        self.sequencer.send(c_scale[4], ticks)
        self.sequencer.send(c_scale[7], ticks)

        ticks += beat_length

        self.sequencer.send(c_scale[2], ticks)
        self.sequencer.send(c_scale[5], ticks)
        self.sequencer.send(c_scale[7], ticks)
        self.sequencer.send(c_scale[11], ticks)

        ticks += beat_length

        self.sequencer.send(c_scale[0], ticks)
        self.sequencer.send(c_scale[4], ticks)
        self.sequencer.send(c_scale[7], ticks)

        time.sleep(3)


if __name__ == "__main__":
    args = parse_args()

    soundfont = args.soundfont
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            print('Error: no sound font can be found')
            sys.exit(1)
    print('Using sound font:', soundfont)
    print('Using audio driver:', args.audio_driver)

    sequencer = Sequencer(soundfont, args.fluidsynth_library, args.audio_driver)
    try:
        sequencer.play()
    except KeyboardInterrupt:
        print('Playback aborted')
