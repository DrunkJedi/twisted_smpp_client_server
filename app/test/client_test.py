from mock import MagicMock
from twisted.test import proto_helpers

from smpp.pdu.pdu_types import CommandStatus
from smpp.pdu import operations
from app.client import EchoClientFactory
from app.client import CONNECTED, DISCONNECTED, BINDED, UNBINDED

class TestClientProtoCreation:
    """
    Test creation of client proto instance ...etc
    """
    IP = '127.0.0.1'

    def _setup(self):
        # setup before test
        factory = EchoClientFactory()
        proto = factory.buildProtocol((self.IP, 0))
        trans = proto_helpers.StringTransport()

        return proto, trans

    def test_bind_fail(self):
        proto, trans = self._setup()
        proto.makeConnection(trans)
        proto._bind()
        pdu_bind_resp = operations.BindTransmitterResp(seqNum=1, status=CommandStatus.ESME_RINVSYSID)
        proto.dataReceived(proto._pdu2bin(pdu_bind_resp))
        assert proto.state != BINDED

    def test_bind_success(self):
        proto, trans = self._setup()
        proto.makeConnection(trans)
        proto._bind()
        pdu_bind_resp = operations.BindTransmitterResp(seqNum=1, status=CommandStatus.ESME_ROK)
        proto.dataReceived(proto._pdu2bin(pdu_bind_resp))
        assert proto.state == BINDED

    def test_asdasdasdas(self):
        proto, trans = self._setup()

        # Send 1 message
        proto.SMSCOUNT = 1

        proto.makeConnection(trans)
        proto.transport.write = MagicMock()
        proto._bind()
        pdu_bind = proto._bin2pdu(proto.transport.write.call_args_list.pop()[0][0])
        assert pdu_bind.status == CommandStatus.ESME_ROK and pdu_bind.commandId.key == 'bind_transmitter'

        # send fake bind_resp for BIND
        pdu_bind_resp = operations.BindTransmitterResp(seqNum=1, status=CommandStatus.ESME_ROK)
        proto.dataReceived(proto._pdu2bin(pdu_bind_resp))

        pdu_submit_sm = proto._bin2pdu(proto.transport.write.call_args_list.pop()[0][0])
        assert pdu_submit_sm.status == CommandStatus.ESME_ROK and pdu_submit_sm.commandId.key == 'submit_sm'

        pdu_submit_sm_resp = operations.SubmitSMResp(seqNum=1, status=CommandStatus.ESME_ROK)
        proto.dataReceived(proto._pdu2bin(pdu_submit_sm_resp))

        # client must send unbind pdu
        pdu_unbind = proto._bin2pdu(proto.transport.write.call_args_list.pop()[0][0])
        assert pdu_unbind.status == CommandStatus.ESME_ROK and pdu_unbind.commandId.key == 'unbind'

        # sending unbind_resp
        pdu_unbind_resp = operations.UnbindResp(seqNum=pdu_unbind.seqNum, status=CommandStatus.ESME_ROK)
        proto.dataReceived(proto._pdu2bin(pdu_unbind_resp))
        assert proto.state == UNBINDED

