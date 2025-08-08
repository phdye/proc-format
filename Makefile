
test: python-tests emacs-tests

python-tests py-tests pytest :
	PYTHONPATH=src pytest tests

emacs-tests e-tests etest :
	emacs --batch -l tests/test_exec_sql_parser.el -f ert-run-tests-batch-and-exit

