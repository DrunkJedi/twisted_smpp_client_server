import binascii
from smpp.pdu.pdu_encoding import PDUEncoder
from StringIO import StringIO


class PDUBin():

    def _bin2pdu(self, bindata):
        io_pdu = StringIO(bindata)
        return PDUEncoder().decode(io_pdu)

    def _pdu2bin(self, bindata):
        return PDUEncoder().encode(bindata)


class MsgDataListener(object):
    """
    Load data and recognize smpp pdu header and return full msg.
    """
    COMMAND_LENGTH = 4

    def append_buffer(self, buffer):
        self._buffer += buffer

    def __init__(self):
        self._buffer = ''

    def get_msg(self):

        if len(self._buffer) >= self.COMMAND_LENGTH:
            length_bin = self._buffer[:self.COMMAND_LENGTH]
            length_hex = binascii.b2a_hex(length_bin)
            pdu_len = int(length_hex, 16)

            if len(self._buffer) >= pdu_len:
                msg = self._buffer[:pdu_len]
                self._buffer = self._buffer[pdu_len:]

                return msg
        return None