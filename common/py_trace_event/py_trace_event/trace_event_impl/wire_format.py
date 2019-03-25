TAG_TYPE_BITS = 3  # Number of bits used to hold type info in a proto tag.

WIRETYPE_VARINT = 0
WIRETYPE_FIXED64 = 1
WIRETYPE_LENGTH_DELIMITED = 2
WIRETYPE_START_GROUP = 3
WIRETYPE_END_GROUP = 4
WIRETYPE_FIXED32 = 5
_WIRETYPE_MAX = 5

def PackTag(field_number, wire_type):
  """Returns an unsigned 32-bit integer that encodes the field number and
  wire type information in standard protocol message wire format.

  Args:
    field_number: Expected to be an integer in the range [1, 1 << 29)
    wire_type: One of the WIRETYPE_* constants.
  """
  if not 0 <= wire_type <= _WIRETYPE_MAX:
    raise RuntimeError('Unknown wire type: %d' % wire_type)
  return (field_number << TAG_TYPE_BITS) | wire_type


