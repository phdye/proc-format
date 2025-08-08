
test: python-tests emacs-check-parens emacs-eval

python-tests py-tests pytest :
	PYTHONPATH=src pytest tests

emacs-eval e-eval :
	emacs --batch -Q -l exec-sql-parser.el --eval "(exec-sql-parser-parse \"EXEC SQL\nSELECT * FROM t\")"

emacs-check-parens e-parens :
	emacs --batch exec-sql-parser.el -f check-parens
