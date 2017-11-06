module Condor =
	autoload xfm
	let kv = key /[a-zA-Z0-9_]+/ . del /[ \t]*=[ \t]*/ " = " . store /[^ \t].*/
	let lns = (Util.empty | Util.comment | [ kv . del "\n" "\n" ])*
	let filter = (incl "/etc/condor/*") . (incl "/etc/condor/config.d/*") 
					. (incl "/tmp/aug-condor-debug")
	let xfm = transform lns filter

