import setuptools

setuptools.setup(
    name='CLC_parellel_window_size',
    version='0.0.1',
    author='Mengzhan Liufu',
    author_email='mliufu@uchicago.edu',
    description='Trodes-based closed loop control system; process multiple window sizes in parallel',
    url='https://bitbucket.org/EMK_Lab/clc/src/master/',
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'ipython',
        'nbformat',
        'trodesnetwork==0.0.11',
        'argparse'
    ],
)
