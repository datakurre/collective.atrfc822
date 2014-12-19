# -*- coding:utf-8 -*-
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting


class ATRFC822Tests(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import venusianconfiguration
        venusianconfiguration.enable()
        import collective.atrfc822
        self.loadZCML(package=collective.atrfc822,
                      name='configure.py')


ATRFC822_FIXTURE = ATRFC822Tests()

ATRFC822_INTEGRATION_TESTING = IntegrationTesting(
    bases=(ATRFC822_FIXTURE,),
    name='ATRFC822Tests:Integration')
