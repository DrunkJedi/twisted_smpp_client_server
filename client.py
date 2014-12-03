# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, task
from smpp.pdu import operations

from pdu_bin import PDUBin
from local_client_settings import HOST, PORT, LOGIN, PASSWORD, SMSCOUNT



class MyProtocol(Protocol, PDUBin):

    def __init__(self):
        self.submit_sm_resp_count = 0
        self.submit_sm_count = 0

        # created schedule task
        # will start after success auth
        self._send_sms = task.LoopingCall(self._submit_sm)

    def dataReceived(self, data):
        pdu = self._bin2pdu(data)
        if pdu.commandId.key == 'submit_sm_resp':
            self.submit_sm_resp_count += 1
            print 'submit_sm_resp: ', self.submit_sm_resp_count
            if SMSCOUNT == self.submit_sm_resp_count:
                self._unbind()
        elif pdu.commandId.key == 'bind_transmitter_resp' and pdu.status.key == 'ESME_ROK':
            print 'Auth OK'
            self._send_sms.start(0.2)
        elif pdu.commandId.key == 'unbind_resp':
            self.transport.loseConnection()
            print 'Unbinding done'
        else:
            print 'Get pdu {0}'.format(pdu)

    def connectionMade(self):
        self._bind()

    def connectionLost(self, reason):
        print 'onConnectionLost:'
        print self.transport.realAddress, '\n'

    def _get_seq_num(self):
        return self.submit_sm_count + 1

    def _submit_sm(self):
        if SMSCOUNT > self.submit_sm_count:
            seq_num = self._get_seq_num()

            print 'Submit sm: ', seq_num

            sm_pdu = operations.SubmitSM(
                seqNum=seq_num,
                short_message="This is MESSAGE!! {0}".format(seq_num),
                destination_addr='380660803034',
                source_address='380501234567'
            )

            self.transport.write(self._pdu2bin(sm_pdu))
            self.submit_sm_count += 1
        else:
            self._send_sms.stop()

    def _enqire_link(self):
        print 'Sending enqirelink start\n'
        enqlink = operations.EnquireLink(
            seqNum=1
        )
        enqlink = self._pdu2bin(enqlink)
        self.transport.write(enqlink)
        print 'Sending enqirelink done\n'

    def _unbind(self):
        print 'Unbinding start'
        unbind = operations.Unbind(
            seqNum=1
        )
        unbind = self._pdu2bin(unbind)
        self.transport.write(unbind)

    def _bind(self):
        bind_pdu = operations.BindTransmitter(seqNum=1,
                                              system_id=LOGIN,
                                              password=PASSWORD,
                                              system_type='speedflow')

        self.transport.write(self._pdu2bin(bind_pdu))


class EchoClientFactory(ClientFactory):
    protocol = MyProtocol

    def startedConnecting(self, connector):
        print 'Started to connect.', '\n'

    def buildProtocol(self, addr):
        p = ClientFactory.buildProtocol(self, addr)
        print 'Connected.'
        print 'protocol', p, '\n'
        return p

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason, '\n'

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason, '\n'


reactor.connectTCP(HOST, PORT, EchoClientFactory())
reactor.run()