# Cloud-One-Conformity-Profile-Builder
script to create conformity profiles based on compliance standards & frameworks available within the tool

## Installation

Ensure build tools such as make, automake, libtool are already installed as these are require to install pyjq.
```
sudo apt-get install build-essential
```

Run the following command:
```
pip3 install -r requirements.txt
```

## Usage
1. Set the `apiKey` and `apiRegion` environment variables for your conformity api key and region.
2. Run the script to create the profiles within conformity and also generate local profile files. Alternative edit the script and comment out either the Create Profiles via API or Create profiles locally sections.
  ```
  python3 cpb.py
  ```
