from tarpit.dao import MongoBase


class MongoSession(MongoBase):
    """Mongo Template."""

    __collection_name__ = 'session'
    __alias__ = 'session'  # optional

    @staticmethod
    def __collection_init__(client):
        """Write some collection initial operation, like set some index."""
        client.storage.drop_indexes()
        client.storage.create_index('timestamp', expireAfterSeconds=86400)
        client.storage.create_index('mail')

    def insert_image(self):
        return self.client.image.update_one(
            {'session_id': 1}, {'$set': {
                'user_id': 2,
                'user_name': 'lkjklj'
            }},
            upsert=True)
