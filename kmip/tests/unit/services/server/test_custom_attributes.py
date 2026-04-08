import mock
import shutil
import sqlalchemy

import tempfile
import testtools

from kmip.core import enums
from kmip.core import exceptions

from kmip.core.factories import attributes as factory

from kmip.core.messages import contents
from kmip.core.messages import payloads

from kmip.pie import objects as pie_objects
from kmip.pie import sqltypes

from kmip.services.server import engine


class MockRegexString(str):
    """
    A comparator string for doing simple containment regex comparisons
    for mock asserts.
    """
    def __eq__(self, other):
        return self in other

class TestCustomAttributes(testtools.TestCase):
    def setUp(self):
        super(TestCustomAttributes, self).setUp()

        self.engine = sqlalchemy.create_engine(
            'sqlite:///:memory:',
            #####'sqlite:////home/ym/tmp/kmiptest-testdelete.db',
        )
        sqltypes.Base.metadata.create_all(self.engine)
        self.session_factory = sqlalchemy.orm.sessionmaker(
            bind=self.engine,
            expire_on_commit=False
        )

        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def tearDown(self):
        super(TestCustomAttributes, self).tearDown()

    def _create_kmip_engine(self):
        e = engine.KmipEngine()
        e._protocol_version = contents.ProtocolVersion(1, 4)
        e._attribute_policy._version = e._protocol_version
        e._data_store = self.engine
        e._data_store_session_factory = self.session_factory
        e._data_session = e._data_store_session_factory()
        e._is_allowed_by_operation_policy = mock.Mock(return_value=True)
        e._logger = mock.MagicMock()
        return e

    def test_private_functions(self):
        e = self._create_kmip_engine()

        managed_object = pie_objects.SymmetricKey(
            enums.CryptographicAlgorithm.AES,
            0,
            b''
        )

        attribute_value_factory = factory.AttributeValueFactory()
        attribute_name = "x-scinet-test"
        attribute_value = attribute_value_factory.create_attribute_value(attribute_name, "test-value")
        e._set_attribute_on_managed_object(
            managed_object,
            (attribute_name, attribute_value)
        )
        
        # engine.KmipEngine._get_attribute_from_managed_object not implemented for custom attributes!        
        attributes = e._get_attributes_from_managed_object(
            managed_object,
            [attribute_name]
        )
        
        self.assertEqual(1, len(attributes))
        self.assertEqual(attribute_value, attributes[0].attribute_value)
        
        # Re-retrieve the managed object and see if the attribute is gone
        e._data_session.add(managed_object)
        e._data_session.commit()
        e._data_session = e._data_store_session_factory()
        e._delete_attribute_from_managed_object(managed_object, (attribute_name, None, None))
        managed_object = e._get_object_with_access_controls(
            "1",
            enums.Operation.DELETE_ATTRIBUTE
        )
        attributes = e._get_attributes_from_managed_object(
            managed_object,
            [attribute_name]
        )
        self.assertEqual(0, len(attributes))

    def test_process_add_attribute(self):
        e = self._create_kmip_engine()

        managed_object = pie_objects.SymmetricKey(
            enums.CryptographicAlgorithm.AES,
            0,
            b''
        )

        e._data_session.add(managed_object)
        e._data_session.commit()
        e._data_session = e._data_store_session_factory()

        attribute_factory = factory.AttributeFactory()
        custom_attribute = attribute_factory.create_attribute(
                        "x-scinet-test",
                        "test-value"
        )
        payload = payloads.AddAttributeRequestPayload(
            unique_identifier="1",
            attribute=custom_attribute
        )
        response_payload = e._process_add_attribute(payload)
        e._data_session.commit()
        e._data_session = e._data_store_session_factory()

        e._logger.info.assert_any_call(
            "Processing operation: AddAttribute"
        )
        self.assertEqual("1", response_payload.unique_identifier)
        self.assertEqual(custom_attribute, response_payload.attribute)
        self.assertIsNone(response_payload.attribute.attribute_index)        

        self.assertRaises(exceptions.KmipError, e._process_add_attribute, payload)

    def test_process_modify_attribute(self):
        e = self._create_kmip_engine()

        managed_object = pie_objects.SymmetricKey(
            enums.CryptographicAlgorithm.AES,
            0,
            b''
        )

        e._data_session.add(managed_object)
        attribute_value_factory = factory.AttributeValueFactory()
        attribute_name = "x-scinet-test"
        attribute_value = attribute_value_factory.create_attribute_value(attribute_name, "test-value")
        e._set_attribute_on_managed_object(
            managed_object,
            (attribute_name, attribute_value)
        )

        attribute_factory = factory.AttributeFactory()
        custom_attribute = attribute_factory.create_attribute(
                        "x-scinet-test",
                        "test-value-new"
                    )
        payload = payloads.ModifyAttributeRequestPayload(
            unique_identifier="1",
            attribute=custom_attribute
        )
        response_payload = e._process_modify_attribute(payload)
        e._data_session.commit()

        e._logger.info.assert_any_call(
            "Processing operation: ModifyAttribute"
        )
        self.assertEqual("1", response_payload.unique_identifier)
        self.assertEqual(custom_attribute, response_payload.attribute)
        self.assertIsNone(response_payload.attribute.attribute_index)
        
        attributes = e._get_attributes_from_managed_object(
            managed_object,
            ["x-scinet-test"]
        )
        self.assertEqual(1, len(attributes))
        self.assertEqual("test-value-new", attributes[0].attribute_value.value)

    def test_process_delete_attribute(self):
        e = self._create_kmip_engine()

        managed_object = pie_objects.SymmetricKey(
            enums.CryptographicAlgorithm.AES,
            0,
            b''
        )

        e._data_session.add(managed_object)
        attribute_factory = factory.AttributeFactory()
        custom_attributes = []
        attribute_value_factory = factory.AttributeValueFactory()
        for i in [1, 2]:
            attribute_name = f"x-scinet-attr-{i}"
            attribute_value = attribute_value_factory.create_attribute_value(attribute_name, "test-value")
            e._set_attribute_on_managed_object(
                managed_object,
                (attribute_name, attribute_value)
            )
            custom_attributes.append(
                attribute_factory.create_attribute(
                    attribute_name,
                    attribute_value.value
                )
            )

        payload = payloads.DeleteAttributeRequestPayload(
            unique_identifier="1",
            attribute_name=custom_attributes[0].attribute_name.value,
        )
        
        response_payload = e._process_delete_attribute(payload)
        e._data_session.commit()
        e._data_session = e._data_store_session_factory()

        e._logger.info.assert_any_call(
            "Processing operation: DeleteAttribute"
        )
        self.assertEqual("1", response_payload.unique_identifier)
        self.assertEqual(
            custom_attributes[0],
            response_payload.attribute
        )

        managed_object = e._get_object_with_access_controls(
            "1",
            enums.Operation.DELETE_ATTRIBUTE
        )
        attributes = e._get_attributes_from_managed_object(
            managed_object,
            []
        )
        self.assertNotIn(
            custom_attributes[0],
            attributes
        )
        self.assertIn(
            custom_attributes[1],
            attributes
        )

    def test_process_get_attributes(self):
        e = self._create_kmip_engine()

        managed_object = pie_objects.SymmetricKey(
            enums.CryptographicAlgorithm.AES,
            0,
            b''
        )

        e._data_session.add(managed_object)
        attribute_value_factory = factory.AttributeValueFactory()
        attribute_name = "x-scinet-test"
        attribute_value = attribute_value_factory.create_attribute_value(attribute_name, "test-value")
        e._set_attribute_on_managed_object(
            managed_object,
            (attribute_name, attribute_value)
        )
        e._data_session.commit()

        attribute_factory = factory.AttributeFactory()
        custom_attribute = attribute_factory.create_attribute(
            attribute_name,
            attribute_value.value
        )

        payload = payloads.GetAttributesRequestPayload(
            unique_identifier="1",
            attribute_names=[attribute_name]
        )
        response_payload = e._process_get_attributes(payload)
        self.assertEqual(1, len(response_payload.attributes))
        self.assertIn(custom_attribute, response_payload.attributes)
        
        payload = payloads.GetAttributesRequestPayload(
            unique_identifier="1",
            attribute_names=[]
        )
        response_payload = e._process_get_attributes(payload)
        self.assertEqual(11, len(response_payload.attributes))
        self.assertIn(custom_attribute, response_payload.attributes)
        
        payload = payloads.GetAttributesRequestPayload(
            unique_identifier="1",
            attribute_names=['Object Type']
        )
        response_payload = e._process_get_attributes(payload)
        self.assertEqual(1, len(response_payload.attributes))
        self.assertNotIn(custom_attribute, response_payload.attributes)

    def test_process_get_attribute_list(self):
        e = self._create_kmip_engine()

        managed_object = pie_objects.SymmetricKey(
            enums.CryptographicAlgorithm.AES,
            0,
            b''
        )

        e._data_session.add(managed_object)
        attribute_value_factory = factory.AttributeValueFactory()
        attribute_name = "x-scinet-test"
        attribute_value = attribute_value_factory.create_attribute_value(attribute_name, "test-value")
        e._set_attribute_on_managed_object(
            managed_object,
            (attribute_name, attribute_value)
        )

        payload = payloads.GetAttributeListRequestPayload(
            unique_identifier="1"
        )
        response_payload = e._process_get_attribute_list(payload)
        self.assertEqual(11, len(response_payload.attribute_names))
        self.assertIn(attribute_name, response_payload.attribute_names)
