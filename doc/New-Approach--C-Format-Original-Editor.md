### New Approach

Let's do the C formatting in the original document editor.

We're keeping all of the functionality but shifting around where things go and added a few additional save points

High level functional steps:
1. Save contents of original file contents to a backup file (as done now)
   - but definitely a fata error if it does not succeed 
2. Copy contents of original document to a temporary document
3. Verify that original document, temporary document and backup file all have
   - same number of characters, the same number of lines, and MD5 checksum
4. Delete all lines from the original document
5. Loop through all lines of the temporary document scanning for EXEC SQL
   - Non EXEC SQL lines are copied to the original document as-is
   - EXEC SQL lines :
     - are numbered and saved in memory
     - a numbered EXEC-SQL-marker line os copied to the original document
6. Initiate formating with the expectation that it will apply to the original document window
7. Restore EXEC SQL segments in their corresponding numbered spots
8. Verify that original document editor has similiar size (withing 0.5%) of backup
   - possibly create a canonical compare that disregards newlines and white space
     - Given two files a & b:
       - Copy a & b to temporary documents u & v, respectively.
       - Replace all newlines in u & v with a single space
       - collapse all whitespace into a single space
       - If the u & v are identical, a & b are functionally identical
9. Retain the backup file, but cleanup any other intermediate objects

- Wrap the 2-8 in a try-except block that restores the backup file if anything fails or is off.
- Retain all of the detailed logging in the current formats.
- Detailed logging of every step
- High level user status messages of progress
