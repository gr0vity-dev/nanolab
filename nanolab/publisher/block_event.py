class BlockConfirmationEvent:

    def __init__(self,
                 block_hash: str,
                 confirmed: bool,
                 conf_duration: float = None):
        self.block_hash = block_hash
        self.confirmed = confirmed
        self.conf_duration = conf_duration
