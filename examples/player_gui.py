#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Show how to use a FluidPlayer object to play one or more midi file(s)
and control their playback.

Run with:

  $ cd /path/to/pyfluidsynth3
  $ PYTHONPATH=. python3 examples/player_gui.py MIDI_FILES

"""

import argparse
import pathlib
import sys
from threading import Timer
import time
import tkinter as tk
from typing import List, Optional

from pyfluidsynth3 import fluidaudiodriver, fluidhandle, fluidsettings, fluidsynth
from pyfluidsynth3.fluidplayer import FluidPlayer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Play MIDI file(s)")

    # Positional arguments
    parser.add_argument("midi_files", nargs='*', help="Path(s) to the MIDI file(s) to play")

    # Optional arguments
    parser.add_argument("-ad", "--audio-driver", default='alsa',
                        help="Audio driver to be used by fluidsynth (default: alsa)")
    parser.add_argument("-sf", "--soundfont",
                        help="Path to the sound font .sf2 file "
                             "(default: %(prog)s will try to find it).")
    parser.add_argument("-l", "--fluidsynth-library",
                        help="Path to libfluidsynth (default: pyfluidsynth3 will try to find it).")

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


class Player:
    def __init__(self, soundfont: Optional[pathlib.Path],
                 fluidsynth_library: Optional[str], audio_driver: str):
        self.handle = fluidhandle.FluidHandle(fluidsynth_library)
        self.settings = fluidsettings.FluidSettings(self.handle)

        self.synth = fluidsynth.FluidSynth(self.handle, self.settings)
        self.synth.load_soundfont(str(soundfont))

        self.settings['audio.driver'] = audio_driver
        self.driver = fluidaudiodriver.FluidAudioDriver(self.handle, self.synth, self.settings)

        self._fluidplayer = None

        self._playlist = []

        self.repeat_count = 1

        # By default, use tempo from midi file or default fluidsynth tempo (120 bpm)
        self.tempo_bpm = None
        self.midi_tempo = None

    def __del__(self):
        if self._fluidplayer is not None:
            del self._fluidplayer
        del self.driver
        del self.synth

    # Playlist management

    def set_playlist(self, playlist):
        for midi_file in playlist:
            print("Player: set_playlist: add midi file:", midi_file)
            self._playlist.append(midi_file)

    def get_playlist(self):
        return list(self._playlist)

    # Playback control

    def play(self):
        """Start playing tunes in the playlist."""
        print("Player: play")

        if self._fluidplayer is None:
            self._fluidplayer = FluidPlayer(self.handle, self.synth)
            self._fluidplayer.set_loop(self.repeat_count)
            self._set_tempo(bpm=self.tempo_bpm, midi_tempo=self.midi_tempo)

            for midi_file in self._playlist:
                self._fluidplayer.add(midi_file)
        else:
            self._fluidplayer.play()
            # TODO: if playback is finished, need to restart

    def pause(self):
        """Pause playback."""
        print("Player: pause")
        if self._fluidplayer is not None:
            self._fluidplayer.stop()  # fluid_player_stop() actually just pauses playback...

    def stop(self):
        """Stop playing."""
        print("Player: stop")
        if self._fluidplayer is not None:
            # No way to stop playback and resume at the beginning of the
            # playlist with fluidsynth, so we just delete the player.
            # Before that we call stop(), else the last note will resonate for a while.
            # We need a short delay to let that happen before the player is
            # deleted.
            self._fluidplayer.stop()
            time.sleep(0.2)
            del self._fluidplayer
            self._fluidplayer = None

    # Loop control

    @property
    def repeat_count(self):
        return self._repeat_count

    @repeat_count.setter
    def repeat_count(self, count):
        if count == 0 or count < -1:
            raise ValueError("repeat count must be > 0 or equal to -1 (infinite)")
        print(f"Player: repeat_count={count}")
        self._repeat_count = count
        if self._fluidplayer is not None:
            self._fluidplayer.set_loop(self.repeat_count)

    # Tempo control

    @property
    def tempo_bpm(self):
        return self._tempo_bpm

    @tempo_bpm.setter
    def tempo_bpm(self, bpm: Optional[int]):
        if bpm is not None and bpm <= 0:
            raise ValueError
        self._tempo_bpm = bpm
        self._midi_tempo = None
        print(f"Player: set tempo bpm={bpm}")
        self._set_tempo(bpm=bpm)

    @property
    def midi_tempo(self):
        return self._midi_tempo

    @midi_tempo.setter
    def midi_tempo(self, midi_tempo: Optional[int]):
        if midi_tempo is not None and midi_tempo <= 0:
            raise ValueError
        self._midi_tempo = midi_tempo
        self._tempo_bpm = None
        print(f"Player: set midi tempo={midi_tempo} us/quarter note")
        self._set_tempo(midi_tempo=midi_tempo)

    def _set_tempo(self, bpm: Optional[int] = None, midi_tempo: Optional[int] = None) -> bool:
        if self._fluidplayer is None:
            return False
        if bpm is not None:
            print(f'Set tempo (bpm): {bpm}')
            self._fluidplayer.set_tempo(FluidPlayer.TEMPO_BPM, bpm)
            return True
        elif midi_tempo is not None:
            print(f'Set MIDI tempo (ms per quarter note): {midi_tempo}')
            self._fluidplayer.set_tempo(FluidPlayer.TEMPO_MIDI, midi_tempo)
            return True
        else:
            print(f'Use default tempo')
            self._fluidplayer.set_tempo(FluidPlayer.TEMPO_DEFAULT, tempo=0)
            return True

    def get_tempo(self):
        if self._fluidplayer is None:
            return None
        tempo_bpm, sync_mode = self._fluidplayer.get_tempo(FluidPlayer.TEMPO_BPM)
        if sync_mode == 0:
            sync_mode_str = "external"
        elif sync_mode == 1:
            sync_mode_str = "internal"
        else:
            sync_mode_str = str(sync_mode)

        midi_tempo, _ = self._fluidplayer.get_tempo(FluidPlayer.TEMPO_MIDI)
        default_tempo, _ = self._fluidplayer.get_tempo(FluidPlayer.TEMPO_DEFAULT)

        return tempo_bpm, midi_tempo, default_tempo, sync_mode_str


class PlayerGui:
    def __init__(self, player: Player):
        self._player = player
        self._timer = None  # 1s cyclic timer to update the get tempo label
        self._root = tk.Tk()
        self._root.protocol('WM_DELETE_WINDOW', self._on_exit)
        self._root.title('pyfluidsynth3 example player GUI')

        self._create_playlist_box()
        self._create_playback_control_frame()
        self._create_loop_control_frame()
        self._create_tempo_frame()

    def _on_exit(self, event=None):
        if self._timer is not None:
            self._timer.cancel()
        self._root.destroy()

    def _create_playlist_box(self):
        self._playlist = tk.Listbox(self._root)
        self._playlist.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        for midi_file in self._player.get_playlist():
            self._playlist.insert(tk.END, midi_file)

    def _create_playback_control_frame(self):
        self._playback_control = tk.Frame(self._root)
        button_stop = tk.Button(self._playback_control, text='Stop',
                                command=self._player.stop)
        button_stop.pack(side=tk.LEFT)
        button_pause = tk.Button(self._playback_control, text='Pause',
                                 command=self._player.pause)
        button_pause.pack(side=tk.LEFT)
        button_play = tk.Button(self._playback_control, text='Play',
                                command=self._on_play)
        button_play.pack(side=tk.LEFT)
        self._playback_control.pack(side=tk.TOP, fill=tk.X)

    def _on_play(self):
        self._player.play()
        if self._timer is None:
            self._timer = Timer(interval=1, function=self._on_timeout)
            self._timer.start()
        self._update_get_tempo_label()

    (NO_LOOP, LOOP_FOREVER, REPEAT) = (1, 2, 3)

    def _create_loop_control_frame(self):
        self._loop_control_frame = tk.Frame(self._root)

        self._loop_value = tk.IntVar()
        self._loop_value.set(self.NO_LOOP)
        for txt, val in [("No Loop", self.NO_LOOP),
                         ("Loop Forever", self.LOOP_FOREVER),
                         ("Repeat", self.REPEAT)]:
            radio_button = tk.Radiobutton(self._loop_control_frame,
                                          text=txt, variable=self._loop_value, value=val,
                                          command=self._on_loop_control)
            radio_button.pack(side=tk.LEFT)

        self._repeat_entry = tk.Entry(self._loop_control_frame, width=3)
        self._repeat_entry.bind("<Return>", self._on_repeat_entry_return_keypress)
        self._repeat_entry.bind("<KP_Enter>", self._on_repeat_entry_return_keypress)
        self._repeat_entry.pack(side=tk.LEFT)
        tk.Label(self._loop_control_frame, text="times").pack(side=tk.LEFT)

        self._loop_control_frame.pack(side=tk.TOP, fill=tk.X)

    def _on_loop_control(self):
        loop_control_mode = self._loop_value.get()
        if loop_control_mode == self.NO_LOOP:
            self._player.repeat_count = 1
        elif loop_control_mode == self.LOOP_FOREVER:
            self._player.repeat_count = -1
        elif loop_control_mode == self.REPEAT:
            try:
                self._player.repeat_count = int(self._repeat_entry.get())
            except ValueError:
                pass

    def _on_repeat_entry_return_keypress(self, event=None):
        self._loop_value.set(self.REPEAT)
        self._on_loop_control()

    def _create_tempo_frame(self):
        self._tempo_frame = tk.Frame(self._root)
        tk.Label(self._tempo_frame, text="Set tempo:").grid(row=0, columnspan=3, sticky=tk.W)

        tk.Label(self._tempo_frame, text="bpm:", justify=tk.RIGHT)\
            .grid(row=1, column=0, sticky=tk.E)
        self._tempo_bpm_entry = tk.Entry(self._tempo_frame, width=3)
        self._tempo_bpm_entry.grid(row=1, column=1, sticky=tk.W)
        self._tempo_bpm_entry.bind("<Return>", self._on_set_tempo_bpm)
        self._tempo_bpm_entry.bind("<KP_Enter>", self._on_set_tempo_bpm)
        self._tempo_bpm_button = tk.Button(self._tempo_frame, text="Set tempo (bpm)",
                                          command=self._on_set_tempo_bpm)
        self._tempo_bpm_button.grid(row=1, column=2, sticky=tk.W)

        tk.Label(self._tempo_frame, text="MIDI tempo:", justify=tk.RIGHT).grid(row=2, sticky=tk.W)
        self._midi_tempo_entry = tk.Entry(self._tempo_frame, width=8)
        self._midi_tempo_entry.grid(row=2, column=1, sticky=tk.W)
        self._midi_tempo_entry.bind("<Return>", self._on_set_midi_tempo)
        self._midi_tempo_entry.bind("<KP_Enter>", self._on_set_midi_tempo)
        self._midi_tempo_button = tk.Button(self._tempo_frame,
                                            text="Set MIDI tempo (µs/quarter note)",
                                            command=self._on_set_midi_tempo)
        self._midi_tempo_button.grid(row=2, column=2, sticky=tk.W)

        self._reset_tempo_button = tk.Button(self._tempo_frame,
                                             text="Reset tempo (use tempo from midi file)",
                                             command=self._on_reset_tempo)
        self._reset_tempo_button.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E)

        self._get_tempo_label = tk.Label(self._tempo_frame, text="Get tempo:")
        self._get_tempo_label.grid(row=5, columnspan=3, sticky=tk.W)

        self._tempo_frame.pack(side=tk.TOP, fill=tk.X)

    def _on_set_tempo_bpm(self, event=None):
        try:
            self._player.tempo_bpm = int(self._tempo_bpm_entry.get())
            self._midi_tempo_entry.delete(0, len(self._midi_tempo_entry.get()))
            self._update_get_tempo_label()
        except ValueError:
            pass

    def _on_set_midi_tempo(self, event=None):
        try:
            self._player.midi_tempo = int(self._midi_tempo_entry.get())
            self._tempo_bpm_entry.delete(0, len(self._tempo_bpm_entry.get()))
            self._update_get_tempo_label()
        except ValueError as e:
            print(e)

    def _on_reset_tempo(self):
        self._tempo_bpm_entry.delete(0, len(self._tempo_bpm_entry.get()))
        self._player.tempo_bpm = None
        self._midi_tempo_entry.delete(0, len(self._midi_tempo_entry.get()))
        self._player.midi_tempo = None
        self._update_get_tempo_label()

    def _update_get_tempo_label(self):
        tempo_label = "Get tempo:"
        try:
            (tempo_bpm, midi_tempo, default_tempo, sync_mode) = self._player.get_tempo()
            tempo_label += " bpm={0}, MIDI tempo={1}, default tempo={2}, sync_mode={3}".format(
                tempo_bpm, midi_tempo, default_tempo, sync_mode)
        except TypeError:
            pass
        self._get_tempo_label.config(text=tempo_label)

    def _on_timeout(self):
        self._update_get_tempo_label()
        self._timer = Timer(interval=1, function=self._on_timeout)
        self._timer.start()

    def mainloop(self):
        self._root.mainloop()


if __name__ == "__main__":
    args = parse_args()

    soundfont = args.soundfont
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            print('Error: no sound font can be found')
            sys.exit(1)
    print('Using sound font:', soundfont)
    if args.fluidsynth_library:
        print('Using libfluidsynth:', args.fluidsynth_library)
    print('Using audio driver:', args.audio_driver)

    player = Player(soundfont, args.fluidsynth_library, args.audio_driver)
    player.set_playlist(args.midi_files)

    gui = PlayerGui(player)
    gui.mainloop()

