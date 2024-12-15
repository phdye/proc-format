Given original code:

```
#include <stdio.h>

EXEC SQL BEGIN DECLARE SECTION;
    char firstName[50];
    char lastName[50];
    int id;
EXEC SQL END DECLARE SECTION;

void fetchEmployeeName(int employeeId) {
        id = employeeId;
            int foo = 0;

      EXEC SQL
        SELECT first_name, last_name
        INTO :firstName, :lastName
        FROM employees
        WHERE employee_id = :id;

printf("Employee Name: %s %s\n", firstName, lastName);
}
```
There are two segments of EXEC SQL:

First:

```
EXEC SQL BEGIN DECLARE SECTION;
```

Second:

```
EXEC SQL END DECLARE SECTION;
```

Third:

```
      EXEC SQL
        SELECT first_name, last_name
        INTO :firstName, :lastName
        FROM employees
        WHERE employee_id = :id;
```

Leaving the following C code with EXEC SQL markers with ordinal

```
#include <stdio.h>

{ // EXEC SQL MARKER :1:
    char firstName[50];
    char lastName[50];
    int id;
} // EXEC SQL MARKER :2:

void fetchEmployeeName(int employeeId) {
        id = employeeId;
            int foo = 0;

// EXEC SQL MARKER :3:

printf("Employee Name: %s %s\n", firstName, lastName);
}
```

After formating, the C code should look like, presumming indent of 2:
```
#include <stdio.h>

{
  char firstName[50];
  char lastName[50];
  int id;
}

void fetchEmployeeName(int employeeId) {
  id = employeeId;
  int foo = 0;

  // EXEC SQL MARKER :3:

  printf("Employee Name: %s %s\n", firstName, lastName);
}
```

And with the EXEC SQL merged properly back in and aligned:
```
#include <stdio.h>

EXEC SQL BEGIN DECLARE SECTION;
  char firstName[50];
  char lastName[50];
  int id;
EXEC SQL END DECLARE SECTION;

void fetchEmployeeName(int employeeId) {
  id = employeeId;
  int foo = 0;

  EXEC SQL
      SELECT first_name, last_name
      INTO :firstName, :lastName
      FROM employees
      WHERE employee_id = :id;

  printf("Employee Name: %s %s\n", firstName, lastName);
}
```

Note that the necessary EXEC SQL multi-line alignment offset
calculated by the column of the EXEC SQL MARKER vs
the original column of the extracted EXEC SQL statement.
