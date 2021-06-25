
import setuptools

with open("README.md") as f:
    long_description = f.read()

setuptools.setup(
    name='twarc-networks',
    version='0.0.6',
    url='https://github.com/kngoledge/twarc-networks',
    author='kngoledge',
    author_email='kngoledge@gmail.com',
    py_modules=['twarc_networks'],
    description='A twarc plugin to create and visualize networks from tweet data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.3',
    install_requires=['twarc>=2.1.1', 'networkx', 'click'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points='''
        [twarc.plugins]
        ids=twarc_networks:networks
    '''
)
