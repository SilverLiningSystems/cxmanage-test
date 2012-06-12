from setuptools import setup

setup(
    name='cxmanage',
    version='0.2.0',
    packages=['cxmanage'],
    scripts=['scripts/cxmanage'],
    description='Calxeda Management Utility',
    install_requires=['pexpect', 'tftpy', 'pyipmi'],
    classifiers=[
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 2.7']
)
