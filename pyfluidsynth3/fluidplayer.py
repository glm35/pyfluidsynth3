#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from . import constants, fluiderror, utility


class FluidPlayer:
    """ Represent the FluidSynth player object as defined in midi.h.

    This class is inspired by the FluidPlayer object from pyfluidsynth by MostAwesomeDude. Method
    documentation is mostly taken from FluidSynth's official API.

    Member:
    handle -- The handle to the FluidSynth library. Should be FluidHandle but a raw handle will
              probably work, too (FluidHandle).
    paused -- Indicates if the player is playing or inactive (boolean).
    player -- The FluidSynth player object (fluid_player_t).
    """

    def __init__(self, handle, synth):
        """ Create a new FluidSynth player instance using given handle and synth objects. """
        self.handle = handle
        self.player = self.handle.new_fluid_player(synth.synth)
        self.paused = True

    def __del__(self):
        """ Delete the player. """
        self.stop()
        self.join()

        if self.handle.delete_fluid_player(self.player) is constants.FAILED:
            raise fluiderror.FluidError("Couldn't delete fluid player!")

    def add(self, midi):
        """ Add a MIDI file to a player queue. """
        midi = utility.fluidstring(midi)
        self.handle.fluid_player_add(self.player, midi)

    def play(self, midi=None):
        """ Activate play mode for a MIDI player if not already playing. Also allows to add a MIDI
        file (see add()). """
        if midi:
            self.add(midi)
        self.handle.fluid_player_play(self.player)
        self.paused = False

    def stop(self):
        """ Stop a MIDI player. """
        self.handle.fluid_player_stop(self.player)
        self.paused = True

    def join(self):
        """ Wait for a MIDI player to terminate (when done playing). """
        self.handle.fluid_player_join(self.player)

    # MIDI player status codes:
    (READY, PLAYING, DONE) = range(0, 3)

    def get_status(self) -> int:
        """ Get MIDI player status.

        Return player status:
            FluidPlayer.READY: Player is ready.
            FluidPlayer.PLAYING: Player is currently playing.
            FluidPlayer.DONE: Player is finished playing.
        """
        return self.handle.fluid_player_get_status(self.player)

    def pause(self):
        """ Pause player or start again if already paused. """
        if self.paused:
            self.play()
        else:
            self.stop()
        self.paused = not self.paused
