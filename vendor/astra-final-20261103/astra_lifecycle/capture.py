"""Fixture replay of viewer events; deliberately no live transport or client."""
from .adapters import Adapters
from .contracts import require, timestamp


class ReplayIntake:
    def __init__(self, lifecycle):
        self.gateway = Adapters(lifecycle)

    def ingest(self, event):
        require(isinstance(event, dict) and event.get('mode') == 'fixture-replay',
                'only fixture replay input is supported; live capture is unbuilt')
        require(set(event) == {'mode', 'id', 'text', 'contributor_id', 'channel', 'timestamp'},
                'closed replay event required')
        require(all(isinstance(event[k], str) and event[k].strip() for k in event),
                'replay fields must be nonempty strings')
        timestamp(event['timestamp'])
        # Stable upstream ID goes durable before any assembly acknowledgement.
        return self.gateway.call('A07', 'intake', prompt_id=event['id'], text=event['text'],
                                 contributor_id=event['contributor_id'], channel=event['channel'],
                                 received_at=event['timestamp'])
