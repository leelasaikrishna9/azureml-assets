# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

import os
import time

print(os.environ)
print("hello, in my own python")
print('Before: %s' % time.ctime())
print('After: %s\n' % time.ctime())
