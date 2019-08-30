"""
    Class for caching function responses in FireStore DB
"""
import functools
import hashlib
import logging

from time import time

from google.cloud import firestore


logging.basicConfig(level=logging.INFO)


class FirestoreCacher(object):

    ROOT_COLLECTION = "tourguide_cache"
    INTERCOLLECTION_BUFFER = "doc"

    @staticmethod
    def hash_inputs_to_key(*args, **kwargs):
        """Hash function inputs to string"""
        hasher = hashlib.md5()
        hasher.update(str(args).encode())
        hasher.update(str(kwargs).encode())
        return hasher.hexdigest()

    @staticmethod
    def _elapsed_days(document):
        now = time()
        last_update = document.update_time.seconds
        return (now - last_update) / (60 * 60 * 24)

    def _get_collection_path(self):

        if isinstance(self.subcollection, str):
            collection_labels = [self.ROOT_COLLECTION, self.subcollection]
        else:
            collection_labels = [self.ROOT_COLLECTION] + self.subcollection

        all_labels = [
            _label
            for label in collection_labels
            for _label in (label, self.INTERCOLLECTION_BUFFER)
        ]

        return "/".join(all_labels[:-1])

    def __init__(self, subcollection, max_lapsed_days=180):

        self.subcollection = subcollection
        self.max_lapsed_days = max_lapsed_days

        self.fs_db = firestore.Client()

        self.fs_collection = (
            self.fs_db
            .collection(self._get_collection_path())
        )

    def get_val_by_key(self, key):
        """ Get data from document by key, unless it
            hasn't been updated recently
        """
        doc_data = self.fs_collection.document(key).get()

        if not doc_data.exists:
            logging.info(
                "No key-value for {}/{} found in cache"
                .format(self.subcollection, key)
            )
            return None

        days_lapsed = self._elapsed_days(doc_data)
        if days_lapsed > self.max_lapsed_days:
            logging.info(
                "Expired key-value for {}/{} found. {} days old."
                .format(self.subcollection, key, days_lapsed)
            )
            return None

        logging.info(
            "Found key-value for {}/{}.".format(self.subcollection, key))

        return doc_data._data

    def upsert_val_for_key(self, key, val):

        document = self.fs_collection.document(key)
        doc_data = document.get()

        if doc_data.exists:
            logging.info(
                "Updating key-value for {}/{} found."
                .format(self.subcollection, key)
            )
            document.update(val)
        else:
            logging.info(
                "Adding new key {}/{}".format(self.subcollection, key))
            document.set(val)


def firestore_cache_wrapper(subcollection, max_lapsed_days=180):

    CACHE = FirestoreCacher(
        subcollection,
        max_lapsed_days=max_lapsed_days
    )

    def cachewrapped_function(function):

        @functools.wraps(function)
        def _cachewrapped_function(*args, **kwargs):

            key = CACHE.hash_inputs_to_key(*args, **kwargs)
            from_cache = CACHE.get_val_by_key(key)
            if from_cache is not None:
                return from_cache["output"]

            to_cache = {
                "args": list(args),
                "kwargs": kwargs,
                "output": function(*args, **kwargs)
            }

            CACHE.upsert_val_for_key(key, to_cache)
            return to_cache["output"]
        return _cachewrapped_function

    return cachewrapped_function
