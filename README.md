##NanoLab

NanoLab is an easy-to-use testing tool designed to run test cases against a local network of nano-nodes. It utilizes [NanoMock](https://github.com/gr0vity-dev/nanomock), a highly customizable tool for creating dockerized nano networks, to facilitate quick and efficient testing of various configurations. Simply provide a config file for the test case and watch NanoLab streamline your testing process.

###Features:

- Run test cases against a local network of nano-nodes
- Leverages NanoMock for dockerized nano network creation
- Simple configuration with JSON
- Compatible with Python 3.8+ and Docker

###How to install:
`pip install nanolab`

###How to use:
|Command| Description
|----|----|
| `nanolab list`| List all available testcases
| `nanolab run -t {testcase}` | execute a testcase 


###How to use with options:

|Command| flag | 
|----|----|
| `-t --test-case`  | Use one of the available testcases (`nanolab list`)
|                   | Can be a `/path/to/config.json` on your disk
| `--gh-user --gh-repo --gh-path` | Default : [gr0vity-dev nanolab-configs default](https://github.com/gr0vity-dev/nanolab-configs/tree/main/default)
|                   | Used in `nanolab list` to show available testcases
|                   | Used in `nanolab run` to download the selected testcase 
| `-i --image`      | List of docker images used per testrun