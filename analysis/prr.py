"""
Copyright (c) 2013 Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions 
are met:

 - Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
 - Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
OF THE POSSIBILITY OF SUCH DAMAGE.
"""
"""
Keti mote protocol implementation and sMAP driver.

@author Stephen Dawson-Haggerty <stevedh@eecs.berkeley.edu>
"""

import datetime

from smap.archiver.client import SmapClient
from smap.contrib import dtutil
import numpy as np
import matplotlib.pyplot as plt

c = SmapClient('http://ar1.openbms.org:8079')

HOURS = 5
RATES = [#("#", 10), 
         ("ppm", 5), ("C", 5)]

prrs = []
for unit, rate in RATES:
    counts = c.query(("apply count to data in now -%ih, now "
                      "limit -1 streamlimit 1000 where "
                      "Properties/UnitofMeasure = '%s' and "
                      "Metadata/SourceName = 'KETI Motes'") %
                     (HOURS, unit))
    for v in counts:
        r = np.array(v['Readings'])
        if len(r):
            prrs.append(np.sum(r[:, 1]) / (3600 * (HOURS) / rate))

plt.hist(prrs, bins=25)
plt.show()
