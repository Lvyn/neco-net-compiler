""" Module handling bitfields as simple masks.
"""

class Mask(object):
    """ Class representing bit masks.
    """

    def __init__(self, value = [0, 0, 0, 0, 0, 0, 0, 0]):
        """ New mask.

        >>> Mask()
        Mask(value=[0, 0, 0, 0, 0, 0, 0, 0])
        >>> Mask([0, 1, 0])
        Mask(value=[0, 1, 0])
        >>> Mask([0, 2, 0])
        Traceback (most recent call last):
        ValueError:...

        @param value: initial mask (list of 0 and 1 values)
        @type value: C{list<int>}
        """
        for b in value:
            if b not in [0, 1]:
                raise ValueError("bits must be 0 or 1.")
        self._width = len(value)
        self._mask = value

    @classmethod
    def from_int(cls, integer, size):
        """ New mask from integer.

        >>> Mask.from_int(0, 8)
        Mask(value=[0, 0, 0, 0, 0, 0, 0, 0])
        >>> Mask.from_int(1, 8)
        Mask(value=[0, 0, 0, 0, 0, 0, 0, 1])
        >>> m = Mask.from_int(42, 8)
        >>> m, int(m)
        (Mask(value=[0, 0, 1, 0, 1, 0, 1, 0]), 42)
        >>> m = Mask.from_int(93, 8)
        >>> m, int(m)
        (Mask(value=[0, 1, 0, 1, 1, 1, 0, 1]), 93)

        @param integer: integer to be converted to mask.
        @type integer: C{int}
        @param size: number of bits to be used.
        @type size: C{int}
        @return: new mask.
        @rtype: C{Mask}
        """
        tmp = Mask([ 0 for _ in range(0, size)])
        for i in range(0, size):
            tmp._mask[size-1-i] = int((integer >> i) & 0x1)
        return tmp

    @classmethod
    def build_mask(cls, offset, bits, width):
        """ Build a mask filled with a range of 1 bits.

        >>> Mask.build_mask(3, 4, 8)
        Mask(value=[0, 1, 1, 1, 1, 0, 0, 0])

        @param offset: position of first 1 bit.
        @type offset: C{int}
        @param bits: how many 1 bits ?
        @type bits: C{int}
        @param width: mask size.
        @type width: C{int}
        @return: new Mask.
        @rtype: C{Mask}
        """
        m = Mask([0 for _ in range(0, width)])
        for i in range(offset, offset + bits):
            m[i] = 1
        return m


    def length(self):
        """ Mask length.

        >>> Mask([]).length(), Mask([0]).length(), Mask([0, 0]).length()
        (0, 1, 2)

        @return: mask length.
        @rtype: C{int}
        """
        return len(self._mask)

    def __len__(self):
        """
        >>> Mask([]).length(), Mask([0]).length(), Mask([0, 0]).length()
        (0, 1, 2)
        """
        return self.length()

    def to_int(self):
        """ Convert mask to integer.

        >>> Mask([0]).to_int()
        0
        >>> Mask([1, 1, 1]).to_int()
        7
        >>> Mask([0, 1, 1]).to_int()
        3
        >>> Mask([1, 0, 0, 1, 1]).to_int()
        19

        @return: integer corresponding to mask.
        @rtype: C{int}
        """
        mask2 = [ 2**i for i,x in enumerate(reversed(self._mask)) if x > 0 ]
        return sum(mask2)

    def __int__(self):
        """
        >>> int(Mask([1, 1, 1]))
        7
        >>> int(Mask([0, 1, 1]))
        3
        >>> int(Mask([1, 0, 0, 1, 1]))
        19
        """
        return self.to_int()

    def __str__(self):
        return str(self._mask)

    def __repr__(self):
        return "Mask(value={value})".format(value=self._mask)

    def set_bit(self, num, value):
        """ Set a bit value.

        >>> m = Mask([0, 0, 0, 0])
        >>> m.set_bit(1, 1)
        >>> m
        Mask(value=[0, 0, 1, 0])
        >>> m.set_bit(1, 2)
        Traceback (most recent call last):
        ValueError:...
        >>> m.set_bit(-1, 2)
        Traceback (most recent call last):
        ValueError:...
        >>> m.set_bit(4, 1)
        Traceback (most recent call last):
        IndexError

        @param num: bit to be set.
        @type num: C{int}
        @param value: bit value to be used (0 or 1).
        @type value: C{int}
        """
        if not value in [ 0, 1 ]:
            raise ValueError("bits must be 0 or 1.")
        if not (0 <= num < self._width):
            raise IndexError()
        self._mask[self._width - 1 - num] = value


    def __setitem__(self, key, value):
        """ Set a bit using subscript syntax.

        >>> m = Mask([0, 0, 0, 0])
        >>> m[1] = 1
        >>> m
        Mask(value=[0, 0, 1, 0])
        >>> m[1] = 2
        Traceback (most recent call last):
        ValueError:...
        >>> m[-1] = 2
        Traceback (most recent call last):
        ValueError:...
        >>> m[4] = 1
        Traceback (most recent call last):
        IndexError

        @param key: bit to be set.
        @type key: C{key}
        @param value: bit value to be used (0 or 1)
        @type value: C{int}
        """
        return self.set_bit(key, value)

    def get_bit(self, num):
        """ Read a bit.

        >>> Mask([0]).get_bit(0), Mask([1]).get_bit(0)
        (0, 1)
        >>> Mask([0]).get_bit(1)
        Traceback (most recent call last):
        IndexError
        >>> m = Mask([0, 1, 0, 1, 1])
        >>> m.get_bit(0), m.get_bit(1), m.get_bit(2), m.get_bit(3), m.get_bit(4)
        (1, 1, 0, 1, 0)

        @param num: bit to be read.
        @type num: C{int}
        @return: read bit value.
        @rtype: C{int}
        """
        if not (0 <= num < self._width):
            raise IndexError()
        return self._mask[self._width - 1 - num]

    def __getitem__(self, key):
        """ Get bit using subscript syntax.

        >>> m = Mask([0, 1, 0, 1, 1])
        >>> m[0], m[1], m[2], m[3], m[4]
        (1, 1, 0, 1, 0)

        @param key: bit to be read.
        @type key: C{int}
        @return: read bit value.
        @rtype: C{int}
        """
        return self.get_bit(key)

    def bit_xor(self, other):
        """ Xor operation on masks.

        >>> Mask([0]).bit_xor(Mask([0]))
        Mask(value=[0])
        >>> Mask([0]).bit_xor(Mask([1]))
        Mask(value=[1])
        >>> Mask([1]).bit_xor(Mask([0]))
        Mask(value=[1])
        >>> Mask([1]).bit_xor(Mask([1]))
        Mask(value=[0])
        >>> Mask([1, 1, 0, 0, 1]).bit_xor(Mask([1, 0, 1, 0, 0]))
        Mask(value=[0, 1, 1, 0, 1])
        >>> Mask([1, 1]).bit_xor(Mask([1]))
        Traceback (most recent call last):
        ValueError:...

        @param other: right operand.
        @type other: C{Mask}
        @return: resulting Mask.
        @rtype: C{Mask}
        """
        if len(self) != len(other):
            raise ValueError("Mask should have the same length.")
        return Mask([ b1 ^ b2 for b1, b2 in zip(self._mask, other._mask)])

    def bit_and(self, other):
        """ And operation on masks.

        >>> Mask([0]).bit_and(Mask([0]))
        Mask(value=[0])
        >>> Mask([0]).bit_and(Mask([1]))
        Mask(value=[0])
        >>> Mask([1]).bit_and(Mask([0]))
        Mask(value=[0])
        >>> Mask([1]).bit_and(Mask([1]))
        Mask(value=[1])
        >>> Mask([1, 1, 0, 1, 1]).bit_and(Mask([1, 0, 1, 1, 0]))
        Mask(value=[1, 0, 0, 1, 0])
        >>> Mask([1, 1]).bit_and(Mask([1]))
        Traceback (most recent call last):
        ValueError:...

        @param other: right operand.
        @type other: C{Mask}
        @return: resulting Mask.
        @rtype: C{Mask}
        """
        if len(self) != len(other):
            raise ValueError("Mask should have the same length.")
        return Mask([ b1 & b2 for b1, b2 in zip(self._mask, other._mask)])


    def bit_or(self, other):
        """ Or opearation on masks.

        >>> Mask([0]).bit_or(Mask([0]))
        Mask(value=[0])
        >>> Mask([0]).bit_or(Mask([1]))
        Mask(value=[1])
        >>> Mask([1]).bit_or(Mask([0]))
        Mask(value=[1])
        >>> Mask([1]).bit_or(Mask([1]))
        Mask(value=[1])
        >>> Mask([1, 1, 0, 0, 1]).bit_or(Mask([1, 0, 0, 1, 0]))
        Mask(value=[1, 1, 0, 1, 1])
        >>> Mask([1, 1]).bit_or(Mask([1]))
        Traceback (most recent call last):
        ValueError:...

        @param other: right operand.
        @type other: C{Mask}
        @return: resulting Mask.
        @rtype: C{Mask}
        """
        if len(self) != len(other):
            raise ValueError("Mask should have the same length.")
        return Mask([ b1 | b2 for b1, b2 in zip(self._mask, other._mask)])

    def bit_not(self):
        """ Inversion operation on masks.

        >>> Mask([]).bit_not()
        Mask(value=[])
        >>> Mask([0]).bit_not()
        Mask(value=[1])
        >>> Mask([1]).bit_not()
        Mask(value=[0])
        >>> Mask([1, 1, 0, 0, 1]).bit_not()
        Mask(value=[0, 0, 1, 1, 0])

        @return: resulting Mask.
        @rtype: C{Mask}
        """
        return Mask([ int(b1 == 0) for b1 in self._mask ])

    def __and__(self, other):
        """
        >>> Mask([1, 1, 0, 0, 1]) & Mask([1, 0, 0, 1, 1])
        Mask(value=[1, 0, 0, 0, 1])
        """
        return self.bit_and(other)

    def __xor__(self, other):
        """
        >>> Mask([1, 1, 0, 0, 1]) ^ Mask([1, 0, 0, 1, 0])
        Mask(value=[0, 1, 0, 1, 1])
        """
        return self.bit_xor(other)

    def __or__(self, other):
        """
        >>> Mask([1, 1, 0, 0, 0]) | Mask([1, 0, 1, 0, 1])
        Mask(value=[1, 1, 1, 0, 1])
        """
        return self.bit_or(other)

    def __invert__(self):
        """
        >>> ~Mask([1, 0, 1, 0, 0])
        Mask(value=[0, 1, 0, 1, 1])
        """
        return self.bit_not()

class Field(object):
    """ Helper class for bit fields. """

    def __init__(self, name, bits, offset):
        """ New Field.

        >>> f = Field('toto', 3, 5)
        >>> f.name, f.bits, f.offset
        ('toto', 3, 5)

        @param name: field name
        @type name: C{str}
        @param bits: number of bits used for the field.
        @type bits: C{int}
        @param offset: offset value in parent bitfield.
        @type offset: C{int}
        """
        self._name = name
        self._bits = bits
        self._offset = offset

    @property
    def name(self):
        """ Field name. """
        return self._name

    @property
    def bits(self):
        """ Number of used bits for the field. """
        return self._bits

    @property
    def offset(self):
        """ Offset value in parent bitfield. """
        return self._offset

class MaskBitfield(object):
    """ Class used to represent bitfields with masks.
    """

    def __init__(self, native_width=8):
        """ New MaskBitfield.

        @param native_width: bit size of the underlying native type (ex. 8 for
        a char if the bit field is represented with chars.)
        @type native_width: C{int}
        """
        self._bits = 0
        self._fields_list = []
        self._fields = {}
        self._native_width = native_width

    @property
    def native_width(self):
        """ Size of the underlying native type. """
        return self._native_width

    def dump_structure(self):
        """ Get a string representing bitfield structure.

        >>> bf = MaskBitfield(native_width=8)
        >>> bf.add_field('f1', 3)
        >>> bf.add_field('f2', 3)
        >>> bf.add_field('f3', 3)
        >>> bf.add_field('f4', 3)
        >>> print bf.dump_structure()
        bitfield nw:8 ub:14
        fields:
          0: name=f1 bits=3 offset=0
          1: name=f2 bits=3 offset=3
          2: name=dummy6 bits=2 offset=6
          3: name=f3 bits=3 offset=8
          4: name=f4 bits=3 offset=11

        @return: bitfield structure string representation.
        @rtype: C{str}
        """
        l = []
        l.append("bitfield nw:{nw} ub:{ub}\nfields:"
                 .format(nw=self._native_width,
                         ub=self._bits))
        for i, field in enumerate(self._fields_list):
            l.append("{num:3}: name={name} bits={bits} offset={offset}"
                     .format(num=i,
                             name=field.name,
                             bits=field.bits,
                             offset=field.offset))
        return "\n".join(l)

    def add_field(self, name, bits):
        """ Add a field.

        @param name: field name.
        @type name: C{str}
        @param bits: field width.
        @type bits: C{int}
        """
        assert( not self._fields.has_key(name) )

        if (bits > self._native_width):
            raise ValueError("You should use a bigger native type (native width={nw})."
                             .format(nw = self._native_width))

        if (self._bits % self._native_width) + bits > self._native_width:
            dummy_width = self._native_width - (self._bits % self._native_width)
            self.add_field('dummy{offset}'.format(offset=self._bits), dummy_width)

        field = Field(name, bits, self._bits)
        self._fields_list.append(field)
        self._fields[name] = field
        self._bits += bits

    def native_field_count(self):
        """ Count of needed native fields to represent the bitfield.

        >>> bf = MaskBitfield(native_width=8)
        >>> bf.native_field_count()
        0
        >>> bf.add_field('f1', 3)
        >>> bf.native_field_count()
        1
        >>> bf.add_field('f2', 3)
        >>> bf.native_field_count()
        1
        >>> bf.add_field('f3', 2)
        >>> bf.native_field_count()
        1
        >>> bf.add_field('f4', 3)
        >>> bf.native_field_count()
        2
        >>> bf.add_field('f5', 3)
        >>> bf.native_field_count()
        2

        @return: Count of needed native fields.
        @rtype: C{int}
        """
        n = self._bits / self._native_width
        if (self._bits % self._native_width) != 0:
            n+=1
        return n

    def get_fields(self):
        """ Get a list of fields in bitfield.

        @return: list of fields.
        @rtype: C{list<Field>}
        """
        return self._fields_list

    def get_field_native_offset(self, field_name):
        """ Get the offset of native component (number of native field
        holding the field).

        >>> bf = MaskBitfield(native_width=8)
        >>> bf.add_field('f1', 3)
        >>> bf.add_field('f2', 3)
        >>> bf.add_field('f3', 3)
        >>> bf.add_field('f4', 3)
        >>> bf.get_field_native_offset('f1')
        0
        >>> bf.get_field_native_offset('f3')
        1

        @param field_name: bitfield field name.
        @type field_name: C{str}
        @return: native offset.
        @rtype: C{int}
        """
        field = self._fields[field_name]
        return field.offset / self._native_width

    def get_field_compatible_mask(self, field_name, integer):
        """ Convert an integer value to mask compatible with a field.

        >>> bf = MaskBitfield(native_width=8)
        >>> bf.add_field('f1', 3)
        >>> bf.add_field('f2', 3)
        >>> bf.add_field('f3', 3)
        >>> bf.add_field('f4', 3)
        >>> m = bf.get_field_compatible_mask('f1', 5)
        >>> m, int(m)
        (Mask(value=[0, 0, 0, 0, 0, 1, 0, 1]), 5)
        >>> m = bf.get_field_compatible_mask('f2', 5)
        >>> m, int(m)
        (Mask(value=[0, 0, 1, 0, 1, 0, 0, 0]), 40)

        @param field_name: name of the field to be compatible with.
        @type field_name: C{str}
        @param integer: integer value to be converted.
        @type integer: C{int}
        @return: resulting mask.
        @rtype: C{mask}
        """
        field = self._fields[field_name]
        mask_offset = field.offset % self._native_width
        return Mask.from_int( integer << mask_offset, self._native_width )

    def get_field_mask(self, field_name):
        """ Get the mask needed to extract a field.

        >>> bf = MaskBitfield(native_width=8)
        >>> bf.add_field('f1', 3)
        >>> bf.add_field('f2', 3)
        >>> bf.add_field('f3', 3)
        >>> bf.add_field('f4', 3)
        >>> bf.get_field_mask('f1')
        Mask(value=[1, 1, 1, 1, 1, 0, 0, 0])
        >>> bf.get_field_mask('f2')
        Mask(value=[1, 1, 0, 0, 0, 1, 1, 1])
        >>> bf.get_field_mask('f3')
        Mask(value=[1, 1, 1, 1, 1, 0, 0, 0])
        >>> bf.get_field_mask('f4')
        Mask(value=[1, 1, 0, 0, 0, 1, 1, 1])

        @param field_name: field corresponding to requested mask.
        @type field_name: C{str}
        @return: a mask.
        @rtype: C{Mask}
        """
        field = self._fields[field_name]
        mask_offset = field.offset % self._native_width
        max_int = 2**field.bits - 1
        return ~Mask.from_int( max_int << mask_offset, self._native_width )

################################################################################
# EOF
################################################################################

