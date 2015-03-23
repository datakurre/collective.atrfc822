# -*- coding: utf-8 -*-
from datetime import datetime
import Acquisition

from DateTime.DateTime import DateTime
from OFS.Image import Pdata
from Products.Archetypes.Field import StringField
from Products.Archetypes.Widget import RichWidget
import pkg_resources
from plone import api
from plone.app.blob.interfaces import IBlobField
from plone.app.blob.interfaces import IBlobImageField
from plone.namedfile.marshaler import NamedFileFieldMarshaler
from plone.namedfile.marshaler import NamedImageFieldMarshaler
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


try:
    pkg_resources.get_distribution('Products.TALESField')
except pkg_resources.DistributionNotFound:
    class TALESString(object):
        """Mock placeholder"""
else:
    from Products.TALESField import TALESString


try:
    pkg_resources.get_distribution('Products.TemplateFields')
except pkg_resources.DistributionNotFound:
    class ZPTField(object):
        """Mock placeholder"""
else:
    from Products.TemplateFields import ZPTField


# Usage:
# message = constructMessage(ob, iterFields(ob))
# initializeObject(ob, iterFields(ob), message)


def cloneField(field, primary=False):
    clone = field.copy()
    if primary:
        alsoProvides(clone, IPrimaryField)
    if ILinesField.providedBy(clone):
        if primary:
            alsoProvides(clone, IStringField)
        else:
            clone.missing_value = list()
    else:
        clone.missing_value = None
    clone._type = list  # possible sequence type
    clone.fromUnicode = lambda x: x
    return clone


def iterFields(ob):
    # noinspection PyUnresolvedReferences
    ob = Acquisition.aq_base(ob)
    primary = ob.getPrimaryField()
    if primary:
        clone = cloneField(primary, primary=True)
        yield clone.__name__, clone

    for name in ob.schema.getSchemataNames():
        for field in ob.schema.getSchemataFields(name):
            if primary and primary.__name__ == field.__name__:
                continue

            # Mark 'primary fields', which get marshaled into payload
            if (bool(getattr(field, 'primary', None)) is True
                    or IBlobField.providedBy(field)
                    or (IFileField.providedBy(field)
                        and not ITextField.providedBy(field))
                    or getattr(field, 'widget', None) == RichWidget
                    or isinstance(field, ZPTField)):
                clone = cloneField(field, primary=True)
            else:
                clone = cloneField(field, primary=False)

            yield clone.__name__, clone


class ATBaseFieldMarshaler(BaseFieldMarshaler):
    # noinspection PyMissingConstructor
    def __init__(self, context, field):
        self.context = context
        self.field = field

    def _query(self, default=None):
        getter = (self.field.getEditAccessor(self.context)
                  or self.field.getAccessor(self.context))
        return getter()

    def _set(self, value):
        setter = self.field.getMutator(self.context)
        setter(value)

    def getContentType(self):
        if hasattr(self.field, 'getContentType'):
            return self.field.getContentType(self.context)
        else:
            return super(ATBaseFieldMarshaler, self).getContentType()


@configure.adapter.factory(for_=(Interface, IIntegerField))
@configure.adapter.factory(for_=(Interface, IFloatField))
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

    def encode(self, value, charset='utf-8', primary=False):
        if not isinstance(value, str) and hasattr(value, 'encode'):
            return value.encode('utf-8')
        else:
            return value


@configure.adapter.factory(for_=(Interface, IStringField))
@configure.adapter.factory(for_=(Interface, ITextField))
@configure.adapter.factory(for_=(Interface, TALESString))
@configure.adapter.factory(for_=(Interface, ZPTField))
@implementer(IFieldMarshaler)
class ATStringFieldMarshaler(ATFieldMarshaler):
    def _set(self, value):
        setter = self.field.getMutator(self.context)
        setter(value or '')


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
        field.value_type = StringField()


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
            filename = value.getFilename() or self.field.getFilename(value)
            if isinstance(filename, str):
                filename = filename.decode('utf-8')
            if isinstance(value.data, Pdata):
                return self.factory(
                    value.data.data, value.getContentType(), filename)
            else:
                return self.factory(
                    value.data, value.getContentType(), filename)
        else:
            return None

    def _set(self, value):
        if value:
            filename = value.filename
            if not isinstance(filename, str):
                filename = filename.encode('utf-8')
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
            filename = value.getFilename() or self.field.getFilename(value)
            if isinstance(filename, str):
                filename = filename.decode('utf-8')
            if isinstance(value.data, Pdata):
                return self.factory(
                    value.data.data, value.getContentType(), filename)
            else:
                return self.factory(
                    value.data, value.getContentType(), filename)
        else:
            return None

    def _set(self, value):
        if value:
            filename = value.filename
            if not isinstance(filename, str):
                filename = filename.encode('utf-8')
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
        field.value_type = StringField()

    def _query(self, default=None):
        value = super(ATReferenceFieldMarshaler, self)._query(default=default)
        if value:
            return value
        else:
            return None

    def _set(self, value):
        resolved_objects = []
        portal_catalog = api.portal.get_tool('portal_catalog')
        for uuid in value or []:
            for brain in portal_catalog.unrestrictedSearchResults(UID=uuid):
                # noinspection PyProtectedMember
                resolved_objects.append(brain._unrestrictedGetObject())
        super(ATReferenceFieldMarshaler, self)._set(resolved_objects)
