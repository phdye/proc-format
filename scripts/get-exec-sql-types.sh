#!/bin/bash

# start(.*?)(?:end)?$

read -r -d '' filter <<__END__
	# Remove comments
	s:/[*].*[*]/::g;
	s:.*[*]/::g;
	s://.*$::g;
	#
	# Collapse all spans of whitespace to a single space character
	s/\s\s*/ /g;
	# Remove any blank lines
	/^\s*$/D;
	# Remove all leading whitespace
	s/^ //g;
	# Remove all trailing whitespace
	s/ $//g;
	#
	# No need for \s+ below due to collapse
 	#
	# -- do not presume '^EXEC SQL ...' as that would hide problems
 	#
 	# Canonicalize some common features
 	#
	# Presume host-variables always used, never literal strings
	#
	# Host Variable,
	s/ :\(\w[_a-zA-Z0-9]*\)\b/ :hostvar/g;
	#
	# SQL Identifier -- variable name, presummed all lowercase by convention in Pro*C
	#   Identifiers can contain letters, numbers, dollar signs, underscores, and number signs.
	#   They cannot contain spaces, hyphens, or slashes. 
	s/ [a-z][#_a-zA-Z0-9\$]*\b/ identifier/g;
        #
		      s/ CONNECT :hostvar\b/ CONNECT :connect/g;
	  s/ :hostvar IDENTIFIED BY :hostvar\b/ CONNECT :connect/g;
		        s/ USING :hostvar\b/ USING :db-string/g;
		           s/ AT :hostvar\b/ AT :db-name/g;
		         s/ OPEN identifier\b/ OPEN csr/g;
		        s/ FETCH identifier\b/ FETCH csr/g;
		        s/ CLOSE identifier\b/ CLOSE csr/g;
	#
		       s/ SELECT .*/ sql-query/g;
	#
	# WORK is optional with no functional effect
		       s/ COMMIT WORK\b/ COMMIT/g;
		     s/ ROLLBACK WORK\b/ ROLLBACK/g;
	#
	# EXEC SQL ... constructs
	# -----------------------
        # While each one could be single or multi line, we favor the forms
	# we have seen most often. 
	#
	s/\b\(EXEC ORACLE OPTION\)\b\s*(\w.*)\s*[;]/EXEC ORACLE OPTION (...)/g;
	#
	# EXEC SQL WHENEVER SQLERROR CONTINUE / DO sql_error(1, "Connection error:");
	s/\b\(EXEC SQL WHENEVER SQLERROR CONTINUE\)\b\s*[;]/\1;/g;
	s/\b\(EXEC SQL WHENEVER SQLERROR DO\)\b\s*\(\w.*\)\s*[;]/\1 ...;/g;
	s/\b\(EXEC SQL WHENEVER NOT FOUND DO\)\b\s*\(\w.*\)\s*[;]/\1 ...;/g;
	#
	# EXEC SQL CONNECT { :user IDENTIFIED BY :oldpswd | :usr_psw }
	#   [[ AT { dbname | :host_variable }] USING :connect_string ]
	#      [ {ALTER AUTHORIZATION :newpswd  |  IN { SYSDBA | SYSOPER } MODE} ] ;
	#
	s/\b\(EXEC SQL CONNECT :connect AT :db\)\b\s*\(\w.*\)\s*[;]/\1 [...];/g;
	s/\b\(EXEC SQL CONNECT :connect AT :db\)\b\s*[;]/\1;/g;
	#
	# EXEC SQL OPEN :cursor_name FOR select_statement;
	s/\b\(EXEC SQL OPEN csr FOR\) \(\w.*\)\s*[;]/\1 sql-statement;/g;
	#
	# EXEC SQL FETCH cursor_name INTO :host_variable1, :host_variable2, ...;
	s/\b\(EXEC SQL FETCH csr INTO\) \s*\(:?\w.*\)\s*\([;]\)?/\1 host-variable(s)\3/g;
	s/\b\(EXEC SQL FETCH csr\)\b\(\w.*\b\)?\s*\([;]\)?/\1 ... \3/g;
	#
	s/\b\(EXEC SQL CLOSE csr\)\s*\([;]\)?/\1 csr\2/g;
	#
	#
	# EXEC SQL COMMIT [WORK] [RELEASE];
	s/\b\(EXEC SQL COMMIT\)\b\s*\(RELEASE\)?\s*[;]/\1 \2;/g;
	#
	# EXEC SQL ROLLBACK [WORK] TO SAVEPOINT savepoint;
	s/\b\(EXEC SQL ROLLBACK\) TO SAVEPOINT\b\s*\(\w.*\)\s*[;]/\1 [...];/g;
	# EXEC SQL ROLLBACK [WORK] [RELEASE];
	s/\b\(EXEC SQL ROLLBACK\)\b\s*\(\w.*\)\s*[;]/\1 [...];/g;
	#
	#
	# EXEC SQL AT <db-name> DECLARE/EXECUTE/COMMIT ...
	s/\b\(EXEC SQL AT :db-name DECLARE\) identifier\b/\1 csr/g;
	s/\b\(EXEC SQL AT :db-name DECLARE csr CURSOR FOR\) \(\w.*\)\s*\([;]\)?/\1 sql-query \3/g;
__END__

read -r -d '' unused <<__END__
	#

__END__

# echo "${filter}"

# echo -n "${filter}" | egrep -v '^\s*[#]' | tr -d '\t'

filter=$(echo -n "${filter}" | sed -e 's/^\s\s*//g;/^#/D' | /bin/tr -d '\t\n')

# echo "$filter"

grep EXEC "$@" | sed -e "${filter}" | sort -u
