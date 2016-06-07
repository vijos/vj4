import setuptools

setuptools.setup(name='vj4',
                 version='4.0',
                 author='Vijos',
                 author_email='me@iceboy.org',
                 description='Vijos Web Server',
                 license='AGPL-3.0',
                 keywords='vijos online judge web',
                 url='https://vijos.org/',
                 packages=[
                   'vj4',
                   'vj4.adaptor',
                   'vj4.model',
                   'vj4.util',
                   'vj4.view',
                 ],
                 package_data={
                   'vj4': ['locale/*.csv', 'ui/templates/*', '.uibuild/*'],
                 },
                 install_requires=open('requirements.txt').readlines(),
                 test_suite='vj4.test')
