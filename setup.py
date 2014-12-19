from setuptools import setup, find_packages


setup(
    name='collective.atrfc822',
    version='0.1.0',
    description='',
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGES.rst').read()),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Plone :: 4.3',
    ],
    keywords='',
    author='Asko Soukka',
    author_email='asko.soukka@iki.fi',
    url='https://source.kopla.jyu.fi/code/plone-packages/collective.atrfc822',
    license='GPL',
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'venusianconfiguration',
        'Products.Archetypes',
        'DateTime>=2.11',
        'plone.rfc822',
        'plone.uuid',
        'plone.api',
        'plone.namedfile'
    ],
    extras_require={'test': [
        'unittest',
        'plone.app.testing',
    ]},
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
