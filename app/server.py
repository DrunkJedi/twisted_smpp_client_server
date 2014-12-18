from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor
from smpp.pdu import operations
from smpp.pdu.pdu_types import CommandStatus
from smpp.pdu.error import PDUParseError

from pdu_bin import PDUBin, MsgDataListener
from server_settings import CLIENT_LOGIN, CLIENT_PASSWORD

UNAUTHORIZED = 'unauthorized'
AUTHORIZED = 'authorized'
CONNECTED = 'connected'
DISCONNECTED = 'disconnected'


class MyProtocol(Protocol, PDUBin):

    def __init__(self):
        self._data_listener = None

    def dataReceived(self, data):

        self._data_listener.append_buffer(data)
        msg = self._data_listener.get_msg()

        while msg is not None:
            # if self.transport.disconnecting:
            #     # this is necessary because the transport may be told to lose
            #     # the connection by a previous packet, and it is
            #     # important to disregard all the packets following
            #     # the one that told it to close.
            #     return

            try:
                pdu = self._bin2pdu(msg)
                self.pduReceived(pdu)
            except PDUParseError as e:
                self.PDUParseErrorHandler(exception=e, wrong_bin=msg)

            msg = self._data_listener.get_msg()

    def connectionMade(self):
        self._data_listener = MsgDataListener()
        self.state = CONNECTED

    def connectionLost(self, reason):
        self.state = DISCONNECTED

    def pduReceived(self, pdu):
        if pdu.commandId.key == 'submit_sm':
            if self.state == AUTHORIZED:
                resp_pdu = operations.SubmitSMResp(seqNum=pdu.seqNum, status=CommandStatus.ESME_ROK)
            else:
                resp_pdu = operations.GenericNack(seqNum=pdu.seqNum, status=CommandStatus.ESME_RINVSYSID)

            self.transport.write(
                self._pdu2bin(resp_pdu)
            )
        elif pdu.commandId.key == 'bind_transmitter':
            if pdu.params['system_id'] == CLIENT_LOGIN and pdu.params['password'] == CLIENT_PASSWORD:
                bind_resp = operations.BindTransmitterResp(seqNum=pdu.seqNum, status=CommandStatus.ESME_ROK)
                self.state = AUTHORIZED
            else:
                bind_resp = operations.BindTransmitterResp(seqNum=pdu.seqNum, status=CommandStatus.ESME_RINVSYSID)
                self.state = UNAUTHORIZED

            self.transport.write(self._pdu2bin(bind_resp))

        elif pdu.commandId.key == 'unbind':
            if self.state == AUTHORIZED:
                self.transport.write(self._pdu2bin(operations.UnbindResp(seqNum=pdu.seqNum)))
                self.transport.loseConnection()
            else:
                self.transport.write(self._pdu2bin(operations.GenericNack(seqNum=pdu.seqNum, status=CommandStatus.ESME_RINVSYSID)))


class MyServerFactory(ServerFactory):

    protocol = MyProtocol

    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        return p

if __name__ == '__main__':
    reactor.listenTCP(2775, MyServerFactory())
    reactor.run()