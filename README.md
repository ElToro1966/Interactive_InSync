Interactive Brokers to Kafka 
Ver. 0.1
by Eric Eikrem

Introduction

This is a simple bridge that reads from an Interactive Brokers' gateway and writes to a Kafka topic. 
It is written in Python and uses the `asyncio`, `ib_insync` and `kafka-python` libraries.

It may be useful for test deployments, air-gapped setups, and similar. In production, and with 
access to the cloud, you may be better off using tried and tested solutions with proper redundancy, 
such as Kafka Connect.

Configuration

The configuration is done by editing config.ini. See comments in the file for details.

systemd Service

The bridge can be run as a service by using systemd. A service file is available for this purpose.
Edit the service file and place it in /etc/systemd/system. Then run:

sudo systemctl daemon-reload

Enable the service to start at boot:

sudo systemctl enable stock_app.service

Start the service:

sudo systemctl start stock_app.service

Check the service status:

sudo systemctl status stock_app.service

Virtual Environment

It is recommended to run the bridge in a virtual environment. To create a virtual environment,
run the following commands:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Next, install the bridge in the virtual environment:

python setup.py install

Before activating the service, make sure to edit the service file to point to the correct Python
interpreter and the correct path to the bridge:

ExecStart={{ venv_home }}/bin/python3 {{ venv_home }}/stock_app.py --serve-in-foreground

To verify that {{ venv_home }} is indeed correct you can check sys.path by running:

{{ venv_home }}/bin/python -m site

and compare the output to:

python -m site


References

I have built on the ideas of others, in particular the following:

1."Automating Python Scripts with Systemd: A Step-by-Step Guide"
https://tecadmin.net/setup-autorun-python-script-using-systemd/
