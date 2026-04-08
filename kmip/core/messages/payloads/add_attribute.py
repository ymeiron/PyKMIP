import six

from kmip.core import enums
from kmip.core import exceptions
from kmip.core import objects
from kmip.core import primitives
from kmip.core import utils
from kmip.core.messages.payloads import base


class AddAttributeRequestPayload(base.RequestPayload):
    """
    A request payload for the AddAttribute operation.

    Attributes:
        unique_identifier: The unique ID of the object on which attribute
            deletion should be performed.
        attribute: The attribute to set on the specified object.
    """

    def __init__(self,
                 unique_identifier=None,
                 attribute=None):
        """
        Construct a AddAttribute request payload.

        Args:
            unique_identifier (string): The unique ID of the object on which
                the attribute should be set. Optional, defaults to
                None.
            attribute (struct): An Attribute object containing the new
                attribute value to set on the specified object. Optional,
                defaults to None. Required for read/write.
        """
        super(AddAttributeRequestPayload, self).__init__()

        self._unique_identifier = None
        self._attribute = None

        self.unique_identifier = unique_identifier
        self.attribute = attribute

    @property
    def unique_identifier(self):
        if self._unique_identifier:
            return self._unique_identifier.value
        return None

    @unique_identifier.setter
    def unique_identifier(self, value):
        if value is None:
            self._unique_identifier = None
        elif isinstance(value, six.string_types):
            self._unique_identifier = primitives.TextString(
                value=value,
                tag=enums.Tags.UNIQUE_IDENTIFIER
            )
        else:
            raise TypeError("The unique identifier must be a string.")

    @property
    def attribute(self):
        if self._attribute:
            return self._attribute
        return None

    @attribute.setter
    def attribute(self, value):
        if value is None:
            self._attribute = None
        elif isinstance(value, objects.Attribute):
            self._attribute = value
        else:
            raise TypeError(
                "The new attribute must be an Attribute object."
            )

    def read(self, input_buffer, kmip_version=enums.KMIPVersion.KMIP_1_0):
        """
        Read the data encoding the AddAttribute request payload and decode
        it into its constituent part.

        Args:
            input_buffer (stream): A data stream containing encoded object
                data, supporting a read method; usually a BytearrayStream
                object.
            kmip_version (KMIPVersion): An enumeration defining the KMIP
                version with which the object will be decoded. Optional,
                defaults to KMIP 1.0.

        Raises:
            InvalidKmipEncoding: Raised if fields are missing from the
                encoding.
        """
        super(AddAttributeRequestPayload, self).read(
            input_buffer,
            kmip_version=kmip_version
        )
        local_buffer = utils.BytearrayStream(input_buffer.read(self.length))

        if self.is_tag_next(enums.Tags.UNIQUE_IDENTIFIER, local_buffer):
            self._unique_identifier = primitives.TextString(
                tag=enums.Tags.UNIQUE_IDENTIFIER
            )
            self._unique_identifier.read(
                local_buffer,
                kmip_version=kmip_version
            )
        else:
            self._unique_identifier = None

        if self.is_tag_next(enums.Tags.ATTRIBUTE, local_buffer):
            self._attribute = objects.Attribute()
            self._attribute.read(
                local_buffer,
                kmip_version=kmip_version
            )
        else:
            raise exceptions.InvalidKmipEncoding(
                "The AddAttribute request payload encoding is missing the"
                "attribute field."
            )

        self.is_oversized(local_buffer)

    def write(self, output_buffer, kmip_version=enums.KMIPVersion.KMIP_1_0):
        """
        Write the data encoding the AddAttribute request payload to a
        stream.

        Args:
            output_buffer (stream): A data stream in which to encode object
                data, supporting a write method; usually a BytearrayStream
                object.
            kmip_version (KMIPVersion): An enumeration defining the KMIP
                version with which the object will be encoded. Optional,
                defaults to KMIP 1.0.

        Raises:
            InvalidField: Raised if a required field is missing from the
                payload object.
        """
        local_buffer = utils.BytearrayStream()

        if self._unique_identifier:
            self._unique_identifier.write(
                local_buffer,
                kmip_version=kmip_version
            )

        if self._attribute:
            self._attribute.write(
                local_buffer,
                kmip_version=kmip_version
            )
        else:
            raise exceptions.InvalidField(
                "The AddAttribute request payload is missing the new "
                "attribute field."
            )

        self.length = local_buffer.length()
        super(AddAttributeRequestPayload, self).write(
            output_buffer,
            kmip_version=kmip_version
        )
        output_buffer.write(local_buffer.buffer)

    def __repr__(self):
        args = [
            "unique_identifier='{}'".format(self.unique_identifier),
            "attribute={}".format(
                repr(self.attribute) if self.attribute else None
            )
        ]
        return "AddAttributeRequestPayload({})".format(", ".join(args))

    def __str__(self):
        return str(
            {
                "unique_identifier": self.unique_identifier,
                "attribute": str(
                    self.attribute
                ) if self.attribute else None
            }
        )

    def __eq__(self, other):
        if isinstance(other, AddAttributeRequestPayload):
            if self.unique_identifier != other.unique_identifier:
                return False
            elif self.attribute != other.attribute:
                return False
            else:
                return True
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, AddAttributeRequestPayload):
            return not self.__eq__(other)
        else:
            return NotImplemented


class AddAttributeResponsePayload(base.ResponsePayload):
    """
    A response payload for the AddAttribute operation.

    Attributes:
        unique_identifier: The unique ID of the object on which the attribute
            was set.
        attribute: The newly added attribute.
    """

    def __init__(self, unique_identifier=None, attribute=None):
        """
        Construct a AddAttribute response payload.

        Args:
            unique_identifier (string): The unique ID of the object on
                which the attribute was set. Defaults to None. Required for
                read/write.
            attribute (struct): An Attribute object representing the newly
                modified attribute. Optional, defaults to None. Required for
                read/write.
        """
        super(AddAttributeResponsePayload, self).__init__()

        self._unique_identifier = None
        self._attribute = None

        self.unique_identifier = unique_identifier
        self.attribute = attribute

    @property
    def unique_identifier(self):
        if self._unique_identifier:
            return self._unique_identifier.value
        return None

    @unique_identifier.setter
    def unique_identifier(self, value):
        if value is None:
            self._unique_identifier = None
        elif isinstance(value, six.string_types):
            self._unique_identifier = primitives.TextString(
                value=value,
                tag=enums.Tags.UNIQUE_IDENTIFIER
            )
        else:
            raise TypeError("The unique identifier must be a string.")

    @property
    def attribute(self):
        if self._attribute:
            return self._attribute
        return None

    @attribute.setter
    def attribute(self, value):
        if value is None:
            self._attribute = None
        elif isinstance(value, objects.Attribute):
            self._attribute = value
        else:
            raise TypeError("The attribute must be an Attribute object.")

    def read(self, input_buffer, kmip_version=enums.KMIPVersion.KMIP_1_0):
        """
        Read the data encoding the AddAttribute response payload and decode
        it into its constituent parts.

        Args:
            input_buffer (stream): A data stream containing encoded object
                data, supporting a read method; usually a BytearrayStream
                object.
            kmip_version (enum): A KMIPVersion enumeration defining the KMIP
                version with which the object will be decoded. Optional,
                defaults to KMIP 1.0.

        Raises:
            InvalidKmipEncoding: Raised if any required fields are missing
                from the encoding.
        """
        super(AddAttributeResponsePayload, self).read(
            input_buffer,
            kmip_version=kmip_version
        )
        local_buffer = utils.BytearrayStream(input_buffer.read(self.length))

        if self.is_tag_next(enums.Tags.UNIQUE_IDENTIFIER, local_buffer):
            self._unique_identifier = primitives.TextString(
                tag=enums.Tags.UNIQUE_IDENTIFIER
            )
            self._unique_identifier.read(
                local_buffer,
                kmip_version=kmip_version
            )
        else:
            raise exceptions.InvalidKmipEncoding(
                "The AddAttribute response payload encoding is missing the "
                "unique identifier field."
            )

        if self.is_tag_next(enums.Tags.ATTRIBUTE, local_buffer):
            self._attribute = objects.Attribute()
            self._attribute.read(local_buffer, kmip_version=kmip_version)
        else:
            raise exceptions.InvalidKmipEncoding(
                "The AddAttribute response payload encoding is missing "
                "the attribute field."
            )

        self.is_oversized(local_buffer)

    def write(self, output_buffer, kmip_version=enums.KMIPVersion.KMIP_1_0):
        """
        Write the data encoding the AddAttribute response payload to a
        buffer.

        Args:
            output_buffer (buffer): A data buffer in which to encode object
                data, supporting a write method; usually a BytearrayStream
                object.
            kmip_version (enum): A KMIPVersion enumeration defining the KMIP
                version with which the object will be encoded. Optional,
                defaults to KMIP 1.0.

        Raises:
            InvalidField: Raised if a required field is missing from the
                payload object.
        """
        local_buffer = utils.BytearrayStream()

        if self._unique_identifier:
            self._unique_identifier.write(
                local_buffer,
                kmip_version=kmip_version
            )
        else:
            raise exceptions.InvalidField(
                "The AddAttribute response payload is missing the unique "
                "identifier field."
            )

        if self._attribute:
            self._attribute.write(local_buffer, kmip_version=kmip_version)
        else:
            raise exceptions.InvalidField(
                "The AddAttribute response payload is missing the "
                "attribute field."
            )

        self.length = local_buffer.length()
        super(AddAttributeResponsePayload, self).write(
            output_buffer,
            kmip_version=kmip_version
        )
        output_buffer.write(local_buffer.buffer)

    def __repr__(self):
        args = [
            "unique_identifier='{}'".format(self.unique_identifier),
            "attribute={}".format(
                repr(self.attribute) if self.attribute else None
            )
        ]
        return "AddAttributeResponsePayload({})".format(", ".join(args))

    def __str__(self):
        return str(
            {
                "unique_identifier": self.unique_identifier,
                "attribute": str(self.attribute) if self.attribute else None
            }
        )

    def __eq__(self, other):
        if isinstance(other, AddAttributeResponsePayload):
            if self.unique_identifier != other.unique_identifier:
                return False
            elif self.attribute != other.attribute:
                return False
            else:
                return True
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, AddAttributeResponsePayload):
            return not self.__eq__(other)
        return NotImplemented
