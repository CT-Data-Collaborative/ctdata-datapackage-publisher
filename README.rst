CTData CKAN Publish
===================

What is it?
-----------

Publishing datasets to CKAN can be tough. Our front end tools make it more so. We require a number of specific fields to be
included in `ckan_extras`. This CLI tool handles mapping a datapackage.json to a proper payload for publishing a dataset.


Install
-------

Install it easily:

Using git
---------

::

    $ git clone https://github.com/CT-Data-Collaborative/ctdata-datapackage-publisher.git
    $ cd ctdata-datapackage-publisher
    $ pip install -e .


Configuration and Use
---------------------

::

     $ publish --datapackage <path-to-datapackage.json> --ckanapikey <your api key>

You can also store your api key in an environment variable called `CKANAPIKEY` and it will be read automatically.

::

    $ export CKANAPIKEY=<your api key>
    $ publish --datapackage <path-to-datapackage.json>
