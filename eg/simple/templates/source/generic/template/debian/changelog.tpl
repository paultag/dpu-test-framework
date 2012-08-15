{{src_pkg}} ({{version.upstream}}{% if version.debian %}-{{version.debian}}{% endif %}) {{suite}}; urgency={{urgency}}

  * Lintian Test Suite.
  * Test: {{testname}}

  * Suppress "should close ITP bug" messages.  (Closes: #123456)

 -- {{maintainer}}  {{get_date()}}
