from setuptools import setup

setup(name='cx_manage_util',
    version='0.0.1',
    packages=['cx_manage_util',
              'cx_manage_util.common',
              'cx_manage_util.cxfwupd'],
    scripts=['scripts/cxmanage']
)
