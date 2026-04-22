# generated from rosidl_generator_py/resource/_idl.py.em
# with input from robot_msg:msg/ExtremeSensorAlert.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_ExtremeSensorAlert(type):
    """Metaclass of message 'ExtremeSensorAlert'."""

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
                'robot_msg.msg.ExtremeSensorAlert')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__extreme_sensor_alert
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__extreme_sensor_alert
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__extreme_sensor_alert
            cls._TYPE_SUPPORT = module.type_support_msg__msg__extreme_sensor_alert
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__extreme_sensor_alert

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


class ExtremeSensorAlert(metaclass=Metaclass_ExtremeSensorAlert):
    """Message class 'ExtremeSensorAlert'."""

    __slots__ = [
        '_sensor_type',
        '_alert_level',
        '_alert_type',
        '_current_value',
        '_threshold_value',
        '_description',
        '_timestamp',
        '_is_active',
        '_alert_id',
    ]

    _fields_and_field_types = {
        'sensor_type': 'string',
        'alert_level': 'string',
        'alert_type': 'string',
        'current_value': 'double',
        'threshold_value': 'double',
        'description': 'string',
        'timestamp': 'builtin_interfaces/Time',
        'is_active': 'boolean',
        'alert_id': 'uint32',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['builtin_interfaces', 'msg'], 'Time'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.sensor_type = kwargs.get('sensor_type', str())
        self.alert_level = kwargs.get('alert_level', str())
        self.alert_type = kwargs.get('alert_type', str())
        self.current_value = kwargs.get('current_value', float())
        self.threshold_value = kwargs.get('threshold_value', float())
        self.description = kwargs.get('description', str())
        from builtin_interfaces.msg import Time
        self.timestamp = kwargs.get('timestamp', Time())
        self.is_active = kwargs.get('is_active', bool())
        self.alert_id = kwargs.get('alert_id', int())

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
        if self.sensor_type != other.sensor_type:
            return False
        if self.alert_level != other.alert_level:
            return False
        if self.alert_type != other.alert_type:
            return False
        if self.current_value != other.current_value:
            return False
        if self.threshold_value != other.threshold_value:
            return False
        if self.description != other.description:
            return False
        if self.timestamp != other.timestamp:
            return False
        if self.is_active != other.is_active:
            return False
        if self.alert_id != other.alert_id:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def sensor_type(self):
        """Message field 'sensor_type'."""
        return self._sensor_type

    @sensor_type.setter
    def sensor_type(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'sensor_type' field must be of type 'str'"
        self._sensor_type = value

    @builtins.property
    def alert_level(self):
        """Message field 'alert_level'."""
        return self._alert_level

    @alert_level.setter
    def alert_level(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'alert_level' field must be of type 'str'"
        self._alert_level = value

    @builtins.property
    def alert_type(self):
        """Message field 'alert_type'."""
        return self._alert_type

    @alert_type.setter
    def alert_type(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'alert_type' field must be of type 'str'"
        self._alert_type = value

    @builtins.property
    def current_value(self):
        """Message field 'current_value'."""
        return self._current_value

    @current_value.setter
    def current_value(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'current_value' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'current_value' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._current_value = value

    @builtins.property
    def threshold_value(self):
        """Message field 'threshold_value'."""
        return self._threshold_value

    @threshold_value.setter
    def threshold_value(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'threshold_value' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'threshold_value' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._threshold_value = value

    @builtins.property
    def description(self):
        """Message field 'description'."""
        return self._description

    @description.setter
    def description(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'description' field must be of type 'str'"
        self._description = value

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

    @builtins.property
    def is_active(self):
        """Message field 'is_active'."""
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'is_active' field must be of type 'bool'"
        self._is_active = value

    @builtins.property
    def alert_id(self):
        """Message field 'alert_id'."""
        return self._alert_id

    @alert_id.setter
    def alert_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'alert_id' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'alert_id' field must be an unsigned integer in [0, 4294967295]"
        self._alert_id = value
