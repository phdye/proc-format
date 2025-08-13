import io
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='proc-format',
    version='0.1.0',
    description='Format Pro*C source files aligning EXEC SQL blocks.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Proc Format Contributors',
    url='https://example.com/proc-format',
    project_urls={'Issues': 'https://example.com/proc-format/issues'},
    license='MIT',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['sqlparse>=0.5,<0.6'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Code Formatters',
    ],
)
