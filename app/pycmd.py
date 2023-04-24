import time
import app.nano_node_interaction as nni


class NodeCommands:
    pass


class TestClass:

    def long_running_method(self, duration=1):
        time.sleep(duration)


class NodeInteraction:

    def publish_blocks_test(self):
        nni.xnolib_publish()
