from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor
from smpp.pdu import operations

from pdu_bin import PDUBin


class MyProtocol(Protocol, PDUBin):

    def __init__(self):
        pass

    def dataReceived(self, data):
        pdu = self._bin2pdu(data)
        print pdu

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

    def connectionLost(self, reason):
        pass


class MyServerFactory(ServerFactory):

    protocol = MyProtocol

    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        return p


reactor.listenTCP(2775, MyServerFactory())
reactor.run()