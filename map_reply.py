
from bitstring import ConstBitStream, BitArray, Bits
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
import numbers


def represent(class_name, instance_dict, ignore=[]):
    params = ['%s=%r' % (key, value)
              for key, value in instance_dict.iteritems()
              if not key.startswith('_') and key not in ignore]

    return "%s(%s)" % (class_name, ', '.join(params))


def get_bitstream_for_afi_address(address):

    # No address is AFI 0
    if address is None:
        return BitArray(16)

    # IPv4
    if isinstance(address, IPv4Address):
        return BitArray('uint:16=1, uint:32=%d' % int(address))

    elif isinstance(address, IPv4Network):
        return BitArray('uint:16=1, uint:32=%d' % int(address[0]))

    # IPv6
    elif isinstance(address, IPv6Address):
        return BitArray('uint:16=2, uint:128=%d' % int(address))

    elif isinstance(address, IPv6Network):
        return BitArray('uint:16=2, uint:128=%d' % int(address[0]))

    #TODO: los primeros 16 bits puede que tengan que ser la barra de la direccion, no 1s o 2s segun si es IPv4 o IPv6

    else:
        raise ValueError('Unsupported address type')


class LocatorRecord(object):

    def __init__(self, priority=0, weight=0, mpriority=0, mweight=0, unusedflags=0, LpR=0, loc_afi='0'*16, locator='0.0.0.0'):
        self.priority = priority
        self.weight = weight
        self.mpriority = mpriority
        self.mweight = mweight
        self.unusedflags = unusedflags
        self.LpR = LpR
        self.loc_afi = loc_afi
        self.locator = locator

    def __iter__(self):
        return iter(self)

    def to_bytes(self):
        return self.to_bitstream().bytes

    def to_bitstream(self):

        # Start with the priority
        bitstream = BitArray('uint:8=%d' % self.priority)

        # Add the weight
        bitstream += BitArray('uint:8=%d' % self.weight)

        # Add the M priority
        bitstream += BitArray('uint:8=%d' % self.mpriority)

        # Add the M weight
        bitstream += BitArray('uint:8=%d' % self.mweight)

        # Add the unused flags
        bitstream += BitArray('uint:13=%d' % self.unusedflags)

        # Add the LpR
        bitstream += BitArray('uint:3=%d' % self.LpR)

        #Add the locator afi
        bitstream += BitArray('uint:16=%d' % self.loc_afi)

        #Add the locator
        if (self.loc_afi == '1'*16):
            bitstream += BitArray('uint:32=%d' % self.locator)
        elif (self.loc_afi == '2'*16):
            bitstream += BitArray('uint:128=%d' % self.locator)
        else:
            raise Exception ('Bad AFI in LocatoRecord')

        return bitstream

class MapReplyRecord(object):
    # The actions defined are used by an ITR or PITR when a
    # destination EID matches a negative mapping cache entry.
    # Unassigned values should cause a map-cache entry to be created
    # and, when packets match this negative cache entry, they will be
    # dropped.  The current assigned values are:
    #
    # (0) No-Action:  The map-cache is kept alive and no packet
    #    encapsulation occurs.
    #
    # (1) Natively-Forward:  The packet is not encapsulated or dropped
    #    but natively forwarded.
    #
    # (2) Send-Map-Request:  The packet invokes sending a Map-Request.
    #
    # (3) Drop:  A packet that matches this map-cache entry is dropped.
    #    An ICMP Unreachable message SHOULD be sent.
    ACT_NO_ACTION = 0
    ACT_NATIVELY_FORWARD = 1
    ACT_SEND_MAP_REQUEST = 2
    ACT_DROP = 3

    def __init__(self, ttl=24*60, action=ACT_NO_ACTION, authoritative=False,
                 map_version=0, eid_prefix=None, locator_records=None):
        '''
        Constructor
        '''
        # Set defaults
        self.ttl = ttl
        self.action = action
        self.authoritative = authoritative
        self.map_version = map_version
        self.eid_prefix = eid_prefix
        self.locator_records = list(locator_records or [])  # array de objetos de la clase LocatorRecord

        # Store space for reserved bits
        self._reserved1 = BitArray(12 + 4)

    def __repr__(self):
        return represent(self.__class__.__name__, self.__dict__)


    def to_bytes(self):
        '''
        Create bytes from properties
        '''
        return self.to_bitstream().bytes

    def to_bitstream(self):
        '''
        Create bitstream from properties
        '''

        # Start with the TTL
        bitstream = BitArray('uint:32=%d' % self.ttl)

        # Add the locator count
        bitstream += BitArray('uint:8=%d' % len(self.locator_records))

        # Add the EID prefix mask length
        bitstream += BitArray('uint:8=%d' % self.eid_prefix.prefixlen)

        # Add the NMR action
        bitstream += BitArray('uint:3=%d' % self.action)

        # Add the authoritative flag
        bitstream += BitArray('bool=%d' % self.authoritative)

        # Add reserved bits
        bitstream += self._reserved1

        # Add the map version
        bitstream += BitArray('uint:12=%d' % self.map_version)

        # Add the EID prefix
        bitstream += get_bitstream_for_afi_address(self.eid_prefix)

        # Add the locator records
        for locator_record in self.locator_records:
            try:
                bitstream += locator_record.to_bitstream()
            except:
                raise Exception('Bad locator in MapReplyRecord')

        return bitstream
