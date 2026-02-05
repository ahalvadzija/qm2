import runpy
import sys
from unittest.mock import patch

def test_main_module_full_execution():
    with patch('qm2.app.main') as mock_main, \
         patch.object(sys, 'argv', ['qm2']): 
        
        runpy.run_module('qm2.__main__', run_name='__main__')
        
        assert mock_main.called