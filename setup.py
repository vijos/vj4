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
                   'vj4.handler',
                   'vj4.model',
                   'vj4.model.adaptor',
                   'vj4.pipeline',
                   'vj4.service',
                   'vj4.util',
                 ],
                 package_data={
                   'vj4': ['locale/*.csv', 'ui/templates/*', '.uibuild/*'],
                 },
                 install_requires=open('requirements.txt').readlines(),
                 test_suite='vj4.test')
