# Latta Vanilla Python recorder


1. Install Latta AI package via pip

```py
pip install latta-python-recorder
```

2. Wrap whole application into Latta

```py

from latta import Latta

latta = Latta('api-key')

@latta.wrap
def divide(x, y):
    return x / y
```

Latta is typed like this `Latta(api_key: str, instance_id: Optional[str]=None, options: Optional[LattaOptions]=None)`

User can also specify extra options, for now just device type, the rest of options we collect Latta takes automatically on its own.