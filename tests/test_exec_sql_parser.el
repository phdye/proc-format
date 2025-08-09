(require 'ert)
(load-file "exec-sql-parser.el")

(defun exec-sql-parser-test-restore (content segments)
  "Restore SEGMENTS into CONTENT replacing numbered markers.

CONTENT contains marker lines produced by `exec-sql-parser-parse'.
SEGMENTS is a list where each element is a list of lines replacing the
corresponding marker.  The restored text is returned as a single
string.  Errors are signaled when markers and segments do not align."
  (let ((lines (split-string content "\n"))
        (result '())
        (counter 1)
        (segs (copy-sequence segments)))
    (dolist (line lines)
      (let ((marker (exec-sql-parser--marker counter)))
        (if (string-match (concat "^\\(\\s-*\\)" (regexp-quote marker) "$") line)
            (progn
              (unless segs
                (error "Missing segment for marker %d" counter))
              (let* ((indent (match-string 1 line))
                     (seg (pop segs)))
                (dolist (seg-line seg)
                  (push (concat indent seg-line) result)))
              (setq counter (1+ counter)))
          (push line result))))
    (when segs
      (error "Unused segments remain"))
    (mapconcat #'identity (nreverse result) "\n")))

(ert-deftest exec-sql-parser-captures-execute-variants ()
  (let* ((path (expand-file-name "data/exec_sql_variants.pc" "tests"))
         (content (with-temp-buffer (insert-file-contents path) (buffer-string)))
         (res (exec-sql-parser-parse content)))
    (should (= (length (cadr res)) 9))))

(ert-deftest exec-sql-parser-captures-at-clauses ()
  (let* ((lines '("EXEC SQL INCLUDE SQLCA;"
                 ""
                 "void call(char * alias_arg) {"
                 "    EXEC SQL BEGIN DECLARE SECTION;"
                 "    char * gl_server_alias = alias_arg;"
                 "    EXEC SQL END DECLARE SECTION;"
                 ""
                 "    EXEC SQL AT :gl_server_alias EXECUTE"
                 "    BEGIN"
                 "        make_call();"
                 "    END;"
                 "    END-EXEC;"
                 "}"))
         (content (mapconcat #'identity lines "\n"))
         (res (exec-sql-parser-parse content)))
    (should (cl-some (lambda (blk)
                       (string-match-p "EXEC SQL AT" (car blk)))
                     (cadr res)))))

(ert-deftest exec-sql-parser-multi-line-terminated-at-eof ()
  (let* ((lines '("EXEC SQL" "SELECT * FROM t"))
         (content (mapconcat #'identity lines "\n"))
         (res (exec-sql-parser-parse content)))
    (should (equal (car res) (list (exec-sql-parser--marker 1))))
    (should (equal (cadr res) (list lines)))))

(ert-deftest exec-sql-parser-load-registry-override-and-disable ()
  (let ((base (make-temp-file "reg" t)))
    (unwind-protect
        (progn
          (with-temp-file (expand-file-name ".exec-sql-parser" base)
            (insert "{\"STATEMENT-Single-Line [1]\": null}"))
          (let* ((sub (expand-file-name "sub" base))
                 (cfg (expand-file-name ".exec-sql-parser" sub)))
            (make-directory sub)
            (with-temp-file cfg
              (insert "{\"CUSTOM\": {\"pattern\": \"EXEC SQL TEST;\", \"end_pattern\": \"END;\"}}"))
            (let ((reg (exec-sql-parser-load-registry sub)))
              (should-not (assoc "STATEMENT-Single-Line [1]" reg))
              (let ((custom (assoc "CUSTOM" reg)))
                (should custom)
                (should (string= (plist-get (cdr custom) :pattern)
                                 "EXEC SQL TEST;"))
                (should (plist-get (cdr custom) :end-pattern))))))
      (delete-directory base t))))

(ert-deftest exec-sql-parser-load-registry-root-stops-search ()
  (let ((base (make-temp-file "reg" t)))
    (unwind-protect
        (progn
          (with-temp-file (expand-file-name ".exec-sql-parser" base)
            (insert "{\"STATEMENT-Single-Line [1]\": null}"))
          (let* ((mid (expand-file-name "mid" base))
                 (sub (expand-file-name "sub" mid)))
            (make-directory mid)
            (with-temp-file (expand-file-name ".exec-sql-parser" mid)
              (insert "{\"root\": true}"))
            (make-directory sub)
            (let ((reg (exec-sql-parser-load-registry sub)))
              (should (assoc "STATEMENT-Single-Line [1]" reg)))))
      (delete-directory base t))))

(ert-deftest exec-sql-parser-restore-blocks-with-indent ()
  (let* ((marker (exec-sql-parser--marker 1))
         (content (format "void f()\n{\n    %s\n}" marker))
         (segments '(("EXEC SQL SELECT 1;" "END-EXEC;")))
         (restored (exec-sql-parser-test-restore content segments))
         (expected "void f()\n{\n    EXEC SQL SELECT 1;\n    END-EXEC;\n}"))
    (should (string= restored expected))))

(ert-deftest exec-sql-parser-restore-blocks-missing-segment ()
  (let* ((marker (exec-sql-parser--marker 1))
         (segments '(("EXEC SQL SELECT 1;") ("EXEC SQL SELECT 2;"))))
    (should-error (exec-sql-parser-test-restore marker segments))))

(ert-deftest exec-sql-parser-get-and-goto-next ()
  (with-temp-buffer
    (insert "void f(){\nEXEC SQL SELECT 1;\nEXEC SQL SELECT 2;\n}\n")
    (goto-char (point-min))
    (let ((first (exec-sql-get-next)))
      (should first)
      (should (string= (plist-get first :type) "STATEMENT-Single-Line [1]"))
      (should (= (plist-get first :offset) 10))
      (should (= (plist-get first :length) 18))
      (should (equal (plist-get first :start) '(2 . 0)))
      (should (equal (plist-get first :end) '(2 . 17))))
    (goto-char (point-min))
    (let ((g1 (exec-sql-goto-next)))
      (should g1)
      (should (equal (point) (+ (point-min) (plist-get g1 :offset))))
      (let ((g2 (exec-sql-goto-next)))
        (should g2)
        (should (equal (point) (+ (point-min) (plist-get g2 :offset))))
        (should (= (plist-get g2 :offset) 29))))))

(ert-deftest exec-sql-parser-get-next-across-types ()
  "`exec-sql-get-next' should return the earliest statement regardless of construct order."
  (with-temp-buffer
    (insert "EXEC SQL INCLUDE SQLCA;\nEXEC ORACLE OPTION (HOLD_CURSOR=YES);\n")
    (goto-char (point-min))
    (let ((info (exec-sql-get-next)))
      (should info)
      (should (string= (plist-get info :type) "STATEMENT-Single-Line [1]"))
      (should (= (plist-get info :offset) 0)))))

(ert-deftest exec-sql-parser-count-remaining-none ()
  (with-temp-buffer
    (insert "int main(){return 0;}\n")
    (goto-char (point-min))
    (let ((pos (point)))
      (should (= 0 (exec-sql-count-remaining)))
      (should (= pos (point))))))

(ert-deftest exec-sql-parser-count-remaining-full-buffer ()
  (with-temp-buffer
    (insert "EXEC SQL SELECT 1;\nEXEC SQL SELECT 2;\nEXEC SQL SELECT 3;\n")
    (goto-char (point-min))
    (let ((pos (point)))
      (should (= 3 (exec-sql-count-remaining)))
      (should (= pos (point))))))

(ert-deftest exec-sql-parser-count-remaining-after-first ()
  (with-temp-buffer
    (insert "EXEC SQL SELECT 1;\nEXEC SQL SELECT 2;\nEXEC SQL SELECT 3;\n")
    (goto-char (point-min))
    (exec-sql-goto-next)
    (let ((pos (point)))
      (should (= 2 (exec-sql-count-remaining)))
      (should (= pos (point))))))

(ert-deftest exec-sql-parser-count-remaining-region ()
  (with-temp-buffer
    (let ((transient-mark-mode t))
      (insert "EXEC SQL SELECT 1;\nEXEC SQL SELECT 2;\nEXEC SQL SELECT 3;\n")
      (goto-char (point-min))
      (search-forward "EXEC SQL SELECT 2;")
      (forward-line 1)
      (set-mark (point))
      (goto-char (point-min))
      (activate-mark)
      (let ((pos (point)))
        (should (= 2 (exec-sql-count-remaining)))
        (should (= pos (point))))
      (deactivate-mark))))

(ert-deftest exec-sql-parser-count-remaining-region-inverse ()
  (with-temp-buffer
    (let ((transient-mark-mode t))
      (insert "EXEC SQL SELECT 1;\nEXEC SQL SELECT 2;\n")
      (goto-char (point-min))
      (set-mark (point))
      (search-forward "EXEC SQL SELECT 2;")
      (activate-mark)
      (let ((pos (point)))
        (should (= 0 (exec-sql-count-remaining)))
        (should (= pos (point))))
      (deactivate-mark))))

(ert-deftest exec-sql-parser-count-remaining-stress ()
  (with-temp-buffer
    (dotimes (_ 200)
      (insert "EXEC SQL SELECT 1;\n"))
    (goto-char (point-min))
    (let ((pos (point)))
      (should (= 200 (exec-sql-count-remaining)))
      (should (= pos (point))))))

(ert-deftest exec-sql-parser-count-three ()
  (with-temp-buffer
    (let ((transient-mark-mode t))
      (insert "
#define SUCCESS 0
#define FAIL    1
 
EXEC SQL INCLUDE SQLCA;

#define OTHER  1

void main(int argc, char **argv) {

  EXEC SQL WHENEVER SQLERROR DO sql_error(1, "Error main()");

  EXEC SQL SELECT 1;
")
      (goto-char (point-min))
      (search-forward "EXEC SQL SELECT 2;")
      (forward-line 1)
      (set-mark (point))
      (goto-char (point-min))
      (activate-mark)
      (let ((pos (point)))
        (should (= 3 (exec-sql-count-remaining)))
        (should (= pos (point))))
      (deactivate-mark))))

(provide 'test-exec-sql-parser)
