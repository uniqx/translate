# -*- coding: utf-8 -*-

from io import BytesIO
from pytest import raises
from translate.misc.multistring import multistring
from translate.storage import base, jsonl10n, test_monolingual
from textwrap import dedent


JSON_I18NEXT = b"""{
    "key": "value",
    "keyDeep": {
        "inner": "value"
    },
    "keyPluralSimple": "the singular",
    "keyPluralSimple_plural": "the plural",
    "keyPluralMultipleEgArabic_0": "the plural form 0",
    "keyPluralMultipleEgArabic_1": "the plural form 1",
    "keyPluralMultipleEgArabic_2": "the plural form 2",
    "keyPluralMultipleEgArabic_3": "the plural form 3",
    "keyPluralMultipleEgArabic_4": "the plural form 4",
    "keyPluralMultipleEgArabic_5": "the plural form 5"
}
"""
JSON_I18NEXT_PLURAL = b"""{
    "key": "value",
    "keyDeep": {
        "inner": "value"
    },
    "keyPluralSimple": "Ahoj",
    "keyPluralMultipleEgArabic": "Nazdar"
}
"""
JSON_ARRAY = b"""{
    "key": [
        "One",
        "Two",
        "Three"
    ]
}
"""
JSON_GOI18N = b"""{
    "key": "simple value",
    "keyWithId": {
        "id": "plural-plus-id-123",
        "other": "Value for {{.Person}}"
    },
    "keyPluralOneOther": {
        "one": "I have {{.Count}} item.",
        "other": "I have {{.Count}} items."
    },
    "keyPluralMany": {
        "zero": "zeroth",
        "one": "first",
        "two": "second",
        "few": "least",
        "many": "most"
    },
    "keyWithNote": {
        "description": "This is a unit with a note.",
        "other": "value with a note"
    }
}
"""


class TestJSONResourceUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = jsonl10n.JsonUnit


class TestJSONResourceStore(test_monolingual.TestMonolingualStore):
    StoreClass = jsonl10n.JsonFile

    def test_serialize(self):
        store = self.StoreClass()
        store.parse('{"key": "value"}')
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == b'{\n    "key": "value"\n}\n'

    def test_error(self):
        store = self.StoreClass()
        with raises(base.ParseError):
            store.parse('{"key": "value"')

    def test_filter(self):
        store = self.StoreClass(filter=['key'])
        store.parse('{"key": "value", "other": "second"}')
        assert len(store.units) == 1
        assert store.units[0].source == 'value'

    def test_ordering(self):
        store = self.StoreClass()
        store.parse('''{
    "foo": "foo",
    "bar": "bar",
    "baz": "baz"
}''')

        assert store.units[0].source == 'foo'
        assert store.units[2].source == 'baz'

    def test_args(self):
        store = self.StoreClass()
        store.parse('''{
    "foo": "foo",
    "bar": "bar",
    "baz": "baz"
}''')
        store.dump_args['sort_keys'] = True

        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == b'''{
    "bar": "bar",
    "baz": "baz",
    "foo": "foo"
}
'''

    def test_bom(self):
        content = "{}\n".encode("utf-8-sig")
        store = self.StoreClass()
        store.parse(content)
        assert len(store.units) == 0
        out = BytesIO()
        store.serialize(out)
        assert out.getvalue() == content


class TestJSONNestedResourceStore(test_monolingual.TestMonolingualUnit):
    StoreClass = jsonl10n.JsonNestedFile

    def test_serialize(self):
        store = self.StoreClass()
        store.parse('{"key": {"second": "value"}}')
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == b'{\n    "key": {\n        "second": "value"\n    }\n}\n'

    def test_ordering(self):
        data = b'''{
    "foo": "foo",
    "bar": {
        "ba1": "bag",
        "ba2": "bag",
        "ba3": "bag",
        "ba4": "baz"
    }
}
'''
        store = self.StoreClass()
        store.parse(data)

        assert store.units[0].source == 'foo'
        assert store.units[1].getid() == '.bar.ba1'
        assert store.units[2].getid() == '.bar.ba2'
        assert store.units[3].getid() == '.bar.ba3'
        assert store.units[4].getid() == '.bar.ba4'

        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == data

    def test_array(self):
        store = self.StoreClass()
        store.parse(JSON_ARRAY)

        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == JSON_ARRAY


class TestWebExtensionUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = jsonl10n.WebExtensionJsonUnit


class TestWebExtensionStore(test_monolingual.TestMonolingualStore):
    StoreClass = jsonl10n.WebExtensionJsonFile

    def test_serialize(self):
        store = self.StoreClass()
        store.parse('{"key": {"message": "value", "description": "note"}}')
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == b'{\n    "key": {\n        "message": "value",\n        "description": "note"\n    }\n}\n'

    def test_serialize_no_description(self):
        store = self.StoreClass()
        store.parse('{"key": {"message": "value"}}')
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == b'{\n    "key": {\n        "message": "value"\n    }\n}\n'

    def test_set_target(self):
        store = self.StoreClass()
        store.parse('{"key": {"message": "value", "description": "note"}}')
        store.units[0].target = 'another'
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == b'{\n    "key": {\n        "message": "another",\n        "description": "note"\n    }\n}\n'

    def test_placeholders(self):
        DATA = """{
    "youCanClose": {
        "message": "Bravo ! Votre compte $SITE$ est relié à Scrobbly. Vous pouvez fermer et revenir en arrière",
        "placeholders": {
            "site": {
                "content": "$1",
                "example": "AniList"
            }
        }
    }
}
""".encode('utf-8')

        store = self.StoreClass()
        store.parse(DATA)
        assert store.units[0].placeholders is not None
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == DATA


class TestI18NextStore(test_monolingual.TestMonolingualStore):
    StoreClass = jsonl10n.I18NextFile

    def test_serialize(self):
        store = self.StoreClass()
        store.parse(JSON_I18NEXT)
        out = BytesIO()
        store.serialize(out)

        print('dir(store):', dir(store))
        print('store.units:', store.units)
        print('store.units[0]:', store.units[0])
        print('store.units[0]._id:', store.units[0]._id)
        print('store.units[0]._item:', store.units[0]._item)

        assert out.getvalue() == JSON_I18NEXT
        # assert False

    def test_units(self):
        store = self.StoreClass()
        store.parse(JSON_I18NEXT)
        assert len(store.units) == 4

    def test_plurals(self):
        store = self.StoreClass()
        store.parse(JSON_I18NEXT)

        # Remove plurals
        store.units[2].target = 'Ahoj'
        store.units[3].target = 'Nazdar'
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == JSON_I18NEXT_PLURAL

        # Bring back plurals
        store.units[2].target = multistring([
            "the singular",
            "the plural",
        ])
        store.units[3].target = multistring([
            "the plural form 0",
            "the plural form 1",
            "the plural form 2",
            "the plural form 3",
            "the plural form 4",
            "the plural form 5"
        ])
        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == JSON_I18NEXT

    def test_new_plural(self):
        EXPECTED = b'''{
    "simple": "the singular",
    "simple_plural": "the plural",
    "complex_0": "the plural form 0",
    "complex_1": "the plural form 1",
    "complex_2": "the plural form 2",
    "complex_3": "the plural form 3",
    "complex_4": "the plural form 4",
    "complex_5": "the plural form 5"
}
'''
        store = self.StoreClass()

        unit = self.StoreClass.UnitClass(
            multistring([
                "the singular",
                "the plural",
            ]),
            'simple'
        )
        store.addunit(unit)

        unit = self.StoreClass.UnitClass(
            multistring([
                "the plural form 0",
                "the plural form 1",
                "the plural form 2",
                "the plural form 3",
                "the plural form 4",
                "the plural form 5"
            ]),
            'complex'
        )
        store.addunit(unit)

        out = BytesIO()
        store.serialize(out)

        assert out.getvalue() == EXPECTED


class TestGoI18nJsonStore(test_monolingual.TestMonolingualStore):
    StoreClass = jsonl10n.GoI18nJsonFile

    #def test_serialize(self):
    #    store = self.StoreClass()
    #    store.parse(JSON_GOI18N)
    #    out = BytesIO()
    #    store.serialize(out)

    #    assert out.getvalue() == JSON_GOI18N

    def test_units(self):
        store = self.StoreClass()
        store.parse(JSON_GOI18N)
        assert [x.getid() for x in store.units] == [
            '.key',
            '.plural-plus-id-123',
            '.keyPluralOneOther',
            '.keyPluralMany',
            '.keyWithNote',
        ]
        assert [x.getkey() for x in store.units] == [
            'key',
            'plural-plus-id-123',
            'keyPluralOneOther',
            'keyPluralMany',
            'keyWithNote',
        ]

    def test_plurals(self):
        store = self.StoreClass()
        store.parse(JSON_GOI18N)

        assert store.units[0].target == "simple value"
        assert store.units[1].target == "Value for {{.Person}}"
        assert store.units[2].target == multistring([
            "I have {{.Count}} item.",
            "I have {{.Count}} items.",
        ])
        assert store.units[3].target == multistring([
            "zeroth",
            "first",
            "second",
            "least",
            "most",
        ])
        assert store.units[4].target == "value with a note"

    def test_notes(self):
        store = self.StoreClass()
        store.parse(JSON_GOI18N)

        assert store.units[4].target == "value with a note"
        assert store.units[4].getnotes() == "This is a unit with a note."

    def test_simple_serialize(self):
        EXPECTED = dedent('''\
        {
            "some": "value"
        }
        ''')

        store = self.StoreClass()
        unit = self.StoreClass.UnitClass(
            'some', 'value'
        )
        print('_id:', unit._id)
        print('_item:', unit._item)
        print('_target:', unit._target)
        print('target:', unit.target)
        print('dir(unit):', dir(unit))
        store.addunit(unit)

        out = BytesIO()
        store.serialize(out)

        # assert out.getvalue().decode('utf-8') == EXPECTED

    #     # Remove plurals
    #     store.units[2].target = 'Ahoj'
    #     store.units[3].target = 'Nazdar'
    #     out = BytesIO()
    #     store.serialize(out)

    #     assert out.getvalue() == JSON_I18NEXT_PLURAL

    #     # Bring back plurals
    #     store.units[2].target = multistring([
    #         "the singular",
    #         "the plural",
    #     ])
    #     store.units[3].target = multistring([
    #         "the plural form 0",
    #         "the plural form 1",
    #         "the plural form 2",
    #         "the plural form 3",
    #         "the plural form 4",
    #         "the plural form 5"
    #     ])
    #     out = BytesIO()
    #     store.serialize(out)

    #     assert out.getvalue() == JSON_I18NEXT

    # def test_new_plural(self):
    #     EXPECTED = b'''{
    # "simple": "the singular",
    # "simple_plural": "the plural",
    # "complex_0": "the plural form 0",
    # "complex_1": "the plural form 1",
    # "complex_2": "the plural form 2",
    # "complex_3": "the plural form 3",
    # "complex_4": "the plural form 4",
    # "complex_5": "the plural form 5"
#}
#'''
    #     store = self.StoreClass()

    #     unit = self.StoreClass.UnitClass(
    #         multistring([
    #             "the singular",
    #             "the plural",
    #         ]),
    #         'simple'
    #     )
    #     store.addunit(unit)

    #     unit = self.StoreClass.UnitClass(
    #         multistring([
    #             "the plural form 0",
    #             "the plural form 1",
    #             "the plural form 2",
    #             "the plural form 3",
    #             "the plural form 4",
    #             "the plural form 5"
    #         ]),
    #         'complex'
    #     )
    #     store.addunit(unit)

    #     out = BytesIO()
    #     store.serialize(out)

    #     assert out.getvalue() == EXPECTED

