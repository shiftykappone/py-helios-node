from abc import (
    ABCMeta,
    abstractmethod
)
from collections.abc import (
    MutableMapping,
)


class BaseDB(MutableMapping, metaclass=ABCMeta):
    """
    This is an abstract key/value lookup with all :class:`bytes` values,
    with some convenience methods for databases. As much as possible,
    you can use a DB as if it were a :class:`dict`.

    Notable exceptions are that you cannot iterate through all values or get the length.
    (Unless a subclass explicitly enables it).

    All subclasses must implement these methods:
    __init__, __getitem__, __setitem__, __delitem__

    Subclasses may optionally implement an _exists method
    that is type-checked for key and value.
    """

    @abstractmethod
    def __init__(self) -> None:
        raise NotImplementedError(
            "The `init` method must be implemented by subclasses of BaseDB"
        )

    def set(self, key: bytes, value: bytes) -> None:
        self[key] = value

    def exists(self, key: bytes) -> bool:
        return self.__contains__(key)

    def __contains__(self, key):
        if hasattr(self, '_exists'):
            return self._exists(key)
        else:
            return super().__contains__(key)

    def delete(self, key: bytes) -> None:
        try:
            del self[key]
        except KeyError:
            return None

    def __iter__(self):
        raise NotImplementedError("By default, DB classes cannot by iterated.")

    def __len__(self):
        raise NotImplementedError("By default, DB classes cannot return the total number of keys.")


class BaseAtomicDB(BaseDB):
    """
    This is an abstract key/value lookup that permits batching of updates, such that the batch of
    changes are atomically saved. They are either all saved, or none are.

    Writes to the database are immediately saved, unless they are explicitly batched
    in a context, like this:

    ::

        atomic_db = AtomicDB()
        with atomic_db.atomic_batch() as db:
            # changes are not immediately saved to the db, inside this context
            db[key] = val

            # changes are still locally visible even though they are not yet committed to the db
            assert db[key] == val

            if some_bad_condition:
                raise Exception("something went wrong, erase all the pending changes")

            db[key2] = val2
            # when exiting the context, the values are saved either key and key2 will both be saved,
            # or neither will
    """
    @abstractmethod
    def atomic_batch(self):
        raise NotImplementedError
