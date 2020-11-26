# Cloud-One-Conformity-Profile-Builder

Python script to create conformity profiles based on compliance standards & frameworks available within Conformity

## Installation

Ensure build tools such as make, automake, libtool are already installed as these are require to install pyjq.

```bash
sudo apt-get install build-essential
```

Run the following command:

```bash
pip3 install -r requirements.txt
```

### Docker

- Create `env.sh` file as mentioned in `build.sh` helper
- Run `./build.sh` to create the Docker image
- Run `./run.sh bash` to run a container and open bash on it

## Usage

1. Optionally set the `apiKey` and `apiRegion` environment variables for your conformity api key and region. (Only required for `online` option).
2. Run the script with one of the following arguments: `local` to generate profile files locally in the current folder, or `online` to create the profiles directly within your Conformity account.

  ```bash
  python3 cpb.py local
  ```
