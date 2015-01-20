from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.protocol import ClientCreator
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
import txamqp.spec


class Consumer(object):
    def __init__(self, host, port, user, password, vhost, specfile):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.specfile = specfile

    @inlineCallbacks
    def run(self):
        delegate = TwistedDelegate()
        cc = ClientCreator(reactor, AMQClient, delegate=delegate,
                           vhost=self.vhost, spec=self.specfile)

        connection = yield cc.connectTCP(self.host, self.port)
        yield connection.authenticate(self.user, self.password)

        channel = yield connection.channel(1)
        yield channel.channel_open()

        channel.queue_declare(queue="process_queue", durable=True)

        yield channel.queue_bind(
            queue="process_queue", exchange="worker",
            routing_key="test_routing_key")

        yield channel.basic_consume(queue="process_queue", consumer_tag="test_consumer_tag", no_ack=True)

        queue = yield connection.queue("test_consumer_tag")
        while True:
            msg = yield queue.get()
            print msg



if __name__ == '__main__':
    spec = txamqp.spec.load("amqp0-8.stripped.rabbitmq.xml")
    consumer = Consumer('localhost', 5672, 'sergey', 'pepsi', '/', spec)
    reactor.callWhenRunning(consumer.run)
    reactor.run()