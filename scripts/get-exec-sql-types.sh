#!/bin/bash

read -r -d '' filter <<__END__
	s/^\s*//g;
	s/\s\s*/ /g;
	s/ OPEN .*/ OPEN csr/g;
	s/ FETCH .*/ FETCH csr/g;
	s/ CLOSE .*/ CLOSE csr/g;
	s/ \(WHENEVER NOT FOUND DO\) .*/ \1 .../g;
	s/ \(WHENEVER SQLERROR DO\) .*/ \1 .../g;
        s/ AT [_:a-zA-Z0-9]* COMMIT.*/ AT <db> COMMIT/g;
        s/ AT [_:a-zA-Z0-9]* DECLARE [_:a-zA-Z0-9]* CURSOR FOR.*/ AT <db> DECLARE <csr> CURSOR FOR/g;
__END__

# echo "${filter}"

filter=$(echo -n "${filter}" | /bin/tr -d '\t\n')

# echo "$filter"

grep EXEC "$@" | sed -e "${filter}" | sort -u
