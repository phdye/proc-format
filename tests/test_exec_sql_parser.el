(require 'ert)
(load-file "exec-sql-parser.el")

(defun write-cfg (dir content)
  (with-temp-file (expand-file-name ".exec-sql-parser" dir)
    (insert content)))

(ert-deftest exec-sql-parser-registry-override-and-disable ()
  (let* ((base (make-temp-file "reg" t))
         (sub (expand-file-name "sub" base)))
    (unwind-protect
        (progn
          (write-cfg base "{\"STATEMENT-Single-Line [1]\": null}")
          (make-directory sub)
          (write-cfg sub "{\"CUSTOM\": {\"pattern\": \"EXEC SQL TEST;\", \"end_pattern\": \"END;\"}}")
          (let ((reg (exec-sql-parser-load-registry sub)))
            (should (not (assoc \"STATEMENT-Single-Line [1]\" reg)))
            (let ((custom (assoc \"CUSTOM\" reg)))
              (should custom)
              (should (equal (plist-get (cdr custom) :pattern) "EXEC SQL TEST;"))
              (should (plist-get (cdr custom) :end-pattern)))))
      (delete-directory base t)))

(ert-deftest exec-sql-parser-registry-no-parents ()
  (let* ((base (make-temp-file "reg" t))
         (sub (expand-file-name "sub" base)))
    (unwind-protect
        (progn
          (write-cfg base "{\"STATEMENT-Single-Line [1]\": null}")
          (make-directory sub)
          (let ((reg (exec-sql-parser-load-registry sub nil)))
            (should (assoc \"STATEMENT-Single-Line [1]\" reg))))
      (delete-directory base t)))

(ert-deftest exec-sql-parser-registry-root-stops-search ()
  (let* ((base (make-temp-file "reg" t))
         (mid (expand-file-name "mid" base))
         (sub (expand-file-name "sub" mid)))
    (unwind-protect
        (progn
          (write-cfg base "{\"STATEMENT-Single-Line [1]\": null}")
          (make-directory mid)
          (write-cfg mid "{\"root\": true}")
          (make-directory sub)
          (let ((reg (exec-sql-parser-load-registry sub)))
            (should (assoc \"STATEMENT-Single-Line [1]\" reg))))
      (delete-directory base t)))

(provide 'test-exec-sql-parser)
