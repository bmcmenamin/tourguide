"""
    Class for caching function responses in FireStore DB
"""
import functools
import hashlib
import logging
import pickle
import zlib

from time import time

from google.cloud import firestore
from google.api_core.exceptions import InvalidArgument


logging.basicConfig(level=logging.INFO)


def to_zip_string(obj):
    return zlib.compress(pickle.dumps(obj))


def unzip_string(zip_str):
    return pickle.loads(zlib.decompress(zip_str))


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

        zipped_string = doc_data._data.get('val')
        if zipped_string:
            return unzip_string(zipped_string)

    def upsert_val_for_key(self, key, val):

        document = self.fs_collection.document(key)
        doc_data = document.get()

        to_cache = {'val': to_zip_string(val)}

        try:
            if doc_data.exists:
                logging.info(
                    "Updating key-value for {}/{} found."
                    .format(self.subcollection, key)
                )
                document.update(to_cache)
            else:
                logging.info(
                    "Adding new key {}/{}".format(self.subcollection, key))
                document.set(to_cache)
        except InvalidArgument:
            logging.warn(
                "Value Not Upserted for {}/{}".format(self.subcollection, key)
            )
