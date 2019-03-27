from tarpit.dao import MongoBase


class MongoSession(MongoBase):
    """Mongo Template."""

    __collection_name__ = 'session'
    __alias__ = 'session'  # optional

    def __collection_init__(self):
        """Write some collection initial operation, like set some index."""
        self.sync_client.storage.drop_indexes()
        self.sync_client.storage.create_index(
            'timestamp', expireAfterSeconds=86400)
        self.sync_client.storage.create_index('mail')

    async def insert_image(self):
        await self.client.image.update_one(
            {'session_id': 1}, {'$set': {
                'user_id': 2,
                'user_name': 'lkjklj'
            }},
            upsert=True)
