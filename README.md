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