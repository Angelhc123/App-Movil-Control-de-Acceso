import sys
try:
    import numpy
    import pandas
    import sklearn
    import fastapi
    import pydantic
    import pydantic_settings
    print(f"OK: pydantic={pydantic.VERSION} fastapi={fastapi.__version__}")
except ImportError as e:
    print(f"FAIL: {e}")
    sys.exit(1)
except AttributeError:
    # Handle older pydantic versions without VERSION const
    print("OK: imports worked (version check skipped)")
