= sMAP Support for Keti environmental sensing motes =

To start an example driver, make sure you have a recent version of
sMAP and then in this directory:

    $ twistd -n smap keti.ini

The driver takes a `Namespace` argument that you can use to override
the default sMAP uuid assignment mechanism.  You can use this so that
time series are named consistently based on the motes' serial ID's.
