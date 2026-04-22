# generated from rosidl_generator_py/resource/_idl.py.em
# with input from robot_msg:msg/SoundType.idl
# generated code does not contain a copyright notice


# Import statements for member types

# Member 'confidence_scores'
import array  # noqa: E402, I100

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_SoundType(type):
    """Metaclass of message 'SoundType'."""

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
                'robot_msg.msg.SoundType')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__sound_type
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__sound_type
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__sound_type
            cls._TYPE_SUPPORT = module.type_support_msg__msg__sound_type
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__sound_type

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


class SoundType(metaclass=Metaclass_SoundType):
    """Message class 'SoundType'."""

    __slots__ = [
        '_sound_category',
        '_detected_sounds',
        '_confidence_scores',
        '_timestamp',
    ]

    _fields_and_field_types = {
        'sound_category': 'string',
        'detected_sounds': 'sequence<string>',
        'confidence_scores': 'sequence<float>',
        'timestamp': 'builtin_interfaces/Time',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.UnboundedString()),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('float')),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['builtin_interfaces', 'msg'], 'Time'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.sound_category = kwargs.get('sound_category', str())
        self.detected_sounds = kwargs.get('detected_sounds', [])
        self.confidence_scores = array.array('f', kwargs.get('confidence_scores', []))
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
        if self.sound_category != other.sound_category:
            return False
        if self.detected_sounds != other.detected_sounds:
            return False
        if self.confidence_scores != other.confidence_scores:
            return False
        if self.timestamp != other.timestamp:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def sound_category(self):
        """Message field 'sound_category'."""
        return self._sound_category

    @sound_category.setter
    def sound_category(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'sound_category' field must be of type 'str'"
        self._sound_category = value

    @builtins.property
    def detected_sounds(self):
        """Message field 'detected_sounds'."""
        return self._detected_sounds

    @detected_sounds.setter
    def detected_sounds(self, value):
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
                 all(isinstance(v, str) for v in value) and
                 True), \
                "The 'detected_sounds' field must be a set or sequence and each value of type 'str'"
        self._detected_sounds = value

    @builtins.property
    def confidence_scores(self):
        """Message field 'confidence_scores'."""
        return self._confidence_scores

    @confidence_scores.setter
    def confidence_scores(self, value):
        if isinstance(value, array.array):
            assert value.typecode == 'f', \
                "The 'confidence_scores' array.array() must have the type code of 'f'"
            self._confidence_scores = value
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
                 all(isinstance(v, float) for v in value) and
                 all(not (val < -3.402823466e+38 or val > 3.402823466e+38) or math.isinf(val) for val in value)), \
                "The 'confidence_scores' field must be a set or sequence and each value of type 'float' and each float in [-340282346600000016151267322115014000640.000000, 340282346600000016151267322115014000640.000000]"
        self._confidence_scores = array.array('f', value)

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
