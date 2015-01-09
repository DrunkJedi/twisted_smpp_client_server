from twisted.internet.protocol import Protocol, ServerFactory, ClientCreator
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from smpp.pdu import operations
from smpp.pdu.pdu_types import CommandStatus
from smpp.pdu.error import PDUParseError

from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient
from txamqp.content import Content
import txamqp.spec

from pdu_bin import PDUBin, MsgDataListener
from server_settings import CLIENT_LOGIN, CLIENT_PASSWORD

import datetime

UNAUTHORIZED = 'unauthorized'
AUTHORIZED = 'authorized'
CONNECTED = 'connected'
DISCONNECTED = 'disconnected'


class MyProtocol(Protocol, PDUBin):

    def __init__(self):
        self._data_listener = None
        self.publish_channel = None

    @inlineCallbacks
    def initRabbitConnection(self):
        spec = txamqp.spec.load('amqp0-8.stripped.rabbitmq.xml')
        delegate = TwistedDelegate()
        protocol = yield ClientCreator(reactor, AMQClient, delegate=delegate, vhost='/',
                                            spec=spec).connectTCP('localhost', 5672)
        yield protocol.start({'LOGIN': 'sergey', 'PASSWORD': 'pepsi'})
        self.publish_channel = yield protocol.channel(1)
        yield self.publish_channel.channel_open()


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

    @inlineCallbacks
    def connectionMade(self):
        self._data_listener = MsgDataListener()
        self.state = CONNECTED
        yield self.initRabbitConnection()

    def connectionLost(self, reason):
        self.state = DISCONNECTED

    @inlineCallbacks
    def processMessage(self, msg):
        print self.publish_channel
        if self.publish_channel:
            result = yield self.publish_channel.queue_declare(exclusive=True)
            msg = Content('asdasdas')
            self.publish_channel.basic_publish(exchange='',
                                  routing_key='rpc_queue',
                                  content=msg)

    def pduReceived(self, pdu):
        if pdu.commandId.key == 'submit_sm':
            if self.state == AUTHORIZED:
                # TODO create connection to rabbit mq
                # TODO push message to route.send.result
                self.processMessage(pdu)

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