from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor
from smpp.pdu import operations
from smpp.pdu.error import PDUParseError

from pdu_bin import PDUBin, MsgDataListener


class MyProtocol(Protocol, PDUBin):

    def __init__(self):
        self._data_listener = None

    def dataReceived(self, data):
        # print data.__len__()
        # print data
        self._data_listener.append_buffer(data)
        msg = self._data_listener.get_msg()

        while msg is not None:
            if self.transport.disconnecting:
                # this is necessary because the transport may be told to lose
                # the connection by a previous packet, and it is
                # important to disregard all the packets following
                # the one that told it to close.
                return

            # try:
            #     self.pduReceived(self._bin2pdu(msg))
            # except PDUParseError as e:
            #     self.PDUParseErrorHandler(exception=e, wrong_bin=msg)
            pdu = self._bin2pdu(msg)
            self.pduReceived(pdu)
            msg = self._data_listener.get_msg()
            # pdu = self._bin2pdu(msg)
            # print pdu

    def connectionMade(self):
        self._data_listener = MsgDataListener()

    def connectionLost(self, reason):
        pass

    def pduReceived(self, pdu):
        # TODO states
        if pdu.commandId.key == 'submit_sm':
            # todo status
            self.transport.write(
                self._pdu2bin(operations.SubmitSMResp(seqNum=pdu.seqNum))
            )
        elif pdu.commandId.key == 'bind_transmitter':
            bind_resp = operations.BindTransmitterResp(seqNum=pdu.seqNum)
            # todo status, ANOTHER PARAMS READ DOC, check login psawd
            self.transport.write(self._pdu2bin(bind_resp))

        elif pdu.commandId.key == 'unbind':
            self.transport.write(self._pdu2bin(operations.UnbindResp(seqNum=pdu.seqNum)))
            # todo close connection


class MyServerFactory(ServerFactory):

    protocol = MyProtocol

    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        return p


reactor.listenTCP(2775, MyServerFactory())
reactor.run()