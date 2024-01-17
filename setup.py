from setuptools import setup

setup(
    name='girder-convert-vip-experiment',
    version='1.0.0',
    description='This plugin allows to convert a VIP experiment into a readable format '
    'for the VIP reproducibility dashboard',
    author='Blot Hippolyte, Creatis',
    author_email='hippolyte.blot@creatis.insa-lyon.fr',
    packages=['girder_convert_vip_experiment'],
    install_requires=[
        'girder>=3',
        'docker==6.1.2',
        'jsonschema==4.20.0',
        'pymongo==3.13.0',
        'setuptools==67.7.2'
    ],
    include_package_data=True,
    entry_points={
        'girder.plugin': [
            'conversion = girder_convert_vip_experiment:ConvertVIPExperiment']
    }
)
