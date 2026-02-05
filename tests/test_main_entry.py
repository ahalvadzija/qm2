from unittest.mock import patch
import runpy

def test_main_module_full_execution():
    """
    runpy.run_module simulira pokretanje fajla kao da si kucao 'python -m qm2'
    """
    with patch('qm2.app.main') as mock_main:
        runpy.run_module('qm2.__main__', run_name='__main__')
        assert mock_main.called