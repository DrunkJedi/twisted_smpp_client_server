from smpp.pdu.pdu_encoding import PDUEncoder
from StringIO import StringIO


class PDUBin():

    def _bin2pdu(self, bindata):
        io_pdu = StringIO(bindata)
        return PDUEncoder().decode(io_pdu)

    def _pdu2bin(self, bindata):
        return PDUEncoder().encode(bindata)