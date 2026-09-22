Installation
============

Requirements
------------

- Python 3.10 or higher
- API credentials for platforms you want to use

Install from PyPI
-----------------

Basic installation:

.. code-block:: bash

    pip install socialia

With optional dependencies:

.. code-block:: bash

    # Reddit support
    pip install socialia[reddit]

    # YouTube support
    pip install socialia[youtube]

    # Google Analytics Data API
    pip install socialia[analytics]

    # MCP server for AI agents
    pip install socialia[mcp]

    # All features
    pip install socialia[all]

Install from Source
-------------------

.. code-block:: bash

    git clone https://github.com/ywatanabe1989/socialia.git
    cd socialia
    pip install -e ".[all]"

Configuration
-------------

Create a ``.env`` file with your API credentials:

.. code-block:: bash

    # Twitter/X API
    SOCIALIA_X_CONSUMER_KEY=your_key
    SOCIALIA_X_CONSUMER_KEY_SECRET=your_secret
    SOCIALIA_X_ACCESSTOKEN=your_token
    SOCIALIA_X_ACCESSTOKEN_SECRET=your_token_secret

    # LinkedIn
    SOCIALIA_LINKEDIN_ACCESS_TOKEN=your_token

    # Reddit
    SOCIALIA_REDDIT_CLIENT_ID=your_id
    SOCIALIA_REDDIT_CLIENT_SECRET=your_secret
    SOCIALIA_REDDIT_USERNAME=your_username
    SOCIALIA_REDDIT_PASSWORD=your_password

    # Google Analytics
    SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID=G-XXXXXXXXXX
    SOCIALIA_GOOGLE_ANALYTICS_API_SECRET=your_secret

See ``socialia setup`` for detailed platform-specific setup instructions.

Verify Installation
-------------------

.. code-block:: bash

    # Check version
    socialia --version

    # Check all platform connections
    socialia check

    # Show configuration status
    socialia status
