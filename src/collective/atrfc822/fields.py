# -*- coding: utf-8 -*-
from datetime import datetime

from DateTime.DateTime import DateTime

from Products.TALESField import TALESString
from plone import api
from plone.app.blob.interfaces import IBlobField
from plone.app.blob.interfaces import IBlobImageField
from plone.namedfile.marshaler import NamedFileFieldMarshaler
from plone.namedfile.marshaler import NamedImageFieldMarshaler
from plone.uuid.interfaces import IUUID
from zope import schema
from Products.Archetypes.interfaces import IStringField
from Products.Archetypes.interfaces import IReferenceField
from Products.Archetypes.interfaces import IFileField
from Products.Archetypes.interfaces import IImageField
from Products.Archetypes.interfaces import ITextField
from Products.Archetypes.interfaces import IDateTimeField
from Products.Archetypes.interfaces import IFixedPointField
from Products.Archetypes.interfaces import ILinesField
from Products.Archetypes.interfaces import IIntegerField
from Products.Archetypes.interfaces import IFloatField
from Products.Archetypes.interfaces import IBooleanField
from plone.rfc822.defaultfields import BaseFieldMarshaler
from plone.rfc822.defaultfields import BytesFieldMarshaler
from plone.rfc822.defaultfields import ASCIISafeFieldMarshaler
from plone.rfc822.defaultfields import DatetimeMarshaler
from plone.rfc822.defaultfields import CollectionMarshaler
from plone.rfc822.interfaces import IFieldMarshaler
from plone.rfc822.interfaces import IPrimaryField
from venusianconfiguration import configure
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from zope.interface import alsoProvides


# Usage:
# message = constructMessage(ob, iterFields(ob))
# initializeObject(ob, iterFields(ob), message)


def iterFields(ob):
    primary = ob.getPrimaryField()
    if primary is not None:
        field = primary.copy()
        alsoProvides(field, IPrimaryField)
        yield field.__name__, field
    for name in ob.schema.getSchemataNames():
        for field in ob.schema.getSchemataFields(name):
            yield field.__name__, field.copy()


class ATBaseFieldMarshaler(BaseFieldMarshaler):
    # noinspection PyMissingConstructor
    def __init__(self, context, field):
        self.context = context
        self.field = field

    def _query(self, default=None):
        getter = self.field.getEditAccessor(self.context)
        return getter()

    def _set(self, value):
        setter = self.field.getMutator(self.context)
        setter(value)


@configure.adapter.factory(for_=(Interface, IStringField))
@configure.adapter.factory(for_=(Interface, ITextField))
@configure.adapter.factory(for_=(Interface, IIntegerField))
@configure.adapter.factory(for_=(Interface, IFloatField))
@configure.adapter.factory(for_=(Interface, TALESString))
@implementer(IFieldMarshaler)
class ATFieldMarshaler(BytesFieldMarshaler, ATBaseFieldMarshaler):
    def _query(self, default=None):
        value = super(ATFieldMarshaler, self)._query(default)
        if not isinstance(value, str) and hasattr(value, 'encode'):
            return value.encode('utf-8')
        elif not isinstance(value, str):
            return str(value)
        else:
            return value


@configure.adapter.factory()
@adapter(Interface, IFixedPointField)
@implementer(IFieldMarshaler)
class ATDecimalFieldMarshaler(ASCIISafeFieldMarshaler, ATBaseFieldMarshaler):
    pass


@configure.adapter.factory()
@adapter(Interface, IDateTimeField)
@implementer(IFieldMarshaler)
class ATDateTimeFieldMarshaler(DatetimeMarshaler, ATBaseFieldMarshaler):
    # Requires DateTime >= 2.11:
    def _query(self, default=None):
        value = super(ATDateTimeFieldMarshaler, self)._query(default=default)
        if isinstance(value, DateTime):
            value = value.asdatetime()
        return value

    def _set(self, value):
        if isinstance(value, datetime):
            value = DateTime(value)
        super(ATDateTimeFieldMarshaler, self)._set(value)


@configure.adapter.factory()
@adapter(Interface, ILinesField)
@implementer(IFieldMarshaler)
class ATLinesFieldMarshaler(CollectionMarshaler, ATBaseFieldMarshaler):
    def __init__(self, context, field):
        super(ATLinesFieldMarshaler, self).__init__(context, field)
        field.value_type = IStringField


@configure.adapter.factory()
@adapter(Interface, IBooleanField)
@implementer(IFieldMarshaler)
class ATBooleanFieldMarshaler(ASCIISafeFieldMarshaler, ATBaseFieldMarshaler):
    pass


@configure.adapter.factory(for_=(Interface, IBlobField))
@configure.adapter.factory(for_=(Interface, IFileField))
@implementer(IFieldMarshaler)
class ATFileFieldMarshaler(NamedFileFieldMarshaler, ATBaseFieldMarshaler):
    def _query(self, default=None):
        value = super(ATFileFieldMarshaler, self)._query(default=default)
        if value:
            if isinstance(value.getFilename(), str):
                filename = value.getFilename().decode('utf-8')
            else:
                filename = value.getFilename()
            return self.factory(value.data, value.getContentType(), filename)
        else:
            return None

    def _set(self, value):
        if value:
            if not isinstance(value.filename, str):
                filename = value.filename.encode('utf-8')
            else:
                filename = value.filename
            super(ATFileFieldMarshaler, self)._set(
                value.data, mimetype=value.contentType, filename=filename)
        else:
            super(ATFileFieldMarshaler, self)._set(None)



@configure.adapter.factory(for_=(Interface, IImageField))
@configure.adapter.factory(for_=(Interface, IBlobImageField))
@implementer(IFieldMarshaler)
class ATImageFieldMarshaler(NamedImageFieldMarshaler, ATBaseFieldMarshaler):
    def _query(self, default=None):
        value = super(ATImageFieldMarshaler, self)._query(default=default)
        if value:
            if isinstance(value.getFilename(), str):
                filename = value.getFilename().decode('utf-8')
            else:
                filename = value.getFilename()
            return self.factory(value.data, value.getContentType(), filename)
        else:
            return None

    def _set(self, value):
        if value:
            if not isinstance(value.filename, str):
                filename = value.filename.encode('utf-8')
            else:
                filename = value.filename
            super(ATImageFieldMarshaler, self)._set(
                value.data, mimetype=value.contentType, filename=filename)
        else:
            super(ATImageFieldMarshaler, self)._set(None)


@configure.adapter.factory()
@adapter(Interface, IReferenceField)
@implementer(IFieldMarshaler)
class ATReferenceFieldMarshaler(CollectionMarshaler, ATBaseFieldMarshaler):
    def __init__(self, context, field):
        super(ATReferenceFieldMarshaler, self).__init__(context, field)
        field.value_type = IStringField

    def _query(self, default=None):
        value = super(ATReferenceFieldMarshaler, self)._query(default=default)
        return map(IUUID, value)

    def _set(self, value):
        resolved_objects = []
        portal_catalog = api.portal.get_tool('portal_catalog')
        for uuid in value:
            for brain in portal_catalog.unrestrictedSearchResults(UID=uuid):
                # noinspection PyProtectedMember
                resolved_objects.append(brain._unrestrictedGetObject())
        super(ATReferenceFieldMarshaler, self)._set(resolved_objects)
