{{source}} ({% if version.epoch %}{{version.epoch}}:{% endif %}{{version.upstream}}{% if version.debian %}-{{version.debian}}{% endif %}) {{suite}}; urgency={{urgency}}

  * Test: {{testname}}
  * Suppress "should close ITP bug" messages.  (Closes: #123456)

 -- {{maintainer}}  {{date}}
