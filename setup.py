from setuptools import setup

setup(name='inca-game',
      version="0.0.1",
      description='Collect enough treasure to fill an entire room.',
      long_description="""A game for pyweek, Oct. 2014.""",
      classifiers=[
        ],
      author='Daniel Holth',
      author_email='dholth@fastmail.fm',
      keywords=['pyweek'],
      license='MIT',
      packages=[
          'inca',
          ],
      install_requires=['pysdl2-cffi>=0.7.0',
                        'pytmx>=3.19.5'],
      tests_require=['pytest'],
      include_package_data=True,
      zip_safe=False,
      )

