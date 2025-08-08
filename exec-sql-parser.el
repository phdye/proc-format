;;; exec-sql-parser.el --- Parse EXEC SQL blocks -*- lexical-binding: t; -*-

;; This file is part of the proc-format project.

;;; Commentary:

;; Provides a reusable component for detecting and capturing Oracle Pro*C
;; EXEC SQL constructs.  It mirrors the Python implementation used by the
;; formatter while exposing a customizable registry of patterns.  By default
;; the parser ignores constructs appearing inside C comments, though this
;; behaviour can be bypassed through `exec-sql-parser-ignore-comments'.

;;; Code:

(require 'cl-lib)

(defgroup exec-sql-parser nil
  "Utilities for parsing EXEC SQL blocks."
  :group 'languages)

(defcustom exec-sql-parser-ignore-comments t
  "When non-nil, `exec-sql-parser-parse' skips EXEC SQL inside C comments."
  :type 'boolean
  :group 'exec-sql-parser)

(defcustom exec-sql-parser-registry
  '(("ORACLE-Single-Line [1]"
     :pattern "^EXEC ORACLE\\b.*;"
     :action #'identity)
    ("ORACLE-Single-Line [2]"
     :pattern "^EXEC ORACLE\\b.*;"
     :action #'identity)
    ("ORACLE-Multi-Line"
     :pattern "^EXEC ORACLE\\b"
     :end-pattern ".*;"
     :action #'identity)
    ("EXECUTE-BEGIN-END-Multi-Line"
     :pattern "^EXEC SQL EXECUTE\\b"
     :end-pattern "END-EXEC;"
     :action #'identity)
    ("STATEMENT-Single-Line [1]"
     :pattern "^EXEC SQL\\b.*;"
     :action #'identity)
    ("STATEMENT-Single-Line [2]"
     :pattern "^EXEC SQL\\b.*;"
     :action #'identity)
    ("STATEMENT-Multi-Line"
     :pattern "^EXEC SQL\\b"
     :end-pattern ".*;"
     :action #'identity)
    ("END-EXEC"
     :pattern "^END-EXEC\\b.*;"
     :action #'identity)
    ("END"
     :pattern "^END\\b.*;"
     :action #'identity
     :error t))
  "Registry mapping EXEC SQL constructs to regexps and handlers.

Each entry is of the form (CONSTRUCT :pattern REGEXP [:end-pattern REGEXP]
:action FUNCTION [:error VALUE]).  The ACTION receives the list of lines
belonging to the construct and should return the processed lines."
  :type 'sexp
  :group 'exec-sql-parser)

(defconst exec-sql-parser--marker-prefix "// EXEC SQL MARKER")

(defun exec-sql-parser--marker (n)
  "Return a marker string for N."
  (format "%s:%d:" exec-sql-parser--marker-prefix n))

(defun exec-sql-parser--action-fn (action)
  "Return callable function from ACTION.

ACTION may be a symbol, a lambda, or a `(function SYMBOL)` form
resulting from using `#'` inside a quoted list.  In the latter case
`plist-get` returns the cons cell `(function SYMBOL)`, which is not
directly callable.  This helper normalizes that representation so the
result can be passed to `funcall` without raising an `invalid-function`
error."
  (if (and (consp action) (eq (car action) 'function))
      (cadr action)
    action))

(defun exec-sql-parser--strip-comments (string)
  "Return STRING with C style comments removed."
  (with-temp-buffer
    (insert string)
    ;; Remove block comments
    (goto-char (point-min))
    (while (re-search-forward "/\\*\(?:.\|\n\)*?\\*/" nil t)
      (replace-match ""))
    ;; Remove line comments
    (goto-char (point-min))
    (while (re-search-forward "//.*" nil t)
      (replace-match ""))
    (buffer-string)))

;;;###autoload
(defun exec-sql-parser-parse (content)
  "Parse CONTENT capturing EXEC SQL blocks.

Returns a list (OUTPUT CAPTURED) where OUTPUT is a list of lines with markers
replacing EXEC SQL blocks, and CAPTURED is the list of captured blocks."
  (let* ((text (if exec-sql-parser-ignore-comments
                   (exec-sql-parser--strip-comments content)
                 content))
         (lines (split-string text "\n"))
         (captured '())
         (output '())
         (inside nil)
         (current-block nil)
         (current-handler nil)
         (current-construct nil)
         (marker-counter 1))
    (dolist (line lines)
      (let ((stripped (string-trim line)))
        (if inside
            (progn
              (push line current-block)
              (when (and (plist-get current-handler :end-pattern)
                         (string-match-p (plist-get current-handler :end-pattern)
                                         stripped))
                (push (funcall (exec-sql-parser--action-fn
                                (plist-get current-handler :action))
                               (nreverse current-block))
                      captured)
                (push (exec-sql-parser--marker marker-counter) output)
                (setq marker-counter (1+ marker-counter)
                      inside nil
                      current-block nil
                      current-handler nil
                      current-construct nil)))
          (let ((matched nil))
            (dolist (entry exec-sql-parser-registry)
              (let ((construct (car entry))
                    (details (cdr entry)))
                (when (and (not matched)
                           (string-match-p (plist-get details :pattern)
                                           stripped))
                  (setq matched t)
                  (if (plist-get details :end-pattern)
                      (setq inside t
                            current-block (list line)
                            current-handler details
                            current-construct construct)
                    (push (funcall (exec-sql-parser--action-fn
                                    (plist-get details :action))
                                   (list line))
                          captured)
                    (push (exec-sql-parser--marker marker-counter) output)
                    (setq marker-counter (1+ marker-counter))))))
            (unless matched
              (push line output))))))
    (when inside
      (push (funcall (exec-sql-parser--action-fn
                      (plist-get current-handler :action))
                     (nreverse current-block))
            captured)
      (push (exec-sql-parser--marker marker-counter) output))
      (list (nreverse output) (nreverse captured))))

(provide 'exec-sql-parser)

;;; exec-sql-parser.el ends here
