from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor
from smpp.pdu import operations
from smpp.pdu.pdu_types import CommandStatus
from smpp.pdu.error import PDUParseError

from pdu_bin import PDUBin, MsgDataListener
from server_settings import client_login, client_password

UNAUTORIZED = 'unauthorized'
AUTORIZED = 'authorized'
CONNECTED = 'connected'
DISCONNECTED = 'disconnected'

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

            try:
                self.pduReceived(self._bin2pdu(msg))
            except PDUParseError as e:
                self.PDUParseErrorHandler(exception=e, wrong_bin=msg)

            msg = self._data_listener.get_msg()

    def connectionMade(self):
        self._data_listener = MsgDataListener()
        self.state = CONNECTED

    def connectionLost(self, reason):
        self.state = DISCONNECTED

    def pduReceived(self, pdu):
        # TODO states
        if pdu.commandId.key == 'submit_sm':
            if self.state == AUTORIZED:
                submit_sm_resp = operations.SubmitSMResp(seqNum=pdu.seqNum, status=CommandStatus.ESME_ROK)
            else:
                submit_sm_resp = operations.SubmitSMResp(seqNum=pdu.seqNum, status=CommandStatus.ESME_RINVSYSID)
            self.transport.write(
                self._pdu2bin(submit_sm_resp)
            )
        elif pdu.commandId.key == 'bind_transmitter':
            if pdu.params['system_id'] == client_login and pdu.params['password'] == client_password:
                bind_resp = operations.BindTransmitterResp(seqNum=pdu.seqNum)
                self.state = AUTORIZED
            else:
                bind_resp = operations.BindTransmitterResp(seqNum=pdu.seqNum, status=CommandStatus.ESME_RINVSYSID)
                self.state = UNAUTORIZED
            self.transport.write(self._pdu2bin(bind_resp))

        elif pdu.commandId.key == 'unbind':
            self.transport.write(self._pdu2bin(operations.UnbindResp(seqNum=pdu.seqNum)))
            self.transport.loseConnection()


class MyServerFactory(ServerFactory):

    protocol = MyProtocol

    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        return p


reactor.listenTCP(2775, MyServerFactory())
reactor.run()