(require 'ert)
(load-file "exec-sql-parser.el")

(ert-deftest exec-sql-parser-captures-execute-variants ()
  (let* ((path (expand-file-name "data/exec_sql_variants.pc" "tests"))
         (content (with-temp-buffer (insert-file-contents path) (buffer-string)))
         (res (exec-sql-parser-parse content)))
    (should (= (length (cadr res)) 9))))

(provide 'test-exec-sql-parser)
