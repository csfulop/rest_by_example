import json_merge_patch
import pecan
from pecan import expose, abort, request
from pecan.rest import RestController

from restbyexample.phonebook.db.adapter import PhonebookDbAdapter, Entry, PhonebookDbException
from restbyexample.phonebook.pecan.utils import objToDict


class PhonebookEntryController(RestController):
    """
    Pecan controller object to handle requests for a given Phonebook Entry.
    """

    def __init__(self, db_adapter: PhonebookDbAdapter, entry_id: str) -> None:
        super().__init__()
        self._db_adapter = db_adapter
        self._entry_id = entry_id

    @expose(template='json')
    def get_all(self) -> Entry:
        """
        Query a Phonebook Entry
        :return: the Phonebook Entry
        """
        result = self._db_adapter.get(self._entry_id)
        if result is None:
            abort(404)
        else:
            return result

    @expose(template='json')
    def put(self) -> Entry:
        """
        Modify a Phonebook Entry.
        The entire content of the Entry will be replaced with the JSON request body.
        :return: the modified Phonebook Entry
        """
        modified_entry = request.json
        entry_id = modified_entry.pop('id', None)
        if not entry_id:
            entry_id = self._entry_id
        elif entry_id != self._entry_id:
            abort(400, detail='Entry ID in URL and body mismatch')
        entry = Entry(entry_id, **modified_entry)
        if self._db_adapter.get(entry_id):  # TODO: add exists to adapter
            self._db_adapter.modify(entry)
        else:
            self._db_adapter.add(entry)
        return entry

    @expose(template='json')
    def patch(self) -> Entry:
        """
        Modify a Phonebook Entry.
        The exising content of the Entry will patched with the JSON request body according to RFC7386 https://tools.ietf.org/html/rfc7386
        :return: the modified Phonebook Entry
        """
        actual = objToDict(self._db_adapter.get(self._entry_id))
        if actual is None:
            abort(404, detail='Entry does not exists with ID: ' + self._entry_id)
        patch = request.json
        if 'id' in patch and patch['id'] != self._entry_id:
            abort(400, detail='Entry ID in URL and body mismatch')
        result = json_merge_patch.merge(actual, patch)
        result.pop('id')
        self._db_adapter.modify(Entry(self._entry_id, **result))
        return self._db_adapter.get(self._entry_id)

    @expose(template='json')
    def delete(self) -> None:
        """
        Delete a Phonebook Entry.
        """
        try:
            self._db_adapter.remove(self._entry_id)
            pecan.response.status = 204
        except PhonebookDbException as e:
            abort(404, e.args[0])
