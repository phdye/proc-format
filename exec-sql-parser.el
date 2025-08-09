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
(require 'json)

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
    ;; EXEC SQL EXECUTE forms ordered to avoid masking
    ("EXECUTE-Block"
      :pattern "^EXEC SQL EXECUTE\\s-*$"
      :end-pattern "^END-EXEC;\\s-*$"
      :action #'identity)
    ("EXECUTE-Immediate-Multi"
      :pattern "^EXEC SQL EXECUTE IMMEDIATE\\b[^;]*$"
      :end-pattern ".*;\\s-*$"
      :action #'identity)
    ("EXECUTE-Prepared-Multi"
      :pattern "^EXEC SQL EXECUTE \(?!IMMEDIATE\)\\S-[^;]*$"
      :end-pattern ".*;\\s-*$"
      :action #'identity)
    ("EXECUTE-Immediate-Single [1]"
      :pattern "^EXEC SQL EXECUTE IMMEDIATE\\b[^;]*;\\s-*$"
      :action #'identity)
    ("EXECUTE-Immediate-Single [2]"
      :pattern "^EXEC SQL EXECUTE IMMEDIATE\\b[^;]*;\\s-*$"
      :action #'identity)
    ("EXECUTE-Prepared-Single [1]"
      :pattern "^EXEC SQL EXECUTE \(?!IMMEDIATE\)\\S-[^;]*;\\s-*$"
      :action #'identity)
    ("EXECUTE-Prepared-Single [2]"
      :pattern "^EXEC SQL EXECUTE \(?!IMMEDIATE\)\\S-[^;]*;\\s-*$"
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

;;;###autoload
(defun exec-sql-parser-load-registry (start-dir &optional search-parents)
  "Load EXEC SQL registry from START-DIR.

Searches for `.exec-sql-parser' files starting at START-DIR and
optionally its parents when SEARCH-PARENTS is non-nil.  Returns a
registry list compatible with `exec-sql-parser-registry'.  Entries set
to null remove the built-in definition while objects with at least a
`pattern' key add or override a definition.  A configuration file may
contain `root': t to stop searching parent directories."
  (let* ((dir (expand-file-name start-dir))
         (search (if (null search-parents) t search-parents))
         (registry (copy-tree exec-sql-parser-registry))
         (configs '()))
    (while dir
      (let ((cfg (expand-file-name ".exec-sql-parser" dir)))
        (when (file-regular-p cfg)
          (let* ((json-object-type 'alist)
                 (json-key-type 'string)
                 (json (ignore-errors (json-read-file cfg))))
            (push (or json '()) configs)
            (when (and json (cdr (assoc "root" json)))
              (setq search nil)))))
      (let ((parent (file-name-directory (directory-file-name dir))))
        (if (or (not search) (equal parent dir))
            (setq dir nil)
          (setq dir parent))))
    (dolist (data (nreverse configs))
      (dolist (entry data)
        (let ((name (car entry))
              (value (cdr entry)))
          (unless (string= name "root")
            (cond
             ((null value)
              (setq registry (cl-remove-if (lambda (e) (equal (car e) name))
                                           registry)))
             ((and (listp value) (assoc "pattern" value))
              (let* ((pattern (cdr (assoc "pattern" value)))
                     (end-pattern (cdr (assoc "end_pattern" value)))
                     (err (cdr (assoc "error" value)))
                     (plist (list :pattern pattern :action #'identity)))
                (when end-pattern
                  (setq plist (plist-put plist :end-pattern end-pattern)))
                (when err
                  (setq plist (plist-put plist :error err)))
                (setq registry (cl-remove-if (lambda (e) (equal (car e) name))
                                             registry))
                (push (cons name plist) registry))))))))
    registry))

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
    (while (re-search-forward "/\\*\\(?:.\\|\\n\\)*?\\*/" nil t)
      (replace-match ""))
    ;; Remove line comments
    (goto-char (point-min))
    (while (re-search-forward "//.*" nil t)
      (replace-match ""))
    (buffer-string)))

;;;###autoload
(defun exec-sql-parser-parse (content &optional registry)
  "Parse CONTENT capturing EXEC SQL blocks using REGISTRY.

Returns a list (OUTPUT CAPTURED) where OUTPUT is a list of lines with markers
replacing EXEC SQL blocks, and CAPTURED is the list of captured blocks.
REGISTRY defaults to `exec-sql-parser-registry`."
  (let* ((registry (or registry exec-sql-parser-registry))
         (text (if exec-sql-parser-ignore-comments
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
            (dolist (entry registry)
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

  (defun exec-sql-get-next (&optional registry)
  "Return metadata for the next EXEC SQL statement after point.

The return value is a plist containing the keys `:type',
`:offset', `:length', `:start' and `:end'.  When no statement is
found, nil is returned.  REGISTRY defaults to
`exec-sql-parser-registry'."
  (let* ((registry (or registry exec-sql-parser-registry))
         (result nil))
    (save-excursion
      (let ((start (point)))
        (while (and start (not result))
          (let ((candidate nil))
            (dolist (entry registry)
              (let* ((pattern (plist-get (cdr entry) :pattern))
                     (pattern (if (string-prefix-p "^" pattern)
                                  (concat "^\\s-*" (substring pattern 1))
                                pattern)))
                (goto-char start)
                (when (re-search-forward pattern nil t)
                  (let ((pos (match-beginning 0)))
                    (goto-char pos)
                    (skip-chars-forward " \t")
                    (setq pos (point))
                    (when (or (null candidate) (< pos (car candidate)))
                      (setq candidate (cons pos entry)))))))
            (if (null candidate)
                (setq start nil)
              (let ((pos (car candidate)))
                (if (and exec-sql-parser-ignore-comments
                         (nth 4 (syntax-ppss pos)))
                    (setq start (1+ pos))
                  (progn
                    (goto-char pos)
                    (setq result (list :pos pos :entry (cdr candidate))))))))))
    (when result
      (let* ((entry (plist-get result :entry))
             (start (plist-get result :pos))
             (type (car entry))
             end)
        (save-excursion
          (goto-char start)
          (if (plist-get (cdr entry) :end-pattern)
              (let ((end-re (plist-get (cdr entry) :end-pattern)))
                (if (re-search-forward end-re nil t)
                    (let ((match-start (match-beginning 0))
                          (match-end (match-end 0)))
                      (goto-char match-end)
                      (if (search-backward ";" match-start t)
                          (setq end (1+ (point)))
                        (setq end match-end)))
                  (setq end (point-max))))
            (when (re-search-forward ";" nil t)
              (setq end (point))))
        (list :type type
              :offset (- start (point-min))
              :length (- end start)
              :start (cons (line-number-at-pos start)
                           (save-excursion
                             (goto-char start)
                             (current-column)))
              :end (cons (line-number-at-pos (1- end))
                         (save-excursion
                           (goto-char (1- end))
                           (current-column))))))))
    ))

(defun exec-sql-goto-next (&optional registry)
  "Move point to the next EXEC SQL statement.

REGISTRY defaults to `exec-sql-parser-registry'.  The metadata
plist returned by `exec-sql-get-next' is returned.  Prior to
searching the buffer, point is advanced by one character so the
function may be called repeatedly to traverse statements."
  (interactive)
  (when (< (point) (point-max))
    (forward-line 1))
  (let ((info (exec-sql-get-next registry)))
    (when info
      (goto-char (+ (point-min) (plist-get info :offset))))
    info))

(defun exec-sql-count-remaining (&optional registry)
  "Return number of remaining EXEC SQL statements after point.

When a region is active, only the portion from point to the end of the
region is considered.  Internally uses `exec-sql-goto-next' to traverse
statements.  Point is restored to its original location after counting.
REGISTRY defaults to `exec-sql-parser-registry'."
  (interactive)
  (let ((count 0))
    (save-excursion
      (save-restriction
        (when (use-region-p)
          (narrow-to-region (point) (region-end)))
        (goto-char (point))
        (while (re-search-forward "^\\s-*EXEC SQL\\b.*;" nil t)
          (setq count (1+ count))
          (forward-line 1))))
    (when (called-interactively-p 'interactive)
      (message "%d" count))
    count))

(provide 'exec-sql-parser)

;;; exec-sql-parser.el ends here
