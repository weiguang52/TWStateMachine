# generated from rosidl_generator_py/resource/_idl.py.em
# with input from robot_msg:msg/SpeechData.idl
# generated code does not contain a copyright notice


# Import statements for member types

# Member 'audio_data'
import array  # noqa: E402, I100

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_SpeechData(type):
    """Metaclass of message 'SpeechData'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('robot_msg')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'robot_msg.msg.SpeechData')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__speech_data
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__speech_data
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__speech_data
            cls._TYPE_SUPPORT = module.type_support_msg__msg__speech_data
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__speech_data

            from builtin_interfaces.msg import Time
            if Time.__class__._TYPE_SUPPORT is None:
                Time.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class SpeechData(metaclass=Metaclass_SpeechData):
    """Message class 'SpeechData'."""

    __slots__ = [
        '_audio_data',
        '_sample_rate',
        '_channels',
        '_duration',
        '_timestamp',
    ]

    _fields_and_field_types = {
        'audio_data': 'sequence<uint8>',
        'sample_rate': 'uint32',
        'channels': 'uint32',
        'duration': 'float',
        'timestamp': 'builtin_interfaces/Time',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint8')),  # noqa: E501
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['builtin_interfaces', 'msg'], 'Time'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.audio_data = array.array('B', kwargs.get('audio_data', []))
        self.sample_rate = kwargs.get('sample_rate', int())
        self.channels = kwargs.get('channels', int())
        self.duration = kwargs.get('duration', float())
        from builtin_interfaces.msg import Time
        self.timestamp = kwargs.get('timestamp', Time())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.audio_data != other.audio_data:
            return False
        if self.sample_rate != other.sample_rate:
            return False
        if self.channels != other.channels:
            return False
        if self.duration != other.duration:
            return False
        if self.timestamp != other.timestamp:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def audio_data(self):
        """Message field 'audio_data'."""
        return self._audio_data

    @audio_data.setter
    def audio_data(self, value):
        if isinstance(value, array.array):
            assert value.typecode == 'B', \
                "The 'audio_data' array.array() must have the type code of 'B'"
            self._audio_data = value
            return
        if __debug__:
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, int) for v in value) and
                 all(val >= 0 and val < 256 for val in value)), \
                "The 'audio_data' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 255]"
        self._audio_data = array.array('B', value)

    @builtins.property
    def sample_rate(self):
        """Message field 'sample_rate'."""
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'sample_rate' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'sample_rate' field must be an unsigned integer in [0, 4294967295]"
        self._sample_rate = value

    @builtins.property
    def channels(self):
        """Message field 'channels'."""
        return self._channels

    @channels.setter
    def channels(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'channels' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'channels' field must be an unsigned integer in [0, 4294967295]"
        self._channels = value

    @builtins.property
    def duration(self):
        """Message field 'duration'."""
        return self._duration

    @duration.setter
    def duration(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'duration' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'duration' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._duration = value

    @builtins.property
    def timestamp(self):
        """Message field 'timestamp'."""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        if __debug__:
            from builtin_interfaces.msg import Time
            assert \
                isinstance(value, Time), \
                "The 'timestamp' field must be a sub message of type 'Time'"
        self._timestamp = value
