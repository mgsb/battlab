import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='battlab',
    version='0.1',
    author='Mark Grosen',
    author_email='mark@grosen.org',
    description='Interact with BattLab-One',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/mgsb/battlab',
    project_urls = {
        "Bug Tracker": "https://github.com/mgsb/battlab/issues"
    },
    license='MIT',
    packages=['battlab'],
    install_requires=['pyserial', 'plotext'],
    entry_points={
        "console_scripts": [
            "bl1cli = battlab.bl1cli:main"
        ]
    }
)
