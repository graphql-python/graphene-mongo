from setuptools import find_packages, setup

setup(
    name='graphene-mongo',
    version='0.2.6',

    description='Graphene Mongoengine integration',
    long_description=open('README.rst').read(),
    url='https://github.com/graphql-python/graphene-mongo',
    author='Abaw Chen',
    author_email='abaw.chen@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='api graphql protocol rest relay graphene mongo mongoengine',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'graphene>=2.1.3,<3',
        'mongoengine>=0.15.0',
        'singledispatch>=3.4.0.3',
        'iso8601>=0.1.12'
    ],
    python_requires='>=2.7',
    zip_safe=True,
    tests_require=[
        'pytest>=3.3.2',
        'mongomock',
        'mock'
    ],
)
