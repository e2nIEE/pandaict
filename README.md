Copyright (c) 2024-2026 by University of Kassel and Fraunhofer Institute for Energy Economics and Energy System Technology (IEE) Kassel and individual contributors
Licensed under BSD-3-Clause

Correct PYTHONPATH setting: 

Windows:
- set PYTHONPATH=%PYTHONPATH%;<pandaict root path>\src;<pandaict root path>\src\pandaict

Linux: 
- export PYTHONPATH="$PYTHONPATH:<pandaict root path>/src:<pandaict root path>/src/pandaict"

Test pandaict (from pandaict root dir): 

Windows: 
- python test\pandaict_test.py 

Linux: 
- python test/pandaict_test.py 