------
PyKMIP
------
|pypi-version|
|travis-status|
|codecov-status|
|python-versions|

PyKMIP is a Python implementation of the Key Management Interoperability
Protocol (KMIP), an `OASIS`_ communication standard for the management of
objects stored and maintained by key management systems. KMIP defines how key
management operations and operation data should be encoded and communicated
between client and server applications. Supported operations include the full
`CRUD`_ key management lifecycle, including operations for managing object
metadata and for conducting cryptographic operations. Supported object types
include:

* symmetric/asymmetric encryption keys
* passwords/passphrases
* certificates
* opaque data blobs, and more

For more information on KMIP, check out the `OASIS KMIP Technical Committee`_
and the `OASIS KMIP Documentation`_.

For more information on PyKMIP, check out the project `Documentation`_.

Installation
------------
You can install PyKMIP via ``pip``:

.. code-block:: console

    $ pip install pykmip

See `Installation`_ for more information.

Community
---------
The PyKMIP community has various forums and resources you can use:

* `Source code`_
* `Issue tracker`_
* IRC: ``#pykmip`` on ``irc.freenode.net``
* Twitter: ``@pykmip``

Unsealing methods
-----------------
The ``unseal_method`` configuration parameter can take the following values:

* ``password``: the database password has to be explicitly given in the configuration file in ``database_password``
* ``password-file``: the database password has to be found in a file, the path has to be given in the configuration file in ``password_path``
* ``sss-interactive``: the database password shares will be added later, the server will hang until this is complete. Use the ``pykmip-sss`` commandline utility and follow the prompt (you can use ``-t`` to specify the share threshold)

If not specified, the SQLite database will not use encryption.

Rekey the backend database
--------------------------
1. make sure the server is stopped
2. enter the following command

   .. code-block:: console

      ./rekey-server.py --database /data/db/pykmip.db -gpg=[u1],[u2],...,[un] -t [threshold, default=2]
  
   where [u1]...[un] are the GPG public key files (comma-separated). We need t/n to unlock the database.

Custom attributes
-----------------
This implementation of the *server* supports KMIP 1.4-style custom attributes (starting with `x-`), with the following caveats:

1. Custom attribute value must be a text string
2. Multiple instances are not permitted
3. The AddAttribute operation *only* supports custom attributes
4. The Locate operation does not support custom attributes
5. ID placeholder not supported (must specify unique identifier at every request)

TTLV tool
---------
The ``ttlv-tool`` utility converts between between human readable XML and the TTLV encoding that used for KMIP client-server communication. The utility has two commands:

* ``encode``: input is XML (from stdin, or a file specified with the ``-i`` option) and output is binary TTLV. The ``-f`` option can be specified to produce hex or base64 encoded TTLV output for debugging purposes. Output goes to stdout by default unless a file path is specified with the ``-o`` option.
* ``decode``: input is binary TTLV (from stdin, or a file specified with the ``-i`` option) and output is XML. Output goes to stdout by default unless a file path is specified with the ``-o`` option.

.. _`CRUD`: https://en.wikipedia.org/wiki/Create,_read,_update_and_delete
.. _`OASIS`: https://www.oasis-open.org
.. _`OASIS KMIP Technical Committee`: https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=kmip
.. _`OASIS KMIP Documentation`: https://docs.oasis-open.org/kmip/spec/
.. _`Documentation`: https://pykmip.readthedocs.io/en/latest/index.html
.. _`Installation`: https://pykmip.readthedocs.io/en/latest/installation.html
.. _`Source code`: https://github.com/openkmip/pykmip
.. _`Issue tracker`: https://github.com/openkmip/pykmip/issues

.. |pypi-version| image:: https://img.shields.io/pypi/v/pykmip.svg
  :target: https://pypi.python.org/pypi/pykmip
  :alt: Latest Version
.. |travis-status| image:: https://travis-ci.org/OpenKMIP/PyKMIP.svg?branch=master
  :target: https://travis-ci.org/OpenKMIP/PyKMIP
.. |codecov-status| image:: https://codecov.io/github/OpenKMIP/PyKMIP/coverage.svg?branch=master
  :target: https://codecov.io/github/OpenKMIP/PyKMIP?branch=master
.. |python-versions| image:: https://img.shields.io/pypi/pyversions/PyKMIP.svg
  :target: https://github.com/OpenKMIP/PyKMIP
