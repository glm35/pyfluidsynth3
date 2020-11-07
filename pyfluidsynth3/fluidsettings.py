#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from . import constants, utility
from ctypes import byref, c_char_p, c_double, c_int


class FluidSettings:
    """ Represent the FluidSynth settings as defined in settings.h. A instance of this class
    can be used like an array aka like the fluidsettings_t object. This means you can get/set
    values using brackets (See example below).

    This class is inspired by the FluidSettings object from pyfluidsynth by MostAwesomeDude.

    Example:
    fluidsettings = FluidSettings(handle)
    fluidsettings['audio.driver'] = 'alsa'

    Constants:
    FLUID_NO_TYPE -- Settings type: Undefined type.
    FLUID_NUM_TYPE -- Settings type: Numeric (double).
    FLUID_INT_TYPE -- Settings type: Integer.
    FLUID_STR_TYPE -- Settings type: String.
    FLUID_SET_TYPE -- Settings type: Set of values.
    QUALITY_LOW -- Quality preset: Low.
    QUALITY_MED -- Quality preset: Medium.
    QUALITY_HIGH -- Quality preset: High.

    Member:
    handle -- The handle to the FluidSynth library. Should be FluidHandle but a raw handle will
               probably work, too (FluidHandle).
    quality -- The last quality preset used (string).
    settings -- The FluidSynth settings object (fluidsettings_t).
    """

    (FLUID_NO_TYPE,
     FLUID_NUM_TYPE,
     FLUID_INT_TYPE,
     FLUID_STR_TYPE,
     FLUID_SET_TYPE) = range(-1, 4)

    QUALITY_LOW = 'low'
    QUALITY_MEDIUM = 'med'
    QUALITY_HIGH = 'high'

    def __init__(self, handle):
        """ Create new FluidSynth settings instance using the given handle.

        Set default quality to medium.
        """
        self.handle = handle
        self.settings = self.handle.new_fluid_settings()
        self.quality = self.QUALITY_MEDIUM

    @property
    def quality(self):
        """ Return the last quality preset used. """
        return self._quality

    @quality.setter
    def quality(self, quality):
        """ Set the given quality preset. """
        self._quality = quality

        if quality == self.QUALITY_LOW:
            self['synth.chorus.active'] = constants.FALSE
            self['synth.reverb.active'] = constants.FALSE
            self['synth.sample-rate'] = 22050

        elif quality == self.QUALITY_MEDIUM:
            self['synth.chorus.active'] = constants.FALSE
            self['synth.reverb.active'] = constants.TRUE
            self['synth.sample-rate'] = 44100

        elif quality == self.QUALITY_HIGH:
            self['synth.chorus.active'] = constants.TRUE
            self['synth.reverb.active'] = constants.TRUE
            self['synth.sample-rate'] = 44100

    def __del__(self):
        """ Delete the FluidSynth settings object. """
        self.handle.delete_fluid_settings(self.settings)

    def __getitem__(self, key):
        """ Return the value of the given settings key. """

        key = utility.fluidstring(key)
        key_type = self.handle.fluid_settings_get_type(self.settings, key)

        if key_type is self.FLUID_NUM_TYPE:
            val = c_double()
            func = self.handle.fluid_settings_getnum
        elif key_type is self.FLUID_INT_TYPE:
            val = c_int()
            func = self.handle.fluid_settings_getint
        elif key_type is self.FLUID_STR_TYPE:
            val = c_char_p()
            try:
                func = self.handle.fluid_settings_getstr
            except AttributeError:
                # fluid_settings_getstr removed from libfluidsynth 2.0.0
                # TODO: what's the alternative?
                raise KeyError(key)
        else:
            raise KeyError(key)

        if func(self.settings, key, byref(val)):
            return val.value
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """ Set the value of the given settings key to value. """

        key = utility.fluidstring(key)
        key_type = self.handle.fluid_settings_get_type(self.settings, key)

        if key_type is self.FLUID_STR_TYPE:
            value = utility.fluidstring(value)
            ret = self.handle.fluid_settings_setstr(self.settings, key, value)
            if self._normalize_ret_code(ret) == constants.FAILED:
                raise KeyError(key)
        elif key_type is self.FLUID_NUM_TYPE:
            # Coerce string value to float before going further.
            value = self._coerce_to_float(value)
            ret = self.handle.fluid_settings_setnum(self.settings, key, value)
            if self._normalize_ret_code(ret) == constants.FAILED:
                raise KeyError(key)
        elif key_type is self.FLUID_INT_TYPE:
            # Coerce string value to integer before going further.
            value = self._coerce_to_int(value)
            ret = self.handle.fluid_settings_setint(self.settings, key, value)
            if self._normalize_ret_code(ret) == constants.FAILED:
                raise KeyError(key)
        else:
            raise KeyError(key)

    @staticmethod
    def _coerce_to_int(string_value):
        """ Turn a string into an integer. """
        try:
            return int(string_value)
        except ValueError:
            return int(string_value.lower() not in ('false', 'no', 'off'))

    @staticmethod
    def _coerce_to_float(string_value):
        """ Turn a string into an float. """
        try:
            return float(string_value)
        except ValueError:
            return float(string_value.lower() not in ('false', 'no', 'off'))

    def _normalize_ret_code(self, ret_code):
        """Normalize the code returned by a fluid_settings_* function.

        In libfluidsynth v1, fluid_settings_* functions return 1 if the value has been set, 0
        otherwise.  In libfluidsynth v2 (since libfluidsynth 2.0.0), they return 0 (FLUID_OK) if
        the value has been set, -1 (FLUID_FAILED) otherwise.

        Return a code following libfluidsynth v2 convention.
        """
        if self.handle.get_version() == 1:
            if ret_code == 1:
                ret_code = constants.OK
            else:
                ret_code = constants.FAILED

        return ret_code
