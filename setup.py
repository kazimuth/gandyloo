from setuptools import setup

setup(
        name="gandyloo",
        version="0.0.1",
        description="Minesweeper client for 6.005",
        license="MIT",
        author="James Gilles",
        author_email="jhgilles@mit.edu",
        install_requires=["py>=1.4.30",
            "pytest>=2.8.2",
            "Twisted>=15.4.0",
            "urwid>=1.3.1"],
        packages=['gandyloo'],
        scripts=['gandysweeper.py']
)
