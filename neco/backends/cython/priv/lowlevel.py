'''
Created on 2 august 2012

@author: Lukasz Fronc
'''
from neco.core.info import TypeInfo
import pprint

def bits_sizeof(cython_type):
    '''
        \todo use module struct 
    '''
    if cython_type.is_Int:
        return 32
    elif cython_type.is_UnsignedInt:
        return 32
    elif cython_type.is_Char:
        return 8
    elif cython_type.is_UnsignedChar:
        return 8
    elif cython_type.is_Bool:
        return 1
    raise RuntimeError

def bytes_sizeof(cython_type):
    if cython_type.is_Int:
        return 4
    elif cython_type.is_Char:
        return 1
    elif cython_type.is_Bool:
        return 1
    raise RuntimeError

class Mask(object):
    """ Class representing bit masks.
    """

    def __init__(self, value=[0, 0, 0, 0, 0, 0, 0, 0]):
        """ New mask.

        >>> Mask()
        Mask(value=[0, 0, 0, 0, 0, 0, 0, 0])
        >>> Mask([0, 1, 0])
        Mask(value=[0, 1, 0])
        >>> Mask([0, 2, 0])
        Traceback (most recent call last):
        ValueError:...

        @param value: initial mask (list of 0 and 1 values)
        @type_info value: C{list<int>}
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
            tmp._mask[size - 1 - i] = int((integer >> i) & 0x1)
        return tmp

    @classmethod
    def build_mask(cls, offset, bits, width):
        """ Build a mask filled with a range of 1 bits.

        >>> Mask.build_mask(3, 4, 8)
        Mask(value=[0, 1, 1, 1, 1, 0, 0, 0])

        @param offset: position of first 1 bit.
        @type offset: C{int}
        @param bits: how many bits ?
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
        mask2 = [ 2 ** i for i, x in enumerate(reversed(self._mask)) if x > 0 ]
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
        IndexError:...

        @param num: bit to be set.
        @type num: C{int}
        @param value: bit value to be used (0 or 1).
        @type value: C{int}
        """
        if not value in [ 0, 1 ]:
            raise ValueError("bits must be 0 or 1.")
        if not (0 <= num < self._width):
            raise IndexError(num)
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
            ...
        IndexError: 4

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
        """ get_param bit using subscript syntax.

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
    
    def lshift(self, value):
        l = self._mask + value * [0]
        # do not pop !
#        for _ in range(0, value):
#            l.pop(0)
        return Mask(l)

    def rshift(self, value):
        l = value * [0] + self._mask
        for _ in range(0, value):
            l.pop(-1)
        return Mask(l)

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

    def __lshift__(self, value):
        return self.lshift(value)
        
    def __rshift__(self, value):
        return self.rshift(value)

    
class MemoryChunk(object):
    '''
    '''
    def __init__(self, mgr, name, cython_type, packed=False):
        ''' 
        '''
        self.name = name
        self.chunk_manager = mgr
        self.cython_type = cython_type
        self.packed = packed
        self.bits = bits_sizeof(cython_type) if packed else 0
        #self.bytes = bytes_sizeof(cython_type)
        self.hint = "no hint"
        
        self.bit_offset = 0
        self.field_offset = 0 
        
    def get_cython_type(self):
        return self.cython_type
    
    def get_attribute_name(self):
        if self.packed:
            return self.chunk_manager.packed_name
        else:
            return self.name

    def offset(self):
        return (self.field_offset, self.bit_offset)
    
    def mask(self):
        (_, chunk_type, _) = self.chunk_manager.packed_attribute()
        return Mask.build_mask(self.bit_offset, self.bits, bits_sizeof(chunk_type))

class ChunkManager(object):
    '''
    Manages memory space reserved to the object, bitfield like.
    '''

    def __init__(self, reserved_packed_name):
        '''
        Constructor
        '''
        self.packed_name = reserved_packed_name
        self.named_chunks = {}
        self.packed_chunks = [] # simple list holding packed memory chunks
        self.normal_chunks = [] # simple list holding memory chunks
        
        
        self.packed_type = TypeInfo.get('UnsignedChar')
        self.packed_field_size = bits_sizeof(self.packed_type)
        self.ordered_chunks = []
        self.packed_field_count = 0
        
    def order_chunks(self):
        self.ordered_chunks = sorted(self.packed_chunks, key=lambda x : -x.bits)
        fields = [(0,[])]
        
        for chunk in self.ordered_chunks:
            placed = False
            for i in range(len(fields)):
                (n, l) = fields[i]
                if n + chunk.bits <= self.packed_field_size:
                    l.append(chunk)
                    placed = True
                    fields[i] = (n+chunk.bits, l)
                    # print "BITS : ", chunk.bits
                    break
            if not placed:
                fields.append( (chunk.bits, [chunk]) )


        for field_offset, (n, chunks) in enumerate(fields):
            bit_offset = 0
            for chunk in chunks:
                chunk.field_offset = field_offset
                chunk.bit_offset = bit_offset
                bit_offset += chunk.bits
        # print " >>>>>>>>>> ", len(fields), fields
        self.packed_field_count = len(fields)

    def new_chunk(self, name, cython_type, packed=False):
        '''
        '''
        chunk = MemoryChunk(self, name, cython_type, packed)
        if name in self.named_chunks:
            raise RuntimeError 
        
        self.named_chunks[name] = chunk
        if packed: 
            self.packed_chunks.append(chunk)
            self.order_chunks()
        else:
            self.normal_chunks.append(chunk)
        return chunk
    
    def get_chunk(self, name):
        return self.named_chunks[name]
    
    def get_offset(self, chunk):
        assert(chunk.packed)
        bits = 0
        for c in self.packed_chunks:
            if c == chunk:
                return (bits / self.packed_field_size, bits % self.packed_field_count)
            bits += c.bits
        raise KeyError

    def packed_bits(self):
        """
        >>> chunk_manager = ChunkManager('reserved_name')
        >>> _ = chunk_manager.new_chunk('p1', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p2', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p3', TypeInfo.Bool, True)
        >>> chunk_manager.packed_bits()
        3
        """
        return sum(map((lambda x : x.bits), self.packed_chunks))
    
    def packed_bytes(self):
        """
        >>> chunk_manager = ChunkManager('reserved_name')
        >>> _ = chunk_manager.new_chunk('p1', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p2', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p3', TypeInfo.Bool, True)
        >>> chunk_manager.packed_bytes()
        1
        """
        bits = self.packed_bits()
        if bits % self.packed_field_size == 0:
            return bits / self.packed_field_size
        else:
            return bits / self.packed_field_size + 1

    def dump(self):
        '''
        Print human readable chunk_manager representation.
        >>> chunk_manager = ChunkManager('reserved_name')
        >>> _ = chunk_manager.new_chunk('p1', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p2', TypeInfo.Int,  False)
        >>> _ = chunk_manager.new_chunk('p3', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p4', TypeInfo.Bool, True)
        >>> _ = chunk_manager.new_chunk('p5', TypeInfo.Int, False)
        >>> chunk_manager.dump()
        '[ 1@p1 1@p3 1@p4 : 1 ][ 4@p2 ][ 4@p5 ]'

        '''
        result = ['[']
        for chunk in self.packed_chunks:
            result.append(' {}@{}'.format(chunk.bits, chunk.name))

        result.append(' : {}'.format(self.packed_bytes()))

        for chunk in self.normal_chunks:
            result.append(' ][ {}@{}'.format(chunk.bytes, chunk.name))
        result.append(' ]')
        return ''.join(result)

    def packed_attribute(self):
        return (self.packed_name, self.packed_type, self.packed_field_count)

    def normal_attributes(self):
        for chunk in self.normal_chunks:
            yield (chunk.name, chunk.cython_type)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE |
                                doctest.REPORT_ONLY_FIRST_FAILURE |
                                doctest.ELLIPSIS)
