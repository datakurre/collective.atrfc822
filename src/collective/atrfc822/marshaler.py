# -*- coding: utf-8 -*-
from venusianconfiguration import configure
from collective.atrfc822.fields import iterFields
from email import message_from_string
from email.generator import Generator
from io import BytesIO
from plone.rfc822 import constructMessage
from plone.rfc822 import initializeObject


def to_string(message):
    out = BytesIO()
    generator = Generator(out, mangle_from_=False, maxheaderlen=0)
    generator.flatten(message)
    return out.getvalue()


# noinspection PyUnusedLocal
def marshall(self, instance, **kwargs):
    message = constructMessage(instance, iterFields(instance))
    content_type = message.get_content_type()
    data = to_string(message)
    length = len(data)
    return content_type, length, data


# noinspection PyUnusedLocal
def demarshall(self, instance, data, **kwargs):
    message = message_from_string(data)
    initializeObject(instance, iterFields(instance), message)


import collective.monkeypatcher
configure.include(package=collective.monkeypatcher)

configure.monkey.patch(
    description=u'Patch Archetype RFC822Marshaller',
    class_='Products.Archetypes.Marshall.RFC822Marshaller',
    original='marshall',
    replacement='.marshaler.marshall'
)

configure.monkey.patch(
    description=u'Patch Archetypes RFC822Marshaller',
    class_='Products.Archetypes.Marshall.RFC822Marshaller',
    original='demarshall',
    replacement='.marshaler.demarshall'
)
