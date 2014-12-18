from mock import MagicMock
from twisted.test import proto_helpers
from smpp.pdu import pdu_types
from smpp.pdu.pdu_encoding import PDUEncoder
from smpp.pdu import operations
from mock import patch

from app.server import CONNECTED, DISCONNECTED, AUTHORIZED, UNAUTHORIZED
from server_settings import CLIENT_LOGIN, CLIENT_PASSWORD
from app.server import MyServerFactory


class TestServerProto:
    """
    Test server
    """

    IP = '127.0.0.1'

    def _setup(self):
        # setup before test
        factory = MyServerFactory()
        proto = factory.buildProtocol((self.IP, 0))
        trans = proto_helpers.StringTransport()

        return proto, trans

    def test_data_received_success(self):
        proto, trans = self._setup()

        proto.makeConnection(trans)

        # mock pduReceived
        proto.pduReceived = MagicMock()

        # create dummy pdus
        bind_tr = operations.BindTransmitter(seqNum=1, system_id='armen', password='666', system_type='speedflow')
        bind_trx = operations.BindTransceiver(seqNum=1, system_id='armen', password='666', system_type='speedflow')
        bind_rx = operations.BindReceiver(seqNum=1, system_id='armen', password='666', system_type='speedflow')
        pdus_list = (bind_rx, bind_tr, bind_trx)

        pdus_bin = ''.join([proto._pdu2bin(v) for v in pdus_list])

        parts_bin = []

        while pdus_bin:
            try:
                parts_bin.append(pdus_bin[:3])
                pdus_bin = pdus_bin[3:]
            except IndexError:
                parts_bin.append(pdus_bin)
                pdus_bin = ''

        # send bins to proto by
        for bin in parts_bin:
            proto.dataReceived(bin)

        # get all pdu received calls
        calls = proto.pduReceived.call_args_list

        assert pdus_list[0].__class__ == tuple(calls[0])[0][0].__class__
        assert pdus_list[1].__class__ == tuple(calls[1])[0][0].__class__
        assert pdus_list[2].__class__ == tuple(calls[2])[0][0].__class__

    def test_data_received_fail(self):
        proto, trans = self._setup()
        proto.makeConnection(trans)

        # mock PDUParseErrorHandler
        proto.PDUParseErrorHandler = MagicMock()

        # create dummy pdus
        bind_tr = operations.BindTransmitter(seqNum=1, system_id='armen', password='666', system_type='speedflow')
        valid_bin = proto._pdu2bin(bind_tr)
        bad_bin = valid_bin[:5] + 'f' + valid_bin[6:]

        proto.dataReceived(bad_bin)

        # get all pdu received calls
        assert proto.PDUParseErrorHandler.called

    def test_disconnect(self):
        proto, trans = self._setup()
        proto.makeConnection(trans)
        proto.connectionLost(self)
        assert proto.state == DISCONNECTED

    def test_statuses(self):
        proto, trans = self._setup()
        proto.makeConnection(trans)
        assert proto.state == CONNECTED
        proto.transport.write = MagicMock()
        pdu_bind_wrong = operations.BindTransmitter()
        # assert proto._bin2pdu(proto.transport.write.call_args_list.pop()[0][0]).status.key == 'ESME_RINVSYSID'
        pdu_submit_sm_wrong = operations.SubmitSM()

        # print proto._bin2pdu(proto.transport.write.call_args_list.pop()[0][0])
        pdu_bind = operations.BindTransmitter(seqNum=1,
                                         system_id=CLIENT_LOGIN,
                                         password=CLIENT_PASSWORD,
                                         system_type='speedflow')
        pdu_submit_sm = operations.SubmitSM()
        pdu_unbind = operations.Unbind()
        bin_list = [pdu_bind_wrong, pdu_submit_sm_wrong, pdu_bind, pdu_submit_sm, pdu_unbind, pdu_unbind]
        proto.connectionLost(proto)

        for pdu in bin_list:
            proto.dataReceived(proto._pdu2bin(pdu))

        # pdu_bind_wrong resp
        pdu = proto._bin2pdu(proto.transport.write.call_args_list[0][0][0])
        assert pdu.status.key == 'ESME_RINVSYSID' and pdu.commandId.key == 'bind_transmitter_resp'

        # pdu_submit_sm wrong
        pdu = proto._bin2pdu(proto.transport.write.call_args_list[1][0][0])
        assert pdu.status.key == 'ESME_RINVSYSID' and pdu.commandId.key == 'generic_nack'

        # pdu_bind ok
        pdu = proto._bin2pdu(proto.transport.write.call_args_list[2][0][0])
        assert pdu.status.key == 'ESME_ROK' and pdu.commandId.key == 'bind_transmitter_resp'

        # pdu_submit ok
        pdu = proto._bin2pdu(proto.transport.write.call_args_list[3][0][0])
        assert pdu.status.key == 'ESME_ROK' and pdu.commandId.key == 'submit_sm_resp'

        # pdu_unbind ok
        pdu = proto._bin2pdu(proto.transport.write.call_args_list[4][0][0])
        assert pdu.status.key == 'ESME_ROK' and pdu.commandId.key == 'unbind_resp'
