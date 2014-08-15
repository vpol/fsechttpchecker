Hello there!

this program is written in, and requires python>=3.4, because it uses asyncio.

additional requirements are aiohttp, pyyaml

$ python3.4 runme.py options --datafile urllist.txt --period 10 --host 0.0.0.0 --port 8080

or

$ python3.4 runme.py config --config config.yaml

by default web page is at http://127.0.0.1:8080

or whatever you put in config file or as command line arguments

urls and "content requirement" is placed in urllist.txt (default) and is divided by "|"