from distutils.core import setup

packages=['celex']
template_patterns = [
    'templates/*.html',
    'templates/*/*.html',
    'templates/*/*/*.html',
    ]

setup(
    name='django-celex-lexicon',
    version='0.1.88',
    author='Michael McAuliffe',
    author_email='michael.e.mcauliffe@gmail.com',
    url='http://pypi.python.org/pypi/django-celex-lexicon/',
    license='LICENSE.txt',
    description='',
    long_description=open('README.md').read(),
    install_requires=['django'],
    packages=packages +['celex.media'],
    package_data=dict( (package_name, template_patterns)
                   for package_name in packages )
)
